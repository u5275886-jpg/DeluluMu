import time
import asyncio
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

import config
from SONALI_MUSIC import app, SUDOERS
from SONALI_MUSIC.misc import BANNED_USERS
from SONALI_MUSIC.clone_system.validators import validate_bot_token, mask_token, sanitize_text
from SONALI_MUSIC.clone_system.lifecycle import clone_lifecycle
from SONALI_MUSIC.clone_system.registry import clone_registry
from SONALI_MUSIC.utils.permissions import is_owner, is_sudo, is_clone_owner, can_delete_clone
from SONALI_MUSIC.utils.database_clone import (
    get_clone_by_token,
    get_clone_by_id,
    get_user_clones,
    save_clone_bot,
    delete_clone_bot,
    get_all_clones,
)
from SONALI_MUSIC.utils.pagination import paginate_list, build_pagination_keyboard
from SONALI_MUSIC.utils.formatting import format_clone_card

@app.on_message(filters.command(["clone"]) & filters.private & ~BANNED_USERS)
async def clone_bot_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ **Usage:** `/clone <BOT_TOKEN>`")

    bot_token = message.command[1].strip()
    if not validate_bot_token(bot_token):
        return await message.reply_text("❌ **Invalid Telegram Bot Token format.**")

    # Limit check
    max_limit = getattr(config, "CLONE_LIMIT", 500)
    all_clones = await get_all_clones()
    if len(all_clones) >= max_limit:
        return await message.reply_text(f"❌ **Platform Clone Limit Reached ({max_limit}).**")

    # Check if clone already exists
    existing = await get_clone_by_token(bot_token)
    if existing:
        return await message.reply_text("⚠️ **This bot token is already registered.**")

    msg = await message.reply_text("🔄 **Validating token and initializing clone...**")

    # Temporary Pyrogram Client to get Identity
    try:
        temp_client = Client(
            f"temp_{message.from_user.id}_{int(time.time())}",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=bot_token,
            in_memory=True,
        )
        await temp_client.start()
        me = await temp_client.get_me()
        await temp_client.stop()
    except Exception as e:
        return await msg.edit_text(f"❌ **Failed to connect with Telegram:**\n`{sanitize_text(str(e))}`")

    # Check duplicate bot_id
    existing_id = await get_clone_by_id(me.id)
    if existing_id:
        return await msg.edit_text("⚠️ **This bot is already registered in the system.**")

    clone_data = {
        "bot_id": me.id,
        "bot_username": me.username or "",
        "bot_name": me.first_name or "Cloned Bot",
        "tenant_id": message.from_user.id,
        "owner_id": message.from_user.id,
        "token": bot_token,
        "token_reference": mask_token(bot_token),
        "created_at": time.time(),
        "updated_at": time.time(),
        "last_activity": time.time(),
        "status": "stopped",
        "runtime_status": "stopped",
        "assistant_status": "system",
        "total_users": 0,
        "total_groups": 0,
        "last_error": None,
        "error_count": 0,
    }

    await save_clone_bot(clone_data)
    success = await clone_lifecycle.start_clone(clone_data)

    if success:
        await msg.edit_text(
            f"🎉 **Bot Cloned Successfully!**\n\n"
            f"🤖 **Bot:** @{me.username}\n"
            f"🆔 **Bot ID:** `{me.id}`\n"
            f"👤 **Owner:** {message.from_user.mention}\n\n"
            f"Use `/mybots` or `/manage_clone` to control your clone."
        )
    else:
        await msg.edit_text("❌ **Failed to start clone runtime.** Please check system logs.")

@app.on_message(filters.command(["delbot", "rmbot", "delcloned", "delclone", "deleteclone", "removeclone", "cancelclone"]) & ~BANNED_USERS)
async def delete_clone_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ **Usage:** `/delbot @username` or `/delbot <bot_id>`")

    target = message.command[1].strip()
    target_id = None

    if target.startswith("@"):
        username = target.lstrip("@").lower()
        all_clones = await get_all_clones()
        for c in all_clones:
            if c.get("bot_username", "").lower() == username:
                target_id = c.get("bot_id")
                break
    else:
        try:
            target_id = int(target)
        except ValueError:
            return await message.reply_text("❌ Invalid bot ID or username provided.")

    if not target_id:
        return await message.reply_text("❌ **Clone bot not found.**")

    # Validate permission
    if not await can_delete_clone(message.from_user.id, target_id):
        return await message.reply_text("⛔ **You are not authorized to delete this clone.**")

    msg = await message.reply_text("🔄 **Stopping and deleting clone bot...**")
    await clone_lifecycle.stop_clone(target_id)
    await delete_clone_bot(target_id)

    await msg.edit_text(f"✅ **Clone Bot (`{target_id}`) successfully removed and stopped.**")

@app.on_message(filters.command(["mybot", "mybots"]) & filters.private & ~BANNED_USERS)
async def my_bots_cmd(client, message: Message):
    clones = await get_user_clones(message.from_user.id)
    if not clones:
        return await message.reply_text("🤖 **You do not own any cloned bots.**\nUse `/clone <BOT_TOKEN>` to create one!")

    page_items, total_pages, page = paginate_list(clones, page=1, page_size=5)
    text = f"🤖 **Your Cloned Bots (Page 1/{total_pages}):**\n\n"
    for c in page_items:
        text += format_clone_card(c) + "\n"

    kbd = build_pagination_keyboard(page, total_pages, "mybots_page")
    await message.reply_text(text, reply_markup=kbd)

@app.on_callback_query(filters.regex(r"^mybots_page_(\d+)$"))
async def my_bots_page_cb(client, callback):
    page = int(callback.matches[0].group(1))
    clones = await get_user_clones(callback.from_user.id)
    page_items, total_pages, page = paginate_list(clones, page=page, page_size=5)

    text = f"🤖 **Your Cloned Bots (Page {page}/{total_pages}):**\n\n"
    for c in page_items:
        text += format_clone_card(c) + "\n"

    kbd = build_pagination_keyboard(page, total_pages, "mybots_page")
    await callback.message.edit_text(text, reply_markup=kbd)
