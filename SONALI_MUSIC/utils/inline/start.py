from pyrogram.types import InlineKeyboardButton

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


async def private_panel(_, bot_id=None):
    if bot_id:
        try:
            from SONALI_MUSIC.utils.database_clone import get_clone_by_id
            clone = await get_clone_by_id(bot_id)
            if clone:
                custom_buttons = clone.get("settings", {}).get("custom_buttons", [])
                if custom_buttons and len(custom_buttons) > 0:
                    buttons = []
                    for idx, btn in enumerate(custom_buttons):
                        b_text = btn.get("text", "Button")
                        b_type = btn.get("type", "url")
                        b_val = btn.get("value", "")
                        if b_type == "url":
                            if not (b_val.startswith("http://") or b_val.startswith("https://")):
                                b_val = "https://" + b_val
                            buttons.append([InlineKeyboardButton(text=b_text, url=b_val)])
                        else:
                            buttons.append([InlineKeyboardButton(text=b_text, callback_data=f"CLONE_CUST_BTN_{bot_id}_{idx}")])
                    return buttons
        except Exception:
            pass

    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_3"],
                url=f"https://t.me/{app.username}?startgroup=true",
            )
        ],
        [
            
            InlineKeyboardButton(text=_["S_B_4"], callback_data="MAIN_CP"),
        ],
        [
            InlineKeyboardButton(text=_["S_B_5"], url=f"https://t.me/{config.OWNER_USERNAME}"),
            InlineKeyboardButton("⌯ ᴧʙσυт ⌯", callback_data="ALLBOT_CP"),
        ],
        [
            InlineKeyboardButton("⌯ ʏᴛ-ᴀᴘɪ ⌯", callback_data="bot_info_data"),
        ],
        [
            InlineKeyboardButton("ᴄʟᴏɴᴇ", callback_data="CLONE_BTN"),
            InlineKeyboardButton("ᴍᴀɴᴀɢᴇ ᴄʟᴏɴᴇ", callback_data="MANAGE_CLONE_BTN"),
        ],
    ]
    return buttons
