from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import time
import logging

import config
from SONALI_MUSIC import app
from SONALI_MUSIC.core.clone_manager import clone_manager
from SONALI_MUSIC.utils.database_clone import (
    get_user_clones,
    save_clone_bot,
    delete_clone_bot,
    check_premium_access,
    update_clone_settings,
    get_clone_by_id,
    log_audit_trail,
    update_clone_assistant_settings,
    update_clone_log_group
)
from SONALI_MUSIC.utils.Sona_font import Fonts

logger = logging.getLogger(__name__)

# Helper to format small cap text
def to_smallcap(text: str) -> str:
    return Fonts.smallcap(text)

# Active interactive state dictionary
# user_id -> {"action": str, "bot_id": int}
user_states = {}

async def check_premium_or_owner(user_id: int) -> bool:
    return True

# Reusable detailed control panel
async def send_bot_details_panel(chat_id, bot_id, reply_to_message_id=None, query=None):
    clone = await get_clone_by_id(bot_id)
    if not clone:
        if query:
            await query.answer("Clone not found.", show_alert=True)
        return

    settings = clone.get("settings", {})
    assistant_mode = clone.get("assistant_mode", "system").upper()
    assistant_id = clone.get("assistant_id", 1)

    welcome_text = settings.get('welcome_text', 'Welcome to my cloned music player bot!')
    welcome_img = settings.get('welcome_img', 'https://litter.catbox.moe/xr9jf82b2umeke7j.jpg')
    play_img = settings.get('play_img', 'https://graph.org/file/4fb9a698630aa5b47be05-060979d72b7752fc8f.jpg')
    play_text = settings.get('play_text', '🎀 **Started Streaming**\n\n🩶 **Title:** {title}\n🪐 **Duration:** {duration} minutes\n🎧 **Requested by:** {user}\n\n🎀 **Powered By:** @{bot_username}')

    text = (
        f"🌌 **『 {clone.get('bot_name')} - ᴄʟᴏɴᴇ ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ 』**\n\n"
        f"🌟 **ʙᴏᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ:**\n"
        f" ├ 👤 **ɴᴀᴍᴇ:** {clone.get('bot_name')}\n"
        f" ├ 🤖 **ᴜsᴇʀɴᴀᴍᴇ:** @{clone.get('bot_username')}\n"
        f" └ ⚡ **sᴛᴀᴛᴜs:** {clone.get('status').upper()}\n\n"
        f"⚙️ **ᴄᴜʀʀᴇɴᴛ ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ:**\n"
        f" ├ 🏷️ **ʙʀᴀɴᴅɪɴɢ ᴛɪᴛʟᴇ:** {settings.get('title')}\n"
        f" ├ 🖼️ **ʙʀᴀɴᴅɪɴɢ ɪᴍᴀɢᴇ:** [ᴄʟɪᴄᴋ ʜᴇʀᴇ ᴛᴏ ᴠɪᴇᴡ]({settings.get('branding_url')})\n"
        f" ├ 🎤 **ᴀssɪsᴛᴀɴᴛ sᴇᴛᴛɪɴɢ:** {assistant_mode} (ᴀssɪsᴛᴀɴᴛ {assistant_id if assistant_mode == 'SYSTEM' else 'ᴄᴜsᴛᴏᴍ'})\n"
        f" ├ 📥 **ᴘʟᴀʏ ᴘʀᴇғᴇʀᴇɴᴄᴇ:** {settings.get('playback_preferences')}\n"
        f" ├ 🔄 **ǫᴜᴇᴜᴇ ʙᴇʜᴀᴠɪᴏʀ:** {settings.get('queue_behavior')}\n"
        f" ├ 📋 **ʟᴏɢ ɢʀᴏᴜᴘ ɪᴅ:** {clone.get('log_group_id') or 'Not Configured'}\n"
        f" ├ 👋 **ᴡᴇʟᴄᴏᴍᴇ ᴛᴇxᴛ:** {welcome_text}\n"
        f" ├ 🖼️ **ᴡᴇʟᴄᴏᴍᴇ ɪᴍᴀɢᴇ:** [ᴠɪᴇᴡ ɪᴍᴀɢᴇ]({welcome_img})\n"
        f" ├ 🖼️ **ᴘʟᴀʏ ɪᴍᴀɢᴇ:** [ᴠɪᴇᴡ ɪᴍᴀɢᴇ]({play_img})\n"
        f" ├ 📝 **ᴘʟᴀʏ ᴛᴇxᴛ:** {play_text[:50]}...\n"
        f" └ 📢 **ᴀᴅs sᴛᴀᴛᴜs:** {'DISABLED (OFF) 🚫' if settings.get('ads_off', False) else 'ENABLED (ON) ✅'}\n\n"
        f"✨ *ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ᴍᴏᴅɪғʏ ᴀɴʏ sᴇᴛᴛɪɴɢ ᴏғ ʏᴏᴜʀ ᴄʟᴏɴᴇ sᴇᴀᴍʟᴇssʟʏ!*"
    )

    buttons = [
        [
            InlineKeyboardButton("👑 ᴄʜᴀɴɢᴇ ᴀssɪsᴛᴀɴᴛ", callback_data=f"EDIT_ASSISTANT_{bot_id}"),
        ],
        [
            InlineKeyboardButton("📝 ᴄʜᴀɴɢᴇ ʙʀᴀɴᴅɪɴɢ", callback_data=f"EDIT_BRAND_{bot_id}"),
            InlineKeyboardButton("👋 ᴄʜᴀɴɢᴇ ᴡᴇʟᴄᴏᴍᴇ", callback_data=f"EDIT_WELCOME_SUB_{bot_id}")
        ],
        [
            InlineKeyboardButton("🎵 ᴘʟᴀʏ ᴄᴜsᴛᴏᴍɪᴢᴇ", callback_data=f"EDIT_PLAY_CUSTOM_{bot_id}"),
            InlineKeyboardButton("🔗 sᴇᴛ ʙᴏᴛ ʟɪɴᴋs", callback_data=f"EDIT_LINKS_{bot_id}")
        ],
        [
            InlineKeyboardButton("📝 ᴄʜᴀɴɢᴇ ᴄᴧᴘᴛɪᴏɴs", callback_data=f"EDIT_CAPTIONS_SUB_{bot_id}_1"),
            InlineKeyboardButton("📥 ᴘʟᴀʏ ᴘʀᴇғᴇʀᴇɴᴄᴇ", callback_data=f"EDIT_PLAY_{bot_id}")
        ],
        [
            InlineKeyboardButton("🔄 ǫᴜᴇᴜᴇ ʙᴇʜᴀᴠɪᴏʀ", callback_data=f"EDIT_QUEUE_{bot_id}"),
            InlineKeyboardButton("📝 sᴇᴛ ʟᴏɢ ɢʀᴏᴜᴘ", callback_data=f"EDIT_LOG_GROUP_{bot_id}")
        ],
        [
            InlineKeyboardButton("⚠️ ᴅᴇʟᴇᴛᴇ ᴄʟᴏɴᴇ", callback_data=f"DELETE_CONFIRM_{bot_id}")
        ],
        [
            InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="MANAGE_CLONE_BTN")
        ]
    ]

    markup = InlineKeyboardMarkup(buttons)
    if query:
        await query.message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
    else:
        await app.send_message(chat_id, text, reply_markup=markup, reply_to_message_id=reply_to_message_id, disable_web_page_preview=True)

# ----------------------------------------------------------------------
# 1. COMMAND: /CLONE & CLONE_BTN CALLBACK
# ----------------------------------------------------------------------

@app.on_message(filters.command(["clone"]) & filters.private)
async def clone_cmd_handler(client, message: Message):
    user_id = message.from_user.id

    is_owner = (user_id == config.OWNER_ID)
    premium_status = await check_premium_access(user_id)

    parts = message.text.split(None, 1)
    if len(parts) < 2:
        return await message.reply_text(
            f"🤖 **{to_smallcap('how to clone')}**\n\n"
            f"To clone the music bot, get a bot token from @BotFather and send:\n"
            f"`/clone BOT_TOKEN_HERE`"
        )

    bot_token = parts[1].strip()

    # CHECK FORCE SUBSCRIBE FIRST
    from SONALI_MUSIC.utils.database_clone import get_force_sub
    force_sub_channel = await get_force_sub()
    if force_sub_channel:
        try:
            await app.get_chat_member(force_sub_channel, user_id)
        except Exception:
            link = f"https://t.me/{force_sub_channel}"
            return await message.reply_text(
                f"⚠️ **{to_smallcap('force subscription required')}**\n\n"
                f"You must join our updates channel first before you can clone a bot!\n\n"
                f"Please join @{force_sub_channel} and try again.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("📢 Join Channel", url=link)
                        ]
                    ]
                )
            )

    status_msg = await message.reply_text("🔍 **Checking bot token...**")

    # Check limits
    user_clones = await get_user_clones(user_id)
    limit = premium_status.get("permissions", {}).get("limits", 1) if not is_owner else 99999
    if len(user_clones) >= limit:
        return await status_msg.edit_text(
            f"❌ **{to_smallcap('clone limit reached')}**\n\n"
            f"Your current plan allows up to {limit} clones. You currently have {len(user_clones)}."
        )

    # Spin up client temporarily to validate
    temp_client = Client(
        name=f"temp_validate_{int(time.time())}",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=bot_token,
        in_memory=True
    )

    try:
        await temp_client.start()
        bot_info = temp_client.me
        await temp_client.stop()
    except Exception as e:
        logger.error(f"Failed to validate token: {e}")
        return await status_msg.edit_text(
            f"❌ **{to_smallcap('invalid token')}**\n\n"
            f"The provided Telegram bot token is invalid or expired. Check @BotFather."
        )

    # Save and start clone
    success = await save_clone_bot(
        tenant_id=user_id,
        bot_token=bot_token,
        bot_id=bot_info.id,
        bot_name=bot_info.first_name,
        bot_username=bot_info.username,
        tenant_username=message.from_user.username
    )

    if success:
        started = await clone_manager.start_clone(bot_token, user_id)
        if started:
            await status_msg.edit_text(
                f"✅ **{to_smallcap('cloning successful')}**\n\n"
                f"Your cloned bot is now running independently!\n"
                f"Bot Name: **{bot_info.first_name}**\n"
                f"Bot Username: @{bot_info.username}\n\n"
                f"Use `/manage_clone` to customize its settings."
            )
            await log_audit_trail(user_id, "clone_created", f"Created cloned bot @{bot_info.username}")
        else:
            await status_msg.edit_text("❌ Failed to register cloned bot client. Please contact support.")
    else:
        await status_msg.edit_text("❌ Failed to save cloned bot to database.")


@app.on_callback_query(filters.regex("^CLONE_BTN$"))
async def clone_btn_callback(client, query: CallbackQuery):
    await query.message.reply_text(
        f"🤖 **{to_smallcap('how to clone')}**\n\n"
        f"To clone the music bot, get a bot token from @BotFather and send:\n"
        f"`/clone BOT_TOKEN_HERE`"
    )
    await query.answer()

# ----------------------------------------------------------------------
# 2. COMMAND: /MANAGE_CLONE & MANAGE_CLONE_BTN CALLBACK
# ----------------------------------------------------------------------

@app.on_message(filters.command(["manage_clone", "clone_panel"]) & filters.private)
async def manage_clone_cmd_handler(client, message: Message):
    user_id = message.from_user.id
    user_clones = await get_user_clones(user_id)

    if not user_clones:
        return await message.reply_text(
            f"🔍 **{to_smallcap('no clones found')}**\n\n"
            f"You don't have any cloned bots registered. Use `/clone <token>` first."
        )

    buttons = []
    for clone in user_clones:
        buttons.append([
            InlineKeyboardButton(
                text=f"⚙️ {clone.get('bot_name')}",
                callback_data=f"MANAGE_BOT_{clone.get('bot_id')}"
            )
        ])

    await message.reply_text(
        f"🛠️ **{to_smallcap('manage clones')}**\n\n"
        f"Select a cloned bot to configure settings:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@app.on_callback_query(filters.regex("^MANAGE_CLONE_BTN$"))
async def manage_clone_btn_callback(client, query: CallbackQuery):
    user_id = query.from_user.id
    user_clones = await get_user_clones(user_id)

    if not user_clones:
        return await query.answer(
            to_smallcap("no active clones"),
            show_alert=True
        )

    buttons = []
    for clone in user_clones:
        buttons.append([
            InlineKeyboardButton(
                text=f"⚙️ {clone.get('bot_name')}",
                callback_data=f"MANAGE_BOT_{clone.get('bot_id')}"
            )
        ])

    await query.message.edit_text(
        f"🛠️ **{to_smallcap('manage clones')}**\n\n"
        f"Select a cloned bot to configure settings:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await query.answer()

# ----------------------------------------------------------------------
# 3. INTERACTIVE SETTINGS PANELS
# ----------------------------------------------------------------------

@app.on_callback_query(filters.regex("^MANAGE_BOT_(\\d+)$"))
async def manage_bot_details_panel(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)

    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    # PREMIUM VERIFICATION CHECK
    if not await check_premium_or_owner(user_id):
        await query.message.edit_text(
            f"⚠️ **{to_smallcap('premium required')}**\n\n"
            f"You need a premium subscription to customize and manage your cloned bot's settings.\n\n"
            f"Please contact the owner to buy premium:\n"
            f"👤 **Owner:** @Xbroze",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("💬 Buy Premium", url="https://t.me/Xbroze")
                    ],
                    [
                        InlineKeyboardButton("🔙 Back", callback_data="MANAGE_CLONE_BTN")
                    ]
                ]
            )
        )
        return await query.answer()

    await send_bot_details_panel(user_id, bot_id, query=query)
    await query.answer()

# ----------------------------------------------------------------------
# 4. BRANDING AND ASSISTANT EDIT CALLBACKS
# ----------------------------------------------------------------------

@app.on_callback_query(filters.regex("^EDIT_BRAND_(\\d+)$"))
async def edit_brand_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    settings = clone.get("settings", {})
    text = (
        f"📝 **『 ʙʀᴀɴᴅɪɴɢ ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ 』**\n\n"
        f"🏷️ **ᴄᴜʀʀᴇɴᴛ ᴛɪᴛʟᴇ:** {settings.get('title')}\n"
        f"🖼️ **ᴄᴜʀʀᴇɴᴛ ɪᴍᴀɢᴇ:** {settings.get('branding_url')}\n\n"
        f"ᴡʜᴀᴛ ᴡᴏᴜʟᴅ ʏᴏᴜ ʟɪᴋᴇ ᴛᴏ ᴇᴅɪᴛ ᴍᴀsᴛᴇʀ?"
    )
    buttons = [
        [
            InlineKeyboardButton("🏷️ ᴇᴅɪᴛ ʙʀᴀɴᴅɪɴɢ ᴛɪᴛʟᴇ", callback_data=f"EDIT_BRAND_TITLE_{bot_id}"),
            InlineKeyboardButton("🖼️ ᴇᴅɪᴛ ʙʀᴀɴᴅɪɴɢ ɪᴍᴀɢᴇ", callback_data=f"EDIT_BRAND_IMAGE_{bot_id}"),
        ],
        [
            InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"MANAGE_BOT_{bot_id}")
        ]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await query.answer()


@app.on_callback_query(filters.regex("^EDIT_BRAND_TITLE_(\\d+)$"))
async def edit_brand_title_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_id = query.from_user.id

    user_states[user_id] = {"action": "wait_for_title", "bot_id": bot_id}
    await query.message.reply_text(
        f"✏️ **『 ᴇᴅɪᴛ ʙʀᴀɴᴅɪɴɢ ᴛɪᴛʟᴇ 』**\n\n"
        f"ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ɴᴇᴡ ᴛɪᴛʟᴇ ɴᴀᴍᴇ ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ display ᴏɴ ʏᴏᴜʀ ᴄʟᴏɴᴇ's player panel:\n\n"
        f"*(Send /cancel to cancel this operation)*"
    )
    await query.answer()


@app.on_callback_query(filters.regex("^EDIT_BRAND_IMAGE_(\\d+)$"))
async def edit_brand_image_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_id = query.from_user.id

    user_states[user_id] = {"action": "wait_for_image_url", "bot_id": bot_id}
    await query.message.reply_text(
        f"🖼️ **『 ᴇᴅɪᴛ ʙʀᴀɴᴅɪɴɢ ɪᴍᴀɢᴇ 』**\n\n"
        f"ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴅɪʀᴇᴄᴛ ɪᴍᴀɢᴇ ᴜʀʟ (e.g. from Catbox, Telegraph, etc.) "
        f"ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇᴛ ᴀs ʏᴏᴜʀ ᴄʟᴏɴᴇ's ʙᴀɴɴᴇʀ / ᴛʜᴜᴍʙɴᴀɪʟ:\n\n"
        f"*(Send /cancel to cancel this operation)*"
    )
    await query.answer()


@app.on_callback_query(filters.regex("^EDIT_WELCOME_(\\d+)$"))
async def edit_welcome_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_id = query.from_user.id

    user_states[user_id] = {"action": "wait_for_welcome", "bot_id": bot_id}
    await query.message.reply_text(
        f"👋 **『 ᴇᴅɪᴛ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ 』**\n\n"
        f"ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ɴᴇᴡ ᴡᴇʟᴄᴏᴍᴇ text message ᴛʜᴀᴛ ᴛʜᴇ ʙᴏᴛ ᴡɪʟʟ sᴇɴᴅ ᴡʜᴇɴ ᴀ ᴜsᴇʀ sᴛᴀʀᴛs ɪᴛ:\n\n"
        f"*(Send /cancel to cancel this operation)*"
    )
    await query.answer()


@app.on_callback_query(filters.regex("^EDIT_ASSISTANT_(\\d+)$"))
async def edit_assistant_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    assistant_mode = clone.get("assistant_mode", "system").upper()
    assistant_id = clone.get("assistant_id", 1)

    text = (
        f"👑 **『 ᴀssɪsᴛᴀɴᴛ ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ 』**\n\n"
        f"ʏᴏᴜ ᴄᴀɴ sᴇʟᴇᴄᴛ ᴀɴʏ sʏsᴛᴇᴍ ᴀssɪsᴛᴀɴᴛ (1-5) ᴘʀᴏᴠɪᴅᴇᴅ ʙʏ ᴛʜᴇ ᴘʟᴀᴛғᴏʀᴍ, "
        f"ᴏʀ sᴇᴛ ʏᴏᴜʀ ᴏᴡɴ **ᴄᴜsᴛᴏᴍ ᴀssɪsᴛᴀɴᴛ sᴇssɪᴏɴ sᴛʀɪɴɢ**!\n\n"
        f"⚙️ **ᴄᴜʀʀᴇɴᴛ sᴇᴛᴛɪɴɢ:**\n"
        f" ├ 🕹️ **ᴍᴏᴅᴇ:** {assistant_mode}\n"
        f" └ 🤖 **ᴀssɪsᴛᴀɴᴛ:** {f'System Assistant ' + str(assistant_id) if assistant_mode == 'SYSTEM' else 'Custom Assistant'}"
    )

    buttons = [
        [
            InlineKeyboardButton("🤖 ᴀssɪsᴛᴀɴᴛ 1", callback_data=f"SET_SYS_ASS_{bot_id}_1"),
            InlineKeyboardButton("🤖 ᴀssɪsᴛᴀɴᴛ 2", callback_data=f"SET_SYS_ASS_{bot_id}_2"),
        ],
        [
            InlineKeyboardButton("🤖 ᴀssɪsᴛᴀɴᴛ 3", callback_data=f"SET_SYS_ASS_{bot_id}_3"),
            InlineKeyboardButton("🤖 ᴀssɪsᴛᴀɴᴛ 4", callback_data=f"SET_SYS_ASS_{bot_id}_4"),
        ],
        [
            InlineKeyboardButton("🤖 ᴀssɪsᴛᴀɴᴛ 5", callback_data=f"SET_SYS_ASS_{bot_id}_5"),
        ],
        [
            InlineKeyboardButton("🔑 sᴇᴛ ᴄᴜsᴛᴏᴍ sᴇssɪᴏɴ", callback_data=f"SET_CUST_ASS_{bot_id}"),
        ],
        [
            InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"MANAGE_BOT_{bot_id}")
        ]
    ]

    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await query.answer()


@app.on_callback_query(filters.regex("^SET_SYS_ASS_(\\d+)_(\\d+)$"))
async def set_sys_assistant_callback(client, query: CallbackQuery):
    parts = query.data.split("_")
    bot_id = int(parts[3])
    assistant_id = int(parts[4])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    # Stop custom assistant first if active
    from SONALI_MUSIC.core.call import Sona
    await Sona.stop_custom_assistant(bot_id)

    # Save system assistant settings
    await update_clone_assistant_settings(bot_id, mode="system", assistant_id=assistant_id)

    await query.answer(f"✅ Configured to use System Assistant {assistant_id} successfully!", show_alert=True)
    # Refresh panel
    await send_bot_details_panel(user_id, bot_id, query=query)


@app.on_callback_query(filters.regex("^SET_CUST_ASS_(\\d+)$"))
async def set_cust_assistant_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_id = query.from_user.id

    user_states[user_id] = {"action": "wait_for_custom_session", "bot_id": bot_id}
    await query.message.reply_text(
        f"🔑 **『 sᴇᴛ ᴄᴜsᴛᴏᴍ ᴀssɪsᴛᴀɴᴛ 』**\n\n"
        f"ᴘʟᴇᴀsᴇ sᴇɴᴅ ʏᴏᴜʀ Pyrogram Userbot Session String:\n\n"
        f"⚠️ **ɪᴍᴘᴏʀᴛᴀɴᴛ:**\n"
        f" - Make sure the session string is generated for Pyrogram v2.\n"
        f" - Your userbot must have joined the support group and log channels.\n\n"
        f"*(Send /cancel to cancel this operation)*"
    )
    await query.answer()


@app.on_callback_query(filters.regex("^EDIT_PLAY_(\\d+)$"))
async def edit_play_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    settings = clone.get("settings", {})
    current_pref = settings.get("playback_preferences", "Direct")
    new_pref = "Everyone" if current_pref == "Direct" else "Direct"

    settings["playback_preferences"] = new_pref
    await update_clone_settings(bot_id, settings)

    await query.answer(f"✅ Play Preference changed to {new_pref}!", show_alert=True)
    # Refresh panel
    await send_bot_details_panel(user_id, bot_id, query=query)


@app.on_callback_query(filters.regex("^EDIT_QUEUE_(\\d+)$"))
async def edit_queue_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    settings = clone.get("settings", {})
    current_behavior = settings.get("queue_behavior", "Standard")
    new_behavior = "Autoplay" if current_behavior == "Standard" else "Standard"

    settings["queue_behavior"] = new_behavior
    await update_clone_settings(bot_id, settings)

    await query.answer(f"✅ Queue Behavior changed to {new_behavior}!", show_alert=True)
    # Refresh panel
    await send_bot_details_panel(user_id, bot_id, query=query)


@app.on_callback_query(filters.regex("^TOGGLE_ADS_(\\d+)$"))
async def toggle_ads_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    # PREMIUM VERIFICATION CHECK
    if not await check_premium_or_owner(user_id):
        return await query.answer(
            "❌ Premium Required!\n\nYou must have a premium subscription to turn Ads OFF. Contact @Xbroze to upgrade.",
            show_alert=True
        )

    settings = clone.get("settings", {})
    current_ads_off = settings.get("ads_off", False)
    new_ads_off = not current_ads_off

    settings["ads_off"] = new_ads_off
    await update_clone_settings(bot_id, settings)

    await query.answer(
        f"📢 Ads have been successfully {'DISABLED (OFF) 🚫' if new_ads_off else 'ENABLED (ON) ✅'}!",
        show_alert=True
    )
    # Refresh panel
    await send_bot_details_panel(user_id, bot_id, query=query)


@app.on_callback_query(filters.regex("^EDIT_LOG_GROUP_(\\d+)$"))
async def edit_log_group_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    user_states[user_id] = {"action": "wait_for_log_group", "bot_id": bot_id}
    await query.message.reply_text(
        f"📝 **『 sᴇᴛ ʟᴏɢ ɢʀᴏᴜᴘ ɪᴅ 』**\n\n"
        f"ᴘʟᴇᴀsᴇ sᴇɴᴅ ʏᴏᴜʀ ʟᴏɢ ɢʀᴏᴜᴘ ɪᴅ (e.g. `-1001234567890`):\n\n"
        f"⚠️ **ɪᴍᴘᴏʀᴛᴀɴᴛ:**\n"
        f" - Ensure that both your cloned bot and the assistant have been added to this group as admins.\n"
        f" - Send `/reset` to clear the log group configuration.\n"
        f" - Send `/cancel` to abort."
    )
    await query.answer()


@app.on_callback_query(filters.regex("^DELETE_CONFIRM_(\\d+)$"))
async def delete_confirm_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    text = (
        f"⚠️ **{to_smallcap('confirm delete')}**\n\n"
        f"Are you sure you want to delete cloned bot **{clone.get('bot_name')}**?\n"
        f"This action cannot be undone."
    )

    buttons = [
        [
            InlineKeyboardButton(f"✅ {to_smallcap('yes')}", callback_data=f"DELETE_YES_{bot_id}"),
            InlineKeyboardButton(f"❌ {to_smallcap('no')}", callback_data=f"MANAGE_BOT_{bot_id}")
        ]
    ]

    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await query.answer()


@app.on_callback_query(filters.regex("^DELETE_YES_(\\d+)$"))
async def delete_yes_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    # Stop clone inside manager
    await clone_manager.stop_clone(bot_id)
    # Remove from DB
    await delete_clone_bot(bot_id)

    await query.answer("Cloned Bot deleted successfully.", show_alert=True)
    await query.message.edit_text(f"✅ **{to_smallcap('deleted successfully')}**")
    await log_audit_trail(user_id, "clone_deleted", f"Deleted cloned bot {bot_id}")

# ----------------------------------------------------------------------
# 5. GENERAL PRIVATE MESSAGE HANDLER FOR INTERACTIVE STATE INPUTS
# ----------------------------------------------------------------------

@app.on_message(filters.private & ~filters.command(["start", "help", "clone", "manage_clone"]))
async def handle_user_input_state(client, message: Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    if not state:
        return

    bot_id = state["bot_id"]
    action = state["action"]

    # Handle cancellation
    if message.text and message.text.strip().lower() == "/cancel":
        del user_states[user_id]
        await message.reply_text("❌ **Operation cancelled successfully.**")
        await send_bot_details_panel(user_id, bot_id)
        return

    clone = await get_clone_by_id(bot_id)
    if not clone:
        del user_states[user_id]
        return await message.reply_text("❌ Clone not found.")

    settings = clone.get("settings", {})

    text_val = message.text.strip() if message.text else ""

    if action == "wait_for_link_channel":
        if text_val.lower() == "/reset":
            settings["channel_link"] = None
            await update_clone_settings(bot_id, settings)
            user_states.pop(user_id, None)
            await message.reply_text("🔄 Update channel link reset to default!")
            return await send_bot_details_panel(user_id, bot_id)

        link = text_val
        if link.startswith("@"):
            link = f"https://t.me/{link[1:]}"
        elif not link.startswith("http://") and not link.startswith("https://") and not link.startswith("tg://"):
            link = f"https://{link}"

        settings["channel_link"] = link
        await update_clone_settings(bot_id, settings)
        user_states.pop(user_id, None)
        await message.reply_text(f"✅ Update Channel Link saved: `{link}`")
        return await send_bot_details_panel(user_id, bot_id)

    elif action == "wait_for_link_support":
        if text_val.lower() == "/reset":
            settings["support_link"] = None
            await update_clone_settings(bot_id, settings)
            user_states.pop(user_id, None)
            await message.reply_text("🔄 Support group link reset to default!")
            return await send_bot_details_panel(user_id, bot_id)

        link = text_val
        if link.startswith("@"):
            link = f"https://t.me/{link[1:]}"
        elif not link.startswith("http://") and not link.startswith("https://") and not link.startswith("tg://"):
            link = f"https://{link}"

        settings["support_link"] = link
        await update_clone_settings(bot_id, settings)
        user_states.pop(user_id, None)
        await message.reply_text(f"✅ Support Group Link saved: `{link}`")
        return await send_bot_details_panel(user_id, bot_id)

    elif action == "wait_for_quick_step1":
        link = text_val
        if link.startswith("@"):
            link = f"https://t.me/{link[1:]}"
        elif not link.startswith("http://") and not link.startswith("https://") and not link.startswith("tg://"):
            link = f"https://{link}"

        settings["channel_link"] = link
        await update_clone_settings(bot_id, settings)

        user_states[user_id] = {"action": "wait_for_quick_step2", "bot_id": bot_id}
        await message.reply_text(
            f"⚡ **『 ǫᴜɪᴄᴋ ʟɪɴᴋ sᴇᴛᴜᴘ - sᴛᴇᴘ 2/2 』**\n\n"
            f"✅ Update Channel saved: `{link}`\n\n"
            f"Now please send your **Support Group link** (e.g. `https://t.me/YourGroup` or `@YourGroup`):\n\n"
            f"Send `/cancel` to abort."
        )
        return

    elif action == "wait_for_quick_step2":
        link = text_val
        if link.startswith("@"):
            link = f"https://t.me/{link[1:]}"
        elif not link.startswith("http://") and not link.startswith("https://") and not link.startswith("tg://"):
            link = f"https://{link}"

        settings["support_link"] = link
        await update_clone_settings(bot_id, settings)
        user_states.pop(user_id, None)

        await message.reply_text(
            f"🎉 **All Links Configured Successfully!**\n\n"
            f"📢 Update Channel: `{settings.get('channel_link')}`\n"
            f"💬 Support Group: `{link}`\n\n"
            f"Your cloned bot's start panel buttons now point to your links!"
        )
        return await send_bot_details_panel(user_id, bot_id)

    elif action == "wait_for_title":
        new_title = message.text.strip()
        if not new_title:
            return await message.reply_text("❌ **Title cannot be empty! Please send a valid text.**")

        settings["title"] = new_title
        await update_clone_settings(bot_id, settings)
        del user_states[user_id]

        await message.reply_text(f"✅ **Branding Title successfully updated to:**\n`{new_title}`")
        await send_bot_details_panel(user_id, bot_id)

    elif action == "wait_for_image_url":
        new_url = message.text.strip()
        if not new_url.startswith("http://") and not new_url.startswith("https://"):
            return await message.reply_text("❌ **Invalid URL! Please send a direct image link starting with http:// or https://.**")

        settings["branding_url"] = new_url
        await update_clone_settings(bot_id, settings)
        del user_states[user_id]

        await message.reply_text(f"✅ **Branding Image successfully updated to:**\n{new_url}")
        await send_bot_details_panel(user_id, bot_id)

    elif action == "wait_for_welcome":
        new_welcome = message.text.strip()
        if not new_welcome:
            return await message.reply_text("❌ **Welcome message cannot be empty! Please send a valid text.**")

        settings["welcome_text"] = new_welcome
        await update_clone_settings(bot_id, settings)
        del user_states[user_id]

        await message.reply_text(f"✅ **Welcome message successfully updated.**")
        await send_bot_details_panel(user_id, bot_id)

    elif action == "wait_for_welcome_img":
        new_url = message.text.strip()
        if not new_url.startswith("http://") and not new_url.startswith("https://"):
            return await message.reply_text("❌ **Invalid URL! Please send a direct image link starting with http:// or https://.**")

        settings["welcome_img"] = new_url
        await update_clone_settings(bot_id, settings)
        del user_states[user_id]

        await message.reply_text(f"✅ **Welcome Image successfully updated to:**\n{new_url}")
        await send_bot_details_panel(user_id, bot_id)

    elif action == "wait_for_play_img":
        new_url = message.text.strip()
        if not new_url.startswith("http://") and not new_url.startswith("https://"):
            return await message.reply_text("❌ **Invalid URL! Please send a direct image link starting with http:// or https://.**")

        settings["play_img"] = new_url
        await update_clone_settings(bot_id, settings)
        del user_states[user_id]

        await message.reply_text(f"✅ **Play Message Image successfully updated to:**\n{new_url}")
        await send_bot_details_panel(user_id, bot_id)

    elif action == "wait_for_play_text":
        new_text = message.text.strip()
        if not new_text:
            return await message.reply_text("❌ **Play message text cannot be empty! Please send a valid text.**")

        settings["play_text"] = new_text
        await update_clone_settings(bot_id, settings)
        del user_states[user_id]

        await message.reply_text(f"✅ **Play Message Text successfully updated.**")
        await send_bot_details_panel(user_id, bot_id)

    elif action.startswith("wait_for_help_text_"):
        key = action.replace("wait_for_help_text_", "")
        new_val = message.text.strip() if message.text else ""

        if not new_val:
            return await message.reply_text("❌ **Text cannot be empty! Please send a valid text.**")

        help_texts = settings.get("help_texts", {})
        if new_val.lower() == "/reset":
            if key in help_texts:
                del help_texts[key]
            await message.reply_text(f"✅ **Restored default text for {key}!**")
        else:
            help_texts[key] = new_val
            await message.reply_text(f"✅ **Successfully updated custom caption/text!**")

        settings["help_texts"] = help_texts
        await update_clone_settings(bot_id, settings)
        del user_states[user_id]

        await send_bot_details_panel(user_id, bot_id)
        return

    elif action == "wait_for_custom_session":
        session_string = message.text.strip()
        if not session_string:
            return await message.reply_text("❌ **Session string cannot be empty!**")

        status_msg = await message.reply_text("⏳ **Testing connection for the custom assistant...**")

        # Validate Pyrogram Session String
        temp_client = Client(
            name=f"temp_cust_ass_{int(time.time())}",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=session_string,
            in_memory=True
        )

        try:
            await temp_client.start()
            me = temp_client.me
            await temp_client.stop()
        except Exception as e:
            logger.error(f"Failed to validate custom assistant session: {e}")
            return await status_msg.edit_text(
                f"❌ **Invalid Session String!**\n\n"
                f"Could not connect to Telegram using the provided session string.\n"
                f"Error: `{e}`\n\n"
                f"Please try again or send `/cancel` to abort."
            )

        # Start dynamic assistant in Call manager
        from SONALI_MUSIC.core.call import Sona
        await status_msg.edit_text("🚀 **Starting custom assistant client...**")
        started = await Sona.start_custom_assistant(bot_id, session_string)

        if started:
            await update_clone_assistant_settings(bot_id, mode="custom", assistant_id=1, custom_session=session_string)
            del user_states[user_id]
            await status_msg.edit_text(
                f"✅ **Custom Assistant Configured Successfully!**\n\n"
                f"Assistant User: @{me.username or ''} ({me.first_name})\n\n"
                f"Your cloned bot will now play music using this custom assistant."
            )
            await send_bot_details_panel(user_id, bot_id)
        else:
            await status_msg.edit_text("❌ **Failed to start Custom Assistant inside Call manager.**")

    elif action == "wait_for_log_group":
        text_val = message.text.strip()
        if text_val == "/reset":
            await update_clone_log_group(bot_id, None)
            del user_states[user_id]
            await message.reply_text("✅ **Log Group ID reset to default (system main log group).**")
            await send_bot_details_panel(user_id, bot_id)
            return

        try:
            log_group_id = int(text_val)
        except ValueError:
            return await message.reply_text("❌ **Invalid ID! Please send a valid integer (e.g., -1001234567890). Try again or send /cancel:**")

        await update_clone_log_group(bot_id, log_group_id)
        del user_states[user_id]

        await message.reply_text(f"✅ **Log Group ID successfully set to:** `{log_group_id}`")
        await send_bot_details_panel(user_id, bot_id)
        return


# ----------------------------------------------------------------------
# NEW SUB PANELS FOR WELCOME AND PLAY CUSTOMIZATION
# ----------------------------------------------------------------------

@app.on_callback_query(filters.regex("^EDIT_WELCOME_SUB_(\\d+)$"))
async def edit_welcome_sub_panel_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    settings = clone.get("settings", {})
    welcome_text = settings.get("welcome_text", "Welcome to my cloned music player bot!")
    welcome_img = settings.get("welcome_img", "https://litter.catbox.moe/xr9jf82b2umeke7j.jpg")

    text = (
        f"👋 **『 ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ ᴄᴜsᴛᴏᴍɪᴢᴀᴛɪᴏɴ 』**\n\n"
        f"👋 **ᴄᴜʀʀᴇɴᴛ ᴡᴇʟᴄᴏᴍᴇ ᴛᴇxᴛ:**\n`{welcome_text}`\n\n"
        f"🖼️ **ᴄᴜʀʀᴇɴᴛ ᴡᴇʟᴄᴏᴍᴇ ɪᴍᴀɢᴇ:**\n{welcome_img}\n\n"
        f"ᴡʜᴀᴛ ᴡᴏᴜʟᴅ ʏᴏᴜ ʟɪᴋᴇ ᴛᴏ ᴇᴅɪᴛ?"
    )
    buttons = [
        [
            InlineKeyboardButton("📝 ᴇᴅɪᴛ ᴡᴇʟᴄᴏᴍᴇ ᴛᴇxᴛ", callback_data=f"EDIT_WELCOME_TEXT_OPT_{bot_id}"),
            InlineKeyboardButton("🖼️ ᴇᴅɪᴛ ᴡᴇʟᴄᴏᴍᴇ ɪᴍᴀɢᴇ", callback_data=f"EDIT_WELCOME_IMAGE_OPT_{bot_id}"),
        ],
        [
            InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"MANAGE_BOT_{bot_id}")
        ]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)
    await query.answer()


@app.on_callback_query(filters.regex("^EDIT_WELCOME_TEXT_OPT_(\\d+)$"))
async def edit_welcome_text_opt_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[4])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    settings = clone.get("settings", {})
    old_welcome = settings.get("welcome_text", "Welcome to my cloned music player bot!")

    user_states[user_id] = {"action": "wait_for_welcome", "bot_id": bot_id}
    await query.message.reply_text(
        f"👋 **『 ᴇᴅɪᴛ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ 』**\n\n"
        f"🔍 **ᴄᴜʀʀᴇɴᴛ ᴡᴇʟᴄᴏᴍᴇ ᴛᴇxᴛ:**\n`{old_welcome}`\n\n"
        f"ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ **ɴᴇᴡ** ᴡᴇʟᴄᴏᴍᴇ text message ᴛʜᴀᴛ ᴛʜᴇ ʙᴏᴛ ᴡɪʟʟ sᴇɴᴅ ᴡʜᴇɴ ᴀ ᴜsᴇʀ sᴛᴀʀᴛs ɪᴛ:\n"
        f"*(You can use placeholders like {{user}} or {{mention}})*\n\n"
        f"*(Send /cancel to cancel this operation)*"
    )
    await query.answer()


@app.on_callback_query(filters.regex("^EDIT_WELCOME_IMAGE_OPT_(\\d+)$"))
async def edit_welcome_image_opt_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[4])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    settings = clone.get("settings", {})
    old_img = settings.get("welcome_img", "https://litter.catbox.moe/xr9jf82b2umeke7j.jpg")

    user_states[user_id] = {"action": "wait_for_welcome_img", "bot_id": bot_id}
    await query.message.reply_text(
        f"🖼️ **『 ᴇᴅɪᴛ ᴡᴇʟᴄᴏᴍᴇ ɪᴍᴀɢᴇ 』**\n\n"
        f"🔍 **ᴄᴜʀʀᴇɴᴛ ᴡᴇʟᴄᴏᴍᴇ ɪᴍᴀɢᴇ:**\n{old_img}\n\n"
        f"ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴅɪʀᴇᴄᴛ ɪᴍᴀɢᴇ ᴜʀʟ (e.g. from Catbox, Telegraph, etc.) "
        f"ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇᴛ ᴀs ʏᴏᴜʀ ᴄʟᴏɴᴇ's ᴡᴇʟᴄᴏᴍᴇ ʙᴀɴɴᴇʀ:\n\n"
        f"*(Send /cancel to cancel this operation)*"
    )
    await query.answer()


@app.on_callback_query(filters.regex("^EDIT_PLAY_CUSTOM_(\\d+)$"))
async def edit_play_custom_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    settings = clone.get("settings", {})
    play_text = settings.get("play_text", "🎀 **Started Streaming**\n\n🩶 **Title:** {title}\n🪐 **Duration:** {duration} minutes\n🎧 **Requested by:** {user}\n\n🎀 **Powered By:** @{bot_username}")
    play_img = settings.get("play_img", "https://graph.org/file/4fb9a698630aa5b47be05-060979d72b7752fc8f.jpg")

    text = (
        f"🎵 **『 ᴘʟᴀʏ ᴍᴇssᴀɢᴇ ᴄᴜsᴛᴏᴍɪᴢᴀᴛɪᴏɴ 』**\n\n"
        f"🎵 **ᴄᴜʀʀᴇɴᴛ ᴘʟᴀʏ ᴛᴇxᴛ:**\n`{play_text}`\n\n"
        f"🖼️ **ᴄᴜʀʀᴇɴᴛ ᴘʟᴀʏ ɪᴍᴀɢᴇ:**\n{play_img}\n\n"
        f"ᴡʜᴀᴛ ᴡᴏᴜʟᴅ ʏᴏᴜ ʟɪᴋᴇ ᴛᴏ ᴇᴅɪᴛ?"
    )
    buttons = [
        [
            InlineKeyboardButton("📝 ᴇᴅɪᴛ ᴘʟᴀʏ ᴛᴇxᴛ", callback_data=f"EDIT_PLAY_TEXT_OPT_{bot_id}"),
            InlineKeyboardButton("🖼️ ᴇᴅɪᴛ ᴘʟᴀʏ ɪᴍᴀɢᴇ", callback_data=f"EDIT_PLAY_IMAGE_OPT_{bot_id}"),
        ],
        [
            InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"MANAGE_BOT_{bot_id}")
        ]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)
    await query.answer()


@app.on_callback_query(filters.regex("^EDIT_PLAY_TEXT_OPT_(\\d+)$"))
async def edit_play_text_opt_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[4])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    settings = clone.get("settings", {})
    old_play_text = settings.get("play_text", "🎀 **Started Streaming**\n\n🩶 **Title:** {title}\n🪐 **Duration:** {duration} minutes\n🎧 **Requested by:** {user}\n\n🎀 **Powered By:** @{bot_username}")

    user_states[user_id] = {"action": "wait_for_play_text", "bot_id": bot_id}
    await query.message.reply_text(
        f"📝 **『 ᴇᴅɪᴛ ᴘʟᴀʏ ᴍᴇssᴀɢᴇ ᴛᴇxᴛ 』**\n\n"
        f"🔍 **ᴄᴜʀʀᴇɴᴛ ᴘʟᴀʏ ᴛᴇxᴛ:**\n`{old_play_text}`\n\n"
        f"ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ **ɴᴇᴡ** play caption template text:\n"
        f"*(You can use placeholders: {{title}}, {{duration}}, {{user}}, {{link}}, {{bot_username}})*\n\n"
        f"*(Send /cancel to cancel this operation)*"
    )
    await query.answer()


@app.on_callback_query(filters.regex("^EDIT_PLAY_IMAGE_OPT_(\\d+)$"))
async def edit_play_image_opt_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[4])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    settings = clone.get("settings", {})
    old_img = settings.get("play_img", "https://graph.org/file/4fb9a698630aa5b47be05-060979d72b7752fc8f.jpg")

    user_states[user_id] = {"action": "wait_for_play_img", "bot_id": bot_id}
    await query.message.reply_text(
        f"🖼️ **『 ᴇᴅɪᴛ ᴘʟᴀʏ ᴍᴇssᴀɢᴇ ɪᴍᴀɢᴇ 』**\n\n"
        f"🔍 **ᴄᴜʀʀᴇɴᴛ ᴘʟᴀʏ ɪᴍᴀɢᴇ:**\n{old_img}\n\n"
        f"ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴅɪʀᴇᴄᴛ ɪᴍᴀɢᴇ ᴜʀʟ (e.g. from Catbox, Telegraph, etc.) "
        f"ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇᴛ ᴀs ʏᴏᴜʀ ᴄʟᴏɴᴇ's sᴏɴɢ ᴘʟᴀʏ ʙᴀɴɴᴇʀ:\n\n"
        f"*(Send /cancel to cancel this operation)*"
    )
    await query.answer()


# ----------------------------------------------------------------------
# CUSTOM INLINE BUTTONS HELPERS AND CONTROLS
# ----------------------------------------------------------------------

@app.on_callback_query(filters.regex("^EDIT_LINKS_(\\d+)$"))
async def edit_links_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    settings = clone.get("settings", {})
    chan_link = settings.get("channel_link", "Default (Main Channel)")
    supp_link = settings.get("support_link", "Default (Main Support Chat)")

    text = (
        f"🔗 **『 ᴄᴜsᴛᴏᴍɪᴢᴇ ʙᴏᴛ ʟɪɴᴋs 』**\n\n"
        f"Customize your cloned bot's Update Channel and Support Group links in 1-2 easy steps!\n\n"
        f"📢 **Update Channel:** `{chan_link}`\n"
        f"💬 **Support Group:** `{supp_link}`\n\n"
        f"✨ *Users clicking 'Updates' or 'Support' buttons on your bot will be directed to your custom links!*"
    )

    buttons = [
        [
            InlineKeyboardButton("📢 sᴇᴛ ᴜᴘᴅᴧᴛᴇ ᴄʜᴧɴɴᴇʟ", callback_data=f"SET_LINK_CHAN_{bot_id}"),
            InlineKeyboardButton("💬 sᴇᴛ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", callback_data=f"SET_LINK_SUPP_{bot_id}")
        ],
        [
            InlineKeyboardButton("⚡ ǫᴜɪᴄᴋ 2-sᴛᴇᴘ sᴇᴛᴜᴘ", callback_data=f"SET_LINK_QUICK_{bot_id}")
        ],
        [
            InlineKeyboardButton("🔄 ʀᴇsᴇᴛ ʟɪɴᴋs", callback_data=f"SET_LINK_RESET_{bot_id}"),
            InlineKeyboardButton("🔙 ʙᴧᴄᴋ", callback_data=f"MANAGE_BOT_{bot_id}")
        ]
    ]

    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await query.answer()


@app.on_callback_query(filters.regex("^SET_LINK_CHAN_(\\d+)$"))
async def set_link_chan_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)

    user_states[user_id] = {"action": "wait_for_link_channel", "bot_id": bot_id}
    await query.message.reply_text(
        f"📢 **『 sᴇᴛ ᴜᴘᴅᴧᴛᴇ ᴄʜᴧɴɴᴇʟ ʟɪɴᴋ 』**\n\n"
        f"Please send your **Update Channel link** (e.g. `https://t.me/YourChannel` or `@YourChannel`):\n\n"
        f"Send `/cancel` to abort or `/reset` to restore default."
    )
    await query.answer()


@app.on_callback_query(filters.regex("^SET_LINK_SUPP_(\\d+)$"))
async def set_link_supp_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)

    user_states[user_id] = {"action": "wait_for_link_support", "bot_id": bot_id}
    await query.message.reply_text(
        f"💬 **『 sᴇᴛ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ ʟɪɴᴋ 』**\n\n"
        f"Please send your **Support Group link** (e.g. `https://t.me/YourGroup` or `@YourGroup`):\n\n"
        f"Send `/cancel` to abort or `/reset` to restore default."
    )
    await query.answer()


@app.on_callback_query(filters.regex("^SET_LINK_QUICK_(\\d+)$"))
async def set_link_quick_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)

    user_states[user_id] = {"action": "wait_for_quick_step1", "bot_id": bot_id}
    await query.message.reply_text(
        f"⚡ **『 ǫᴜɪᴄᴋ ʟɪɴᴋ sᴇᴛᴜᴘ - sᴛᴇᴘ 1/2 』**\n\n"
        f"Please send your **Update Channel link** (e.g. `https://t.me/YourChannel` or `@YourChannel`):\n\n"
        f"Send `/cancel` to abort."
    )
    await query.answer()


@app.on_callback_query(filters.regex("^SET_LINK_RESET_(\\d+)$"))
async def set_link_reset_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)

    settings = clone.get("settings", {})
    settings["channel_link"] = None
    settings["support_link"] = None
    await update_clone_settings(bot_id, settings)

    await query.answer("🔄 Links reset to default main bot links!", show_alert=True)
    await edit_links_callback(client, query)


@app.on_callback_query(filters.regex("^EDIT_CAPTIONS_SUB_(\\d+)_(\\d+)$"))
async def edit_captions_sub_callback(client, query: CallbackQuery):
    parts = query.data.split("_")
    bot_id = int(parts[3])
    page = int(parts[4])
    user_id = query.from_user.id

    if not await check_premium_or_owner(user_id):
        return await query.answer("Premium required! Contact @Xbroze to buy premium.", show_alert=True)

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)

    buttons = []
    if page == 1:
        text = "📝 **『 ᴄᴧᴘᴛɪᴏɴs ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ - ᴘᴀɢᴇ 1 』**\n\nSelect a caption or help section text below to customize it for your cloned bot:"
        buttons = [
            [
                InlineKeyboardButton("ℹ️ About Text", callback_data=f"EDIT_HELP_KEY_{bot_id}_about"),
                InlineKeyboardButton("🤖 Main Help Text", callback_data=f"EDIT_HELP_KEY_{bot_id}_main_help"),
            ],
            [
                InlineKeyboardButton("💬 ChatGPT Help", callback_data=f"EDIT_HELP_KEY_{bot_id}_help_01"),
                InlineKeyboardButton("🔍 Search Help", callback_data=f"EDIT_HELP_KEY_{bot_id}_help_02"),
            ],
            [
                InlineKeyboardButton("🎙️ Whisper Help", callback_data=f"EDIT_HELP_KEY_{bot_id}_help_03"),
            ],
            [
                InlineKeyboardButton("➡️ Page 2", callback_data=f"EDIT_CAPTIONS_SUB_{bot_id}_2")
            ]
        ]
    elif page == 2:
        text = "📝 **『 ᴄᴧᴘᴛɪᴏɴs ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ - ᴘᴀɢᴇ 2 』**\n\nSelect a caption or help section text below to customize it for your cloned bot:"
        buttons = [
            [
                InlineKeyboardButton("ℹ️ Info Help", callback_data=f"EDIT_HELP_KEY_{bot_id}_help_04"),
                InlineKeyboardButton("🔤 Fonts Help", callback_data=f"EDIT_HELP_KEY_{bot_id}_help_05"),
            ],
            [
                InlineKeyboardButton("➕ Math Help", callback_data=f"EDIT_HELP_KEY_{bot_id}_help_06"),
                InlineKeyboardButton("🏷️ Tagall Help", callback_data=f"EDIT_HELP_KEY_{bot_id}_help_07"),
            ],
            [
                InlineKeyboardButton("🖼️ Stickers Help", callback_data=f"EDIT_HELP_KEY_{bot_id}_help_10"),
            ],
            [
                InlineKeyboardButton("⬅️ Page 1", callback_data=f"EDIT_CAPTIONS_SUB_{bot_id}_1"),
                InlineKeyboardButton("➡️ Page 3", callback_data=f"EDIT_CAPTIONS_SUB_{bot_id}_3")
            ]
        ]
    elif page == 3:
        text = "📝 **『 ᴄᴧᴘᴛɪᴏɴs ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ - ᴘᴀɢᴇ 3 』**\n\nSelect a caption or help section text below to customize it for your cloned bot:"
        buttons = [
            [
                InlineKeyboardButton("🎯 Fun Help", callback_data=f"EDIT_HELP_KEY_{bot_id}_help_11"),
                InlineKeyboardButton("💬 Quotly Help", callback_data=f"EDIT_HELP_KEY_{bot_id}_help_12"),
            ],
            [
                InlineKeyboardButton("🎲 Truth/Dare Help", callback_data=f"EDIT_HELP_KEY_{bot_id}_help_13"),
                InlineKeyboardButton("🚫 Admin/Ban Help", callback_data=f"EDIT_HELP_KEY_{bot_id}_help_14"),
            ],
            [
                InlineKeyboardButton("🌐 Translate Help", callback_data=f"EDIT_HELP_KEY_{bot_id}_help_24"),
            ],
            [
                InlineKeyboardButton("⬅️ Page 2", callback_data=f"EDIT_CAPTIONS_SUB_{bot_id}_2"),
                InlineKeyboardButton("➡️ Page 4", callback_data=f"EDIT_CAPTIONS_SUB_{bot_id}_4")
            ]
        ]
    elif page == 4:
        text = "📝 **『 ᴄᴧᴘᴛɪᴏɴs ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ - ᴘᴀɢᴇ 4 』**\n\nSelect a caption or help text below to customize:"
        buttons = [
            [
                InlineKeyboardButton("💻 Github Help", callback_data=f"EDIT_HELP_KEY_{bot_id}_help_25"),
                InlineKeyboardButton("🔗 Telegraph Help", callback_data=f"EDIT_HELP_KEY_{bot_id}_help_26"),
            ],
            [
                InlineKeyboardButton("📢 Promotion Text", callback_data=f"EDIT_HELP_KEY_{bot_id}_promotion"),
                InlineKeyboardButton("⚙️ Setup Help", callback_data=f"EDIT_HELP_KEY_{bot_id}_help_17"),
            ],
            [
                InlineKeyboardButton("⬅️ Page 3", callback_data=f"EDIT_CAPTIONS_SUB_{bot_id}_3"),
                InlineKeyboardButton("➡️ Page 5", callback_data=f"EDIT_CAPTIONS_SUB_{bot_id}_5")
            ]
        ]
    elif page == 5:
        text = "📝 **『 ᴄᴧᴘᴛɪᴏɴs ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ - ᴘᴀɢᴇ 5 』**\n\nSelect a music help caption to edit:"
        buttons = [
            [
                InlineKeyboardButton("🛡️ Music Admin", callback_data=f"EDIT_HELP_KEY_{bot_id}_hb1"),
                InlineKeyboardButton("🔑 Music Auth", callback_data=f"EDIT_HELP_KEY_{bot_id}_hb2"),
            ],
            [
                InlineKeyboardButton("📢 Music G-Cast", callback_data=f"EDIT_HELP_KEY_{bot_id}_hb3"),
                InlineKeyboardButton("💬 Music BL-Chat", callback_data=f"EDIT_HELP_KEY_{bot_id}_hb4"),
            ],
            [
                InlineKeyboardButton("👤 Music BL-User", callback_data=f"EDIT_HELP_KEY_{bot_id}_hb5"),
            ],
            [
                InlineKeyboardButton("⬅️ Page 4", callback_data=f"EDIT_CAPTIONS_SUB_{bot_id}_4"),
                InlineKeyboardButton("➡️ Page 6", callback_data=f"EDIT_CAPTIONS_SUB_{bot_id}_6")
            ]
        ]
    elif page == 6:
        text = "📝 **『 ᴄᴧᴘᴛɪᴏɴs ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ - ᴘᴀɢᴇ 6 』**\n\nSelect a music help caption to edit:"
        buttons = [
            [
                InlineKeyboardButton("📺 Music C-Play", callback_data=f"EDIT_HELP_KEY_{bot_id}_hb6"),
                InlineKeyboardButton("🚫 Music G-Ban", callback_data=f"EDIT_HELP_KEY_{bot_id}_hb7"),
            ],
            [
                InlineKeyboardButton("🔁 Music Loop", callback_data=f"EDIT_HELP_KEY_{bot_id}_hb8"),
                InlineKeyboardButton("📝 Music Log", callback_data=f"EDIT_HELP_KEY_{bot_id}_hb9"),
            ],
            [
                InlineKeyboardButton("⚡ Music Ping", callback_data=f"EDIT_HELP_KEY_{bot_id}_hb10"),
            ],
            [
                InlineKeyboardButton("⬅️ Page 5", callback_data=f"EDIT_CAPTIONS_SUB_{bot_id}_5"),
                InlineKeyboardButton("➡️ Page 7", callback_data=f"EDIT_CAPTIONS_SUB_{bot_id}_7")
            ]
        ]
    else: # Page 7
        text = "📝 **『 ᴄᴧᴘᴛɪᴏɴs ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ - ᴘᴀɢᴇ 7 』**\n\nSelect a music help caption to edit:"
        buttons = [
            [
                InlineKeyboardButton("🎵 Music Play", callback_data=f"EDIT_HELP_KEY_{bot_id}_hb11"),
                InlineKeyboardButton("🔀 Music Shuffle", callback_data=f"EDIT_HELP_KEY_{bot_id}_hb12"),
            ],
            [
                InlineKeyboardButton("⏩ Music Seek", callback_data=f"EDIT_HELP_KEY_{bot_id}_hb13"),
                InlineKeyboardButton("🎶 Music Song", callback_data=f"EDIT_HELP_KEY_{bot_id}_hb14"),
            ],
            [
                InlineKeyboardButton("🏃 Music Speed", callback_data=f"EDIT_HELP_KEY_{bot_id}_hb15"),
            ],
            [
                InlineKeyboardButton("⬅️ Page 6", callback_data=f"EDIT_CAPTIONS_SUB_{bot_id}_6")
            ]
        ]

    buttons.append([
        InlineKeyboardButton("🔙 Back to Main Menu", callback_data=f"MANAGE_BOT_{bot_id}")
    ])

    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await query.answer()


@app.on_callback_query(filters.regex("^EDIT_HELP_KEY_(\\d+)_(.+)$"))
async def edit_help_key_callback(client, query: CallbackQuery):
    parts = query.data.split("_")
    bot_id = int(parts[3])
    key = parts[4]
    user_id = query.from_user.id

    if not await check_premium_or_owner(user_id):
        return await query.answer("Premium required! Contact @Xbroze to buy premium.", show_alert=True)

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)

    key_name = HELP_KEYS_MAP.get(key, key)
    current_val = clone.get("settings", {}).get("help_texts", {}).get(key, "Default (not customized)")

    user_states[user_id] = {"action": f"wait_for_help_text_{key}", "bot_id": bot_id}

    prompt = (
        f"📝 **『 ᴇᴅɪᴛ ᴄᴧᴘᴛɪᴏɴ: {key_name} 』**\n\n"
        f"🔍 **Current Customization:**\n"
        f"`{current_val}`\n\n"
        f"Please send the **NEW** text message for this section.\n"
        f"Send `/cancel` to abort or `/reset` to restore the default text."
    )
    await query.message.reply_text(prompt)
    await query.answer()
