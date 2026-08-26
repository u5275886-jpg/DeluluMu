# 🎵 Multitenant Telegram Music Bot Platform

A powerful, high-performance, multitenant Telegram Music Bot platform utilizing Pyrogram, local JSON / MongoDB Atlas, and Py-Tgcalls for seamless audio and video streaming. This project supports dynamic **bot cloning**, customization, 100% free clone management, and advanced administrative global broadcasting capabilities.

---

## 📢 Global Broadcast System (Owner Broadcast Guide)

### 🌟 High-Powered Multi-Tenant Broadcast (`/broadcast`)
When the **Platform Owner** or a **Supreme Admin** executes the `/broadcast` command, the bot automatically broadcasts the message to **ALL Group Chats AND ALL Private DM Chats** across the **Main Bot AND ALL Active Cloned Bots** simultaneously in a single execution!

#### 💡 How to Broadcast (Owner / Supreme Admin):
1. **Broadcast Text Message**:
   - `/broadcast <Your Message Text>`
   - Example: `/broadcast Hello everyone! New updates are live!`

2. **Broadcast Media / Reply Message (Photos, Videos, Audio, Documents, Stickers, Voice)**:
   - Reply to any message (photo, video, sticker, document, audio, etc.) with `/broadcast`.
   - The exact media, caption, and inline buttons will be copied and broadcasted to all groups and DMs across all bots!

3. **Pin Broadcasted Message in Groups**:
   - Append `-pin` or `-pinloud` to pin the message in all target group chats.
   - Example: `/broadcast -pin Check out this important announcement!`

#### 📊 Target Metrics & Delivery Report:
When `/broadcast` starts, it displays target metrics (total group chats + total private users across all bots). Upon completion, it delivers a detailed execution report showing:
- ✅ Successfully delivered group messages
- 📌 Pinned messages count
- 👤 Successfully delivered private DM messages
- ❌ Failed/blocked messages (Stale or blocked users/chats are automatically cleaned up from the database).

#### 🛠️ Additional Global Broadcast Helper Commands:
* `/broadcast_group_all [text]` - Broadcast text message to all groups across Main Bot + All Clone Bots.
* `/broadcast_private_all [text]` - Broadcast text message to all private DMs across Main Bot + All Clone Bots.
* `/broadcast_clones [text]` - Broadcast an administrative alert directly to all Clone Bot Owners in their personal chats.
* `/cbroadcast -user|-group|-all|-owner [text]` - Background job-queued global broadcast with stop controls (`/stopcbroadcast <JOB_ID>`).

---

## 🚀 Free Bot Cloning & 1-2 Step Link Setup

Users can clone their own music bots and customize them for **100% FREE** without requiring any premium subscription!

### 📋 Cloning Commands for Users:
* `/clone [BOT_TOKEN]` - Clone a new music bot using a token obtained from [@BotFather](https://t.me/BotFather).
* `/manage_clone` (or `/clone_panel`) - Open your cloned bot's control panel to configure settings.

### 🔗 1-2 Step Custom Link Setup (`Set Bot Links`):
Clone owners can configure their own **Update Channel** and **Support Group** links in **1 to 2 simple steps**:

1. Open `/manage_clone` -> Select your cloned bot.
2. Click **`🔗 sᴇᴛ ʙᴏᴛ ʟɪɴᴋs`** in the control panel.
3. Choose your preferred setup option:
   - **`📢 Set Update Channel`**: Send your channel link (e.g. `https://t.me/YourChannel` or `@YourChannel`).
   - **`💬 Set Support Group`**: Send your support group link (e.g. `https://t.me/YourGroup` or `@YourGroup`).
   - **`⚡ Quick 2-Step Setup`**: Step 1 asks for your Update Channel link, Step 2 asks for your Support Group link. Done in 2 quick messages!
   - **`🔄 Reset Links`**: Restores default main bot links anytime.

Once set, your cloned bot's `/start` panel buttons (`📢 ᴜᴘᴅᴧᴛᴇs` and `💬 sᴜᴘᴘᴏʀᴛ`) will immediately redirect users to **YOUR custom channel and support group**!

---

## 🛠️ Cloned Bot Customization Features (100% Free)

Using the `/manage_clone` panel, users can freely customize:
1. **Custom Links Setup**: Set Update Channel and Support Group links in 1-2 steps.
2. **Assistant Settings**: Rotate system assistants (1-5) or set a custom assistant via Pyrogram Session string.
3. **Branding Configuration**: Change branding title or preview banner image URL.
4. **Welcome Message**: Customize welcome text and banner image (supports `{user}` and `{mention}` placeholders).
5. **Play Messages**: Customize streaming status message caption template and thumbnail image URL.
6. **Playback & Queue Preference**: Toggle playback rights or queue behaviors.
7. **Log Group Setup**: Assign a custom Telegram group ID for clone event logs.

---

## 👑 Supreme Admin Panel & Management Commands

Reserved for the Platform Owner (`OWNER_ID`) and appointed **Supreme Admins**.

### 🔺 Supreme Admin Authorization (Owner Only)
* `/addsupreme [user_id / username / reply]` - Appoint a user as a Supreme Admin.
* `/removesupreme [user_id / username / reply]` - Revoke Supreme Admin privileges.
* `/supremes` (or `/supremelist`) - List all authorized Supreme Admins.

### 🤖 Cloned Bots Monitoring & Control
* `/clones_list` (or `/clones`) - Retrieve master list of all registered cloned bots with status and real-time playing song details.
* `/delete_clone [bot_id]` (or `/remove_clone [bot_id]`) - Forcibly stop and delete any cloned bot.
* `/clones_stats` - View resource utilization (CPU, RAM) and total active/paused clones.
* `/restart_clones` - Stop and restart all active clones in memory.
* `/setfs [channel_username/none]` - Set mandatory channel force subscription for cloning.

### 🛡️ Global Moderation & Bans
* `/clone_ban [user_id]` - Globally ban a user across all cloned bots and main bot.
* `/clone_unban [user_id]` - Globally unban a user.

---

## 💻 Tech Stack

* **Language:** Python 3.10+
* **Framework:** Pyrogram (kurigram fork), py-tgcalls
* **Database:** Local JSON Database (AsyncJsonClient) / MongoDB Atlas
* **Server Framework:** aiohttp (Administration REST API & WebSockets)
