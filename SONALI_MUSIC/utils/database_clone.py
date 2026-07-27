import time
from typing import Dict, List, Optional, Union
from SONALI_MUSIC.core.mongo import mongodb

# Database collections setup
cloned_db = mongodb.cloned_bots
premium_db = mongodb.premium_users
broadcast_db = mongodb.broadcast_jobs
audit_db = mongodb.audit_trails
logs_db = mongodb.cloned_logs

# ----------------------------------------------------------------------
# 1. PREMIUM CONTROLS
# ----------------------------------------------------------------------

async def get_premium_user(user_id: int) -> Optional[Dict]:
    """Retrieves a user's premium subscription and tier status."""
    return await premium_db.find_one({"user_id": user_id})

async def add_premium_user(user_id: int, plan: str, duration_days: int) -> bool:
    """Activates or updates a premium subscription for a user."""
    expires_at = int(time.time()) + (duration_days * 86400) if duration_days > 0 else 0
    await premium_db.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "plan": plan, # "free", "basic", "pro", "elite"
                "expires_at": expires_at,
                "status": "active",
                "updated_at": int(time.time())
            }
        },
        upsert=True
    )
    return True

async def remove_premium_user(user_id: int) -> bool:
    """Cancels or deletes a premium subscription."""
    await premium_db.delete_one({"user_id": user_id})
    return True

async def check_premium_access(user_id: int) -> Dict:
    """
    Validates a user's plan and expiry.
    Returns plan details and boolean status.
    """
    user = await get_premium_user(user_id)
    if not user:
        return {"has_premium": False, "plan": "free", "permissions": {}}

    expires_at = user.get("expires_at", 0)
    current_time = int(time.time())

    if expires_at != 0 and current_time > expires_at:
        # Plan expired
        await premium_db.update_one({"user_id": user_id}, {"$set": {"status": "expired"}})
        return {"has_premium": False, "plan": "free", "permissions": {}}

    plan = user.get("plan", "free")

    # Permissions matrix based on plan
    permissions = {}
    if plan == "basic":
        permissions = {"custom_assistant": False, "custom_metadata": True, "limits": 1}
    elif plan == "pro":
        permissions = {"custom_assistant": True, "custom_metadata": True, "limits": 5}
    elif plan == "elite":
        permissions = {"custom_assistant": True, "custom_metadata": True, "limits": 9999}

    return {
        "has_premium": plan != "free",
        "plan": plan,
        "expires_at": expires_at,
        "permissions": permissions
    }

# ----------------------------------------------------------------------
# 2. CLONE CONTROLS
# ----------------------------------------------------------------------

async def get_clone_by_token(bot_token: str) -> Optional[Dict]:
    """Retrieves clone bot details via bot token."""
    return await cloned_db.find_one({"bot_token": bot_token})

async def get_clone_by_id(bot_id: int) -> Optional[Dict]:
    """Retrieves clone bot details via bot user ID."""
    return await cloned_db.find_one({"bot_id": bot_id})

async def get_user_clones(tenant_id: int) -> List[Dict]:
    """Retrieves all cloned bots created by a specific user (tenant)."""
    clones = []
    async for clone in cloned_db.find({"tenant_id": tenant_id}):
        clones.append(clone)
    return clones

async def save_clone_bot(
    tenant_id: int,
    bot_token: str,
    bot_id: int,
    bot_name: str,
    bot_username: str,
    assistant_id: int = 1,
    settings: Optional[Dict] = None
) -> bool:
    """Saves or updates a cloned bot in the system."""
    default_settings = {
        "title": f"{bot_name} Play",
        "branding_url": "https://litter.catbox.moe/vtsad2y91ytmincf.jpg",
        "welcome_text": "Welcome to my cloned music player bot!",
        "playback_preferences": "Direct",
        "queue_behavior": "Standard"
    }

    if settings:
        default_settings.update(settings)

    await cloned_db.update_one(
        {"bot_id": bot_id},
        {
            "$set": {
                "tenant_id": tenant_id,
                "bot_token": bot_token,
                "bot_name": bot_name,
                "bot_username": bot_username,
                "assistant_id": assistant_id,
                "settings": default_settings,
                "status": "active",
                "created_at": int(time.time()),
                "last_active": int(time.time())
            }
        },
        upsert=True
    )
    return True

async def delete_clone_bot(bot_id: int) -> bool:
    """Removes a cloned bot from the database."""
    await cloned_db.delete_one({"bot_id": bot_id})
    return True

async def update_clone_status(bot_id: int, status: str) -> bool:
    """Changes the status of a clone (e.g. active, paused, suspended)."""
    await cloned_db.update_one({"bot_id": bot_id}, {"$set": {"status": status}})
    return True

async def update_clone_settings(bot_id: int, settings: Dict) -> bool:
    """Updates a cloned bot's configuration/branding settings."""
    await cloned_db.update_one({"bot_id": bot_id}, {"$set": {"settings": settings}})
    return True

async def get_all_clones() -> List[Dict]:
    """Retrieves all active and inactive clones in the platform."""
    clones = []
    async for clone in cloned_db.find({}):
        clones.append(clone)
    return clones

# ----------------------------------------------------------------------
# 3. BROADCAST JOBS
# ----------------------------------------------------------------------

async def create_broadcast_job(sender_id: int, scope: str, content: Dict) -> str:
    """Stores a new broadcast job execution profile."""
    job_id = f"job_{int(time.time())}"
    await broadcast_db.insert_one({
        "job_id": job_id,
        "sender_id": sender_id,
        "scope": scope, # "all", "active", "premium"
        "content": content,
        "status": "queued",
        "delivery_report": {"success": 0, "failed": 0, "total": 0},
        "created_at": int(time.time())
    })
    return job_id

async def update_broadcast_report(job_id: str, success_count: int, failed_count: int, status: str):
    """Updates progress for broadcast tracking reports."""
    await broadcast_db.update_one(
        {"job_id": job_id},
        {
            "$set": {
                "status": status,
                "delivery_report.success": success_count,
                "delivery_report.failed": failed_count,
                "delivery_report.total": success_count + failed_count
            }
        }
    )

# ----------------------------------------------------------------------
# 4. AUDIT & ERROR TRAILS
# ----------------------------------------------------------------------

async def log_audit_trail(user_id: int, action: str, details: str):
    """Saves records of sensitive admin actions for security audit verification."""
    await audit_db.insert_one({
        "user_id": user_id,
        "action": action,
        "details": details,
        "timestamp": int(time.time())
    })

async def log_clone_error(bot_id: int, bot_name: str, error_msg: str):
    """Logs runtime exceptions experienced by cloned bots."""
    await logs_db.insert_one({
        "bot_id": bot_id,
        "bot_name": bot_name,
        "error": error_msg,
        "timestamp": int(time.time())
    })

async def update_clone_assistant_settings(bot_id: int, mode: str, assistant_id: int = 1, custom_session: str = None) -> bool:
    """Updates a cloned bot assistant settings."""
    await cloned_db.update_one(
        {"bot_id": bot_id},
        {
            "$set": {
                "assistant_mode": mode,
                "assistant_id": assistant_id,
                "custom_session": custom_session
            }
        }
    )
    return True
