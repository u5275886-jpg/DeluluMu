import traceback
from typing import Dict, Any
from SONALI_MUSIC.clone_system.validators import sanitize_text, mask_token

def format_exception_safe(exc: Exception) -> str:
    tb = traceback.format_exc()
    return sanitize_text(str(exc))

def format_clone_card(clone: Dict[str, Any]) -> str:
    bot_id = clone.get("bot_id", "N/A")
    bot_name = clone.get("bot_name", "Unknown")
    bot_username = clone.get("bot_username", "None")
    owner_id = clone.get("tenant_id") or clone.get("owner_id", "N/A")
    status = clone.get("runtime_status") or clone.get("status", "stopped")
    created_at = clone.get("created_at", 0)

    text = (
        f"🤖 **Bot Name:** {bot_name}\n"
        f"🔗 **Username:** @{bot_username} (`{bot_id}`)\n"
        f"👤 **Owner ID:** `{owner_id}`\n"
        f"⚡ **Status:** `{status.upper()}`\n"
    )
    return text
