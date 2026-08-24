import asyncio
import logging
import time
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class CloneRegistry:
    def __init__(self):
        self._clones: Dict[int, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def register(self, bot_id: int, clone_info: Dict[str, Any]):
        async with self._lock:
            clone_info["last_activity"] = time.time()
            self._clones[bot_id] = clone_info

    async def unregister(self, bot_id: int) -> Optional[Dict[str, Any]]:
        async with self._lock:
            return self._clones.pop(bot_id, None)

    async def get(self, bot_id: int) -> Optional[Dict[str, Any]]:
        async with self._lock:
            return self._clones.get(bot_id)

    async def update_activity(self, bot_id: int):
        async with self._lock:
            if bot_id in self._clones:
                self._clones[bot_id]["last_activity"] = time.time()

    async def update_status(self, bot_id: int, status: str, error: Optional[str] = None):
        async with self._lock:
            if bot_id in self._clones:
                self._clones[bot_id]["runtime_status"] = status
                if error:
                    self._clones[bot_id]["last_error"] = error

    async def get_all(self) -> List[Dict[str, Any]]:
        async with self._lock:
            return list(self._clones.values())

    async def get_active(self, active_seconds: int = 2592000) -> List[Dict[str, Any]]: # Default 30 days
        now = time.time()
        async with self._lock:
            return [
                c for c in self._clones.values()
                if (now - c.get("last_activity", 0)) <= active_seconds
            ]

    async def get_inactive(self, inactive_seconds: int = 2592000) -> List[Dict[str, Any]]:
        now = time.time()
        async with self._lock:
            return [
                c for c in self._clones.values()
                if (now - c.get("last_activity", 0)) > inactive_seconds
            ]

clone_registry = CloneRegistry()
