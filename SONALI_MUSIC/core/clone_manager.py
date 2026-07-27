import asyncio
import logging
import functools
from typing import Dict, Optional
from pyrogram import Client
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from contextvars import ContextVar

import config
from SONALI_MUSIC import app
from SONALI_MUSIC.utils.database_clone import get_all_clones, update_clone_status, log_clone_error

logger = logging.getLogger(__name__)

# Context variable to hold reference to current active clone bot client in the executing async context.
current_clone_client = ContextVar("current_clone_client", default=None)

class CloneManager:
    def __init__(self):
        self.clones: Dict[int, Client] = {} # mapping bot_id -> Pyrogram Client
        self._patched = False

    def patch_app_properties(self):
        """
        Contextually monkeypatches app (main Sona client instance) to route actions and
        attribute lookups (id, username, mention, etc.) to the active cloned client
        whenever running inside a cloned handler context.
        """
        if self._patched:
            return

        app_class = type(app)

        # Patch properties
        for prop in ["id", "username", "mention", "name"]:
            orig_attr_name = f"_orig_{prop}"
            if not hasattr(app, orig_attr_name):
                # Backup original value
                setattr(app, orig_attr_name, getattr(app, prop, None))

                # We define a custom descriptor / property proxy
                class ContextPropertyProxy:
                    def __init__(self, name):
                        self.name = name
                    def __get__(self, obj, objtype=None):
                        clone = current_clone_client.get()
                        if clone is not None:
                            if self.name == "id":
                                return clone.me.id if clone.me else None
                            elif self.name == "username":
                                return clone.me.username if clone.me else None
                            elif self.name == "mention":
                                return clone.me.mention if clone.me else None
                            elif self.name == "name":
                                return (clone.me.first_name + " " + (clone.me.last_name or "")) if clone.me else ""
                        return getattr(app, f"_orig_{self.name}", None)

                setattr(app_class, prop, ContextPropertyProxy(prop))

        # Patch core Pyrogram async methods to delegate contextually
        methods_to_patch = [
            "send_message", "send_photo", "send_audio", "send_video",
            "send_animation", "send_document", "edit_message_text",
            "edit_message_caption", "edit_message_reply_markup",
            "delete_messages", "leave_chat", "get_chat", "get_chat_member"
        ]

        for method_name in methods_to_patch:
            orig_method = getattr(app, method_name, None)
            if orig_method and not hasattr(orig_method, "_cloned_patched"):
                # We wrap the original coroutine method
                def make_wrapper(m_name, o_method):
                    @functools.wraps(o_method)
                    async def wrapper(*args, **kwargs):
                        clone = current_clone_client.get()
                        if clone is not None:
                            clone_method = getattr(clone, m_name)
                            return await clone_method(*args, **kwargs)
                        return await o_method(*args, **kwargs)
                    wrapper._cloned_patched = True
                    return wrapper

                setattr(app, method_name, make_wrapper(method_name, orig_method))

        self._patched = True
        logger.info("Main bot client patched successfully for contextual clone execution.")

    def wrap_handler(self, handler, clone_client: Client):
        """
        Wraps Pyrogram dispatcher handlers so they set the ContextVar
        pointing to the clone client during their async execution thread.
        """
        if hasattr(handler, "callback"):
            orig_callback = handler.callback

            @functools.wraps(orig_callback)
            async def wrapped_callback(*args, **kwargs):
                token = current_clone_client.set(clone_client)
                try:
                    return await orig_callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in cloned bot {clone_client.me.username if clone_client.me else 'Unknown'} handler: {e}", exc_info=True)
                    await log_clone_error(
                        bot_id=clone_client.me.id if clone_client.me else 0,
                        bot_name=clone_client.me.first_name if clone_client.me else "Cloned Bot",
                        error_msg=str(e)
                    )
                finally:
                    current_clone_client.reset(token)

            handler.callback = wrapped_callback
        return handler

    def register_handlers_on_clone(self, clone_client: Client):
        """
        Copies all registered handlers (from message groups/callbacks)
        from the main app dispatcher to the cloned client dispatcher,
        wrapping them contextually.
        """
        for group_index, handlers in app.dispatcher.groups.items():
            for handler in handlers:
                # Copy the handler
                import copy
                cloned_handler = copy.copy(handler)
                self.wrap_handler(cloned_handler, clone_client)
                clone_client.dispatcher.add_handler(cloned_handler, group=group_index)

    async def start_clone(self, bot_token: str, tenant_id: int) -> Optional[Client]:
        """Dynamically starts a new cloned client."""
        self.patch_app_properties()

        logger.info("Initializing cloned Pyrogram client...")
        clone_client = Client(
            name=f"cloned_{bot_token.split(':')[0]}",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=bot_token,
            in_memory=True
        )

        try:
            await clone_client.start()
            me = clone_client.me
            logger.info(f"Cloned bot started successfully: @{me.username} (ID: {me.id})")

            # Register copied handlers
            self.register_handlers_on_clone(clone_client)

            self.clones[me.id] = clone_client
            await update_clone_status(me.id, "active")

            # Start custom assistant if configured
            try:
                from SONALI_MUSIC.utils.database_clone import get_clone_by_id
                from SONALI_MUSIC.core.call import Sona
                clone_db = await get_clone_by_id(me.id)
                if clone_db and clone_db.get("assistant_mode") == "custom":
                    custom_session = clone_db.get("custom_session")
                    if custom_session:
                        await Sona.start_custom_assistant(me.id, custom_session)
            except Exception as e:
                logger.error(f"Failed to start custom assistant for clone @{me.username}: {e}")

            return clone_client
        except Exception as e:
            logger.error(f"Failed to start cloned bot with token {bot_token[:10]}...: {e}")
            return None

    async def stop_clone(self, bot_id: int) -> bool:
        """Stops and removes an active cloned client."""
        if bot_id in self.clones:
            # Stop custom assistant if active
            try:
                from SONALI_MUSIC.core.call import Sona
                await Sona.stop_custom_assistant(bot_id)
            except Exception as e:
                logger.error(f"Failed to stop custom assistant for clone {bot_id}: {e}")

            client = self.clones[bot_id]
            try:
                await client.stop()
                logger.info(f"Cloned bot {bot_id} stopped.")
            except Exception as e:
                logger.error(f"Error while stopping cloned bot {bot_id}: {e}")
            del self.clones[bot_id]
            await update_clone_status(bot_id, "paused")
            return True
        return False

    async def start_all_clones(self):
        """Loads and runs all active cloned bots registered in MongoDB."""
        all_clones = await get_all_clones()
        logger.info(f"Found {len(all_clones)} cloned bots in database. Starting active ones...")
        for clone_data in all_clones:
            if clone_data.get("status") == "active":
                token = clone_data.get("bot_token")
                tenant_id = clone_data.get("tenant_id")
                if token:
                    await self.start_clone(token, tenant_id)
                    await asyncio.sleep(1) # Add delay to avoid Telegram rate limits on startup

    async def stop_all_clones(self):
        """Gracefully stops all running cloned bot instances."""
        logger.info("Stopping all cloned bots...")
        for bot_id in list(self.clones.keys()):
            await self.stop_clone(bot_id)

# Global singleton instance for the clone manager
clone_manager = CloneManager()
