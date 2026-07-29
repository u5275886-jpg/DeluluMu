import socket
import time

import heroku3
from pyrogram import filters

import config
from SONALI_MUSIC.core.mongo import mongodb

from .logging import LOGGER

from pyrogram.filters import Filter

class DynamicSudoersFilter(Filter):
    def __init__(self):
        super().__init__()
        self.users = set()

    def add(self, user_id):
        self.users.add(user_id)

    def remove(self, user_id):
        if user_id in self.users:
            self.users.remove(user_id)

    def copy(self):
        return self.users.copy()

    def __iter__(self):
        return iter(self.users)

    def __len__(self):
        return len(self.users)

    def __contains__(self, user_id):
        return user_id in self.users

    async def __call__(self, _, update):
        user = update.from_user if hasattr(update, "from_user") else None
        user_id = user.id if user else None
        if not user_id:
            return False

        # Check if we are running in a cloned bot context
        try:
            from SONALI_MUSIC.core.clone_manager import current_clone_client
            clone = current_clone_client.get()
            if clone is not None:
                bot_id = clone.me.id
                from SONALI_MUSIC.utils.database_clone import get_clone_by_id
                clone_db = await get_clone_by_id(bot_id)
                if clone_db:
                    tenant_id = clone_db.get("tenant_id")
                    if user_id == tenant_id:
                        return True
        except Exception:
            pass

        # Check main bot owner
        import config
        if user_id == config.OWNER_ID:
            return True

        # Check supreme admins
        try:
            from SONALI_MUSIC.utils.database_clone import is_supreme_admin
            if await is_supreme_admin(user_id):
                return True
        except Exception:
            pass

        # Main bot sudoers
        if user_id in self.users:
            return True

        return False

SUDOERS = DynamicSudoersFilter()

HAPP = None
_boot_ = time.time()


def is_heroku():
    return "heroku" in socket.getfqdn()


XCB = [
    "/",
    "@",
    ".",
    "com",
    ":",
    "git",
    "heroku",
    "push",
    str(config.HEROKU_API_KEY),
    "https",
    str(config.HEROKU_APP_NAME),
    "HEAD",
    "master",
]


def dbb():
    global db
    db = {}
    LOGGER(__name__).info(f"𝗗𝗔𝗧𝗔𝗕𝗔𝗦𝗘 𝗟𝗢𝗔𝗗𝗘𝗗 𝗕𝗢𝗦𝗦")


async def sudo():
    global SUDOERS
    SUDOERS.add(config.OWNER_ID)
    sudoersdb = mongodb.sudoers
    sudoers = await sudoersdb.find_one({"sudo": "sudo"})
    sudoers = [] if not sudoers else sudoers["sudoers"]
    if config.OWNER_ID not in sudoers:
        sudoers.append(config.OWNER_ID)
        await sudoersdb.update_one(
            {"sudo": "sudo"},
            {"$set": {"sudoers": sudoers}},
            upsert=True,
        )
    if sudoers:
        for user_id in sudoers:
            SUDOERS.add(user_id)
    LOGGER(__name__).info(f"𝗦𝗨𝗗𝗢 𝗨𝗦𝗘𝗥 𝗗𝗢𝗡𝗘 𝗕𝗢𝗦𝗦")


def heroku():
    global HAPP
    if is_heroku():
        if config.HEROKU_API_KEY and config.HEROKU_APP_NAME:
            try:
                Heroku = heroku3.from_key(config.HEROKU_API_KEY)
                HAPP = Heroku.app(config.HEROKU_APP_NAME)
                LOGGER(__name__).info(f"𝗛𝗘𝗥𝗢𝗞𝗨 𝗔𝗣𝗣 𝗡𝗔𝗠𝗘 𝗟𝗢𝗔𝗗𝗘𝗗 || 𝗗𝗢𝗡𝗘")
            except BaseException:
                LOGGER(__name__).warning(
                    f"𝗬𝗢𝗨 𝗛𝗔𝗩𝗘 𝗡𝗢𝗧 𝗙𝗜𝗟𝗟𝗘𝗗 𝗛𝗘𝗥𝗢𝗞𝗨 𝗔𝗣𝗜 𝗞𝗘𝗬 𝗔𝗡𝗗 𝗛𝗘𝗥𝗢𝗞𝗨 𝗔𝗣𝗣 𝗡𝗔𝗠𝗘 𝗖𝗢𝗥𝗥𝗘𝗖𝗧"
)
