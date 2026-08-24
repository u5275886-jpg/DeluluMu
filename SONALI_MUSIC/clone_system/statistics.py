import time
import psutil
import asyncio
from typing import Dict, Any, List
from SONALI_MUSIC.utils.database_clone import get_all_clones
from SONALI_MUSIC.clone_system.lifecycle import clone_lifecycle

async def get_system_clone_stats() -> Dict[str, Any]:
    all_clones = await get_all_clones()
    now = time.time()

    total = len(all_clones)
    running = 0
    stopped = 0
    failed = 0
    active_24h = 0
    active_7d = 0
    active_30d = 0

    for c in all_clones:
        status = c.get("status", "stopped")
        if status == "running":
            running += 1
        elif status == "failed":
            failed += 1
        else:
            stopped += 1

        last_act = c.get("last_activity") or c.get("created_at") or 0
        diff = now - last_act
        if diff <= 86400: # 24h
            active_24h += 1
        if diff <= 604800: # 7d
            active_7d += 1
        if diff <= 2592000: # 30d
            active_30d += 1

    # System info
    cpu_usage = psutil.cpu_percent(interval=None)
    ram_usage = psutil.virtual_memory().percent
    active_tasks = len([t for t in asyncio.all_tasks() if not t.done()])
    running_clients = len(clone_lifecycle.clients)

    return {
        "total_clones": total,
        "running_clones": running,
        "stopped_clones": stopped,
        "failed_clones": failed,
        "active_24h": active_24h,
        "active_7d": active_7d,
        "active_30d": active_30d,
        "inactive_30d": total - active_30d,
        "cpu_percent": cpu_usage,
        "ram_percent": ram_usage,
        "active_async_tasks": active_tasks,
        "active_clients_count": running_clients,
    }
