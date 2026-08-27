import asyncio
import logging
import os

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

async def send_broadcast_message(client, chat_id, message, query=None, reply_markup=None, media_path=None):
    """
    Sends the broadcast message (either text query or message reply) to chat_id
    using the specified client.
    """
    from SONALI_MUSIC.core.clone_manager import current_clone_client
    token = current_clone_client.set(client if client != app else None)
    try:
        if message.reply_to_message:
            reply = message.reply_to_message
            try:
                return await client.copy_message(
                    chat_id=chat_id,
                    from_chat_id=message.chat.id,
                    message_id=reply.id,
                    reply_markup=reply_markup or reply.reply_markup
                )
            except Exception:
                caption = reply.caption
                markup = reply_markup or reply.reply_markup
                if reply.text:
                    return await client.send_message(chat_id, text=reply.text, reply_markup=markup)

                target_media = media_path if (media_path and os.path.exists(media_path)) else None

                if reply.photo:
                    return await client.send_photo(chat_id, photo=target_media or reply.photo.file_id, caption=caption, reply_markup=markup)
                elif reply.audio:
                    return await client.send_audio(chat_id, audio=target_media or reply.audio.file_id, caption=caption, reply_markup=markup)
                elif reply.video:
                    return await client.send_video(chat_id, video=target_media or reply.video.file_id, caption=caption, reply_markup=markup)
                elif reply.document:
                    return await client.send_document(chat_id, document=target_media or reply.document.file_id, caption=caption, reply_markup=markup)
                elif reply.animation:
                    return await client.send_animation(chat_id, animation=target_media or reply.animation.file_id, caption=caption, reply_markup=markup)
                elif reply.sticker:
                    return await client.send_sticker(chat_id, sticker=target_media or reply.sticker.file_id, reply_markup=markup)
                elif reply.voice:
                    return await client.send_voice(chat_id, voice=target_media or reply.voice.file_id, caption=caption, reply_markup=markup)
                elif reply.video_note:
                    return await client.send_video_note(chat_id, video_note=target_media or reply.video_note.file_id, reply_markup=markup)
        else:
            return await client.send_message(chat_id, text=query, reply_markup=reply_markup)
    finally:
        current_clone_client.reset(token)


@app.on_message(filters.command("broadcast") & SUDOERS)
@language
async def braodcast_message(client, message, _):
    global IS_BROADCASTING

    if IS_BROADCASTING:
        return await message.reply_text("Already broadcasting in progress...")

    reply_markup = None
    query = None

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
                return await message.reply_text("❌ **Access Denied:** Only the owner of this cloned bot can initiate a broadcast!")

    IS_BROADCASTING = True
    media_path = None
    progress_msg = None

    try:
        progress_msg = await message.reply_text("⚡ **Initiating Global Contextual Broadcast...**\n*Processing targets...*")

        # Download media if reply message contains media
        if message.reply_to_message:
            reply = message.reply_to_message
            if not reply.text:
                try:
                    media_path = await message._client.download_media(reply)
                except Exception as e:
                    logger.error(f"Failed to download media for broadcast: {e}")

        chats_targets = []  # list of (bot_client, chat_id)
        users_targets = []  # list of (bot_client, user_id)

        if is_owner:
            # Platform Owner / Supreme Admin context: Broadcast to EVERYTHING!
            # 1. Main bot chats and users
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
            # Main bot sudoer context
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
            b_id = getattr(b_client, "id", None) or (b_client.me.id if (hasattr(b_client, "me") and b_client.me) else app.id)

            try:
                m = await send_broadcast_message(b_client, chat_id, message, query if not message.reply_to_message else None, reply_markup, media_path)
                if m:
                    sent_chats += 1
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
                    m = await send_broadcast_message(b_client, chat_id, message, query if not message.reply_to_message else None, reply_markup, media_path)
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
            b_id = getattr(b_client, "id", None) or (b_client.me.id if (hasattr(b_client, "me") and b_client.me) else app.id)

            try:
                m = await send_broadcast_message(b_client, user_id, message, query if not message.reply_to_message else None, reply_markup, media_path)
                if m:
                    sent_users += 1
                else:
                    failed_users += 1
                await asyncio.sleep(0.1)
            except FloodWait as fw:
                await asyncio.sleep(fw.value)
                try:
                    m = await send_broadcast_message(b_client, user_id, message, query if not message.reply_to_message else None, reply_markup, media_path)
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
        assistant_report = ""
        if "-assistant" in message.text:
            if clone is not None:
                assistant_report = "\n❌ *Assistant broadcast is not supported on cloned bots.*"
            else:
                assistant_report = "\n\n🤖 **Assistant Broadcast:**"
                from SONALI_MUSIC.core.userbot import assistants
                for num in assistants:
                    sent_ass = 0
                    c_client = await get_client(num)
                    async for dialog in c_client.get_dialogs():
                        try:
                            if message.reply_to_message:
                                await c_client.copy_message(
                                    chat_id=dialog.chat.id,
                                    from_chat_id=message.chat.id,
                                    message_id=message.reply_to_message.id
                                )
                            else:
                                await c_client.send_message(dialog.chat.id, text=query)
                            sent_ass += 1
                            await asyncio.sleep(1)
                        except FloodWait as fw:
                            await asyncio.sleep(fw.value)
                        except:
                            continue
                    assistant_report += f"\n ├ Assistant {num}: `{sent_ass}` chats"

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

        if progress_msg:
            try:
                await progress_msg.delete()
            except Exception:
                pass
        await message.reply_text(summary)

    except Exception as e:
        logger.error(f"Error during broadcast execution: {e}", exc_info=True)
        await message.reply_text(f"❌ **Broadcast Failed:** `{e}`")
    finally:
        IS_BROADCASTING = False
        if media_path and os.path.exists(media_path):
            try:
                os.remove(media_path)
            except Exception:
                pass


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


try:
    asyncio.create_task(auto_clean())
except RuntimeError:
    pass
