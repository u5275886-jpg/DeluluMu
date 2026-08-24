import logging
import time
from typing import List, Dict, Any
from SONALI_MUSIC.utils.database_clone import get_all_clones, delete_clone_bot
from SONALI_MUSIC.clone_system.lifecycle import clone_lifecycle

logger = logging.getLogger(__name__)

async def find_inactive_clones(days: int = 30) -> List[Dict[str, Any]]:
    all_clones = await get_all_clones()
    now = time.time()
    threshold = days * 86400

    inactive = []
    for c in all_clones:
        last_act = c.get("last_activity") or c.get("created_at") or 0
        if (now - last_act) > threshold:
            c["days_inactive"] = round((now - last_act) / 86400, 1)
            inactive.append(c)

    return inactive

async def purge_inactive_clones(days: int = 30) -> Dict[str, Any]:
    inactive_clones = await find_inactive_clones(days)
    purged_count = 0
    errors = []

    for clone in inactive_clones:
        bot_id = clone.get("bot_id")
        try:
            await clone_lifecycle.stop_clone(bot_id)
            await delete_clone_bot(bot_id)
            purged_count += 1
            logger.info(f"Purged inactive clone bot ID {bot_id} (Inactive > {days} days)")
        except Exception as e:
            err = f"Failed to purge clone {bot_id}: {e}"
            logger.error(err)
            errors.append(err)

    return {
        "purged_count": purged_count,
        "total_found": len(inactive_clones),
        "errors": errors
    }
