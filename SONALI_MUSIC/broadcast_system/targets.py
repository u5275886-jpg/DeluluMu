from typing import List, Set, Dict, Any
from SONALI_MUSIC.utils.database import get_served_chats, get_served_users
from SONALI_MUSIC.utils.database_clone import (
    get_cloned_served_chats,
    get_cloned_served_users,
    get_main_bot_served_chats,
    get_main_bot_served_users,
    get_all_clones,
)

async def resolve_broadcast_targets(
    broadcast_type: str, # "main", "cbroadcast", "individual"
    target_type: str,    # "user", "group", "all", "owner"
    bot_id: int = None,
    dedup_mode: str = "GLOBAL_USER" # "PER_BOT", "GLOBAL_USER", "GLOBAL_CHAT"
) -> List[int]:
    targets: Set[int] = set()

    if broadcast_type == "main":
        if target_type in ["user", "all"]:
            users = await get_main_bot_served_users()
            targets.update(users)
        if target_type in ["group", "all"]:
            chats = await get_main_bot_served_chats()
            targets.update(chats)

    elif broadcast_type == "individual" and bot_id:
        if target_type in ["user", "all"]:
            users = await get_cloned_served_users(bot_id)
            targets.update(users)
        if target_type in ["group", "all"]:
            chats = await get_cloned_served_chats(bot_id)
            targets.update(chats)

    elif broadcast_type == "cbroadcast":
        all_clones = await get_all_clones()
        for clone in all_clones:
            c_id = clone.get("bot_id")
            if target_type == "owner":
                tenant_id = clone.get("tenant_id") or clone.get("owner_id")
                if tenant_id:
                    targets.add(tenant_id)
            else:
                if target_type in ["user", "all"]:
                    users = await get_cloned_served_users(c_id)
                    targets.update(users)
                if target_type in ["group", "all"]:
                    chats = await get_cloned_served_chats(c_id)
                    targets.update(chats)

    return list(targets)
