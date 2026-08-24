import asyncio
import logging
from typing import List, Dict, Any, Optional
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, PeerIdInvalid, ChatWriteForbidden

from SONALI_MUSIC.broadcast_system.cancellation import cancellation_manager
from SONALI_MUSIC.broadcast_system.rate_limiter import rate_limiter
from SONALI_MUSIC.broadcast_system.progress import BroadcastProgressTracker
from SONALI_MUSIC.database.broadcast_repository import broadcast_repo
from SONALI_MUSIC.utils.database_clone import cleanup_stale_chat, cleanup_stale_user

logger = logging.getLogger(__name__)

async def dispatch_broadcast_to_client(
    client: Client,
    job_id: str,
    target_ids: List[int],
    msg: Message,
    pin: bool = False,
    progress_tracker: Optional[BroadcastProgressTracker] = None,
    dry_run: bool = False
):
    is_cancelled_event = cancellation_manager._tokens.get(job_id)

    async def _send_worker(target_id: int):
        if is_cancelled_event and is_cancelled_event.is_set():
            if progress_tracker:
                await progress_tracker.update(skip=True)
            return

        if dry_run:
            await rate_limiter.throttle()
            if progress_tracker:
                await progress_tracker.update(success=True)
            return

        async with rate_limiter.semaphore:
            if is_cancelled_event and is_cancelled_event.is_set():
                if progress_tracker:
                    await progress_tracker.update(skip=True)
                return

            await rate_limiter.throttle()
            try:
                sent_msg = await msg.copy(target_id)
                if pin and sent_msg:
                    try:
                        await sent_msg.pin(disable_notification=False)
                    except Exception:
                        pass
                if progress_tracker:
                    await progress_tracker.update(success=True)
            except FloodWait as fw:
                wait_time = fw.value + 1
                logger.warning(f"Broadcast FloodWait on {target_id}: waiting {wait_time}s")
                if progress_tracker:
                    await progress_tracker.update(floodwait=True)
                await asyncio.sleep(wait_time)
                # Retry once after FloodWait
                try:
                    sent_msg = await msg.copy(target_id)
                    if pin and sent_msg:
                        try:
                            await sent_msg.pin(disable_notification=False)
                        except Exception:
                            pass
                    if progress_tracker:
                        await progress_tracker.update(success=True)
                except Exception:
                    if progress_tracker:
                        await progress_tracker.update(fail=True)
            except (UserIsBlocked, InputUserDeactivated):
                bot_me = getattr(client, "me", None)
                bot_id = bot_me.id if bot_me else 0
                await cleanup_stale_user(bot_id, target_id)
                if progress_tracker:
                    await progress_tracker.update(fail=True)
            except (PeerIdInvalid, ChatWriteForbidden):
                bot_me = getattr(client, "me", None)
                bot_id = bot_me.id if bot_me else 0
                await cleanup_stale_chat(bot_id, target_id)
                if progress_tracker:
                    await progress_tracker.update(fail=True)
            except Exception as ex:
                logger.debug(f"Broadcast error for target {target_id}: {ex}")
                if progress_tracker:
                    await progress_tracker.update(fail=True)

    tasks = [_send_worker(t_id) for t_id in target_ids]
    await asyncio.gather(*tasks, return_exceptions=True)
