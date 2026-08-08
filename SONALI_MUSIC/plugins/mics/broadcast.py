import asyncio
import logging

from pyrogram import filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.errors import (
    FloodWait,
    PeerIdInvalid,
    ChannelInvalid,
    ChannelPrivate,
    ChatWriteForbidden,
    UserIsBlocked,
    InputUserDeactivated
)

from SONALI_MUSIC import app
from SONALI_MUSIC.utils.database_clone import cleanup_stale_chat, cleanup_stale_user

logger = logging.getLogger(__name__)
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
    progress_msg = await message.reply_text("⚡ **Initiating Global Contextual Broadcast...**\n*Processing targets...*")

    chats_targets = []  # list of (bot_client, chat_id)
    users_targets = []  # list of (bot_client, user_id)

    from SONALI_MUSIC.utils.database_clone import is_supreme_admin, get_cloned_served_chats, get_cloned_served_users, get_clone_by_id
    is_owner = await is_supreme_admin(message.from_user.id)

    from SONALI_MUSIC.core.clone_manager import current_clone_client
    clone = current_clone_client.get()

    # Contextual security check for cloned bot broadcasts
    if clone is not None:
        clone_data = await get_clone_by_id(clone.me.id)
        if clone_data:
            tenant_id = clone_data.get("tenant_id")
            if message.from_user.id != tenant_id and not is_owner:
                IS_BROADCASTING = False
                return await message.reply_text("❌ **Access Denied:** Only the owner of this cloned bot can initiate a broadcast!")

    if is_owner:
        # Platform Owner / Supreme Admin context: Broadcast to EVERYTHING!
        # 1. Main bot chats and users (isolated to avoid invalid peer/channel errors)
        from SONALI_MUSIC.utils.database_clone import get_main_bot_served_chats, get_main_bot_served_users
        main_chats = await get_main_bot_served_chats()
        for c in main_chats:
            chats_targets.append((app, c))

        main_users = await get_main_bot_served_users()
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
    elif clone is not None:
        # Clone tenant context: Broadcast ONLY to this clone's targets
        cloned_chats = await get_cloned_served_chats(clone.me.id)
        for c in cloned_chats:
            chats_targets.append((clone, c))

        cloned_users = await get_cloned_served_users(clone.me.id)
        for u in cloned_users:
            users_targets.append((clone, u))
    else:
        # Main bot sudoer context (isolated to avoid invalid peer/channel errors)
        from SONALI_MUSIC.utils.database_clone import get_main_bot_served_chats, get_main_bot_served_users
        main_chats = await get_main_bot_served_chats()
        for c in main_chats:
            chats_targets.append((app, c))

        main_users = await get_main_bot_served_users()
        for u in main_users:
            users_targets.append((app, u))

    await progress_msg.edit_text(
        f"⏳ **Broadcasting in Progress...**\n\n"
        f"📊 **Target Metrics:**\n"
        f" ├ 👥 **Group Chats:** `{len(chats_targets)}`\n"
        f" └ 👤 **Private Users:** `{len(users_targets)}`"
    )

    sent_chats = 0
    pin_chats = 0
    failed_chats = 0

    # ================= CHAT BROADCAST =================
    for b_client, chat_id in chats_targets:
        # Resolve bot_id safely
        b_id = getattr(b_client, "id", None) or (b_client.me.id if (hasattr(b_client, "me") and b_client.me) else app.id)

        try:
            m = await send_broadcast_message(b_client, chat_id, message, query if not message.reply_to_message else None, reply_markup)
            if m:
                sent_chats += 1
                # 🔹 Pin logic
                if "-pin" in message.text:
                    try:
                        await m.pin(disable_notification=True)
                        pin_chats += 1
                    except:
                        pass
                elif "-pinloud" in message.text:
                    try:
                        await m.pin(disable_notification=False)
                        pin_chats += 1
                    except:
                        pass
            else:
                failed_chats += 1
            await asyncio.sleep(0.1)
        except FloodWait as fw:
            await asyncio.sleep(fw.value)
            try:
                m = await send_broadcast_message(b_client, chat_id, message, query if not message.reply_to_message else None, reply_markup)
                if m:
                    sent_chats += 1
                else:
                    failed_chats += 1
            except (PeerIdInvalid, ChannelInvalid, ChannelPrivate, ChatWriteForbidden) as e:
                logger.warning(f"Group/channel became stale during broadcast retry on clone {b_id} for chat {chat_id}: {e}. Removing from DB.")
                await cleanup_stale_chat(b_id, chat_id)
                failed_chats += 1
            except Exception:
                failed_chats += 1
        except (PeerIdInvalid, ChannelInvalid, ChannelPrivate, ChatWriteForbidden) as e:
            logger.warning(f"Stale group/channel entity detected on clone {b_id} for chat {chat_id}: {e}. Removing from DB.")
            await cleanup_stale_chat(b_id, chat_id)
            failed_chats += 1
        except Exception:
            failed_chats += 1

    # ================= USER BROADCAST =================
    sent_users = 0
    failed_users = 0

    for b_client, user_id in users_targets:
        # Resolve bot_id safely
        b_id = getattr(b_client, "id", None) or (b_client.me.id if (hasattr(b_client, "me") and b_client.me) else app.id)

        try:
            m = await send_broadcast_message(b_client, user_id, message, query if not message.reply_to_message else None, reply_markup)
            if m:
                sent_users += 1
            else:
                failed_users += 1
            await asyncio.sleep(0.1)
        except FloodWait as fw:
            await asyncio.sleep(fw.value)
            try:
                m = await send_broadcast_message(b_client, user_id, message, query if not message.reply_to_message else None, reply_markup)
                if m:
                    sent_users += 1
                else:
                    failed_users += 1
            except (PeerIdInvalid, UserIsBlocked, InputUserDeactivated) as e:
                logger.warning(f"User became stale during broadcast retry on clone {b_id} for user {user_id}: {e}. Removing from DB.")
                await cleanup_stale_user(b_id, user_id)
                failed_users += 1
            except Exception:
                failed_users += 1
        except (PeerIdInvalid, UserIsBlocked, InputUserDeactivated) as e:
            logger.warning(f"Stale user entity detected on clone {b_id} for user {user_id}: {e}. Removing from DB.")
            await cleanup_stale_user(b_id, user_id)
            failed_users += 1
        except Exception:
            failed_users += 1

    # ================= ASSISTANT BROADCAST =================
    sent_assistant = 0
    assistant_report = ""
    if "-assistant" in message.text:
        from SONALI_MUSIC.core.clone_manager import current_clone_client
        clone = current_clone_client.get()
        if clone is not None:
            assistant_report = "\n❌ *Assistant broadcast is not supported on cloned bots.*"
        else:
            assistant_report = "\n\n🤖 **Assistant Broadcast:**"
            from SONALI_MUSIC.core.userbot import assistants
            for num in assistants:
                sent_ass = 0
                client = await get_client(num)
                async for dialog in client.get_dialogs():
                    try:
                        if message.reply_to_message:
                            await client.copy_message(
                                chat_id=dialog.chat.id,
                                from_chat_id=message.chat.id,
                                message_id=message.reply_to_message.id
                            )
                        else:
                            await client.send_message(dialog.chat.id, text=query)
                        sent_ass += 1
                        await asyncio.sleep(1)
                    except FloodWait as fw:
                        await asyncio.sleep(fw.value)
                    except:
                        continue
                assistant_report += f"\n ├ Assistant {num}: `{sent_ass}` chats"

    # Compile a highly powerful, detailed summary report
    summary = (
        f"📢 **『 ʙʀᴏᴀᴅᴄᴀsᴛ ᴇxᴇᴄᴜᴛɪᴏɴ sᴜᴍᴍᴀʀʏ 』**\n\n"
        f"✅ **ᴄʜᴀᴛ ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴀᴛs:**\n"
        f" ├ 📤 **sᴇɴᴛ sᴜᴄᴄᴇssғᴜʟʟʏ:** `{sent_chats}`\n"
        f" ├ 📌 **ᴘɪɴɴᴇᴅ ᴍᴇssᴀɢᴇs:** `{pin_chats}`\n"
        f" └ ❌ **ғᴀɪʟᴇᴅ/ʙʟᴏᴄᴋᴇᴅ:** `{failed_chats}`\n\n"
        f"👤 **ᴜsᴇʀ ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴀᴛs:**\n"
        f" ├ 📤 **sᴇɴᴛ sᴜᴄᴄᴇssғᴜʟʟʏ:** `{sent_users}`\n"
        f" └ ❌ **ғᴀɪʟᴇᴅ/ʙʟᴏᴄᴋᴇᴅ:** `{failed_users}`"
        f"{assistant_report}\n\n"
        f"🌟 **ᴛᴀsᴋ ᴄᴏᴍᴘʟᴇᴛᴇᴅ sᴇᴀᴍʟᴇssʟʏ!**"
    )

    await progress_msg.delete()
    await message.reply_text(summary)

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
