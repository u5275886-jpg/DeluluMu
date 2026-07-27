import random
import logging
from typing import Optional, List
from pyrogram import Client
from SONALI_MUSIC import userbot
import config

logger = logging.getLogger(__name__)

class AssistantPool:
    def __init__(self):
        # We hold mapping to the configured userbots from Sona userbot
        self._assistant_indices = [1, 2, 3, 4, 5]
        self._busy_assistants = set()

    def get_assistant_client(self, index: int) -> Optional[Client]:
        """Returns the Client instance for a given assistant index (1-5)."""
        if index == 1 and config.STRING1:
            return userbot.one
        elif index == 2 and config.STRING2:
            return userbot.two
        elif index == 3 and config.STRING3:
            return userbot.three
        elif index == 4 and config.STRING4:
            return userbot.four
        elif index == 5 and config.STRING5:
            return userbot.five
        return None

    def get_active_assistants(self) -> List[int]:
        """Returns list of active, configured assistant indices."""
        active = []
        if config.STRING1: active.append(1)
        if config.STRING2: active.append(2)
        if config.STRING3: active.append(3)
        if config.STRING4: active.append(4)
        if config.STRING5: active.append(5)
        return active

    async def check_assistant_health(self, index: int) -> bool:
        """Runs a heartbeat/ping check on a specific assistant."""
        client = self.get_assistant_client(index)
        if not client:
            return False
        try:
            if not client.is_connected:
                await client.connect()
            # Simple api check
            me = await client.get_me()
            return me is not None
        except Exception as e:
            logger.error(f"Assistant {index} health check failed: {e}")
            return False

    async def get_balanced_assistant(self, exclude_indices: Optional[List[int]] = None) -> int:
        """
        Retrieves an available assistant using load-balancing.
        Prioritizes assistants that are online and not marked busy.
        """
        active = self.get_active_assistants()
        if not active:
            raise RuntimeError("No assistants are configured in the system.")

        exclude = exclude_indices or []
        candidates = [idx for idx in active if idx not in exclude]

        # Filter out busy assistants if possible
        available = [idx for idx in candidates if idx not in self._busy_assistants]

        if not available:
            # If all are busy, clear busy markers or use any candidate
            available = candidates if candidates else active

        # Select randomly or sequentially for load distribution
        selected = random.choice(available)
        return selected

    def mark_busy(self, index: int):
        """Marks an assistant as busy with active playback."""
        self._busy_assistants.add(index)

    def mark_free(self, index: int):
        """Marks an assistant as free."""
        self._busy_assistants.discard(index)

    async def failover_switch(self, current_index: int) -> int:
        """
        Invoked when an assistant fails/disconnects during setup or playback.
        Finds a suitable replacement.
        """
        logger.warning(f"Failover triggered for Assistant {current_index}.")
        self.mark_busy(current_index) # Temporarily avoid re-assigning the failed assistant
        try:
            new_assistant = await self.get_balanced_assistant(exclude_indices=[current_index])
            return new_assistant
        except Exception:
            # Fallback to any active assistant
            active = self.get_active_assistants()
            if active:
                return active[0]
            raise RuntimeError("No assistant available for failover.")

# Singleton instance for assistant pool management
assistant_pool = AssistantPool()
