import time
import asyncio
import logging
from typing import Optional
from pyrogram.types import Message

logger = logging.getLogger(__name__)

class BroadcastProgressTracker:
    def __init__(self, message: Optional[Message], total: int, interval: float = 5.0):
        self.message = message
        self.total = total
        self.interval = interval
        self.last_update = 0.0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        self.floodwaits = 0
        self.start_time = time.time()

    async def update(self, success: bool = False, fail: bool = False, skip: bool = False, floodwait: bool = False, force: bool = False):
        if success:
            self.successful += 1
        if fail:
            self.failed += 1
        if skip:
            self.skipped += 1
        if floodwait:
            self.floodwaits += 1

        now = time.time()
        if not force and (now - self.last_update) < self.interval:
            return

        self.last_update = now
        if not self.message:
            return

        processed = self.successful + self.failed + self.skipped
        elapsed = round(now - self.start_time)
        mins, secs = divmod(elapsed, 60)
        time_str = f"{mins:02d}:{secs:02d}"

        text = (
            f"📢 **Broadcast Progress**\n\n"
            f"📊 **Progress:** {processed} / {self.total}\n"
            f"✅ **Sent:** {self.successful}\n"
            f"❌ **Failed:** {self.failed}\n"
            f"⏭ **Skipped:** {self.skipped}\n"
            f"⏳ **FloodWaits:** {self.floodwaits}\n"
            f"⏱ **Elapsed:** {time_str}\n"
        )
        try:
            await self.message.edit_text(text)
        except Exception as e:
            logger.debug(f"Progress update message edit failed: {e}")
