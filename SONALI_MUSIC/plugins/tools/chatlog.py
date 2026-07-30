import random
from pyrogram import Client
from pyrogram.types import Message
from pyrogram import filters
from pyrogram.types import(InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo, Message)
from config import LOGGER_ID as LOG_GROUP_ID
from SONALI_MUSIC import app 
from pyrogram.errors import RPCError
from pyrogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from os import environ
from typing import Union, Optional
from PIL import Image, ImageDraw, ImageFont
from os import environ
from pyrogram.types import ChatJoinRequest, InlineKeyboardButton, InlineKeyboardMarkup
from PIL import Image, ImageDraw, ImageFont
import asyncio, os, time, aiohttp
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from asyncio import sleep
from pyrogram import filters, Client, enums
from pyrogram.enums import ParseMode


photo = [
    "https://files.catbox.moe/tdj8he.jpg",
    "https://files.catbox.moe/ygpszq.jpg",
]  


@app.on_message(filters.new_chat_members, group=2)
async def join_watcher(_, message):    
    chat = message.chat

    # Check if the bot itself was added
    is_bot_added = False
    for member in message.new_chat_members:
        if member.id == app.id:
            is_bot_added = True
            break

    if not is_bot_added:
        return

    # Now that we know the bot itself was added, get the invite link robustly
    try:
        link = await app.export_chat_invite_link(message.chat.id)
    except Exception:
        link = "No Link (Need Admin Rights)"

    try:
        count = await app.get_chat_members_count(chat.id)
    except Exception:
        count = "Unknown"

    added_by = message.from_user.mention if message.from_user else "Unknown User"
    msg = (
        f"#𝗕𝗢𝗧_𝗔𝗗𝗗𝗘𝗗_𝗡𝗘𝗪_𝗚𝗥𝗢𝗨𝗣\n\n"
        f"⦿───────────────────⦿\n\n"
        f"◎ ᴄʜᴀᴛ ɴᴀᴍᴇ ▸ {message.chat.title}\n"
        f"◎ ᴄʜᴀᴛ ɪᴅ ▸ {message.chat.id}\n"
        f"◎ ᴄʜᴀᴛ ᴜsᴇʀɴᴀᴍᴇ ▸ @{message.chat.username if message.chat.username else 'Private Group'}\n"
        f"◎ ᴄʜᴀᴛ ʟɪɴᴋ ▸ {link if link.startswith('http') else '[No Link]'}\n"
        f"◎ ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀs ▸ {count}\n"
        f"◎ ᴀᴅᴅᴇᴅ ʙʏ ▸ {added_by}\n"
        f"⦿───────────────────⦿"
    )

    from SONALI_MUSIC.utils.database import get_log_group_id
    log_group_id = await get_log_group_id()
    if log_group_id:
        reply_markup = None
        if link.startswith("http"):
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"#𝗚𝗥𝗢𝗨𝗣 #𝗟𝗜𝗡𝗞", url=link)]
            ])
        try:
            await app.send_photo(
                log_group_id,
                photo=random.choice(photo),
                caption=msg,
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"Error sending group add log: {e}")


@app.on_message(filters.left_chat_member)
async def on_left_chat_member(_, message: Message):
    if message.left_chat_member.id == app.id:
        remove_by = message.from_user.mention if message.from_user else "𝐔ɴᴋɴᴏᴡɴ 𝐔sᴇʀ"
        title = message.chat.title
        username = f"@{message.chat.username}" if message.chat.username else "𝐏ʀɪᴠᴀᴛᴇ 𝐂ʜᴀᴛ"
        chat_id = message.chat.id
        left = f"✫ <b><u>#𝗟𝗘𝗙𝗧_𝗚𝗥𝗢𝗨𝗣</u></b> ✫\n\nᴄʜᴀᴛ ᴛɪᴛʟᴇ : {title}\n\nᴄʜᴀᴛ ɪᴅ : {chat_id}\n\nʀᴇᴍᴏᴠᴇᴅ ʙʏ : {remove_by}\n\nʙᴏᴛ : @{app.username}"
        from SONALI_MUSIC.utils.database import get_log_group_id
        log_group_id = await get_log_group_id()
        if log_group_id:
            try:
                await app.send_photo(log_group_id, photo=random.choice(photo), caption=left)
            except Exception as e:
                print(f"Error sending group left log: {e}")
