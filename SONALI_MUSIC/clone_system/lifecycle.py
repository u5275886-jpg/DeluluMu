import asyncio
import logging
import time
from typing import Dict, Any, Optional
from pyrogram import Client
from pyrogram.errors import RPCError, TokenInvalid, AuthKeyUnregistered

import config
from SONALI_MUSIC.clone_system.registry import clone_registry
from SONALI_MUSIC.clone_system.validators import mask_token, sanitize_text
from SONALI_MUSIC.utils.database_clone import get_all_clones, update_clone_status, log_clone_error

logger = logging.getLogger(__name__)

class CloneLifecycleManager:
    def __init__(self):
        self.clients: Dict[int, Client] = {}
        self.starting_tasks: Dict[int, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self.max_start_concurrency = getattr(config, "MAX_CLONE_START_CONCURRENCY", 5)

    async def start_clone(self, clone_data: Dict[str, Any]) -> bool:
        bot_id = clone_data.get("bot_id")
        token = clone_data.get("bot_token") or clone_data.get("token")
        tenant_id = clone_data.get("tenant_id") or clone_data.get("owner_id")

        if not bot_id or not token:
            logger.error("Cannot start clone: missing bot_id or token")
            return False

        async with self._lock:
            if bot_id in self.clients and self.clients[bot_id].is_connected:
                logger.info(f"Clone bot {bot_id} is already connected.")
                return True

        masked = mask_token(token)
        logger.info(f"Starting clone bot ID {bot_id} (Token: {masked})...")

        try:
            client = Client(
                name=f"clone_{bot_id}",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                bot_token=token,
                in_memory=True,
            )

            # Bind handlers dynamically
            from SONALI_MUSIC.core.clone_manager import clone_manager
            clone_manager._register_handlers_to_client(client)

            await client.start()
            me = await client.get_me()

            async with self._lock:
                self.clients[me.id] = client

            await clone_registry.register(me.id, {
                "bot_id": me.id,
                "bot_username": me.username or "",
                "bot_name": me.first_name or "Cloned Bot",
                "owner_id": tenant_id,
                "token_reference": masked,
                "created_at": clone_data.get("created_at", time.time()),
                "last_activity": time.time(),
                "runtime_status": "running",
                "assistant_status": clone_data.get("assistant_status", "system"),
            })

            await update_clone_status(me.id, "running")
            logger.info(f"Successfully started clone bot @{me.username} ({me.id})")
            return True

        except (TokenInvalid, AuthKeyUnregistered) as e:
            err_msg = f"Invalid/Revoked Bot Token: {sanitize_text(str(e))}"
            logger.error(f"Clone {bot_id} failed startup: {err_msg}")
            await log_clone_error(bot_id, clone_data.get("bot_name", "Unknown"), err_msg)
            await update_clone_status(bot_id, "failed")
            return False
        except Exception as e:
            err_msg = f"Startup Error: {sanitize_text(str(e))}"
            logger.exception(f"Error starting clone bot {bot_id}")
            await log_clone_error(bot_id, clone_data.get("bot_name", "Unknown"), err_msg)
            await update_clone_status(bot_id, "failed")
            return False

    async def stop_clone(self, bot_id: int) -> bool:
        async with self._lock:
            client = self.clients.pop(bot_id, None)

        await clone_registry.unregister(bot_id)

        if client:
            try:
                if client.is_connected:
                    await client.stop()
                logger.info(f"Stopped clone bot client {bot_id}")
            except Exception as e:
                logger.warning(f"Error stopping client {bot_id}: {e}")

        await update_clone_status(bot_id, "stopped")
        return True

    async def startup_recovery(self):
        """Loads and starts saved clones up to max concurrency limit."""
        logger.info("Executing clone startup recovery...")
        all_clones = await get_all_clones()
        semaphore = asyncio.Semaphore(self.max_start_concurrency)

        async def _safe_start(c):
            async with semaphore:
                try:
                    await self.start_clone(c)
                except Exception as ex:
                    logger.error(f"Startup recovery failed for clone {c.get('bot_id')}: {ex}")

        tasks = [_safe_start(c) for c in all_clones if c.get("status") != "disabled"]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"Startup recovery complete. Active clones: {len(self.clients)}")

    async def shutdown_cleanup(self):
        logger.info("Executing clone shutdown cleanup...")
        async with self._lock:
            bot_ids = list(self.clients.keys())

        for b_id in bot_ids:
            await self.stop_clone(b_id)
        logger.info("All clone clients cleanly disconnected.")

clone_lifecycle = CloneLifecycleManager()
