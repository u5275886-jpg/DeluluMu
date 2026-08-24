import logging
from functools import wraps
from traceback import format_exc as err

from pyrogram.errors.exceptions.forbidden_403 import ChatWriteForbidden
from pyrogram.types import Message

from SONALI_MUSIC import app
from SONALI_MUSIC.misc import SUDOERS


async def member_permissions(chat_id: int, user_id: int):
    perms = []
    member = (await app.get_chat_member(chat_id, user_id)).privileges
    if not member:
        return []
    if member.can_post_messages:
        perms.append("can_post_messages")
    if member.can_edit_messages:
        perms.append("can_edit_messages")
    if member.can_delete_messages:
        perms.append("can_delete_messages")
    if member.can_restrict_members:
        perms.append("can_restrict_members")
    if member.can_promote_members:
        perms.append("can_promote_members")
    if member.can_change_info:
        perms.append("can_change_info")
    if member.can_invite_users:
        perms.append("can_invite_users")
    if member.can_pin_messages:
        perms.append("can_pin_messages")
    if member.can_manage_video_chats:
        perms.append("can_manage_video_chats")
    return perms


async def authorised(func, subFunc2, client, message, *args, **kwargs):
    chatID = message.chat.id
    try:
        await func(client, message, *args, **kwargs)
    except ChatWriteForbidden:
        await app.leave_chat(chatID)
    except Exception as e:
        logging.exception(e)
        try:
            await message.reply_text(str(e.MESSAGE))
        except AttributeError:
            await message.reply_text(str(e))
        e = err()
        print(str(e))
    return subFunc2


async def unauthorised(
    message: Message, permission, subFunc2, bot_lacking_permission=False
):
    chatID = message.chat.id
    if bot_lacking_permission:
        text = (
            "I don't have the required permission to perform this action."
            + f"\n**Permission:** __{permission}__"
        )
    else:
        text = (
            "You don't have the required permission to perform this action."
            + f"\n**Permission:** __{permission}__"
        )
    try:
        await message.reply_text(text)
    except ChatWriteForbidden:
        await app.leave_chat(chatID)
    return subFunc2


async def bot_permissions(chat_id: int):
    perms = []
    bot_id = (await app.get_me()).id
    return await member_permissions(chat_id, bot_id)


def adminsOnly(permission):
    def subFunc(func):
        @wraps(func)
        async def subFunc2(client, message: Message, *args, **kwargs):
            chatID = message.chat.id

            # Check if the bot has the required permission
            bot_perms = await bot_permissions(chatID)
            if permission not in bot_perms:
                return await unauthorised(
                    message, permission, subFunc2, bot_lacking_permission=True
                )

            if not message.from_user:
                # For anonymous admins
                if message.sender_chat and message.sender_chat.id == message.chat.id:
                    return await authorised(
                        func,
                        subFunc2,
                        client,
                        message,
                        *args,
                        **kwargs,
                    )
                return await unauthorised(message, permission, subFunc2)

            # For admins and sudo users
            userID = message.from_user.id
            permissions = await member_permissions(chatID, userID)
            if userID not in SUDOERS and permission not in permissions:
                return await unauthorised(message, permission, subFunc2)
            return await authorised(func, subFunc2, client, message, *args, **kwargs)

        return subFunc2

    return subFunc

# ==================== Centralized System Permission Helpers ==================== #

import config
from SONALI_MUSIC.utils.database_clone import get_supreme_admins, get_clone_by_id

async def is_owner(user_id: int) -> bool:
    return user_id == config.OWNER_ID

async def is_sudo(user_id: int) -> bool:
    if user_id == config.OWNER_ID:
        return True
    supremes = await get_supreme_admins()
    if user_id in supremes:
        return True
    return user_id in SUDOERS

async def is_admin(chat_id: int, user_id: int) -> bool:
    if await is_sudo(user_id):
        return True
    perms = await member_permissions(chat_id, user_id)
    return "can_manage_video_chats" in perms or len(perms) > 0

async def is_clone_owner(user_id: int, bot_id: int) -> bool:
    if user_id == config.OWNER_ID:
        return True
    supremes = await get_supreme_admins()
    if user_id in supremes:
        return True
    clone = await get_clone_by_id(bot_id)
    if clone:
        tenant_id = clone.get("tenant_id") or clone.get("owner_id")
        return tenant_id == user_id
    return False

async def can_broadcast(user_id: int, bot_id: Optional[int] = None) -> bool:
    if await is_sudo(user_id):
        return True
    if bot_id:
        return await is_clone_owner(user_id, bot_id)
    return False

async def can_delete_clone(user_id: int, bot_id: int) -> bool:
    return await is_clone_owner(user_id, bot_id)

async def can_view_clone_stats(user_id: int, bot_id: Optional[int] = None) -> bool:
    if await is_sudo(user_id):
        return True
    if bot_id:
        return await is_clone_owner(user_id, bot_id)
    return False
