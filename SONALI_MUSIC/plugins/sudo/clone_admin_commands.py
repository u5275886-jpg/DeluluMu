import asyncio
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

import config
from SONALI_MUSIC import app, SUDOERS
from SONALI_MUSIC.misc import BANNED_USERS
from SONALI_MUSIC.clone_system.lifecycle import clone_lifecycle
from SONALI_MUSIC.clone_system.manager import clone_sys_manager
from SONALI_MUSIC.utils.permissions import is_sudo, is_owner
from SONALI_MUSIC.utils.database_clone import get_all_clones, delete_clone_bot
from SONALI_MUSIC.utils.pagination import paginate_list, build_pagination_keyboard
from SONALI_MUSIC.utils.formatting import format_clone_card

@app.on_message(filters.command(["cloned", "allclones"]) & SUDOERS)
async def global_clones_list_cmd(client, message: Message):
    clones = await get_all_clones()
    if not clones:
        return await message.reply_text("🤖 **No cloned bots registered in the system.**")

    page_items, total_pages, page = paginate_list(clones, page=1, page_size=5)
    text = f"🌐 **Global Clones List (Page 1/{total_pages}):**\n\n"
    for c in page_items:
        text += format_clone_card(c) + "\n"

    kbd = build_pagination_keyboard(page, total_pages, "gclones_page")
    await message.reply_text(text, reply_markup=kbd)

@app.on_callback_query(filters.regex(r"^gclones_page_(\d+)$"))
async def global_clones_page_cb(client, callback: CallbackQuery):
    if not await is_sudo(callback.from_user.id):
        return await callback.answer("⛔ Authorized Sudo Only.", show_alert=True)

    page = int(callback.matches[0].group(1))
    clones = await get_all_clones()
    page_items, total_pages, page = paginate_list(clones, page=page, page_size=5)

    text = f"🌐 **Global Clones List (Page {page}/{total_pages}):**\n\n"
    for c in page_items:
        text += format_clone_card(c) + "\n"

    kbd = build_pagination_keyboard(page, total_pages, "gclones_page")
    await callback.message.edit_text(text, reply_markup=kbd)

@app.on_message(filters.command(["totalbots", "botcount"]) & SUDOERS)
async def total_bots_cmd(client, message: Message):
    stats = await clone_sys_manager.get_stats()
    text = (
        f"📊 **Clone Bot Count Statistics:**\n\n"
        f"🤖 **Total Clones:** {stats['total_clones']}\n"
        f"🟢 **Running:** {stats['running_clones']}\n"
        f"🔴 **Stopped:** {stats['stopped_clones']}\n"
        f"⚠️ **Failed:** {stats['failed_clones']}\n"
    )
    await message.reply_text(text)

@app.on_message(filters.command(["active"]) & SUDOERS)
async def active_clones_cmd(client, message: Message):
    days = 30
    if len(message.command) > 1 and message.command[1].isdigit():
        days = int(message.command[1])

    clones = await get_all_clones()
    active_clones = [c for c in clones if (time.time() - (c.get("last_activity") or c.get("created_at") or 0)) <= (days * 86400)]

    text = f"🟢 **Active Clones (Last {days} days):** `{len(active_clones)}` / `{len(clones)}`"
    await message.reply_text(text)

@app.on_message(filters.command(["inactive"]) & SUDOERS)
async def inactive_clones_cmd(client, message: Message):
    days = 30
    if len(message.command) > 1 and message.command[1].isdigit():
        days = int(message.command[1])

    inactive = await clone_sys_manager.find_inactive(days)
    if not inactive:
        return await message.reply_text(f"✨ **No inactive clones found for the past {days} days.**")

    text = f"💤 **Inactive Clones (>{days} days): {len(inactive)}**\n\n"
    for c in inactive[:10]:
        text += f"• @{c.get('bot_username')} (`{c.get('bot_id')}`) - Inactive for {c.get('days_inactive')} days\n"

    if len(inactive) > 10:
        text += f"\n... and {len(inactive) - 10} more."

    await message.reply_text(text)

@app.on_message(filters.command(["delinactive"]) & SUDOERS)
async def del_inactive_cmd(client, message: Message):
    days = 30
    if len(message.command) > 1 and message.command[1].isdigit():
        days = int(message.command[1])

    inactive = await clone_sys_manager.find_inactive(days)
    if not inactive:
        return await message.reply_text(f"✨ **No inactive clones found older than {days} days.**")

    text = f"⚠️ **Found {len(inactive)} inactive clones older than {days} days.**\nAre you sure you want to purge them?"
    kbd = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm Purge", callback_data=f"CONFIRM_PURGE_{days}"),
            InlineKeyboardButton("❌ Cancel", callback_data="CANCEL_PURGE")
        ]
    ])
    await message.reply_text(text, reply_markup=kbd)

@app.on_callback_query(filters.regex(r"^CONFIRM_PURGE_(\d+)$"))
async def confirm_purge_cb(client, callback: CallbackQuery):
    if not await is_sudo(callback.from_user.id):
        return await callback.answer("⛔ Authorized Sudo Only.", show_alert=True)

    days = int(callback.matches[0].group(1))
    await callback.message.edit_text("🔄 **Purging inactive clones...**")
    res = await clone_sys_manager.purge_inactive(days)

    await callback.message.edit_text(
        f"✅ **Inactive Clone Purge Complete!**\n\n"
        f"🗑 **Purged:** {res['purged_count']} / {res['total_found']}\n"
        f"❌ **Errors:** {len(res['errors'])}"
    )

@app.on_callback_query(filters.regex("^CANCEL_PURGE$"))
async def cancel_purge_cb(client, callback: CallbackQuery):
    await callback.message.edit_text("❌ Purge operation cancelled.")

@app.on_message(filters.command(["botstats"]) & SUDOERS)
async def bot_stats_cmd(client, message: Message):
    stats = await clone_sys_manager.get_stats()
    text = (
        f"📊 **Clone Platform System Statistics**\n\n"
        f"🤖 **Total Clones:** {stats['total_clones']}\n"
        f"🟢 **Running Clones:** {stats['running_clones']}\n"
        f"🔴 **Stopped Clones:** {stats['stopped_clones']}\n"
        f"⚠️ **Failed Clones:** {stats['failed_clones']}\n\n"
        f"📈 **Active (24h):** {stats['active_24h']}\n"
        f"📈 **Active (7d):** {stats['active_7d']}\n"
        f"📈 **Active (30d):** {stats['active_30d']}\n"
        f"💤 **Inactive (30d+):** {stats['inactive_30d']}\n\n"
        f"💻 **System Health:**\n"
        f"• **CPU Usage:** `{stats['cpu_percent']}%`\n"
        f"• **RAM Usage:** `{stats['ram_percent']}%`\n"
        f"• **Active Async Tasks:** `{stats['active_async_tasks']}`\n"
        f"• **Connected Clients:** `{stats['active_clients_count']}`"
    )
    await message.reply_text(text)

@app.on_message(filters.command(["delallclones"]) & filters.user(config.OWNER_ID))
async def del_all_clones_cmd(client, message: Message):
    clones = await get_all_clones()
    if not clones:
        return await message.reply_text("🤖 No clones to delete.")

    text = f"🚨 **DANGER ZONE** 🚨\n\nAre you sure you want to delete ALL {len(clones)} cloned bots?"
    kbd = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚨 YES, DELETE ALL", callback_data="CONFIRM_DEL_ALL_CLONES"),
            InlineKeyboardButton("❌ CANCEL", callback_data="CANCEL_PURGE")
        ]
    ])
    await message.reply_text(text, reply_markup=kbd)

@app.on_callback_query(filters.regex("^CONFIRM_DEL_ALL_CLONES$"))
async def confirm_del_all_clones_cb(client, callback: CallbackQuery):
    if callback.from_user.id != config.OWNER_ID:
        return await callback.answer("⛔ Platform Owner Only.", show_alert=True)

    await callback.message.edit_text("🔄 Deleting all cloned bots...")
    clones = await get_all_clones()
    count = 0
    for c in clones:
        b_id = c.get("bot_id")
        await clone_lifecycle.stop_clone(b_id)
        await delete_clone_bot(b_id)
        count += 1

    await callback.message.edit_text(f"✅ **Deleted {count} cloned bots completely.**")
