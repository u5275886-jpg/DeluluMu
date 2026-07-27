import psutil
import asyncio
import logging
from pyrogram import filters
from pyrogram.types import Message
from aiohttp import web
import json

import config
from SONALI_MUSIC import app
from SONALI_MUSIC.core.clone_manager import clone_manager, current_clone_client
from SONALI_MUSIC.utils.database_clone import (
    add_premium_user,
    remove_premium_user,
    check_premium_access,
    get_all_clones,
    update_clone_status,
    log_audit_trail
)
from SONALI_MUSIC.utils.Sona_font import Fonts

logger = logging.getLogger(__name__)

# Helper to format small cap text
def to_smallcap(text: str) -> str:
    return Fonts.smallcap(text)

# ----------------------------------------------------------------------
# 1. SUDO COMMANDS: PREMIUM ASSIGNMENT & CLONE CONTROL
# ----------------------------------------------------------------------

@app.on_message(filters.command(["addpremium", "add_premium"]) & filters.user(config.OWNER_ID))
async def add_premium_cmd(client, message: Message):
    parts = message.text.split()
    if len(parts) < 3:
        return await message.reply_text(
            f"❓ **Usage:** `/addpremium [user_id] [duration_days]`\n\n"
            f"Example: `/addpremium 123456789 30`"
        )

    try:
        user_id = int(parts[1])
        days = int(parts[2])
    except ValueError:
        return await message.reply_text("❌ User ID and days must be valid integers.")

    await add_premium_user(user_id, "pro", days)
    await message.reply_text(
        f"✅ **{to_smallcap('premium activated')}**\n\n"
        f"User ID: `{user_id}`\n"
        f"Plan: **Premium Pro**\n"
        f"Duration: **{days} Days**"
    )
    await log_audit_trail(config.OWNER_ID, "add_premium", f"Added premium to user {user_id} for {days} days.")


@app.on_message(filters.command(["removepremium", "remove_premium"]) & filters.user(config.OWNER_ID))
async def remove_premium_cmd(client, message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply_text("❓ **Usage:** `/removepremium [user_id]`")

    try:
        user_id = int(parts[1])
    except ValueError:
        return await message.reply_text("❌ User ID must be an integer.")

    await remove_premium_user(user_id)
    await message.reply_text(
        f"✅ **{to_smallcap('premium deactivated')}**\n\n"
        f"User ID: `{user_id}` has been downgraded to free plan."
    )
    await log_audit_trail(config.OWNER_ID, "remove_premium", f"Removed premium for user {user_id}")


@app.on_message(filters.command(["clones_list", "clones"]) & filters.user(config.OWNER_ID))
async def list_clones_cmd(client, message: Message):
    clones = await get_all_clones()
    if not clones:
        return await message.reply_text("🔍 **No cloned bots found in database.**")

    text = f"📊 **{to_smallcap('master clone list')}**\n\n"
    for i, clone in enumerate(clones, 1):
        text += (
            f"{i}. **{clone.get('bot_name')}** (@{clone.get('bot_username')})\n"
            f"   ID: `{clone.get('bot_id')}` | Tenant: `{clone.get('tenant_id')}`\n"
            f"   Status: **{clone.get('status').upper()}**\n\n"
        )

    await message.reply_text(text)


@app.on_message(filters.command(["delete_clone", "remove_clone"]) & filters.user(config.OWNER_ID))
async def delete_clone_by_owner_cmd(client, message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply_text("❓ **Usage:** `/delete_clone [bot_id]`\n*You can get bot_id from /clones_list*")

    try:
        bot_id = int(parts[1])
    except ValueError:
        return await message.reply_text("❌ Bot ID must be a valid integer.")

    clone = await get_all_clones()
    target = next((c for c in clone if c.get("bot_id") == bot_id), None)
    if not target:
        return await message.reply_text("❌ Clone bot not found in the database.")

    from SONALI_MUSIC.utils.database_clone import delete_clone_bot
    # Stop clone inside manager
    await clone_manager.stop_clone(bot_id)
    # Remove from DB
    await delete_clone_bot(bot_id)

    await message.reply_text(f"✅ **Clone @{target.get('bot_username')} has been successfully deleted & stopped.**")
    await log_audit_trail(config.OWNER_ID, "owner_clone_deleted", f"Owner deleted cloned bot {bot_id} (@{target.get('bot_username')})")


@app.on_message(filters.command(["clone_ban"]) & filters.user(config.OWNER_ID))
async def clone_ban_cmd(client, message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply_text("❓ **Usage:** `/clone_ban [user_id]`")

    try:
        user_id = int(parts[1])
    except ValueError:
        return await message.reply_text("❌ User ID must be a valid integer.")

    from SONALI_MUSIC.utils.database import add_banned_user
    from config import BANNED_USERS

    await add_banned_user(user_id)
    BANNED_USERS.add(user_id)
    await message.reply_text(f"✅ **User `{user_id}` has been globally banned from all cloned bots and main bot.**")
    await log_audit_trail(config.OWNER_ID, "clone_ban", f"Banned user {user_id} globally.")


@app.on_message(filters.command(["clone_unban"]) & filters.user(config.OWNER_ID))
async def clone_unban_cmd(client, message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply_text("❓ **Usage:** `/clone_unban [user_id]`")

    try:
        user_id = int(parts[1])
    except ValueError:
        return await message.reply_text("❌ User ID must be a valid integer.")

    from SONALI_MUSIC.utils.database import remove_banned_user
    from config import BANNED_USERS

    await remove_banned_user(user_id)
    if user_id in BANNED_USERS:
        BANNED_USERS.remove(user_id)
    await message.reply_text(f"✅ **User `{user_id}` has been unbanned successfully.**")
    await log_audit_trail(config.OWNER_ID, "clone_unban", f"Unbanned user {user_id} globally.")


@app.on_message(filters.command(["set_clone_limit"]) & filters.user(config.OWNER_ID))
async def set_clone_limit_cmd(client, message: Message):
    parts = message.text.split()
    if len(parts) < 3:
        return await message.reply_text("❓ **Usage:** `/set_clone_limit [user_id] [limit]`")

    try:
        user_id = int(parts[1])
        limit = int(parts[2])
    except ValueError:
        return await message.reply_text("❌ User ID and limit must be valid integers.")

    from SONALI_MUSIC.utils.database_clone import set_user_clone_limit
    await set_user_clone_limit(user_id, limit)
    await message.reply_text(f"✅ **Custom clone limit of `{limit}` set successfully for user `{user_id}`.**")
    await log_audit_trail(config.OWNER_ID, "set_clone_limit", f"Set clone limit for user {user_id} to {limit}.")


@app.on_message(filters.command(["clones_stats", "clone_stats"]) & filters.user(config.OWNER_ID))
async def clones_stats_cmd(client, message: Message):
    clones = await get_all_clones()
    total = len(clones)
    active_clones = sum(1 for c in clones if c.get("status") == "active")
    paused_clones = total - active_clones

    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    text = (
        f"📊 **{to_smallcap('clone platform stats')}**\n\n"
        f"🤖 **Total Cloned Bots:** {total}\n"
        f" ├ ⚡ **Active:** {active_clones}\n"
        f" └ ⏸️ **Paused:** {paused_clones}\n\n"
        f"🖥️ **System Resource Usage:**\n"
        f" ├ 🧠 **CPU:** {cpu}%\n"
        f" └ 📼 **RAM:** {ram}%\n"
    )
    await message.reply_text(text)


@app.on_message(filters.command(["restart_clones", "reboot_clones"]) & filters.user(config.OWNER_ID))
async def restart_clones_cmd(client, message: Message):
    status_msg = await message.reply_text("🔄 **Stopping all cloned bots dynamically...**")
    await clone_manager.stop_all_clones()
    await status_msg.edit_text("🚀 **Restarting all cloned bots dynamically...**")
    await clone_manager.start_all_clones()
    await status_msg.edit_text("✅ **All cloned bots have been restarted successfully!**")
    await log_audit_trail(config.OWNER_ID, "restart_clones", "Restarted all cloned bot instances.")

# ----------------------------------------------------------------------
# 2. OWNER GLOBAL BROADCAST ENGINE WITH RETRIES & ANTI-SPAM
# ----------------------------------------------------------------------

@app.on_message(filters.command(["broadcast_clones", "clone_broadcast"]) & filters.user(config.OWNER_ID))
async def broadcast_clones_cmd(client, message: Message):
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        return await message.reply_text("❓ **Usage:** `/broadcast_clones [message text]`")

    broadcast_text = parts[1].strip()
    status_msg = await message.reply_text("📢 **Preparing global broadcast to cloned bots...**")

    clones = await get_all_clones()
    success_count = 0
    fail_count = 0

    for clone in clones:
        if clone.get("status") == "active":
            bot_id = clone.get("bot_id")
            clone_client = clone_manager.clones.get(bot_id)
            if clone_client:
                try:
                    # Retrieve the served users for that clone bot to send them the broadcast
                    # In this platform, we can broadcast to the channels or main owner chat
                    await clone_client.send_message(
                        chat_id=clone.get("tenant_id"),
                        text=f"📢 **[GLOBAL OWNER BROADCAST]**\n\n{broadcast_text}"
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to send broadcast on clone {bot_id}: {e}")
                    fail_count += 1
                # Anti-spam delay
                await asyncio.sleep(0.5)

    await status_msg.edit_text(
        f"✅ **{to_smallcap('broadcast complete')}**\n\n"
        f"Successfully delivered: **{success_count}** bots\n"
        f"Failed delivery: **{fail_count}** bots"
    )

# ----------------------------------------------------------------------
# 3. SAAS SAAS REST API & WEBSOCKET ENGINE (aiohttp)
# ----------------------------------------------------------------------

async def api_get_clones(request):
    """GET /api/clones -> Lists all registered clone bots and status."""
    clones = await get_all_clones()
    serialized = []
    for clone in clones:
        bot_id = clone.get("bot_id")
        serialized.append({
            "bot_id": bot_id,
            "bot_name": clone.get("bot_name"),
            "bot_username": clone.get("bot_username"),
            "tenant_id": clone.get("tenant_id"),
            "status": clone.get("status"),
            "is_loaded": bot_id in clone_manager.clones,
            "settings": clone.get("settings", {})
        })
    return web.json_response({"success": True, "clones": serialized})

async def api_clone_action(request):
    """POST /api/clones/action -> Performs start/stop operations on clone bot."""
    try:
        data = await request.json()
        bot_id = int(data.get("bot_id"))
        action = data.get("action") # "start", "stop", "delete"
    except Exception as e:
        return web.json_response({"success": False, "error": f"Invalid body: {e}"}, status=400)

    if action == "start":
        clone = await get_all_clones()
        target = next((c for c in clone if c.get("bot_id") == bot_id), None)
        if not target:
            return web.json_response({"success": False, "error": "Clone not found"}, status=404)
        started = await clone_manager.start_clone(target.get("bot_token"), target.get("tenant_id"))
        return web.json_response({"success": started is not None})

    elif action == "stop":
        stopped = await clone_manager.stop_clone(bot_id)
        return web.json_response({"success": stopped})

    return web.json_response({"success": False, "error": f"Unknown action: {action}"}, status=400)

async def api_get_metrics(request):
    """GET /api/metrics -> System resources utilization metrics."""
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    active_clones = len(clone_manager.clones)
    return web.json_response({
        "success": True,
        "metrics": {
            "cpu_percent": cpu,
            "memory_percent": ram,
            "active_clones_loaded": active_clones
        }
    })

# Live stream SSE / WebSocket server
async def ws_live_updates(request):
    """WebSocket /api/live -> Push-based real-time event stream."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    logger.info("New WebSocket connection to live API stream established.")
    try:
        while True:
            # Send system stats in loop every 3 seconds
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            payload = {
                "event": "stats_update",
                "cpu": cpu,
                "ram": ram,
                "active_clones": len(clone_manager.clones)
            }
            await ws.send_str(json.dumps(payload))
            await asyncio.sleep(3)
    except Exception as e:
        logger.warning(f"WebSocket live client disconnected: {e}")
    return ws

# Create the Web application
async def init_web_api():
    web_app = web.Application()
    web_app.add_routes([
        web.get('/api/clones', api_get_clones),
        web.post('/api/clones/action', api_clone_action),
        web.get('/api/metrics', api_get_metrics),
        web.get('/api/live', ws_live_updates)
    ])

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)

    # Run in background asynchronously
    asyncio.create_task(site.start())
    logger.info("Admin Web API & WebSocket server running smoothly on port 8080.")

# Start the web server in background
asyncio.create_task(init_web_api())


# ----------------------------------------------------------------------
# 4. SET FORCE JOIN FOR CLONING (/SETFS)
# ----------------------------------------------------------------------

@app.on_message(filters.command(["setfs"]) & filters.user(config.OWNER_ID))
async def set_force_sub_cmd(client, message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        from SONALI_MUSIC.utils.database_clone import get_force_sub
        current = await get_force_sub()
        current_status = f"@{current}" if current else "Disabled"
        return await message.reply_text(
            f"❓ **Usage:** `/setfs [channel_username/none]`\n\n"
            f"Current Channel: **{current_status}**\n\n"
            f"Example: `/setfs kriti_bot_update` or `/setfs none` to disable."
        )

    channel = parts[1].strip()
    if channel.lower() in ["none", "off", "disable"]:
        from SONALI_MUSIC.utils.database_clone import set_force_sub
        await set_force_sub(None)
        await message.reply_text("✅ **Force subscription for cloning has been disabled.**")
        await log_audit_trail(config.OWNER_ID, "set_force_sub", "Disabled force subscription.")
    else:
        if channel.startswith("@"):
            channel = channel[1:]
        from SONALI_MUSIC.utils.database_clone import set_force_sub
        await set_force_sub(channel)
        await message.reply_text(f"✅ **Force subscription channel for cloning set to:** @{channel}")
        await log_audit_trail(config.OWNER_ID, "set_force_sub", f"Set force sub channel to @{channel}")
