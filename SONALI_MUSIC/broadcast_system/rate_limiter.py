import asyncio
import random
import config

class BroadcastRateLimiter:
    def __init__(self):
        self.workers = getattr(config, "BROADCAST_WORKERS", 2)
        self.min_delay = getattr(config, "BROADCAST_MIN_DELAY", 0.2)
        self.max_delay = getattr(config, "BROADCAST_MAX_DELAY", 1.0)
        self.semaphore = asyncio.Semaphore(self.workers)

    async def throttle(self):
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)

rate_limiter = BroadcastRateLimiter()
