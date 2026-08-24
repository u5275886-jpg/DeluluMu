import time
import logging
from typing import Dict, Any, List, Optional
from SONALI_MUSIC.core.mongo import mongodb

logger = logging.getLogger(__name__)

clone_db = mongodb.cloned_bots
served_chats_db = mongodb.cloned_chats
served_users_db = mongodb.cloned_users

class CloneRepository:
    async def get_by_bot_id(self, bot_id: int) -> Optional[Dict[str, Any]]:
        return await clone_db.find_one({"bot_id": bot_id})

    async def get_by_token(self, bot_token: str) -> Optional[Dict[str, Any]]:
        return await clone_db.find_one({"token": bot_token})

    async def get_by_owner(self, owner_id: int) -> List[Dict[str, Any]]:
        return await clone_db.find({"tenant_id": owner_id})

    async def get_all(self) -> List[Dict[str, Any]]:
        return await clone_db.find({})

    async def save_clone(self, clone_data: Dict[str, Any]) -> bool:
        bot_id = clone_data.get("bot_id")
        now = time.time()
        clone_data["updated_at"] = now
        if "created_at" not in clone_data:
            clone_data["created_at"] = now
        if "last_activity" not in clone_data:
            clone_data["last_activity"] = now

        existing = await clone_db.find_one({"bot_id": bot_id})
        if existing:
            await clone_db.update_one({"bot_id": bot_id}, {"$set": clone_data})
        else:
            await clone_db.insert_one(clone_data)
        return True

    async def update_status(self, bot_id: int, status: str, last_error: Optional[str] = None) -> bool:
        update_fields = {"status": status, "updated_at": time.time()}
        if status == "running":
            update_fields["last_started"] = time.time()
        elif status == "stopped":
            update_fields["last_stopped"] = time.time()
        if last_error:
            update_fields["last_error"] = last_error

        await clone_db.update_one({"bot_id": bot_id}, {"$set": update_fields})
        return True

    async def update_last_activity(self, bot_id: int):
        await clone_db.update_one({"bot_id": bot_id}, {"$set": {"last_activity": time.time()}})

    async def delete_clone(self, bot_id: int) -> bool:
        await clone_db.delete_one({"bot_id": bot_id})
        await served_chats_db.delete_one({"bot_id": bot_id})
        await served_users_db.delete_one({"bot_id": bot_id})
        return True

clone_repo = CloneRepository()
