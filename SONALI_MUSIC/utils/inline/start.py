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
    from SONALI_MUSIC.utils.database_clone import get_clone_links, get_user_clones

    active_bot_id = bot_id or getattr(app, "_orig_id", app.id)
    support_chat, support_channel, owner_link = await get_clone_links(active_bot_id)

    bot_username = app.username
    main_bot_id = getattr(app, "_orig_id", app.id)

    clones = []
    if user_id:
        try:
            clones = await get_user_clones(user_id)
        except Exception:
            pass

    clone_manage_row = []
    if len(clones) == 0:
        clone_manage_row.append(InlineKeyboardButton("ᴄʟᴏɴᴇ", callback_data="CLONE_BTN"))
    else:
        clone_manage_row.append(InlineKeyboardButton("ᴍᴀɴᴀɢᴇ ᴄʟᴏɴᴇ", callback_data="MANAGE_CLONE_BTN"))

    if bot_id and bot_id != main_bot_id:
        try:
            from SONALI_MUSIC.utils.database_clone import get_clone_by_id
            clone = await get_clone_by_id(bot_id)
            if clone:
                bot_username = clone.get("bot_username") or app.username
        except Exception:
            pass

        # Cloned bot panel layout with custom links
        buttons = [
            [
                InlineKeyboardButton(
                    text=_["S_B_3"],
                    url=f"https://t.me/{bot_username}?startgroup=true",
                )
            ],
            [
                InlineKeyboardButton(text="📢 ᴜᴘᴅᴧᴛᴇs", url=support_channel),
                InlineKeyboardButton(text="💬 sᴜᴘᴘᴏʀᴛ", url=support_chat),
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
                InlineKeyboardButton("⌯ ᴧʙσᴜᴛ ⌯", callback_data="ALLBOT_CP"),
            ],
            clone_manage_row,
        ]
        return buttons

    # Main Bot Start Panel layout
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_3"],
                url=f"https://t.me/{bot_username}?startgroup=true",
            )
        ],
        [
            InlineKeyboardButton(text="📢 ᴜᴘᴅᴧᴛᴇs", url=support_channel),
            InlineKeyboardButton(text="💬 sᴜᴘᴘᴏʀᴛ", url=support_chat),
        ],
        [
            InlineKeyboardButton(text=_["S_B_4"], callback_data="MAIN_CP"),
        ],
        [
            InlineKeyboardButton(text=_["S_B_5"], url=owner_link),
            InlineKeyboardButton("⌯ ᴧʙσᴜᴛ ⌯", callback_data="ALLBOT_CP"),
        ],
        [
            InlineKeyboardButton("⌯ ʏᴛ-ᴀᴘɪ ⌯", callback_data="bot_info_data"),
        ],
        clone_manage_row,
    ]
    return buttons
