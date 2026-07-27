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
    update_clone_assistant_settings
)
from SONALI_MUSIC.utils.Sona_font import Fonts

logger = logging.getLogger(__name__)

# Helper to format small cap text
def to_smallcap(text: str) -> str:
    return Fonts.smallcap(text)

# Active interactive state dictionary
# user_id -> {"action": str, "bot_id": int}
user_states = {}

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
        f" ├ 👋 **ᴡᴇʟᴄᴏᴍᴇ ᴛᴇxᴛ:** {welcome_text}\n"
        f" ├ 🖼️ **ᴡᴇʟᴄᴏᴍᴇ ɪᴍᴀɢᴇ:** [ᴠɪᴇᴡ ɪᴍᴀɢᴇ]({welcome_img})\n"
        f" ├ 🖼️ **ᴘʟᴀʏ ɪᴍᴀɢᴇ:** [ᴠɪᴇᴡ ɪᴍᴀɢᴇ]({play_img})\n"
        f" └ 📝 **ᴘʟᴀʏ ᴛᴇxᴛ:** {play_text[:50]}...\n\n"
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
            InlineKeyboardButton("🔘 ᴍᴀɴᴀɢᴇ ɪɴʟɪɴᴇ ʙᴜᴛᴛᴏɴs", callback_data=f"MANAGE_CUST_BTNS_{bot_id}")
        ],
        [
            InlineKeyboardButton("📥 ᴘʟᴀʏ ᴘʀᴇғᴇʀᴇɴᴄᴇ", callback_data=f"EDIT_PLAY_{bot_id}"),
            InlineKeyboardButton("🔄 ǫᴜᴇᴜᴇ ʙᴇʜᴀᴠɪᴏʀ", callback_data=f"EDIT_QUEUE_{bot_id}")
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
        bot_username=bot_info.username
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
        if action.startswith("wait_for_btn_"):
            await send_custom_buttons_panel(user_id, bot_id)
        else:
            await send_bot_details_panel(user_id, bot_id)
        return

    clone = await get_clone_by_id(bot_id)
    if not clone:
        del user_states[user_id]
        return await message.reply_text("❌ Clone not found.")

    settings = clone.get("settings", {})

    if action == "wait_for_btn_text":
        btn_text = message.text.strip()
        if not btn_text:
            return await message.reply_text("❌ **Button text cannot be empty! Please send valid text.**")
        if len(btn_text) > 30:
            return await message.reply_text("❌ **Button text is too long! Keep it under 30 characters.**")

        user_states[user_id] = {
            "action": "wait_for_btn_type",
            "bot_id": bot_id,
            "btn_text": btn_text
        }

        buttons = [
            [
                InlineKeyboardButton("🔗 ʟɪɴᴋ (ᴜʀʟ)", callback_data=f"CHOOSE_BTN_TYPE_url"),
                InlineKeyboardButton("🔔 ᴀʟᴇʀᴛ (ᴘᴏᴘᴜᴘ)", callback_data=f"CHOOSE_BTN_TYPE_alert")
            ],
            [
                InlineKeyboardButton("💬 ᴍᴇssᴀɢᴇ (ʀᴇᴘʟʏ)", callback_data=f"CHOOSE_BTN_TYPE_message")
            ],
            [
                InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data=f"CANCEL_CUST_BTN_{bot_id}")
            ]
        ]

        await message.reply_text(
            f"🎯 **Button Text Set:** `{btn_text}`\n\n"
            f"ᴘʟᴇᴀsᴇ sᴇʟᴇᴄᴛ ᴛʜᴇ **ᴛʏᴘᴇ** of this inline button:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    elif action == "wait_for_btn_value":
        btn_value = message.text.strip()
        btn_text = state["btn_text"]
        btn_type = state["btn_type"]

        if not btn_value:
            return await message.reply_text("❌ **Value cannot be empty! Please send a valid text.**")

        if btn_type == "url":
            if not (btn_value.startswith("http://") or btn_value.startswith("https://")):
                return await message.reply_text("❌ **Invalid URL! The link must start with http:// or https://. Try again:**")
        elif btn_type == "alert":
            if len(btn_value) > 200:
                return await message.reply_text("❌ **Alert text is too long! Keep it under 200 characters. Try again:**")

        custom_buttons = settings.get("custom_buttons", [])
        custom_buttons.append({
            "text": btn_text,
            "type": btn_type,
            "value": btn_value
        })
        settings["custom_buttons"] = custom_buttons
        await update_clone_settings(bot_id, settings)
        del user_states[user_id]

        await message.reply_text(
            f"✅ **Button Added Successfully!**\n\n"
            f"🏷️ **Text:** `{btn_text}`\n"
            f"⚙️ **Type:** `{btn_type.upper()}`\n"
            f"🔗 **Value:** `{btn_value}`"
        )
        await send_custom_buttons_panel(user_id, bot_id)
        return

    elif action.startswith("wait_for_btn_edit_"):
        field = action.replace("wait_for_btn_edit_", "")
        idx = state["btn_idx"]
        new_val = message.text.strip()

        if not new_val:
            return await message.reply_text("❌ **Value cannot be empty! Please send a valid text.**")

        custom_buttons = settings.get("custom_buttons", [])
        if idx >= len(custom_buttons):
            del user_states[user_id]
            return await message.reply_text("❌ Button not found. Operation cancelled.")

        if field == "text":
            if len(new_val) > 30:
                return await message.reply_text("❌ **Button text is too long! Keep it under 30 characters. Try again:**")
            custom_buttons[idx]["text"] = new_val
        else: # value
            btn_type = custom_buttons[idx].get("type", "url")
            if btn_type == "url":
                if not (new_val.startswith("http://") or new_val.startswith("https://")):
                    return await message.reply_text("❌ **Invalid URL! The link must start with http:// or https://. Try again:**")
            elif btn_type == "alert":
                if len(new_val) > 200:
                    return await message.reply_text("❌ **Alert text is too long! Keep it under 200 characters. Try again:**")
            custom_buttons[idx]["value"] = new_val

        settings["custom_buttons"] = custom_buttons
        await update_clone_settings(bot_id, settings)
        del user_states[user_id]

        await message.reply_text(f"✅ **Button {field} updated successfully!**")
        await send_custom_buttons_panel(user_id, bot_id)
        return

    if action == "wait_for_title":
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

async def send_custom_buttons_panel(chat_id, bot_id, reply_to_message_id=None, query=None):
    clone = await get_clone_by_id(bot_id)
    if not clone:
        if query:
            await query.answer("Clone not found.", show_alert=True)
        return

    custom_buttons = clone.get("settings", {}).get("custom_buttons", [])
    text = (
        f"🔘 **『 ᴍᴀɴᴀɢᴇ ɪɴʟɪɴᴇ ʙᴜᴛᴛᴏɴs 』**\n\n"
        f"ʏᴏᴜ ᴄᴀɴ ᴄᴏɴғɪɢᴜʀᴇ ᴛʜᴇ ʟɪɴᴋs ᴏʀ ᴍᴇssᴀɢᴇs ᴏғ ʏᴏᴜʀ ᴄʟᴏɴᴇᴅ ʙᴏᴛ's ɪɴʟɪɴᴇ ʙᴜᴛᴛᴏɴs ʜᴇʀᴇ!\n\n"
        f"📋 **ᴄᴜʀʀᴇɴᴛ ʙᴜᴛᴛᴏɴs ({len(custom_buttons)}):**\n"
    )
    if not custom_buttons:
        text += " └ ❌ *No custom buttons configured. Default panel buttons will be shown.*"
    else:
        for idx, btn in enumerate(custom_buttons):
            b_text = btn.get("text", "Button")
            b_type = btn.get("type", "url").upper()
            b_val = btn.get("value", "")
            if len(b_val) > 40:
                b_val = b_val[:37] + "..."
            text += f" {idx+1}. 🏷️ **{b_text}** | ⚙️ **{b_type}**\n   └ 🔗 `{b_val}`\n"

    buttons = [
        [
            InlineKeyboardButton("➕ ᴀᴅᴅ ʙᴜᴛᴛᴏɴ", callback_data=f"ADD_CUST_BTN_{bot_id}"),
            InlineKeyboardButton("✏️ ᴇᴅɪᴛ ʙᴜᴛᴛᴏɴ", callback_data=f"EDIT_CUST_BTN_{bot_id}"),
        ],
        [
            InlineKeyboardButton("🔄 ʀᴇsᴇᴛ ᴛᴏ ᴅᴇғᴀᴜʟᴛ", callback_data=f"RESET_CUST_BTN_{bot_id}")
        ],
        [
            InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"MANAGE_BOT_{bot_id}")
        ]
    ]
    markup = InlineKeyboardMarkup(buttons)
    if query:
        await query.message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
    else:
        await app.send_message(chat_id, text, reply_markup=markup, reply_to_message_id=reply_to_message_id, disable_web_page_preview=True)


@app.on_callback_query(filters.regex("^MANAGE_CUST_BTNS_(\\d+)$"))
async def manage_custom_buttons_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    await send_custom_buttons_panel(user_id, bot_id, query=query)




@app.on_callback_query(filters.regex("^CHOOSE_BTN_TYPE_(url|alert|message)$"))
async def choose_button_type_callback(client, query: CallbackQuery):
    user_id = query.from_user.id
    state = user_states.get(user_id)
    if not state or state.get("action") != "wait_for_btn_type":
        return await query.answer("Session expired or invalid.", show_alert=True)

    btn_type = query.data.split("_")[3]
    bot_id = state["bot_id"]
    btn_text = state["btn_text"]

    user_states[user_id] = {
        "action": "wait_for_btn_value",
        "bot_id": bot_id,
        "btn_text": btn_text,
        "btn_type": btn_type
    }

    if btn_type == "url":
        prompt = (
            f"🔗 **『 sᴇᴛ ʙᴜᴛᴛᴏɴ ʟɪɴᴋ 』**\n\n"
            f"Button Text: `{btn_text}`\n"
            f"Button Type: `LINK (URL)`\n\n"
            f"ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ **ᴜʀʟ** (link) that this button should open when clicked:\n"
            f"*(e.g., https://t.me/your_channel)*"
        )
    elif btn_type == "alert":
        prompt = (
            f"🔔 **『 sᴇᴛ ʙᴜᴛᴛᴏɴ ᴀʟᴇʀᴛ ᴍᴇssᴀɢᴇ 』**\n\n"
            f"Button Text: `{btn_text}`\n"
            f"Button Type: `ALERT (POPUP)`\n\n"
            f"ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ **ᴀʟᴇʀᴛ ᴍᴇssᴀɢᴇ** (up to 200 chars) that should pop up when clicked:\n"
            f"*(Send /cancel to cancel this operation)*"
        )
    else:
        prompt = (
            f"💬 **『 sᴇᴛ ʙᴜᴛᴛᴏɴ ʀᴇᴘʟʏ ᴍᴇssᴀɢᴇ 』**\n\n"
            f"Button Text: `{btn_text}`\n"
            f"Button Type: `MESSAGE (REPLY)`\n\n"
            f"ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ **ᴍᴇssᴀɢᴇ ᴛᴇxᴛ** that the bot should reply when clicked:\n"
            f"*(Send /cancel to cancel this operation)*"
        )

    await query.message.reply_text(prompt)
    await query.answer()




@app.on_callback_query(filters.regex("^ADD_CUST_BTN_(\\d+)$"))
async def add_custom_button_init_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    user_states[user_id] = {"action": "wait_for_btn_text", "bot_id": bot_id}
    await query.message.reply_text(
        f"➕ **『 ᴀᴅᴅ ᴄᴜsᴛᴏᴍ ɪɴʟɪɴᴇ ʙᴜᴛᴛᴏɴ 』**\n\n"
        f"ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ **ᴛᴇxᴛ** (label) for the new button (e.g. `Join Channel`):\n\n"
        f"*(Send /cancel to cancel this operation)*"
    )
    await query.answer()


@app.on_callback_query(filters.regex("^EDIT_CUST_BTN_(\\d+)$"))
async def edit_custom_buttons_list_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    custom_buttons = clone.get("settings", {}).get("custom_buttons", [])
    if not custom_buttons:
        return await query.answer("❌ No custom buttons to edit.", show_alert=True)

    text = (
        f"✏️ **『 ᴇᴅɪᴛ ᴄᴜsᴛᴏᴍ ʙᴜᴛᴛᴏɴ 』**\n\n"
        f"sᴇʟᴇᴄᴛ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ edit:"
    )

    buttons = []
    for idx, btn in enumerate(custom_buttons):
        buttons.append([
            InlineKeyboardButton(f"✏️ {btn.get('text')}", callback_data=f"SELECT_EDIT_CUST_BTN_{bot_id}_{idx}")
        ])
    buttons.append([InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"MANAGE_CUST_BTNS_{bot_id}")])

    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await query.answer()


@app.on_callback_query(filters.regex("^SELECT_EDIT_CUST_BTN_(\\d+)_(\\d+)$"))
async def select_edit_custom_button_callback(client, query: CallbackQuery):
    parts = query.data.split("_")
    bot_id = int(parts[4])
    idx = int(parts[5])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    custom_buttons = clone.get("settings", {}).get("custom_buttons", [])
    if idx >= len(custom_buttons):
        return await query.answer("Button not found.", show_alert=True)

    btn = custom_buttons[idx]
    text = (
        f"✏️ **『 ᴍᴏᴅɪғʏ ʙᴜᴛᴛᴏɴ 』**\n\n"
        f"🏷️ **Current Text:** `{btn.get('text')}`\n"
        f"⚙️ **Current Type:** `{btn.get('type').upper()}`\n"
        f"🔗 **Current Value:** `{btn.get('value')}`\n\n"
        f"ᴡʜᴀᴛ ᴡᴏᴜʟᴅ ʏᴏᴜ ʟɪᴋᴇ ᴛᴏ ᴇᴅɪᴛ?"
    )

    buttons = [
        [
            InlineKeyboardButton("🏷️ ᴇᴅɪᴛ ᴛᴇxᴛ", callback_data=f"FIELD_EDIT_CUST_BTN_{bot_id}_{idx}_text"),
            InlineKeyboardButton("⚙️ ᴇᴅɪᴛ ᴛʏᴘᴇ", callback_data=f"FIELD_EDIT_CUST_BTN_{bot_id}_{idx}_type")
        ],
        [
            InlineKeyboardButton("🔗 ᴇᴅɪᴛ ᴠᴀʟᴜᴇ", callback_data=f"FIELD_EDIT_CUST_BTN_{bot_id}_{idx}_value"),
            InlineKeyboardButton("🗑️ ᴅᴇʟᴇᴛᴇ ʙᴜᴛᴛᴏɴ", callback_data=f"DELETE_CUST_BTN_{bot_id}_{idx}")
        ],
        [
            InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"EDIT_CUST_BTN_{bot_id}")
        ]
    ]

    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await query.answer()


@app.on_callback_query(filters.regex("^DELETE_CUST_BTN_(\\d+)_(\\d+)$"))
async def delete_custom_button_callback(client, query: CallbackQuery):
    parts = query.data.split("_")
    bot_id = int(parts[3])
    idx = int(parts[4])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    settings = clone.get("settings", {})
    custom_buttons = settings.get("custom_buttons", [])
    if idx < len(custom_buttons):
        deleted_btn = custom_buttons.pop(idx)
        settings["custom_buttons"] = custom_buttons
        await update_clone_settings(bot_id, settings)
        await query.answer(f"🗑️ Deleted button: {deleted_btn.get('text')}", show_alert=True)
    else:
        await query.answer("❌ Button not found.", show_alert=True)

    await send_custom_buttons_panel(user_id, bot_id, query=query)


@app.on_callback_query(filters.regex("^FIELD_EDIT_CUST_BTN_(\\d+)_(\\d+)_(text|type|value)$"))
async def field_edit_custom_button_callback(client, query: CallbackQuery):
    parts = query.data.split("_")
    bot_id = int(parts[4])
    idx = int(parts[5])
    field = parts[6]
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    custom_buttons = clone.get("settings", {}).get("custom_buttons", [])
    if idx >= len(custom_buttons):
        return await query.answer("Button not found.", show_alert=True)

    btn = custom_buttons[idx]

    if field == "type":
        buttons = [
            [
                InlineKeyboardButton("🔗 ʟɪɴᴋ (ᴜʀʟ)", callback_data=f"SAVE_EDIT_CUST_BTN_TYPE_{bot_id}_{idx}_url"),
                InlineKeyboardButton("🔔 ᴀʟᴇʀᴛ (ᴘᴏᴘᴜᴘ)", callback_data=f"SAVE_EDIT_CUST_BTN_TYPE_{bot_id}_{idx}_alert")
            ],
            [
                InlineKeyboardButton("💬 ᴍᴇssᴀɢᴇ (ʀᴇᴘʟʏ)", callback_data=f"SAVE_EDIT_CUST_BTN_TYPE_{bot_id}_{idx}_message")
            ],
            [
                InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"SELECT_EDIT_CUST_BTN_{bot_id}_{idx}")
            ]
        ]
        await query.message.edit_text(
            f"⚙️ **『 ᴄʜᴀɴɢᴇ ʙᴜᴛᴛᴏɴ ᴛʏᴘᴇ 』**\n\n"
            f"Button Text: `{btn.get('text')}`\n"
            f"Current Type: `{btn.get('type').upper()}`\n\n"
            f"sᴇʟᴇᴄᴛ ᴛʜᴇ ɴᴇᴡ **ᴛʏᴘᴇ** for this button:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        await query.answer()
        return

    # For text and value, set user state to wait for text input
    user_states[user_id] = {
        "action": f"wait_for_btn_edit_{field}",
        "bot_id": bot_id,
        "btn_idx": idx
    }

    if field == "text":
        prompt = (
            f"✏️ **『 ᴇᴅɪᴛ ʙᴜᴛᴛᴏɴ ᴛᴇxᴛ 』**\n\n"
            f"Current Text: `{btn.get('text')}`\n\n"
            f"ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ɴᴇᴡ **ᴛᴇxᴛ** (label) for this button:\n"
            f"*(Send /cancel to cancel this operation)*"
        )
    else:  # value
        btn_type = btn.get('type')
        if btn_type == "url":
            prompt = (
                f"🔗 **『 ᴇᴅɪᴛ ʙᴜᴛᴛᴏɴ ʟɪɴᴋ 』**\n\n"
                f"Current URL: `{btn.get('value')}`\n\n"
                f"ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ɴᴇᴡ **ᴜʀʟ** (link) starting with http:// or https://:\n"
                f"*(Send /cancel to cancel this operation)*"
            )
        elif btn_type == "alert":
            prompt = (
                f"🔔 **『 ᴇᴅɪᴛ ʙᴜᴛᴛᴏɴ ᴀʟᴇʀᴛ 』**\n\n"
                f"Current Alert: `{btn.get('value')}`\n\n"
                f"ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ɴᴇᴡ **ᴀʟᴇʀᴛ ᴍᴇssᴀɢᴇ** (up to 200 chars):\n"
                f"*(Send /cancel to cancel this operation)*"
            )
        else:
            prompt = (
                f"💬 **『 ᴇᴅɪᴛ ʙᴜᴛᴛᴏɴ ʀᴇᴘʟʏ 』**\n\n"
                f"Current Reply: `{btn.get('value')}`\n\n"
                f"ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ɴᴇᴡ **ᴍᴇssᴀɢᴇ ᴛᴇxᴛ**:\n"
                f"*(Send /cancel to cancel this operation)*"
            )

    await query.message.reply_text(prompt)
    await query.answer()


@app.on_callback_query(filters.regex("^SAVE_EDIT_CUST_BTN_TYPE_(\\d+)_(\\d+)_(url|alert|message)$"))
async def save_edit_custom_button_type_callback(client, query: CallbackQuery):
    parts = query.data.split("_")
    bot_id = int(parts[5])
    idx = int(parts[6])
    new_type = parts[7]
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    settings = clone.get("settings", {})
    custom_buttons = settings.get("custom_buttons", [])
    if idx < len(custom_buttons):
        custom_buttons[idx]["type"] = new_type
        settings["custom_buttons"] = custom_buttons
        await update_clone_settings(bot_id, settings)
        await query.answer("✅ Button type updated successfully!", show_alert=True)
    else:
        await query.answer("❌ Button not found.", show_alert=True)

    await select_edit_custom_button_callback(client, query)


@app.on_callback_query(filters.regex("^RESET_CUST_BTN_(\\d+)$"))
async def reset_custom_buttons_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_id = query.from_user.id

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Clone not found.", show_alert=True)
    is_owner = (user_id == config.OWNER_ID)
    if not is_owner and clone.get("tenant_id") != user_id:
        return await query.answer("Access Denied.", show_alert=True)

    # Re-initialize to empty to trigger main bot design fallback
    default_buttons = []

    settings = clone.get("settings", {})
    settings["custom_buttons"] = default_buttons
    await update_clone_settings(bot_id, settings)
    await query.answer("🔄 Custom buttons reset to inherit main bot design!", show_alert=True)

    await send_custom_buttons_panel(user_id, bot_id, query=query)


@app.on_callback_query(filters.regex("^CANCEL_CUST_BTN_(\\d+)$"))
async def cancel_custom_button_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_id = query.from_user.id
    if user_id in user_states:
        del user_states[user_id]
    await query.answer("Operation cancelled.")
    await send_custom_buttons_panel(user_id, bot_id, query=query)


@app.on_callback_query(filters.regex(r"^CLONE_CUST_BTN_(\d+)_(\d+)$"))
async def custom_button_trigger_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    btn_idx = int(query.data.split("_")[4])

    clone = await get_clone_by_id(bot_id)
    if not clone:
        return await query.answer("Bot settings not found.", show_alert=True)

    custom_buttons = clone.get("settings", {}).get("custom_buttons", [])
    if btn_idx >= len(custom_buttons):
        return await query.answer("Button not found.", show_alert=True)

    btn = custom_buttons[btn_idx]
    b_type = btn.get("type", "url")
    b_val = btn.get("value", "")

    if b_type == "alert":
        await query.answer(b_val, show_alert=True)
    elif b_type == "message":
        await query.answer()
        await query.message.reply_text(b_val)
    else:
        await query.answer()
