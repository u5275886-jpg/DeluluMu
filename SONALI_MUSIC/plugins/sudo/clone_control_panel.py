from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

import config
from SONALI_MUSIC import app, SUDOERS
from SONALI_MUSIC.utils.permissions import is_sudo
from SONALI_MUSIC.clone_system.manager import clone_sys_manager

@app.on_message(filters.command(["clonepanel", "cpanel"]) & SUDOERS)
async def clone_control_panel_cmd(client, message: Message):
    text = "⚙️ **Clone Bot & Broadcast Control Panel**\n\nChoose an option below to manage the platform:"
    kbd = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Stats", callback_data="CPANEL_STATS"),
            InlineKeyboardButton("🤖 All Clones", callback_data="gclones_page_1")
        ],
        [
            InlineKeyboardButton("💤 Inactive Clones", callback_data="CPANEL_INACTIVE"),
            InlineKeyboardButton("🗑 Delete Inactive", callback_data="CPANEL_DEL_INACTIVE")
        ],
        [
            InlineKeyboardButton("📢 Main Broadcast", callback_data="CPANEL_MAIN_BC"),
            InlineKeyboardButton("🌐 Clone Broadcast", callback_data="CPANEL_CLONE_BC")
        ]
    ])
    await message.reply_text(text, reply_markup=kbd)

@app.on_callback_query(filters.regex("^CPANEL_STATS$"))
async def cpanel_stats_cb(client, callback: CallbackQuery):
    if not await is_sudo(callback.from_user.id):
        return await callback.answer("Authorized Sudo Only.", show_alert=True)
    stats = await clone_sys_manager.get_stats()
    text = (
        f"📊 **Clone Platform System Statistics**\n\n"
        f"🤖 **Total Clones:** {stats['total_clones']}\n"
        f"🟢 **Running Clones:** {stats['running_clones']}\n"
        f"🔴 **Stopped Clones:** {stats['stopped_clones']}\n"
        f"⚠️ **Failed Clones:** {stats['failed_clones']}\n\n"
        f"💻 **CPU:** `{stats['cpu_percent']}%` | **RAM:** `{stats['ram_percent']}%`"
    )
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="CPANEL_BACK")]]))

@app.on_callback_query(filters.regex("^CPANEL_BACK$"))
async def cpanel_back_cb(client, callback: CallbackQuery):
    text = "⚙️ **Clone Bot & Broadcast Control Panel**\n\nChoose an option below to manage the platform:"
    kbd = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Stats", callback_data="CPANEL_STATS"),
            InlineKeyboardButton("🤖 All Clones", callback_data="gclones_page_1")
        ],
        [
            InlineKeyboardButton("💤 Inactive Clones", callback_data="CPANEL_INACTIVE"),
            InlineKeyboardButton("🗑 Delete Inactive", callback_data="CPANEL_DEL_INACTIVE")
        ],
        [
            InlineKeyboardButton("📢 Main Broadcast", callback_data="CPANEL_MAIN_BC"),
            InlineKeyboardButton("🌐 Clone Broadcast", callback_data="CPANEL_CLONE_BC")
        ]
    ])
    await callback.message.edit_text(text, reply_markup=kbd)
