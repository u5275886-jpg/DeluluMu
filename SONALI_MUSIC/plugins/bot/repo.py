from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from SONALI_MUSIC import app
from config import BOT_USERNAME
from SONALI_MUSIC.utils.errors import capture_err
import httpx 
import config
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

start_txt = f"""**
<u>❃ ᴡєʟᴄσϻє ᴛᴏ ˹ꜱᴇᴊᴀʟ ꭙ ᴍᴜꜱɪᴄ˼ ʀєᴘσs ❃</u>
 
✼ ʀєᴘᴏ ɪs ηᴏᴡ ᴘʀɪᴠᴧᴛє ᴅᴜᴅє 😌
 
❉  ʏᴏᴜ ᴄᴧη мʏ ᴜsє ᴘᴜʙʟɪᴄ ʀєᴘσs !!  

✼ || [˹ꜱᴇᴊᴀʟ ꭙ ᴍᴜꜱɪᴄ˼]({config.SUPPORT_CHANNEL}) ||
 
❊ ʀᴜη 24x7 ʟᴧɢ ϝʀєє ᴡɪᴛʜσᴜᴛ sᴛσᴘ**
"""




@app.on_message(filters.command("repo"))
async def start(_, msg):
    buttons = [
        [ 
          InlineKeyboardButton("✙ ᴧᴅᴅ ϻє вᴧʙʏ ✙", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
        ],
        [
          InlineKeyboardButton("• ɴєᴛᴡᴏʀᴋ •", url=config.SUPPORT_CHANNEL),
          InlineKeyboardButton("• 𝛅ᴜᴘᴘσʀᴛ •", url="https://t.me/Xbroze"),
          ],
[
InlineKeyboardButton("• ᴧʟʟ ʙσᴛѕ •", url=config.SUPPORT_CHANNEL),

        ]]
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await msg.reply_photo(
        photo="https://graph.org/file/4fb9a698630aa5b47be05-060979d72b7752fc8f.jpg",
        caption=start_txt,
        reply_markup=reply_markup
    )
