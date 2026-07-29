import time
import random
from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from youtubesearchpython.__future__ import VideosSearch
 
import config
from SONALI_MUSIC import app
from SONALI_MUSIC.misc import _boot_
from SONALI_MUSIC.plugins.sudo.sudoers import sudoers_list
from SONALI_MUSIC.utils.database import get_served_chats, get_served_users, get_sudoers
from SONALI_MUSIC.utils import bot_sys_stats
from SONALI_MUSIC.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
    get_log_group_id,
)
from SONALI_MUSIC.utils.decorators.language import LanguageStart
from SONALI_MUSIC.utils.formatters import get_readable_time
from SONALI_MUSIC.utils.inline import help_pannel, private_panel, start_panel
from config import BANNED_USERS
from strings import get_string
 
NEXIO = [
          "https://litter.catbox.moe/vtsad2y91ytmincf.jpg",
          "https://litter.catbox.moe/4w9ecqcg6gzijzwt.jpg",
          "https://litter.catbox.moe/ql33xyx1bawu1c2v.jpg",
          "https://litter.catbox.moe/wvszrn7kqj0lrme6.jpg",
          "https://litter.catbox.moe/oc71pbepf8cxkk4r.jpg",
          "https://litter.catbox.moe/00ty0hx8cbrs2299.jpg",
          "https://litter.catbox.moe/pdn1i4ze2hl1u6gf.jpg",
          "https://litter.catbox.moe/qcgtbz6keobcc8iz.jpg",
]
 
@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)
    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]
        if name[0:4] == "help":
            keyboard = help_pannel(_)
            return await message.reply_photo(
                random.choice(NEXIO),
                caption=_["help_1"].format(config.SUPPORT_CHAT),
                reply_markup=keyboard,
                has_spoiler=True
            )
        if name[0:3] == "sud":
            await sudoers_list(client=client, message=message, _=_)
            if await is_on_off(2):
                log_group_id = await get_log_group_id()
                return await app.send_message(
                    chat_id=log_group_id,
                    text=f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>sᴜᴅᴏʟɪsᴛ</b>.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
                )
            return
        if name[0:3] == "inf":
            m = await message.reply_text("🔎")
            query = (str(name)).replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"
            results = VideosSearch(query, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration = result["duration"]
                views = result["viewCount"]["short"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                channellink = result["channel"]["link"]
                channel = result["channel"]["name"]
                link = result["link"]
                published = result["publishedTime"]
            searched_text = _["start_6"].format(
                title, duration, views, published, channellink, channel, app.mention
            )
            key = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text=_["S_B_8"], url=link),
                        InlineKeyboardButton(text=_["S_B_9"], url=config.SUPPORT_CHAT),
                    ],
                ]
            )
            await m.delete()
            await app.send_photo(
                chat_id=message.chat.id,
                photo=thumbnail,
                caption=searched_text,
                reply_markup=key,
                has_spoiler=True,
            )
            if await is_on_off(2):
                log_group_id = await get_log_group_id()
                return await app.send_message(
                    chat_id=log_group_id,
                    text=f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>ᴛʀᴀᴄᴋ ɪɴғᴏʀᴍᴀᴛɪᴏɴ</b>.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
                )
    else:
        out = await private_panel(_, bot_id=client.me.id)
        baby = await message.reply_text(f"**__ᴅɪηɢ ᴅᴏηɢ.🥀__**")
        await baby.edit_text(f"**__ᴅɪηɢ ᴅᴏηɢ..🥀__**")
        await baby.edit_text(f"**__ᴅɪηɢ ᴅᴏηɢ...🥀__**")
        await baby.edit_text(f"**__ᴅɪηɢ ᴅᴏηɢ....🥀__**")
        await baby.edit_text(f"**__ᴅɪηɢ ᴅᴏηɢ.....🥀__**")
        await baby.edit_text(f"**__sᴛᴧʀᴛɪηɢ.❤️‍🔥__**")
        await baby.edit_text(f"**__sᴛᴧʀᴛɪηɢ..❤️‍🔥__**")
        await baby.edit_text(f"**__sᴛᴧʀᴛɪηɢ...❤️‍🔥__**")
        await baby.edit_text(f"**__sᴛᴧʀᴛɪηɢ....❤️‍🔥__**")
        await baby.edit_text(f"**__sᴛᴧʀᴛɪηɢ.....❤️‍🔥__**")
        await baby.edit_text(f"**__ʙσᴛ sᴛᴧʀᴛєᴅ.💤__**")
        await baby.edit_text(f"**__ʙσᴛ sᴛᴧʀᴛєᴅ..💤__**")
        await baby.edit_text(f"**__ʙσᴛ sᴛᴧʀᴛєᴅ...💤__**")
        await baby.edit_text(f"**__ʙσᴛ sᴛᴧʀᴛєᴅ....💤__**")
        await baby.edit_text(f"**__ʙσᴛ sᴛᴧʀᴛєᴅ.....💤__**")
        await baby.delete()

        # Context-aware welcome customization for Cloned bot
        welcome_img = random.choice(NEXIO)
        welcome_caption = _["start_2"].format(message.from_user.mention, app.mention)

        try:
            from SONALI_MUSIC.utils.database_clone import get_clone_by_id
            clone = await get_clone_by_id(client.me.id)
            if clone:
                settings = clone.get("settings", {})
                cust_img = settings.get("welcome_img")
                cust_text = settings.get("welcome_text")
                if cust_img and cust_img != "https://litter.catbox.moe/xr9jf82b2umeke7j.jpg":
                    welcome_img = cust_img
                if cust_text and cust_text != "Welcome to my cloned music player bot!":
                    welcome_caption = cust_text.replace("{user}", message.from_user.first_name).replace("{mention}", message.from_user.mention)
        except Exception as e:
            print(f"Error loading clone welcome customization: {e}")
        
        await message.reply_photo(
            welcome_img,
            caption=welcome_caption,
            reply_markup=InlineKeyboardMarkup(out),
            has_spoiler=True,
        )
        if await is_on_off(2):
            log_group_id = await get_log_group_id()
            return await app.send_message(
                chat_id=log_group_id,
                text=f"{message.from_user.mention} 🚀 Just Started the Bot!.\n\n<b>🆔 Telegram ID :</b> <code>{message.from_user.id}</code>\n<b>🔗 Username:  :</b> @{message.from_user.username}",
            )
 
@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    out = start_panel(_)
    uptime = int(time.time() - _boot_)
    await message.reply_photo(
        random.choice(NEXIO),
        caption=_["start_1"].format(app.mention, get_readable_time(uptime)),
        reply_markup=InlineKeyboardMarkup(out),
        has_spoiler=True,
    )
    return await add_served_chat(message.chat.id)
 
@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)
            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                except:
                    pass
            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    return await app.leave_chat(message.chat.id)
                if message.chat.id in await blacklisted_chats():
                    await message.reply_text(
                        _["start_5"].format(
                            app.mention,
                            f"https://t.me/{app.username}?start=sudolist",
                            config.SUPPORT_CHAT,
                        ),
                        disable_web_page_preview=True,
                    )
                    return await app.leave_chat(message.chat.id)
 
                out = start_panel(_)
                await message.reply_photo(
                    random.choice(NEXIO),
                    caption=_["start_3"].format(
                        message.from_user.mention,
                        app.mention,
                        message.chat.title,
                        app.mention,
                    ),
                    reply_markup=InlineKeyboardMarkup(out),
                    has_spoiler=True,
                )
                await add_served_chat(message.chat.id)
                await message.stop_propagation()
        except Exception as ex:
            print(ex)
