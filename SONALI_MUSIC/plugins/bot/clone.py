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
    log_audit_trail
)
from SONALI_MUSIC.utils.Sona_font import Fonts

logger = logging.getLogger(__name__)

# Helper to format small cap text
def to_smallcap(text: str) -> str:
    return Fonts.smallcap(text)

# ----------------------------------------------------------------------
# 1. COMMAND: /CLONE & CLONE_BTN CALLBACK
# ----------------------------------------------------------------------

@app.on_message(filters.command(["clone"]) & filters.private)
async def clone_cmd_handler(client, message: Message):
    user_id = message.from_user.id

    # 1. Premium check (bypass for central owner)
    is_owner = (user_id == config.OWNER_ID)
    premium_status = await check_premium_access(user_id)

    if not is_owner and not premium_status.get("has_premium", False):
        return await message.reply_text(
            f"❌ **{to_smallcap('access denied')}**\n\n"
            f"You need a premium subscription to create and manage cloned bots.\n"
            f"Please contact the admin @{config.OWNER_USERNAME} to upgrade."
        )

    parts = message.text.split(None, 1)
    if len(parts) < 2:
        return await message.reply_text(
            f"🤖 **{to_smallcap('how to clone')}**\n\n"
            f"To clone the music bot, get a bot token from @BotFather and send:\n"
            f"`/clone BOT_TOKEN_HERE`"
        )

    bot_token = parts[1].strip()
    status_msg = await message.reply_text("🔍 **Checking bot token...**")

    # 2. Check limits
    user_clones = await get_user_clones(user_id)
    limit = premium_status.get("permissions", {}).get("limits", 1) if not is_owner else 99999
    if len(user_clones) >= limit:
        return await status_msg.edit_text(
            f"❌ **{to_smallcap('clone limit reached')}**\n\n"
            f"Your current plan allows up to {limit} clones. You currently have {len(user_clones)}."
        )

    # 3. Spin up client temporarily to validate
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

    # 4. Save and start clone
    success = await save_clone_bot(
        tenant_id=user_id,
        bot_token=bot_token,
        bot_id=bot_info.id,
        bot_name=bot_info.first_name,
        bot_username=bot_info.username
    )

    if success:
        # Start clone inside manager
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
    user_id = query.from_user.id
    is_owner = (user_id == config.OWNER_ID)
    premium_status = await check_premium_access(user_id)

    if not is_owner and not premium_status.get("has_premium", False):
        return await query.answer(
            to_smallcap("premium access required"),
            show_alert=True
        )

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

    await query.message.reply_text(
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

    settings = clone.get("settings", {})
    text = (
        f"🤖 **{to_smallcap('clone details')}**\n\n"
        f"Name: **{clone.get('bot_name')}**\n"
        f"Username: @{clone.get('bot_username')}\n"
        f"Status: **{clone.get('status').upper()}**\n\n"
        f"**Branding Title**: {settings.get('title')}\n"
        f"**Welcome Text**: {settings.get('welcome_text')}\n"
        f"**Play Preference**: {settings.get('playback_preferences')}\n"
        f"**Queue Behavior**: {settings.get('queue_behavior')}\n"
    )

    buttons = [
        [
            InlineKeyboardButton(f"{to_smallcap('change branding')}", callback_data=f"EDIT_BRAND_{bot_id}"),
            InlineKeyboardButton(f"{to_smallcap('change welcome')}", callback_data=f"EDIT_WELCOME_{bot_id}")
        ],
        [
            InlineKeyboardButton(f"{to_smallcap('play preference')}", callback_data=f"EDIT_PLAY_{bot_id}"),
            InlineKeyboardButton(f"{to_smallcap('queue behavior')}", callback_data=f"EDIT_QUEUE_{bot_id}")
        ],
        [
            InlineKeyboardButton(f"⚠️ {to_smallcap('delete clone')}", callback_data=f"DELETE_CONFIRM_{bot_id}")
        ],
        [
            InlineKeyboardButton(f"🔙 {to_smallcap('back')}", callback_data="MANAGE_CLONE_BTN")
        ]
    ]

    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
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

    await query.answer(f"Playback Preference changed to {new_pref}")
    # Refresh panel
    query.data = f"MANAGE_BOT_{bot_id}"
    await manage_bot_details_panel(client, query)


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

    await query.answer(f"Queue Behavior changed to {new_behavior}")
    # Refresh panel
    query.data = f"MANAGE_BOT_{bot_id}"
    await manage_bot_details_panel(client, query)


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
