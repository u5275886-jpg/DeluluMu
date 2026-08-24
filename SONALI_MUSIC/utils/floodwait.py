import asyncio
import logging
from typing import Callable, Any
from pyrogram.errors import FloodWait

logger = logging.getLogger(__name__)

async def handle_floodwait(coro_func: Callable, *args, **kwargs) -> Any:
    """Executes an async Pyrogram API call with automatic FloodWait pause and retry."""
    while True:
        try:
            return await coro_func(*args, **kwargs)
        except FloodWait as fw:
            wait_time = fw.value + 1
            logger.warning(f"FloodWait encountered: Pausing for {wait_time}s")
            await asyncio.sleep(wait_time)
        except Exception as e:
            raise e
