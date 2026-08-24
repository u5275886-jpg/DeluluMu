import config
import logging
from typing import Dict, Any, Optional
from pyrogram import Client
from pyrogram.types import Message

from SONALI_MUSIC.broadcast_system.cancellation import cancellation_manager
from SONALI_MUSIC.broadcast_system.targets import resolve_broadcast_targets
from SONALI_MUSIC.broadcast_system.progress import BroadcastProgressTracker
from SONALI_MUSIC.broadcast_system.dispatcher import dispatch_broadcast_to_client
from SONALI_MUSIC.database.broadcast_repository import broadcast_repo

logger = logging.getLogger(__name__)

class BroadcastManager:
    async def start_broadcast(
        self,
        client: Client,
        sender_id: int,
        broadcast_type: str, # "main", "cbroadcast", "individual"
        target_type: str,    # "user", "group", "all", "owner"
        message_to_send: Message,
        progress_message: Optional[Message] = None,
        pin: bool = False,
        bot_id: Optional[int] = None
    ) -> str:
        dry_run = getattr(config, "BROADCAST_DRY_RUN", False)
        targets = await resolve_broadcast_targets(broadcast_type, target_type, bot_id=bot_id)

        job_id = await broadcast_repo.create_job(
            sender_id=sender_id,
            broadcast_type=broadcast_type,
            target_type=target_type,
            total_targets=len(targets),
            content={"text": message_to_send.text or message_to_send.caption or "Media"},
            dry_run=dry_run
        )

        cancellation_manager.create_token(job_id)
        tracker = BroadcastProgressTracker(progress_message, total=len(targets))

        # Run dispatch in background task
        async def _run_job():
            try:
                await broadcast_repo.update_progress(job_id, 0, 0, 0, 0, status="RUNNING")
                await dispatch_broadcast_to_client(
                    client=client,
                    job_id=job_id,
                    target_ids=targets,
                    msg=message_to_send,
                    pin=pin,
                    progress_tracker=tracker,
                    dry_run=dry_run
                )

                final_status = "CANCELLED" if cancellation_manager.is_cancelled(job_id) else "COMPLETED"
                await tracker.update(force=True)
                await broadcast_repo.update_progress(
                    job_id,
                    tracker.successful,
                    tracker.failed,
                    tracker.skipped,
                    tracker.floodwaits,
                    status=final_status
                )
                await broadcast_repo.finalize_job(job_id, status=final_status, cancelled=(final_status == "CANCELLED"))
            except Exception as e:
                logger.exception(f"Broadcast job {job_id} failed: {e}")
                await broadcast_repo.finalize_job(job_id, status="FAILED", error_summary=[str(e)])
            finally:
                cancellation_manager.remove_token(job_id)

        import asyncio
        asyncio.create_task(_run_job())
        return job_id

broadcast_manager = BroadcastManager()
