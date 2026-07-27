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
        f" └ 👋 **ᴡᴇʟᴄᴏᴍᴇ ᴛᴇxᴛ:** {settings.get('welcome_text')}\n\n"
        f"✨ *ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ᴍᴏᴅɪғʏ ᴀɴʏ sᴇᴛᴛɪɴɢ ᴏғ ʏᴏᴜʀ ᴄʟᴏɴᴇ sᴇᴀᴍʟᴇssʟʏ!*"
    )

    buttons = [
        [
            InlineKeyboardButton("👑 ᴄʜᴀɴɢᴇ ᴀssɪsᴛᴀɴᴛ", callback_data=f"EDIT_ASSISTANT_{bot_id}"),
        ],
        [
            InlineKeyboardButton("📝 ᴄʜᴀɴɢᴇ ʙʀᴀɴᴅɪɴɢ", callback_data=f"EDIT_BRAND_{bot_id}"),
            InlineKeyboardButton("👋 ᴄʜᴀɴɢᴇ ᴡᴇʟᴄᴏᴍᴇ", callback_data=f"EDIT_WELCOME_{bot_id}")
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
    if not clone or clone.get("tenant_id") != user_id:
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
    if not clone or clone.get("tenant_id") != user_id:
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
    if not clone or clone.get("tenant_id") != user_id:
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
    if not clone or clone.get("tenant_id") != user_id:
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
    if not clone or clone.get("tenant_id") != user_id:
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
    if not clone or clone.get("tenant_id") != user_id:
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
    if not clone or clone.get("tenant_id") != user_id:
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
    if not clone or clone.get("tenant_id") != user_id:
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
