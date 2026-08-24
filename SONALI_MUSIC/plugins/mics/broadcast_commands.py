import asyncio
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

import config
from SONALI_MUSIC import app
from config import BANNED_USERS
from SONALI_MUSIC.misc import SUDOERS
from SONALI_MUSIC.broadcast_system.manager import broadcast_manager
from SONALI_MUSIC.broadcast_system.cancellation import cancellation_manager
from SONALI_MUSIC.utils.permissions import is_sudo, can_broadcast

@app.on_message(filters.command(["cbroadcast", "clonebroadcast"]) & SUDOERS)
async def global_clone_broadcast_cmd(client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text(
            "❌ **Usage:** `/cbroadcast -user|-group|-all|-owner <message>` or reply to a message."
        )

    target_type = "all"
    flags = [arg.lower() for arg in message.command if arg.startswith("-")]
    if "-user" in flags:
        target_type = "user"
    elif "-group" in flags:
        target_type = "group"
    elif "-owner" in flags:
        target_type = "owner"
    elif "-all" in flags:
        target_type = "all"

    pin = "-pin" in flags or "-pinloud" in flags
    msg_to_send = message.reply_to_message if message.reply_to_message else message

    prog_msg = await message.reply_text("📢 **Preparing Global Clone Broadcast...**")
    job_id = await broadcast_manager.start_broadcast(
        client=client,
        sender_id=message.from_user.id,
        broadcast_type="cbroadcast",
        target_type=target_type,
        message_to_send=msg_to_send,
        progress_message=prog_msg,
        pin=pin
    )

    await message.reply_text(
        f"🚀 **Global Clone Broadcast Started!**\n🆔 **Job ID:** `{job_id}`\n\nUse `/stopcbroadcast {job_id}` to cancel."
    )

@app.on_message(filters.command(["stopcbroadcast", "stopbroadcast"]) & SUDOERS)
async def stop_broadcast_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ **Usage:** `/stopcbroadcast <JOB_ID>`")

    job_id = message.command[1].strip()
    if cancellation_manager.cancel_job(job_id):
        await message.reply_text(f"🛑 **Cancellation signal sent for broadcast job `{job_id}`.**")
    else:
        await message.reply_text(f"⚠️ **Active broadcast job `{job_id}` not found.**")
