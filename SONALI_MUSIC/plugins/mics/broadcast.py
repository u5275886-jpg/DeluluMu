import asyncio

from pyrogram import filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.errors import FloodWait

from SONALI_MUSIC import app
from SONALI_MUSIC.misc import SUDOERS
from SONALI_MUSIC.utils.database import (
    get_active_chats,
    get_authuser_names,
    get_client,
    get_served_chats,
    get_served_users,
)
from SONALI_MUSIC.utils.decorators.language import language
from SONALI_MUSIC.utils.formatters import alpha_to_int
from config import adminlist

IS_BROADCASTING = False

async def send_broadcast_message(client, chat_id, message, query=None, reply_markup=None):
    """
    Sends the broadcast message (either text query or message reply) to chat_id
    using the specified client.
    """
    if message.reply_to_message:
        reply = message.reply_to_message
        try:
            m = await client.copy_message(
                chat_id=chat_id,
                from_chat_id=message.chat.id,
                message_id=reply.id,
                reply_markup=reply_markup or reply.reply_markup
            )
            return m
        except Exception:
            caption = reply.caption
            markup = reply_markup or reply.reply_markup
            if reply.photo:
                return await client.send_photo(chat_id, photo=reply.photo.file_id, caption=caption, reply_markup=markup)
            elif reply.audio:
                return await client.send_audio(chat_id, audio=reply.audio.file_id, caption=caption, reply_markup=markup)
            elif reply.video:
                return await client.send_video(chat_id, video=reply.video.file_id, caption=caption, reply_markup=markup)
            elif reply.document:
                return await client.send_document(chat_id, document=reply.document.file_id, caption=caption, reply_markup=markup)
            elif reply.animation:
                return await client.send_animation(chat_id, animation=reply.animation.file_id, caption=caption, reply_markup=markup)
            elif reply.sticker:
                return await client.send_sticker(chat_id, sticker=reply.sticker.file_id, reply_markup=markup)
            elif reply.voice:
                return await client.send_voice(chat_id, voice=reply.voice.file_id, caption=caption, reply_markup=markup)
            elif reply.video_note:
                return await client.send_video_note(chat_id, video_note=reply.video_note.file_id, reply_markup=markup)
            elif reply.text:
                return await client.send_message(chat_id, text=reply.text, reply_markup=markup)
    else:
        return await client.send_message(chat_id, text=query)


@app.on_message(filters.command("broadcast") & SUDOERS)
@language
async def braodcast_message(client, message, _):
    global IS_BROADCASTING

    if IS_BROADCASTING:
        return await message.reply_text("Already broadcasting in progress...")

    reply_markup = None

    # 🔹 If reply message
    if message.reply_to_message:
        x = message.reply_to_message.id
        y = message.chat.id
        reply_markup = message.reply_to_message.reply_markup
    else:
        if len(message.command) < 2:
            return await message.reply_text(_["broad_2"])

        query = message.text.split(None, 1)[1]

        # 🔹 Clean flags
        flags = ["-pin", "-nobot", "-pinloud", "-assistant", "-user"]
        for f in flags:
            query = query.replace(f, "")

        query = query.strip()

        if query == "":
            return await message.reply_text(_["broad_8"])

    IS_BROADCASTING = True
    await message.reply_text(_["broad_1"])

    chats_targets = []  # list of (bot_client, chat_id)
    users_targets = []  # list of (bot_client, user_id)

    from SONALI_MUSIC.utils.database_clone import is_supreme_admin, get_cloned_served_chats, get_cloned_served_users
    is_owner = await is_supreme_admin(message.from_user.id)

    if is_owner:
        # Platform Owner / Supreme Admin context: Broadcast to EVERYTHING!
        # 1. Main bot chats and users
        main_chats = [int(chat["chat_id"]) for chat in await get_served_chats()]
        for c in main_chats:
            chats_targets.append((app, c))

        main_users = [int(user["user_id"]) for user in await get_served_users()]
        for u in main_users:
            users_targets.append((app, u))

        # 2. All active cloned bots' chats and users
        from SONALI_MUSIC.core.clone_manager import clone_manager
        for bot_id, clone_client in clone_manager.clones.items():
            cloned_chats = await get_cloned_served_chats(bot_id)
            for c in cloned_chats:
                chats_targets.append((clone_client, c))

            cloned_users = await get_cloned_served_users(bot_id)
            for u in cloned_users:
                users_targets.append((clone_client, u))
    else:
        # Non-owner / Clone Tenant context
        from SONALI_MUSIC.core.clone_manager import current_clone_client
        clone = current_clone_client.get()
        if clone is not None:
            # Cloned bot owner broadcasting on their own bot
            cloned_chats = await get_cloned_served_chats(clone.me.id)
            for c in cloned_chats:
                chats_targets.append((clone, c))

            cloned_users = await get_cloned_served_users(clone.me.id)
            for u in cloned_users:
                users_targets.append((clone, u))
        else:
            # Main bot sudoer context
            main_chats = [int(chat["chat_id"]) for chat in await get_served_chats()]
            for c in main_chats:
                chats_targets.append((app, c))

            main_users = [int(user["user_id"]) for user in await get_served_users()]
            for u in main_users:
                users_targets.append((app, u))

    # ================= CHAT BROADCAST =================
    if "-nobot" not in message.text:
        sent = 0
        pin = 0

        for b_client, chat_id in chats_targets:
            try:
                m = await send_broadcast_message(b_client, chat_id, message, query if not message.reply_to_message else None, reply_markup)
                if m:
                    sent += 1
                    # 🔹 Pin logic
                    if "-pin" in message.text:
                        try:
                            await m.pin(disable_notification=True)
                            pin += 1
                        except:
                            pass
                    elif "-pinloud" in message.text:
                        try:
                            await m.pin(disable_notification=False)
                            pin += 1
                        except:
                            pass
                await asyncio.sleep(0.2)
            except FloodWait as fw:
                await asyncio.sleep(fw.value)
            except Exception:
                continue

        await message.reply_text(_["broad_3"].format(sent, pin))

    # ================= USER BROADCAST =================
    if "-user" in message.text:
        susr = 0

        for b_client, user_id in users_targets:
            try:
                m = await send_broadcast_message(b_client, user_id, message, query if not message.reply_to_message else None, reply_markup)
                if m:
                    susr += 1
                await asyncio.sleep(0.2)
            except FloodWait as fw:
                await asyncio.sleep(fw.value)
            except Exception:
                continue

        await message.reply_text(_["broad_4"].format(susr))

    # ================= ASSISTANT BROADCAST =================
    if "-assistant" in message.text:
        from SONALI_MUSIC.core.clone_manager import current_clone_client
        clone = current_clone_client.get()
        if clone is not None:
            await message.reply_text("❌ Assistant broadcast is not supported on cloned bots.")
        else:
            aw = await message.reply_text(_["broad_5"])
            text = _["broad_6"]

            from SONALI_MUSIC.core.userbot import assistants

            for num in assistants:
                sent = 0
                client = await get_client(num)

                async for dialog in client.get_dialogs():
                    try:
                        if message.reply_to_message:
                            await client.copy_message(
                                chat_id=dialog.chat.id,
                                from_chat_id=y,
                                message_id=x
                            )
                        else:
                            await client.send_message(dialog.chat.id, text=query)

                        sent += 1
                        await asyncio.sleep(2)

                    except FloodWait as fw:
                        await asyncio.sleep(fw.value)
                    except:
                        continue

                text += _["broad_7"].format(num, sent)

            await aw.edit_text(text)

    IS_BROADCASTING = False


# ================= AUTO CLEAN =================
async def auto_clean():
    while True:
        await asyncio.sleep(10)
        try:
            served_chats = await get_active_chats()

            for chat_id in served_chats:
                if chat_id not in adminlist:
                    adminlist[chat_id] = []

                    async for user in app.get_chat_members(
                        chat_id, filter=ChatMembersFilter.ADMINISTRATORS
                    ):
                        if user.privileges.can_manage_video_chats:
                            adminlist[chat_id].append(user.user.id)

                    authusers = await get_authuser_names(chat_id)

                    for user in authusers:
                        user_id = await alpha_to_int(user)
                        adminlist[chat_id].append(user_id)

        except:
            continue


asyncio.create_task(auto_clean())
