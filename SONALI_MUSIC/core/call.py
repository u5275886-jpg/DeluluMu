import asyncio
import os
from datetime import datetime, timedelta
from typing import Union

from ntgcalls import ConnectionNotFound, TelegramServerError
from pyrogram import Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pytgcalls import PyTgCalls, exceptions, types
from pytgcalls.pytgcalls_session import PyTgCallsSession

import config
from SONALI_MUSIC import LOGGER, YouTube, app
from SONALI_MUSIC.misc import db
from SONALI_MUSIC.utils.database import (add_active_chat, add_active_video_chat,
                                       get_lang, get_loop, group_assistant,
                                       is_autoend, music_on,
                                       remove_active_chat,
                                       remove_active_video_chat, set_loop)
from SONALI_MUSIC.utils.exceptions import AssistantErr
from SONALI_MUSIC.utils.formatters import (check_duration, seconds_to_min,
                                         speed_converter)
from SONALI_MUSIC.utils.inline.play import stream_markup
from SONALI_MUSIC.utils.stream.autoclear import auto_clean
from SONALI_MUSIC.utils.thumbnails import get_thumb
from strings import get_string


async def delete_old_message(chat_id: int):
    try:
        old = db.get(chat_id, [{}])[0].get("mystic")
        if old:
            await old.delete()
    except:
        pass


autoend = {}
counter = {}


async def _clear_(chat_id: int):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)


class Call(PyTgCalls):
    def __init__(self):
        PyTgCallsSession.notice_displayed = True

        self.userbot1 = Client(
            name="SonaXAss1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
        )
        self.one = PyTgCalls(self.userbot1, cache_duration=100)

        self.userbot2 = Client(
            name="SonaXAss2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
        )
        self.two = PyTgCalls(self.userbot2, cache_duration=100)

        self.userbot3 = Client(
            name="SonaXAss3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
        )
        self.three = PyTgCalls(self.userbot3, cache_duration=100)

        self.userbot4 = Client(
            name="SonaXAss4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
        )
        self.four = PyTgCalls(self.userbot4, cache_duration=100)

        self.userbot5 = Client(
            name="SonaXAss5",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING5),
        )
        self.five = PyTgCalls(self.userbot5, cache_duration=100)
        self.custom_assistants = {}

    async def start_custom_assistant(self, bot_id: int, session_string: str) -> bool:
        await self.stop_custom_assistant(bot_id)
        try:
            userbot = Client(
                name=f"CustomAss_{bot_id}",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                session_string=session_string,
                no_updates=True,
            )
            await userbot.start()
            userbot.id = userbot.me.id
            userbot.name = userbot.me.mention
            userbot.username = userbot.me.username
            try:
                await userbot.join_chat("kriti_bot_update")
                await userbot.join_chat("KRITI_SUPPORT_GROUP")
            except Exception:
                pass

            pytgcalls_client = PyTgCalls(userbot, cache_duration=100)

            @pytgcalls_client.on_update()
            async def _update_handler(_, update: types.Update, _client=pytgcalls_client):
                if isinstance(update, types.StreamEnded):
                    if update.stream_type == types.StreamEnded.Type.AUDIO:
                        await self.change_stream(_client, update.chat_id)
                elif isinstance(update, types.ChatUpdate):
                    if update.status in [
                        types.ChatUpdate.Status.KICKED,
                        types.ChatUpdate.Status.LEFT_GROUP,
                        types.ChatUpdate.Status.CLOSED_VOICE_CHAT,
                    ]:
                        await self.stop_stream(update.chat_id)

            await pytgcalls_client.start()

            self.custom_assistants[bot_id] = {
                "userbot": userbot,
                "pytgcalls": pytgcalls_client
            }
            LOGGER(__name__).info(f"Custom Assistant for bot {bot_id} started successfully.")
            return True
        except Exception as e:
            LOGGER(__name__).error(f"Failed to start custom assistant for bot {bot_id}: {e}")
            return False

    async def stop_custom_assistant(self, bot_id: int):
        if hasattr(self, "custom_assistants") and bot_id in self.custom_assistants:
            data = self.custom_assistants[bot_id]
            try:
                await data["pytgcalls"].stop()
            except Exception:
                pass
            try:
                await data["userbot"].stop()
            except Exception:
                pass
            del self.custom_assistants[bot_id]
            LOGGER(__name__).info(f"Custom Assistant for bot {bot_id} stopped.")

    def _build_stream(
        self,
        source: str,
        video: bool,
        ffmpeg: str | None = None,
    ) -> types.MediaStream:
        return types.MediaStream(
            media_path=source,
            audio_parameters=types.AudioQuality.HIGH,
            video_parameters=types.VideoQuality.HD_720p,
            audio_flags=types.MediaStream.Flags.REQUIRED,
            video_flags=(
                types.MediaStream.Flags.AUTO_DETECT
                if video
                else types.MediaStream.Flags.IGNORE
            ),
            ffmpeg_parameters=ffmpeg,
        )

    
    async def _play_on_assistant(
        self,
        client: PyTgCalls,
        chat_id: int,
        stream: types.MediaStream,
    ):
        try:
            await client.play(
                chat_id=chat_id,
                stream=stream,
                config=types.GroupCallConfig(auto_start=False),
            )
        except exceptions.NoActiveGroupCall:
            raise
        except exceptions.NoAudioSourceFound:
            raise
        except (ConnectionNotFound, TelegramServerError):
            raise
        except Exception:
            raise

    
    async def pause_stream(self, chat_id: int):
        await delete_old_message(chat_id)
        assistant = await group_assistant(self, chat_id)
        await assistant.pause(chat_id)

    
    async def resume_stream(self, chat_id: int):
        await delete_old_message(chat_id)
        assistant = await group_assistant(self, chat_id)
        await assistant.resume(chat_id)

    
    async def stop_stream(self, chat_id: int):
        await delete_old_message(chat_id)
        assistant = await group_assistant(self, chat_id)
        try:
            await _clear_(chat_id)
            await assistant.leave_call(chat_id, close=False)
        except Exception:
            pass

    
    async def stop_stream_force(self, chat_id: int):
        for string, client in [
            (config.STRING1, self.one),
            (config.STRING2, self.two),
            (config.STRING3, self.three),
            (config.STRING4, self.four),
            (config.STRING5, self.five),
        ]:
            if not string:
                continue
            try:
                await client.leave_call(chat_id, close=False)
            except Exception:
                pass
        for bot_id, data in getattr(self, "custom_assistants", {}).items():
            try:
                await data["pytgcalls"].leave_call(chat_id, close=False)
            except Exception:
                pass
        try:
            await _clear_(chat_id)
        except Exception:
            pass

    
    async def speedup_stream(self, chat_id: int, file_path, speed, playing):
        assistant = await group_assistant(self, chat_id)
        if str(speed) != "1.0":
            base = os.path.basename(file_path)
            chatdir = os.path.join(os.getcwd(), "playback", str(speed))
            if not os.path.isdir(chatdir):
                os.makedirs(chatdir)
            out = os.path.join(chatdir, base)
            if not os.path.isfile(out):
                if str(speed) == "0.5":
                    vs = 2.0
                elif str(speed) == "0.75":
                    vs = 1.35
                elif str(speed) == "1.5":
                    vs = 0.68
                elif str(speed) == "2.0":
                    vs = 0.5
                else:
                    vs = 1.0
                proc = await asyncio.create_subprocess_shell(
                    cmd=(
                        "ffmpeg "
                        "-i "
                        f"{file_path} "
                        "-filter:v "
                        f"setpts={vs}*PTS "
                        "-filter:a "
                        f"atempo={speed} "
                        f"{out}"
                    ),
                    stdin=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
        else:
            out = file_path
        dur = await asyncio.get_event_loop().run_in_executor(None, check_duration, out)
        dur = int(dur)
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration = seconds_to_min(dur)
        xx = f"-ss {played} -to {duration}"
        video_mode = playing[0]["streamtype"] == "video"
        stream = self._build_stream(out, video=video_mode, ffmpeg=xx)
        if str(db[chat_id][0]["file"]) == str(file_path):
            await self._play_on_assistant(assistant, chat_id, stream)
        else:
            raise AssistantErr("Umm")
        if str(db[chat_id][0]["file"]) == str(file_path):
            exis = (playing[0]).get("old_dur")
            if not exis:
                db[chat_id][0]["old_dur"] = db[chat_id][0]["dur"]
                db[chat_id][0]["old_second"] = db[chat_id][0]["seconds"]
            db[chat_id][0]["played"] = con_seconds
            db[chat_id][0]["dur"] = duration
            db[chat_id][0]["seconds"] = dur
            db[chat_id][0]["speed_path"] = out
            db[chat_id][0]["speed"] = speed

    async def force_stop_stream(self, chat_id: int):
        await delete_old_message(chat_id)
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            check.pop(0)
        except Exception:
            pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        try:
            await assistant.leave_call(chat_id, close=False)
        except Exception:
            pass

    
    async def skip_stream(
        self,
        chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        stream = self._build_stream(link, video=bool(video))
        await self._play_on_assistant(assistant, chat_id, stream)

    
    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        assistant = await group_assistant(self, chat_id)
        ffmpeg = f"-ss {to_seek} -to {duration}"
        video_mode = mode == "video"
        stream = self._build_stream(
            file_path,
            video=video_mode,
            ffmpeg=ffmpeg,
        )
        await self._play_on_assistant(assistant, chat_id, stream)

    
    async def stream_call(self, link):
        assistant = await group_assistant(self, config.LOGGER_ID)
        stream = self._build_stream(link, video=True)
        await self._play_on_assistant(assistant, config.LOGGER_ID, stream)
        await asyncio.sleep(0.2)
        try:
            await assistant.leave_call(config.LOGGER_ID, close=False)
        except Exception:
            pass

    
    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        from SONALI_MUSIC.core.clone_manager import current_clone_client, clone_manager
        from SONALI_MUSIC.utils.database import assistantdict

        bot_id = None
        check = db.get(chat_id)
        if check and len(check) > 0:
            bot_id = check[0].get("bot_id")

        if not bot_id:
            for (b_id, c_id), assis_idx in assistantdict.items():
                if c_id == chat_id:
                    bot_id = b_id
                    break

        token = None
        if bot_id:
            clone_client = clone_manager.clones.get(bot_id)
            if clone_client:
                token = current_clone_client.set(clone_client)

        try:
            assistant = await group_assistant(self, chat_id)
            language = await get_lang(chat_id)
            _ = get_string(language)

            # Check if assistant is in the chat, and join if not
            from pyrogram.enums import ChatMemberStatus
            from pyrogram.errors import (
                ChatAdminRequired,
                InviteRequestSent,
                UserAlreadyParticipant,
                UserNotParticipant,
                PeerIdInvalid,
            )
            from SONALI_MUSIC.utils.database import get_assistant

            userbot = await get_assistant(chat_id)
            try:
                try:
                    if hasattr(userbot, "username") and userbot.username:
                        try:
                            await app.resolve_peer(userbot.username)
                        except Exception:
                            pass
                    get = await app.get_chat_member(chat_id, userbot.id)
                except ChatAdminRequired:
                    raise AssistantErr(_["call_1"])
                except (PeerIdInvalid, KeyError):
                    raise UserNotParticipant
                if (
                    get.status == ChatMemberStatus.BANNED
                    or get.status == ChatMemberStatus.RESTRICTED
                ):
                    try:
                        await app.unban_chat_member(chat_id, userbot.id)
                    except Exception:
                        raise AssistantErr(
                            _["call_2"].format(
                                app.mention, userbot.id, userbot.name, userbot.username
                            )
                        )
            except UserNotParticipant:
                added_directly = False
                try:
                    await app.add_chat_members(chat_id, userbot.id)
                    added_directly = True
                except Exception:
                    pass

                if not added_directly:
                    try:
                        chat = await app.get_chat(chat_id)
                        if chat.username:
                            invitelink = chat.username
                            try:
                                await userbot.resolve_peer(invitelink)
                            except Exception:
                                pass
                        else:
                            invitelink = await app.export_chat_invite_link(chat_id)
                    except ChatAdminRequired:
                        raise AssistantErr(_["call_1"])
                    except Exception as e:
                        raise AssistantErr(
                            _["call_3"].format(app.mention, type(e).__name__)
                        )

                    if invitelink.startswith("https://t.me/+"):
                        invitelink = invitelink.replace(
                            "https://t.me/+", "https://t.me/joinchat/"
                        )
                    try:
                        await userbot.join_chat(invitelink)
                    except InviteRequestSent:
                        try:
                            await app.approve_chat_join_request(chat_id, userbot.id)
                        except Exception as e:
                            raise AssistantErr(
                                _["call_3"].format(app.mention, type(e).__name__)
                            )
                    except UserAlreadyParticipant:
                        pass
                    except Exception as e:
                        raise AssistantErr(
                            _["call_3"].format(app.mention, type(e).__name__)
                        )

                try:
                    await userbot.resolve_peer(chat_id)
                except Exception:
                    pass

            stream = self._build_stream(link, video=bool(video))
            try:
                await self._play_on_assistant(assistant, chat_id, stream)
            except exceptions.NoActiveGroupCall:
                raise AssistantErr(_["call_8"])
            except exceptions.NoAudioSourceFound:
                raise AssistantErr(
                    "❖ <b>ᴀᴜᴅɪᴏ sᴏᴜʀᴄᴇ ɴᴏᴛ ғᴏᴜɴᴅ</b>\n\n"
                    "ᴛʜᴇ ᴀssɪsᴛᴀɴᴛ ᴄᴏᴜʟᴅ ɴᴏᴛ ғɪɴᴅ ᴀ ᴠᴀʟɪᴅ ᴀᴜᴅɪᴏ/ᴠɪᴅᴇᴏ sᴏᴜʀᴄᴇ ᴛᴏ sᴛʀᴇᴀᴍ. "
                    "ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ᴡɪᴛʜ ᴀ ᴅɪғғᴇʀᴇɴᴛ ʟɪɴᴋ ᴏʀ ʀᴇsᴛᴀʀᴛ ᴛʜᴇ ᴠɪᴅᴇᴏᴄʜᴀᴛ."
                )
            except (ConnectionNotFound, TelegramServerError):
                raise AssistantErr(_["call_10"])
            except Exception as e:
                raise AssistantErr(
                    f"❖ <b>ᴀssɪsᴛᴀɴᴛ ᴇʀʀᴏʀ</b>\n\n"
                    f"ᴀɴ ᴇxᴄᴇᴘᴛɪᴏɴ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴘʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ.\n\n"
                    f"<b>Exception Type:</b> <code>{type(e).__name__}</code>\n"
                    f"<b>Error Details:</b> <code>{str(e)}</code>"
                )
            await add_active_chat(chat_id)
            await music_on(chat_id)
            if video:
                await add_active_video_chat(chat_id)
            if await is_autoend():
                counter[chat_id] = {}
                users = len(await assistant.get_participants(chat_id))
                if users == 1:
                    autoend[chat_id] = datetime.now() + timedelta(minutes=1)
        finally:
            if token:
                current_clone_client.reset(token)

    
    async def change_stream(self, client: PyTgCalls, chat_id: int):
        from SONALI_MUSIC.core.clone_manager import current_clone_client, clone_manager
        from SONALI_MUSIC.utils.database import assistantdict

        bot_id = None
        check = db.get(chat_id)
        if check and len(check) > 0:
            bot_id = check[0].get("bot_id")

        if not bot_id:
            for (b_id, c_id), assis_idx in assistantdict.items():
                if c_id == chat_id:
                    bot_id = b_id
                    break

        token = None
        if bot_id:
            clone_client = clone_manager.clones.get(bot_id)
            if clone_client:
                token = current_clone_client.set(clone_client)

        try:
            await self._change_stream_impl(client, chat_id)
        finally:
            if token:
                current_clone_client.reset(token)

    async def _change_stream_impl(self, client: PyTgCalls, chat_id: int):
        await delete_old_message(chat_id)
        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)
        try:
            if loop == 0:
                popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)
            await auto_clean(popped)
            if not check:
                await _clear_(chat_id)
                try:
                    buttons = InlineKeyboardMarkup(
                        [
                            [
                                                                InlineKeyboardButton(
                                    "✙ ʌᴅᴅ ϻє вᴧʙʏ ✙", url=f"https://t.me/{app.username}?startgroup=true"
                                )],
                            [
                                InlineKeyboardButton(
                                    "⋞ ᴄʟᴏsє ⋟", callback_data="close_message"
                                ),
                            ]
                        ]
                    )
                    await app.send_message(
    chat_id,
    """
🎵 𝐓ʜᴇ 𝐌ᴜsɪᴄ 𝐐ᴜᴇᴜᴇ 𝐇ᴀ𝐬 𝐄ɴᴅᴇᴅ.
➤ 𝐔𝐬𝐞 /play 𝐓𝐨 𝐀𝐝𝐝 𝐌𝐨𝐫𝐞 𝐒𝐨𝐧𝐠𝐬 🎶
""",
    reply_markup=buttons,
)
                except:
                    pass
                return await client.leave_call(chat_id, close=False)
        except Exception:
            try:
                await _clear_(chat_id)
                try:
                    buttons = InlineKeyboardMarkup(
                        [
                            [
                                                                InlineKeyboardButton(
                                    "✙ ʌᴅᴅ ϻє вᴧʙʏ ✙", url=f"https://t.me/{app.username}?startgroup=true"
                                )],
                            [
                                InlineKeyboardButton(
                                    "⋞ ᴄʟᴏsє ⋟", callback_data="close_message"
                                ),
                            ]
                        ]
                    )
                    await app.send_message(
    chat_id,
    """
🎵 𝐓ʜᴇ 𝐌ᴜsɪᴄ 𝐐ᴜᴇᴜᴇ 𝐇ᴀ𝐬 𝐄ɴᴅᴇᴅ.
➤ 𝐔𝐬𝐞 /play 𝐓𝐨 𝐀𝐝𝐝 𝐌𝐨𝐫𝐞 𝐒𝐨𝐧𝐠𝐬 🎶
""",
    reply_markup=buttons,
)
                except:
                    pass
                return await client.leave_call(chat_id, close=False)
            except Exception:
                return
        queued = check[0]["file"]
        language = await get_lang(chat_id)
        _ = get_string(language)
        title = (check[0]["title"]).title()
        user = check[0]["by"]
        original_chat_id = check[0]["chat_id"]
        streamtype = check[0]["streamtype"]
        videoid = check[0]["vidid"]
        db[chat_id][0]["played"] = 0
        exis = (check[0]).get("old_dur")
        if exis:
            db[chat_id][0]["dur"] = exis
            db[chat_id][0]["seconds"] = check[0]["old_second"]
            db[chat_id][0]["speed_path"] = None
            db[chat_id][0]["speed"] = 1.0
        video = True if str(streamtype) == "video" else False
        if "live_" in queued:
            n, link = await YouTube.video(videoid, True)
            if n == 0:
                return await app.send_message(
                    original_chat_id,
                    text=_["call_6"],
                )
            stream = self._build_stream(link, video=video)
            try:
                await self._play_on_assistant(client, chat_id, stream)
            except Exception:
                return await app.send_message(
                    original_chat_id,
                    text=_["call_6"],
                )
            img = await get_thumb(videoid)
            button = stream_markup(_, chat_id)
            play_caption = _["stream_1"].format(
                f"https://t.me/{app.username}?start=info_{videoid}",
                title[:23],
                check[0]["dur"],
                user,
            )
            from SONALI_MUSIC.utils.database_clone import get_custom_play_metadata
            img, play_caption = await get_custom_play_metadata(
                app.id, title, check[0]["dur"], user, videoid, img, play_caption
            )
            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=img,
                has_spoiler=True,
                caption=play_caption,
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
        elif "vid_" in queued:
            mystic = await app.send_message(original_chat_id, _["call_7"])
            try:
                file_path, direct = await YouTube.download(
                    videoid,
                    mystic,
                    videoid=True,
                    video=video,
                )
            except Exception:
                return await mystic.edit_text(
                    _["call_6"], disable_web_page_preview=True
                )
            stream = self._build_stream(file_path, video=video)
            try:
                await self._play_on_assistant(client, chat_id, stream)
            except Exception:
                return await app.send_message(
                    original_chat_id,
                    text=_["call_6"],
                )
            img = await get_thumb(videoid)
            button = stream_markup(_, chat_id)
            await mystic.delete()
            play_caption = _["stream_1"].format(
                f"https://t.me/{app.username}?start=info_{videoid}",
                title[:23],
                check[0]["dur"],
                user,
            )
            from SONALI_MUSIC.utils.database_clone import get_custom_play_metadata
            img, play_caption = await get_custom_play_metadata(
                app.id, title, check[0]["dur"], user, videoid, img, play_caption
            )
            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=img,
                has_spoiler=True,
                caption=play_caption,
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"

        elif "index_" in queued:
            stream = self._build_stream(videoid, video=video)
            try:
                await self._play_on_assistant(client, chat_id, stream)
            except Exception:
                return await app.send_message(
                    original_chat_id,
                    text=_["call_6"],
                )
            button = stream_markup(_, chat_id)
            play_img = config.STREAM_IMG_URL
            play_caption = _["stream_2"].format(user)
            from SONALI_MUSIC.utils.database_clone import get_custom_play_metadata
            play_img, play_caption = await get_custom_play_metadata(
                app.id, title, check[0]["dur"], user, "", play_img, play_caption
            )
            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=play_img,
                has_spoiler=True,
                caption=play_caption,
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
        else:
            stream = self._build_stream(queued, video=video)
            try:
                await self._play_on_assistant(client, chat_id, stream)
            except Exception:
                return await app.send_message(
                    original_chat_id,
                    text=_["call_6"],
                )
            if videoid == "telegram":
                button = stream_markup(_, chat_id)
                play_img = config.TELEGRAM_AUDIO_URL if str(streamtype) == "audio" else config.TELEGRAM_VIDEO_URL
                play_caption = _["stream_1"].format(config.SUPPORT_CHAT, title[:23], check[0]["dur"], user)
                from SONALI_MUSIC.utils.database_clone import get_custom_play_metadata
                play_img, play_caption = await get_custom_play_metadata(
                    app.id, title, check[0]["dur"], user, "", play_img, play_caption
                )
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=play_img,
                    caption=play_caption,
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            elif videoid == "soundcloud":
                button = stream_markup(_, chat_id)
                play_img = config.SOUNCLOUD_IMG_URL
                play_caption = _["stream_1"].format(config.SUPPORT_CHAT, title[:23], check[0]["dur"], user)
                from SONALI_MUSIC.utils.database_clone import get_custom_play_metadata
                play_img, play_caption = await get_custom_play_metadata(
                    app.id, title, check[0]["dur"], user, "", play_img, play_caption
                )
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=play_img,
                    caption=play_caption,
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            else:
                img = await get_thumb(videoid)
                button = stream_markup(_, chat_id)
                play_caption = _["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    title[:23],
                    check[0]["dur"],
                    user,
                )
                from SONALI_MUSIC.utils.database_clone import get_custom_play_metadata
                img, play_caption = await get_custom_play_metadata(
                    app.id, title, check[0]["dur"], user, videoid, img, play_caption
                )
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    has_spoiler=True,
                    caption=play_caption,
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

    
    async def ping(self):
        pings = []
        if config.STRING1:
            pings.append(self.one.ping)
        if config.STRING2:
            pings.append(self.two.ping)
        if config.STRING3:
            pings.append(self.three.ping)
        if config.STRING4:
            pings.append(self.four.ping)
        if config.STRING5:
            pings.append(self.five.ping)
        return str(round(sum(pings) / len(pings), 3)) if pings else "0"

    
    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Client...\n")
        if config.STRING1:
            await self.one.start()
        if config.STRING2:
            await self.two.start()
        if config.STRING3:
            await self.three.start()
        if config.STRING4:
            await self.four.start()
        if config.STRING5:
            await self.five.start()

    
    async def decorators(self):
        for string, client in [
            (config.STRING1, self.one),
            (config.STRING2, self.two),
            (config.STRING3, self.three),
            (config.STRING4, self.four),
            (config.STRING5, self.five),
        ]:
            if not string:
                continue

            @client.on_update()
            async def _update_handler(_, update: types.Update, _client=client):
                if isinstance(update, types.StreamEnded):
                    if update.stream_type == types.StreamEnded.Type.AUDIO:
                        await self.change_stream(_client, update.chat_id)
                elif isinstance(update, types.ChatUpdate):
                    if update.status in [
                        types.ChatUpdate.Status.KICKED,
                        types.ChatUpdate.Status.LEFT_GROUP,
                        types.ChatUpdate.Status.CLOSED_VOICE_CHAT,
                    ]:
                        await self.stop_stream(update.chat_id)


Sona = Call()
