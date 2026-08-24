import logging
from SONALI_MUSIC.clone_system.lifecycle import clone_lifecycle
from SONALI_MUSIC.clone_system.registry import clone_registry
from SONALI_MUSIC.clone_system.statistics import get_system_clone_stats
from SONALI_MUSIC.clone_system.cleanup import find_inactive_clones, purge_inactive_clones

logger = logging.getLogger(__name__)

class CloneSystemManager:
    """Unified Facade for Clone System management."""
    def __init__(self):
        self.lifecycle = clone_lifecycle
        self.registry = clone_registry

    async def get_stats(self):
        return await get_system_clone_stats()

    async def find_inactive(self, days: int = 30):
        return await find_inactive_clones(days)

    async def purge_inactive(self, days: int = 30):
        return await purge_inactive_clones(days)

clone_sys_manager = CloneSystemManager()
