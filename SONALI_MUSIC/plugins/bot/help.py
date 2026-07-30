from typing import Union
from pyrogram import filters, types, enums
from pyrogram.types import InlineKeyboardMarkup, Message, InlineKeyboardButton
from SONALI_MUSIC import app
from SONALI_MUSIC.utils import help_pannel
from SONALI_MUSIC.utils.database import get_lang
from SONALI_MUSIC.utils.decorators.language import LanguageStart, languageCB
from SONALI_MUSIC.utils.inline.help import help_back_markup, private_help_panel
from config import BANNED_USERS, START_IMG_URL, SUPPORT_CHAT
from strings import get_string, helpers
from SONALI_MUSIC.help.buttons import BUTTONS
from SONALI_MUSIC.help.helper import Helper

#------------------------------------------------------------------------------------------------------------------------
# MUSIC | MUSIC | MUSIC | MUSIC | MUSIC | MUSIC | MUSIC | MUSIC | MUSIC | MUSIC | MUSIC | MUSIC | MUSIC | MUSIC | MUSIC | 
#------------------------------------------------------------------------------------------------------------------------





@app.on_message(filters.command(["help"]) & filters.private & ~BANNED_USERS)
@app.on_callback_query(filters.regex("settings_back_helper") & ~BANNED_USERS)
async def helper_private(
    client: app, update: Union[types.Message, types.CallbackQuery]
):
    is_callback = isinstance(update, types.CallbackQuery)
    if is_callback:
        try:
            await update.answer()
        except:
            pass
        chat_id = update.message.chat.id
        language = await get_lang(chat_id)
        _ = get_string(language)
        keyboard = help_pannel(_, True)
        default_val = _["help_1"].format(SUPPORT_CHAT)
        from SONALI_MUSIC.utils.database_clone import get_custom_help_text
        help_text = await get_custom_help_text(client.me.id, "main_help", default_val)
        await update.edit_message_text(
            help_text, reply_markup=keyboard
        )
    else:
        try:
            await update.delete()
        except:
            pass
        language = await get_lang(update.chat.id)
        _ = get_string(language)
        keyboard = help_pannel(_)
        default_val = _["help_1"].format(SUPPORT_CHAT)
        from SONALI_MUSIC.utils.database_clone import get_custom_help_text
        help_text = await get_custom_help_text(client.me.id, "main_help", default_val)
        await update.reply_photo(
            photo=START_IMG_URL,
            caption=help_text,
            reply_markup=keyboard,
        )


@app.on_message(filters.command(["help"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def help_com_group(client, message: Message, _):
    keyboard = private_help_panel(_)
    default_val = _["help_2"]
    from SONALI_MUSIC.utils.database_clone import get_custom_help_text
    help_text = await get_custom_help_text(client.me.id, "main_help", default_val)
    await message.reply_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard))

@app.on_callback_query(filters.regex("help_callback") & ~BANNED_USERS)
@languageCB
async def helper_cb(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    cb = callback_data.split(None, 1)[1]
    keyboard = help_back_markup(_)

    if cb.startswith("hb"):
        try:
            num = int(cb[2:])
            default_val = getattr(helpers, f"HELP_{num}", "")
        except ValueError:
            default_val = getattr(helpers, cb.upper(), "")
    else:
        default_val = getattr(helpers, cb.upper(), "")
    from SONALI_MUSIC.utils.database_clone import get_custom_help_text
    help_text = await get_custom_help_text(client.me.id, cb.lower(), default_val)
    await CallbackQuery.edit_message_text(help_text, reply_markup=keyboard)





#------------------------------------------------------------------------------------------------------------------------
# MANAGEMENT | MANAGEMENT | MANAGEMENT | MANAGEMENT | MANAGEMENT | MANAGEMENT | MANAGEMENT | MANAGEMENT | MANAGEMENT | 
#------------------------------------------------------------------------------------------------------------------------





@app.on_callback_query(filters.regex("MANAGEMENT_CP") & ~BANNED_USERS)
async def management_cp_cb(client, CallbackQuery):
    from SONALI_MUSIC.utils.database_clone import get_custom_help_text
    help_text = await get_custom_help_text(client.me.id, "management_main", Helper.HELP_M)
    await CallbackQuery.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(BUTTONS.MBUTTON))
    
        
@app.on_callback_query(filters.regex('MANAGEMENT_BACK'))      
async def management_back_cb(client, CallbackQuery):
    callback_data = CallbackQuery.data.strip()
    cb = callback_data.split(None, 1)[1]
    keyboard = InlineKeyboardMarkup(
    [
    [
    InlineKeyboardButton("⌯ ʙᴧᴄᴋ ⌯", callback_data=f"MANAGEMENT_CP")
    ]
    ]
    )
    if cb == "MANAGEMENT":
        await CallbackQuery.edit_message_text(f"`something errors`",reply_markup=keyboard,parse_mode=enums.ParseMode.MARKDOWN)
    else:
        default_val = getattr(Helper, cb, f"`something errors`")
        from SONALI_MUSIC.utils.database_clone import get_custom_help_text
        help_text = await get_custom_help_text(client.me.id, cb.lower(), default_val)
        await CallbackQuery.edit_message_text(help_text, reply_markup=keyboard)





#------------------------------------------------------------------------------------------------------------------------
# TOOL | TOOL | TOOL | TOOL | TOOL | TOOL | TOOL | TOOL | TOOL | TOOL | TOOL | TOOL | TOOL | TOOL | TOOL | TOOL | TOOL |
#------------------------------------------------------------------------------------------------------------------------





@app.on_callback_query(filters.regex("TOOL_CP") & ~BANNED_USERS)
async def tool_cp_cb(client, CallbackQuery):
    from SONALI_MUSIC.utils.database_clone import get_custom_help_text
    help_text = await get_custom_help_text(client.me.id, "tool_main", Helper.HELP_B)
    await CallbackQuery.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(BUTTONS.BBUTTON))


@app.on_callback_query(filters.regex('TOOL_BACK'))      
async def tool_back_cb(client, CallbackQuery):
    callback_data = CallbackQuery.data.strip()
    cb = callback_data.split(None, 1)[1]
    keyboard = InlineKeyboardMarkup(
    [
    [
    InlineKeyboardButton("ʙᴀᴄᴋ", callback_data=f"TOOL_CP")
    ]
    ]
    )
    if cb == "TOOL":
        await CallbackQuery.edit_message_text(f"`something errors`",reply_markup=keyboard,parse_mode=enums.ParseMode.MARKDOWN)
    else:
        default_val = getattr(Helper, cb, f"`something errors`")
        from SONALI_MUSIC.utils.database_clone import get_custom_help_text
        help_text = await get_custom_help_text(client.me.id, cb.lower(), default_val)
        await CallbackQuery.edit_message_text(help_text, reply_markup=keyboard)






#------------------------------------------------------------------------------------------------------------------------
# MAIN HELP | MAIN HELP | MAIN HELP | MAIN HELP | MAIN HELP | MAIN HELP | MAIN HELP | MAIN HELP | MAIN HELP | MAIN HELP |
#------------------------------------------------------------------------------------------------------------------------





@app.on_callback_query(filters.regex("MAIN_CP") & ~BANNED_USERS)
async def main_cp_cb(client, CallbackQuery):
    from SONALI_MUSIC.utils.database_clone import get_custom_help_text
    help_text = await get_custom_help_text(client.me.id, "main_cp", Helper.HELP_Sona)
    await CallbackQuery.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(BUTTONS.SBUTTON))

        
@app.on_callback_query(filters.regex('MAIN_BACK'))      
async def main_back_cb(client, CallbackQuery):
    callback_data = CallbackQuery.data.strip()
    cb = callback_data.split(None, 1)[1]
    keyboard = InlineKeyboardMarkup(
    [
    [
    InlineKeyboardButton("ʙᴀᴄᴋ", callback_data=f"MAIN_CP")
    ]
    ]
    )
    if cb == "MAIN":
        await CallbackQuery.edit_message_text(f"`something errors`",reply_markup=keyboard,parse_mode=enums.ParseMode.MARKDOWN)
    else:
        default_val = getattr(Helper, cb, f"`something errors`")
        from SONALI_MUSIC.utils.database_clone import get_custom_help_text
        help_text = await get_custom_help_text(client.me.id, cb.lower(), default_val)
        await CallbackQuery.edit_message_text(help_text, reply_markup=keyboard)




#------------------------------------------------------------------------------------------------------------------------
# PROMOTION | PROMOTION | PROMOTION | PROMOTION | PROMOTION | PROMOTION | PROMOTION | PROMOTION | PROMOTION | PROMOTION |
#------------------------------------------------------------------------------------------------------------------------


@app.on_callback_query(filters.regex("PROMOTION_CP") & ~BANNED_USERS)
async def promotion_cp_cb(client, CallbackQuery):
    from SONALI_MUSIC.utils.database_clone import get_custom_help_text
    help_text = await get_custom_help_text(client.me.id, "promotion", Helper.HELP_PROMOTION)
    await CallbackQuery.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(BUTTONS.PBUTTON))

        
@app.on_callback_query(filters.regex('PROMOTION_BACK'))      
async def promotion_back_cb(client, CallbackQuery):
    callback_data = CallbackQuery.data.strip()
    cb = callback_data.split(None, 1)[1]
    keyboard = InlineKeyboardMarkup(
    [
    [
    InlineKeyboardButton("ʙᴀᴄᴋ", callback_data=f"PROMOTION_CP")
    ]
    ]
    )
    if cb == "PROMOTION":
        await CallbackQuery.edit_message_text(f"`something errors`",reply_markup=keyboard,parse_mode=enums.ParseMode.MARKDOWN)
    else:
        default_val = getattr(Helper, cb, f"`something errors`")
        from SONALI_MUSIC.utils.database_clone import get_custom_help_text
        help_text = await get_custom_help_text(client.me.id, cb.lower(), default_val)
        await CallbackQuery.edit_message_text(help_text, reply_markup=keyboard)

        
        

#------------------------------------------------------------------------------------------------------------------------
# ALL BOT'S | ALL BOT'S | ALL BOT'S | ALL BOT'S | ALL BOT'S | ALL BOT'S | ALL BOT'S | ALL BOT'S | ALL BOT'S | ALL BOT'S | 
#------------------------------------------------------------------------------------------------------------------------



@app.on_callback_query(filters.regex("ALLBOT_CP") & ~BANNED_USERS)
async def allbot_cp_cb(client, CallbackQuery):
    from SONALI_MUSIC.utils.database_clone import get_custom_help_text
    help_text = await get_custom_help_text(client.me.id, "about", Helper.HELP_ALLBOT)
    await CallbackQuery.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(BUTTONS.ABUTTON))

        
@app.on_callback_query(filters.regex('ALLBOT_BACK'))      
async def allbot_back_cb(client, CallbackQuery):
    callback_data = CallbackQuery.data.strip()
    cb = callback_data.split(None, 1)[1]
    keyboard = InlineKeyboardMarkup(
    [
    [
    InlineKeyboardButton("ʙᴀᴄᴋ", callback_data=f"ALLBOT_CP")
    ]
    ]
    )
    if cb == "ALLBOT":
        await CallbackQuery.edit_message_text(f"`something errors`",reply_markup=keyboard,parse_mode=enums.ParseMode.MARKDOWN)
    else:
        default_val = getattr(Helper, cb, f"`something errors`")
        from SONALI_MUSIC.utils.database_clone import get_custom_help_text
        help_text = await get_custom_help_text(client.me.id, cb.lower(), default_val)
        await CallbackQuery.edit_message_text(help_text, reply_markup=keyboard)


#------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------
