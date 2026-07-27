<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">
<p align="center">
𝐁 𝐀 𝐃 𝐍 𝐀 𝐌 
<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">
<p align="center">
𝗧𝗘𝗔𝗠 𝗞𝗥𝗜𝗧𝗜 𝗕𝗢𝗧𝗦
<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">

    ─「 ᴅᴇᴩʟᴏʏ ᴏɴ ʜᴇʀᴏᴋᴜ 」─
</h3>
<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">
<p align="center"><a href="https://dashboard.heroku.com/new?template=https://github.com/Badnam465/Yadav"> <img src="https://img.shields.io/badge/Deploy%20On%20Heroku-00FFFF?style=for-the-badge&logo=heroku" width="220" height="38.45"/></a></p>
<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">

---

# 🤖 Bot Cloning Feature & Commands

This bot supports a powerful **multi-tenant bot cloning feature** allowing any user to easily clone and run their own independent instance of the music player bot. Below are all the commands related to the clone feature.

---

### 👤 User Clone Commands (Available in Private Chat)

These commands are used by general users to create and manage their own cloned bots:

*   **/clone `[BOT_TOKEN]`**
    *   **Description:** Spin up a new cloned bot using your own custom Telegram bot token.
    *   **How to get token:** Go to [@BotFather](https://t.me/BotFather), create a new bot, copy the token, and send `/clone YOUR_BOT_TOKEN`.
    *   *Note:* Free users can clone up to **1 bot** by default without requiring a premium subscription. Premium plans unlock higher limits!

*   **/manage_clone** or **/clone_panel**
    *   **Description:** Open the interactive configuration panel for your cloned bots.
    *   **Features available in the panel:**
        *   **Change Branding:** Set a custom title.
        *   **Change Welcome:** Customize the welcome text for your cloned bot.
        *   **Play Preference:** Toggle between *Direct* and *Everyone* playback settings.
        *   **Queue Behavior:** Toggle between *Standard* and *Autoplay* queues.
        *   **Delete Clone:** Safely stop and delete your cloned bot instance.

---

### 👑 Owner & Sudo Commands (Admin Control)

These administrative commands are available only to the central bot Owner/Sudoers:

*   **/addpremium `[USER_ID] [DURATION_DAYS]`** (or `/add_premium`)
    *   **Description:** Grant premium privileges to a user.
    *   **Effect:** Unlocks higher clone limits and advanced permissions (such as custom assistants).

*   **/removepremium `[USER_ID]`** (or `/remove_premium`)
    *   **Description:** Downgrade a user's subscription back to the free plan.

*   **/clones_list** (or `/clones`)
    *   **Description:** View the master list of all cloned bots currently registered in the database along with their online status.

*   **/broadcast_clones `[MESSAGE_TEXT]`** (or `/clone_broadcast`)
    *   **Description:** Send a global broadcast notification message to the owners (tenants) of all active cloned bots in the database.
