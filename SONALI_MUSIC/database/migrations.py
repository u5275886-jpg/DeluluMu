import logging
import time
from SONALI_MUSIC.core.mongo import mongodb

logger = logging.getLogger(__name__)

async def run_database_migrations():
    """Ensure all clone database records contain standardized fields."""
    logger.info("Checking database migrations...")
    try:
        all_clones = await mongodb.cloned_bots.find({})
        now = time.time()
        for c in all_clones:
            bot_id = c.get("bot_id")
            updates = {}
            if "created_at" not in c:
                updates["created_at"] = now
            if "last_activity" not in c:
                updates["last_activity"] = now
            if "status" not in c:
                updates["status"] = "stopped"
            if "error_count" not in c:
                updates["error_count"] = 0

            if updates:
                await mongodb.cloned_bots.update_one({"bot_id": bot_id}, {"$set": updates})
        logger.info("Database schema migration verification completed.")
    except Exception as e:
        logger.error(f"Error executing database migrations: {e}")
