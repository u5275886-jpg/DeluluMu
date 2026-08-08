from pyrogram.types import InlineKeyboardButton, WebAppInfo

import config
from SONALI_MUSIC import app


def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"], url=f"https://t.me/{app.username}?startgroup=true"
            ),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT),
        ],
    ]
    return buttons


async def private_panel(_, bot_id=None, user_id=None):
    bot_username = app.username
    owner_link = f"https://t.me/{config.OWNER_USERNAME}"

    main_bot_id = getattr(app, "_orig_id", app.id)
    if bot_id and bot_id != main_bot_id:
        try:
            from SONALI_MUSIC.utils.database_clone import get_clone_by_id
            clone = await get_clone_by_id(bot_id)
            if clone:
                bot_username = clone.get("bot_username") or app.username
                tenant_id = clone.get("tenant_id")
                tenant_username = clone.get("tenant_username")
                if tenant_username:
                    owner_link = f"https://t.me/{tenant_username}"
                else:
                    owner_link = f"tg://user?id={tenant_id}"

                # Fetch clones for this visiting user to determine Clone or Manage Clone button
                clones = []
                if user_id:
                    try:
                        from SONALI_MUSIC.utils.database_clone import get_user_clones
                        clones = await get_user_clones(user_id)
                    except Exception:
                        pass

                clone_manage_row = []
                if len(clones) == 0:
                    clone_manage_row.append(InlineKeyboardButton("ᴄʟᴏɴᴇ", callback_data="CLONE_BTN"))
                else:
                    clone_manage_row.append(InlineKeyboardButton("ᴍᴀɴᴀɢᴇ ᴄʟᴏɴᴇ", callback_data="MANAGE_CLONE_BTN"))

                custom_buttons = clone.get("settings", {}).get("custom_buttons", [])
                if custom_buttons and len(custom_buttons) > 0:
                    buttons = []
                    for idx, btn in enumerate(custom_buttons):
                        b_text = btn.get("text", "Button")
                        b_type = btn.get("type", "url")
                        b_val = btn.get("value", "")
                        if b_type == "url":
                            if not (b_val.startswith("http://") or b_val.startswith("https://") or b_val.startswith("tg://")):
                                b_val = "https://" + b_val
                            buttons.append([InlineKeyboardButton(text=b_text, url=b_val)])
                        else:
                            buttons.append([InlineKeyboardButton(text=b_text, callback_data=f"CLONE_CUST_BTN_{bot_id}_{idx}")])
                    buttons.append(clone_manage_row)
                    return buttons
                else:
                    # Default custom start panel for cloned bots (includes Mini App and dynamic clone/manage clone buttons)
                    buttons = [
                        [
                            InlineKeyboardButton(
                                text=_["S_B_3"],
                                url=f"https://t.me/{bot_username}?startgroup=true",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="Mini App 🚀",
                                web_app=WebAppInfo(url="https://music-theta-teal-86.vercel.app/"),
                            )
                        ],
                        [
                            InlineKeyboardButton(text=_["S_B_4"], callback_data="MAIN_CP"),
                        ],
                        [
                            InlineKeyboardButton(text=_["S_B_5"], url=owner_link),
                            InlineKeyboardButton("⌯ ᴧʙσυт ⌯", callback_data="ALLBOT_CP"),
                        ],
                        clone_manage_row
                    ]
                    return buttons
        except Exception:
            pass

    # Main Bot Start Panel logic: check user clones to conditionally show Clone or Manage Clone
    clones = []
    if user_id:
        try:
            from SONALI_MUSIC.utils.database_clone import get_user_clones
            clones = await get_user_clones(user_id)
        except Exception:
            pass

    clone_manage_row = []
    if len(clones) == 0:
        clone_manage_row.append(InlineKeyboardButton("ᴄʟᴏɴᴇ", callback_data="CLONE_BTN"))
    else:
        clone_manage_row.append(InlineKeyboardButton("ᴍᴀɴᴀɢᴇ ᴄʟᴏɴᴇ", callback_data="MANAGE_CLONE_BTN"))

    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_3"],
                url=f"https://t.me/{bot_username}?startgroup=true",
            )
        ],
        [
            InlineKeyboardButton(text=_["S_B_4"], callback_data="MAIN_CP"),
        ],
        [
            InlineKeyboardButton(text=_["S_B_5"], url=owner_link),
            InlineKeyboardButton("⌯ ᴧʙσυт ⌯", callback_data="ALLBOT_CP"),
        ],
        [
            InlineKeyboardButton("⌯ ʏᴛ-ᴀᴘɪ ⌯", callback_data="bot_info_data"),
        ],
        clone_manage_row,
    ]
    return buttons
