import random
from typing import Dict, List, Union

from SONALI_MUSIC import userbot
from SONALI_MUSIC.core.mongo import mongodb

authdb = mongodb.adminauth
authuserdb = mongodb.authuser
autoenddb = mongodb.autoend
assdb = mongodb.assistants
blacklist_chatdb = mongodb.blacklistChat
blockeddb = mongodb.blockedusers
chatsdb = mongodb.chats
channeldb = mongodb.cplaymode
countdb = mongodb.upcount
gbansdb = mongodb.gban
langdb = mongodb.language
onoffdb = mongodb.onoffper
playmodedb = mongodb.playmode
playtypedb = mongodb.playtypedb
skipdb = mongodb.skipmode
sudoersdb = mongodb.sudoers
usersdb = mongodb.tgusersdb

# Shifting to memory [mongo sucks often]
active = []
activevideo = []
assistantdict = {}
autoend = {}
count = {}
channelconnect = {}
langm = {}
loop = {}
maintenance = []
nonadmin = {}
pause = {}
playmode = {}
playtype = {}
skipmode = {}


def get_active_bot_id() -> int:
    from SONALI_MUSIC.core.clone_manager import current_clone_client
    from SONALI_MUSIC import app
    clone = current_clone_client.get()
    if clone is not None:
        return clone.me.id if (clone.me and hasattr(clone.me, "id")) else 0
    if hasattr(app, "_orig_id"):
        return app._orig_id
    return app.id if (hasattr(app, "me") and app.me) else 0


async def get_log_group_id() -> int:
    from SONALI_MUSIC.core.clone_manager import current_clone_client
    from SONALI_MUSIC.utils.database_clone import get_clone_by_id
    import config

    clone = current_clone_client.get()
    if clone is not None:
        bot_id = clone.me.id
        clone_db = await get_clone_by_id(bot_id)
        if clone_db:
            log_group_id = clone_db.get("log_group_id")
            if log_group_id is not None:
                try:
                    return int(log_group_id)
                except ValueError:
                    pass
    return config.LOGGER_ID


async def get_dynamic_assistant(chat_id: int, bot_id: int) -> int:
    from SONALI_MUSIC.core.userbot import assistants
    if not assistants:
        return 1

    # Check memory first
    assis = assistantdict.get((bot_id, chat_id))
    if assis in assistants:
        return assis

    # Check DB
    dbassistant = await assdb.find_one({"bot_id": bot_id, "chat_id": chat_id})
    if not dbassistant:
        # Fallback to old schema (without bot_id)
        dbassistant = await assdb.find_one({"chat_id": chat_id, "bot_id": {"$exists": False}})

    if dbassistant:
        got_assis = dbassistant.get("assistant")
        if got_assis in assistants:
            # Verify if this assistant is already in use in this chat by another bot
            used_in_chat = {val for (b_id, c_id), val in assistantdict.items() if c_id == chat_id and b_id != bot_id}
            if got_assis not in used_in_chat:
                assistantdict[(bot_id, chat_id)] = got_assis
                return got_assis

    # Assign dynamically with load balancing and collision-avoidance
    used_in_chat = {val for (b_id, c_id), val in assistantdict.items() if c_id == chat_id}
    busy_assistants = {val for (b_id, c_id), val in assistantdict.items() if c_id in active}

    candidates = [a for a in assistants if a not in used_in_chat]
    if not candidates:
        candidates = assistants

    non_busy_candidates = [a for a in candidates if a not in busy_assistants]
    if non_busy_candidates:
        selected = random.choice(non_busy_candidates)
    else:
        selected = random.choice(candidates)

    assistantdict[(bot_id, chat_id)] = selected
    await assdb.update_one(
        {"bot_id": bot_id, "chat_id": chat_id},
        {"$set": {"assistant": selected}},
        upsert=True,
    )
    return selected


async def get_assistant_number(chat_id: int) -> str:
    bot_id = get_active_bot_id()
    assistant = assistantdict.get((bot_id, chat_id))
    return assistant


async def get_client(assistant: int):
    if int(assistant) == 1:
        return userbot.one
    elif int(assistant) == 2:
        return userbot.two
    elif int(assistant) == 3:
        return userbot.three
    elif int(assistant) == 4:
        return userbot.four
    elif int(assistant) == 5:
        return userbot.five


async def set_assistant_new(chat_id, number):
    number = int(number)
    bot_id = get_active_bot_id()
    assistantdict[(bot_id, chat_id)] = number
    await assdb.update_one(
        {"bot_id": bot_id, "chat_id": chat_id},
        {"$set": {"assistant": number}},
        upsert=True,
    )


async def set_assistant(chat_id):
    bot_id = get_active_bot_id()
    ran_assistant = await get_dynamic_assistant(chat_id, bot_id)
    userbot = await get_client(ran_assistant)
    return userbot


async def get_assistant(chat_id: int) -> str:
    from SONALI_MUSIC.core.clone_manager import current_clone_client
    from SONALI_MUSIC.utils.database_clone import get_clone_by_id
    from SONALI_MUSIC.core.call import Sona
    from SONALI_MUSIC.utils.exceptions import AssistantErr

    clone = current_clone_client.get()
    if clone is not None:
        bot_id = clone.me.id
        clone_db = await get_clone_by_id(bot_id)
        if clone_db:
            custom_session = clone_db.get('custom_session')
            if custom_session:
                if hasattr(Sona, 'custom_assistants') and bot_id in Sona.custom_assistants:
                    return Sona.custom_assistants[bot_id]['userbot']
                else:
                    started = await Sona.start_custom_assistant(bot_id, custom_session)
                    if started:
                        return Sona.custom_assistants[bot_id]['userbot']
                    else:
                        raise AssistantErr("❖ <b>ᴄᴜsᴛᴏᴍ ᴀssɪsᴛᴀɴᴛ ᴇʀʀᴏʀ</b>\n\nʏᴏᴜʀ ᴄᴜsᴛᴏᴍ ᴀssɪsᴛᴀɴᴛ sᴇssɪᴏɴ sᴛʀɪɴɢ ɪs ɪɴᴠᴀʟɪᴅ ᴏʀ ᴄᴏᴜʟᴅ ɴᴏᴛ ʙᴇ sᴛᴀʀᴛᴇᴅ. ᴘʟᴇᴀsᴇ ᴜᴘᴅᴀᴛᴇ ɪᴛ ᴠɪᴀ `/manage_clone`.")

            # If no custom session is set at all
            assis = await get_dynamic_assistant(chat_id, bot_id)
            return await get_client(assis)

    bot_id = get_active_bot_id()
    assis = await get_dynamic_assistant(chat_id, bot_id)
    return await get_client(assis)


async def set_calls_assistant(chat_id):
    bot_id = get_active_bot_id()
    ran_assistant = await get_dynamic_assistant(chat_id, bot_id)
    return ran_assistant


async def group_assistant(self, chat_id: int) -> int:
    from SONALI_MUSIC.core.clone_manager import current_clone_client
    from SONALI_MUSIC.utils.database_clone import get_clone_by_id
    from SONALI_MUSIC.utils.exceptions import AssistantErr

    clone = current_clone_client.get()
    if clone is not None:
        bot_id = clone.me.id
        clone_db = await get_clone_by_id(bot_id)
        if clone_db:
            custom_session = clone_db.get('custom_session')
            if custom_session:
                if hasattr(self, 'custom_assistants') and bot_id in self.custom_assistants:
                    return self.custom_assistants[bot_id]['pytgcalls']
                else:
                    started = await self.start_custom_assistant(bot_id, custom_session)
                    if started:
                        return self.custom_assistants[bot_id]['pytgcalls']
                    else:
                        raise AssistantErr("❖ <b>ᴄᴜsᴛᴏᴍ ᴀssɪsᴛᴀɴᴛ ᴇʀʀᴏʀ</b>\n\nʏᴏᴜʀ ᴄᴜsᴛᴏᴍ ᴀssɪsᴛᴀɴᴛ sᴇssɪᴏɴ sᴛʀɪɴɢ ɪs ɪɴᴠᴀʟɪᴅ ᴏʀ ᴄᴏᴜʟᴅ ɴᴏᴛ ʙᴇ sᴛᴀʀᴛᴇᴅ. ᴘʟᴇᴀsᴇ ᴜᴘᴅᴀᴛᴇ ɪᴛ ᴠɪᴀ `/manage_clone`.")

            # If no custom session is set at all
            assis = await get_dynamic_assistant(chat_id, bot_id)
            if int(assis) == 1:
                return self.one
            elif int(assis) == 2:
                return self.two
            elif int(assis) == 3:
                return self.three
            elif int(assis) == 4:
                return self.four
            elif int(assis) == 5:
                return self.five

    bot_id = get_active_bot_id()
    assis = await get_dynamic_assistant(chat_id, bot_id)
    if int(assis) == 1:
        return self.one
    elif int(assis) == 2:
        return self.two
    elif int(assis) == 3:
        return self.three
    elif int(assis) == 4:
        return self.four
    elif int(assis) == 5:
        return self.five

async def is_skipmode(chat_id: int) -> bool:
    mode = skipmode.get(chat_id)
    if not mode:
        user = await skipdb.find_one({"chat_id": chat_id})
        if not user:
            skipmode[chat_id] = True
            return True
        skipmode[chat_id] = False
        return False
    return mode


async def skip_on(chat_id: int):
    skipmode[chat_id] = True
    user = await skipdb.find_one({"chat_id": chat_id})
    if user:
        return await skipdb.delete_one({"chat_id": chat_id})


async def skip_off(chat_id: int):
    skipmode[chat_id] = False
    user = await skipdb.find_one({"chat_id": chat_id})
    if not user:
        return await skipdb.insert_one({"chat_id": chat_id})


async def get_upvote_count(chat_id: int) -> int:
    mode = count.get(chat_id)
    if not mode:
        mode = await countdb.find_one({"chat_id": chat_id})
        if not mode:
            return 5
        count[chat_id] = mode["mode"]
        return mode["mode"]
    return mode


async def set_upvotes(chat_id: int, mode: int):
    count[chat_id] = mode
    await countdb.update_one(
        {"chat_id": chat_id}, {"$set": {"mode": mode}}, upsert=True
    )


async def is_autoend() -> bool:
    chat_id = 1234
    user = await autoenddb.find_one({"chat_id": chat_id})
    if not user:
        return False
    return True


async def autoend_on():
    chat_id = 1234
    await autoenddb.insert_one({"chat_id": chat_id})


async def autoend_off():
    chat_id = 1234
    await autoenddb.delete_one({"chat_id": chat_id})


async def get_loop(chat_id: int) -> int:
    lop = loop.get(chat_id)
    if not lop:
        return 0
    return lop


async def set_loop(chat_id: int, mode: int):
    loop[chat_id] = mode


async def get_cmode(chat_id: int) -> int:
    mode = channelconnect.get(chat_id)
    if not mode:
        mode = await channeldb.find_one({"chat_id": chat_id})
        if not mode:
            return None
        channelconnect[chat_id] = mode["mode"]
        return mode["mode"]
    return mode


async def set_cmode(chat_id: int, mode: int):
    channelconnect[chat_id] = mode
    await channeldb.update_one(
        {"chat_id": chat_id}, {"$set": {"mode": mode}}, upsert=True
    )


async def get_playtype(chat_id: int) -> str:
    mode = playtype.get(chat_id)
    if not mode:
        mode = await playtypedb.find_one({"chat_id": chat_id})
        if not mode:
            playtype[chat_id] = "Everyone"
            return "Everyone"
        playtype[chat_id] = mode["mode"]
        return mode["mode"]
    return mode


async def set_playtype(chat_id: int, mode: str):
    playtype[chat_id] = mode
    await playtypedb.update_one(
        {"chat_id": chat_id}, {"$set": {"mode": mode}}, upsert=True
    )


async def get_playmode(chat_id: int) -> str:
    mode = playmode.get(chat_id)
    if not mode:
        mode = await playmodedb.find_one({"chat_id": chat_id})
        if not mode:
            playmode[chat_id] = "Direct"
            return "Direct"
        playmode[chat_id] = mode["mode"]
        return mode["mode"]
    return mode


async def set_playmode(chat_id: int, mode: str):
    playmode[chat_id] = mode
    await playmodedb.update_one(
        {"chat_id": chat_id}, {"$set": {"mode": mode}}, upsert=True
    )


async def get_lang(chat_id: int) -> str:
    mode = langm.get(chat_id)
    if not mode:
        lang = await langdb.find_one({"chat_id": chat_id})
        if not lang:
            langm[chat_id] = "en"
            return "en"
        langm[chat_id] = lang["lang"]
        return lang["lang"]
    return mode


async def set_lang(chat_id: int, lang: str):
    langm[chat_id] = lang
    await langdb.update_one({"chat_id": chat_id}, {"$set": {"lang": lang}}, upsert=True)


async def is_music_playing(chat_id: int) -> bool:
    mode = pause.get(chat_id)
    if not mode:
        return False
    return mode


async def music_on(chat_id: int):
    pause[chat_id] = True


async def music_off(chat_id: int):
    pause[chat_id] = False


async def get_active_chats() -> list:
    return active


async def is_active_chat(chat_id: int) -> bool:
    if chat_id not in active:
        return False
    else:
        return True


async def add_active_chat(chat_id: int):
    if chat_id not in active:
        active.append(chat_id)


async def remove_active_chat(chat_id: int):
    if chat_id in active:
        active.remove(chat_id)


async def get_active_video_chats() -> list:
    return activevideo


async def is_active_video_chat(chat_id: int) -> bool:
    if chat_id not in activevideo:
        return False
    else:
        return True


async def add_active_video_chat(chat_id: int):
    if chat_id not in activevideo:
        activevideo.append(chat_id)


async def remove_active_video_chat(chat_id: int):
    if chat_id in activevideo:
        activevideo.remove(chat_id)


async def check_nonadmin_chat(chat_id: int) -> bool:
    user = await authdb.find_one({"chat_id": chat_id})
    if not user:
        return False
    return True


async def is_nonadmin_chat(chat_id: int) -> bool:
    mode = nonadmin.get(chat_id)
    if not mode:
        user = await authdb.find_one({"chat_id": chat_id})
        if not user:
            nonadmin[chat_id] = False
            return False
        nonadmin[chat_id] = True
        return True
    return mode


async def add_nonadmin_chat(chat_id: int):
    nonadmin[chat_id] = True
    is_admin = await check_nonadmin_chat(chat_id)
    if is_admin:
        return
    return await authdb.insert_one({"chat_id": chat_id})


async def remove_nonadmin_chat(chat_id: int):
    nonadmin[chat_id] = False
    is_admin = await check_nonadmin_chat(chat_id)
    if not is_admin:
        return
    return await authdb.delete_one({"chat_id": chat_id})


async def is_on_off(on_off: int) -> bool:
    onoff = await onoffdb.find_one({"on_off": on_off})
    if not onoff:
        return False
    return True


async def add_on(on_off: int):
    is_on = await is_on_off(on_off)
    if is_on:
        return
    return await onoffdb.insert_one({"on_off": on_off})


async def add_off(on_off: int):
    is_off = await is_on_off(on_off)
    if not is_off:
        return
    return await onoffdb.delete_one({"on_off": on_off})


async def is_maintenance():
    if not maintenance:
        get = await onoffdb.find_one({"on_off": 1})
        if not get:
            maintenance.clear()
            maintenance.append(2)
            return True
        else:
            maintenance.clear()
            maintenance.append(1)
            return False
    else:
        if 1 in maintenance:
            return False
        else:
            return True


async def maintenance_off():
    maintenance.clear()
    maintenance.append(2)
    is_off = await is_on_off(1)
    if not is_off:
        return
    return await onoffdb.delete_one({"on_off": 1})


async def maintenance_on():
    maintenance.clear()
    maintenance.append(1)
    is_on = await is_on_off(1)
    if is_on:
        return
    return await onoffdb.insert_one({"on_off": 1})


async def is_served_user(user_id: int) -> bool:
    user = await usersdb.find_one({"user_id": user_id})
    if not user:
        return False
    return True


async def get_served_users() -> list:
    users_list = []
    async for user in usersdb.find({"user_id": {"$gt": 0}}):
        users_list.append(user)
    return users_list


async def add_served_user(user_id: int):
    try:
        from SONALI_MUSIC import app
        from SONALI_MUSIC.utils.database_clone import add_cloned_served_user
        # app.id automatically resolves to active clone bot id or main bot id
        await add_cloned_served_user(app.id, user_id)
    except Exception:
        pass

    is_served = await is_served_user(user_id)
    if is_served:
        return
    return await usersdb.insert_one({"user_id": user_id})


async def get_served_chats() -> list:
    chats_list = []
    async for chat in chatsdb.find({"chat_id": {"$lt": 0}}):
        chats_list.append(chat)
    return chats_list


async def is_served_chat(chat_id: int) -> bool:
    chat = await chatsdb.find_one({"chat_id": chat_id})
    if not chat:
        return False
    return True


async def add_served_chat(chat_id: int):
    try:
        from SONALI_MUSIC import app
        from SONALI_MUSIC.utils.database_clone import add_cloned_served_chat
        # app.id automatically resolves to active clone bot id or main bot id
        await add_cloned_served_chat(app.id, chat_id)
    except Exception:
        pass

    is_served = await is_served_chat(chat_id)
    if is_served:
        return
    return await chatsdb.insert_one({"chat_id": chat_id})


async def blacklisted_chats() -> list:
    chats_list = []
    async for chat in blacklist_chatdb.find({"chat_id": {"$lt": 0}}):
        chats_list.append(chat["chat_id"])
    return chats_list


async def blacklist_chat(chat_id: int) -> bool:
    if not await blacklist_chatdb.find_one({"chat_id": chat_id}):
        await blacklist_chatdb.insert_one({"chat_id": chat_id})
        return True
    return False


async def whitelist_chat(chat_id: int) -> bool:
    if await blacklist_chatdb.find_one({"chat_id": chat_id}):
        await blacklist_chatdb.delete_one({"chat_id": chat_id})
        return True
    return False


async def _get_authusers(chat_id: int) -> Dict[str, int]:
    _notes = await authuserdb.find_one({"chat_id": chat_id})
    if not _notes:
        return {}
    return _notes["notes"]


async def get_authuser_names(chat_id: int) -> List[str]:
    _notes = []
    for note in await _get_authusers(chat_id):
        _notes.append(note)
    return _notes


async def get_authuser(chat_id: int, name: str) -> Union[bool, dict]:
    name = name
    _notes = await _get_authusers(chat_id)
    if name in _notes:
        return _notes[name]
    else:
        return False


async def save_authuser(chat_id: int, name: str, note: dict):
    name = name
    _notes = await _get_authusers(chat_id)
    _notes[name] = note

    await authuserdb.update_one(
        {"chat_id": chat_id}, {"$set": {"notes": _notes}}, upsert=True
    )


async def delete_authuser(chat_id: int, name: str) -> bool:
    notesd = await _get_authusers(chat_id)
    name = name
    if name in notesd:
        del notesd[name]
        await authuserdb.update_one(
            {"chat_id": chat_id},
            {"$set": {"notes": notesd}},
            upsert=True,
        )
        return True
    return False


async def get_gbanned() -> list:
    results = []
    async for user in gbansdb.find({"user_id": {"$gt": 0}}):
        user_id = user["user_id"]
        results.append(user_id)
    return results


async def is_gbanned_user(user_id: int) -> bool:
    user = await gbansdb.find_one({"user_id": user_id})
    if not user:
        return False
    return True


async def add_gban_user(user_id: int):
    is_gbanned = await is_gbanned_user(user_id)
    if is_gbanned:
        return
    return await gbansdb.insert_one({"user_id": user_id})


async def remove_gban_user(user_id: int):
    is_gbanned = await is_gbanned_user(user_id)
    if not is_gbanned:
        return
    return await gbansdb.delete_one({"user_id": user_id})


async def get_sudoers() -> list:
    sudoers = await sudoersdb.find_one({"sudo": "sudo"})
    if not sudoers:
        return []
    return sudoers["sudoers"]


async def add_sudo(user_id: int) -> bool:
    sudoers = await get_sudoers()
    sudoers.append(user_id)
    await sudoersdb.update_one(
        {"sudo": "sudo"}, {"$set": {"sudoers": sudoers}}, upsert=True
    )
    return True


async def remove_sudo(user_id: int) -> bool:
    sudoers = await get_sudoers()
    sudoers.remove(user_id)
    await sudoersdb.update_one(
        {"sudo": "sudo"}, {"$set": {"sudoers": sudoers}}, upsert=True
    )
    return True


async def get_banned_users() -> list:
    results = []
    async for user in blockeddb.find({"user_id": {"$gt": 0}}):
        user_id = user["user_id"]
        results.append(user_id)
    return results


async def get_banned_count() -> int:
    users = blockeddb.find({"user_id": {"$gt": 0}})
    users = await users.to_list(length=100000)
    return len(users)


async def is_banned_user(user_id: int) -> bool:
    user = await blockeddb.find_one({"user_id": user_id})
    if not user:
        return False
    return True


async def add_banned_user(user_id: int):
    is_gbanned = await is_banned_user(user_id)
    if is_gbanned:
        return
    return await blockeddb.insert_one({"user_id": user_id})


async def remove_banned_user(user_id: int):
    is_gbanned = await is_banned_user(user_id)
    if not is_gbanned:
        return
    return await blockeddb.delete_one({"user_id": user_id})
