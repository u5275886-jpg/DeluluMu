# 🎵 Multitenant Telegram Music Bot Platform

A powerful, high-performance, multitenant Telegram Music Bot platform utilizing Pyrogram, Motor (MongoDB), and Py-Tgcalls for seamless audio and video streaming. This project supports dynamic **bot cloning**, customization, and advanced administrative capabilities.

---

## 🚀 Cloning Commands for Users

Users can clone their own bots and customize them directly through Telegram!

*   `/clone [BOT_TOKEN]` - Clone the music bot using a token generated from [@BotFather](https://t.me/BotFather).
*   `/manage_clone` (or `/clone_panel`) - Open the settings control panel to configure your cloned bot.

### 🛠️ Cloned Bot Customization Features
Using the `/manage_clone` panel, users can customize:
1.  **Assistant Settings**: Rotate or set a custom assistant via Pyrogram Session string.
2.  **Branding Configuration**: Change branding title or branding preview banner image URL.
3.  **Welcome Message**: Customize welcome text and welcome banner image (supports placeholders like `{user}` and `{mention}`).
4.  **Play Messages**: Customize streaming status message caption template and image URL.
5.  **Playback & Queue Preference**: Toggle playback rights or queue behaviors.
6.  **Inline Buttons Customization**:
    *   **Add Button**: Add new custom inline buttons to the private panel.
    *   **Edit Button**: Modify any configured button's label, type (URL Link, Alert Pop-up, or Reply Message), and value seamlessly.
    *   **Delete Button**: Delete any configured inline button.
    *   **Reset to Default**: Revert to the original 4 default customizable buttons.

---

## 👑 Supreme Admin Panel & Management Commands

These commands are reserved for the Platform Owner (`OWNER_ID`) and appointed **Supreme Admins** who have full management rights across all cloned bots and the main bot.

### 🔺 Supreme Admin Authorization (Owner Only)
*   `/addsupreme [user_id / username / reply]` - Appoint a user as a Supreme Admin. (Only the main platform Owner can run this).
*   `/removesupreme [user_id / username / reply]` - Revoke Supreme Admin privileges from a user. (Only the main platform Owner can run this).
*   `/supremes` (or `/supremelist`) - List all currently authorized Supreme Admins in the platform.

### 💎 Premium Plan Management
*   `/addpremium [user_id] [duration_days]` - Grant premium privileges to a user.
*   `/removepremium [user_id]` - Revoke premium status and downgrade user to free plan limits.
*   `/set_clone_limit [user_id] [limit]` - Set a customized cloning limit for a specific user.

### 🤖 Cloned Bots Monitoring & Control
*   `/clones_list` (or `/clones`) - Retrieve a master list of all registered cloned bots with:
    *   **Bot Name & Username**
    *   **Bot ID**
    *   **Tenant ID & Username** (Who cloned the bot)
    *   **Active Status**
    *   **Currently Playing Song** (Tracks real-time song title and streaming group chat ID)
*   `/delete_clone [bot_id]` (or `/remove_clone [bot_id]`) - Forcibly stop and delete any cloned bot in the system.
*   `/clones_stats` - View real-time resource utilization (CPU, RAM) and total active/paused clones.
*   `/restart_clones` - Dynamically stop and restart all active clones in memory.
*   `/setfs [channel_username/none]` - Set a mandatory channel force subscription that users must join before they can clone a bot (or `/setfs none` to disable).

### 🛡️ Global Moderation & Bans
*   `/clone_ban [user_id]` - Globally ban a user from accessing/interacting with all cloned bots and the main bot.
*   `/clone_unban [user_id]` - Globally unban a user.

### 📢 Advanced Global Broadcast Engines
*   `/broadcast_group_all [message]` - Broadcast an administrative message to all groups where any cloned bot (or the main bot) is added and currently active.
*   `/broadcast_private_all [message]` - Broadcast an administrative message to all private chats (personal PMs) across all active cloned bots and the main bot.
*   `/broadcast_clones [message]` - Broadcast an administrative alert to all cloned bot owners/tenants in their personal chats.

---

## 💻 Tech Stack

*   **Language:** Python 3.10+
*   **Libraries:** Pyrogram (kurigram fork), motor (MongoDB Driver), py-tgcalls
*   **Database:** MongoDB Atlas
*   **API Framework:** aiohttp (Administration REST API & SSE/WebSockets)

---

## 🎵 How Song Playback Works (Streaming Architecture)

The platform streams high-quality audio and video directly into Telegram Voice Chats/Group Calls using a multi-layered architecture:

1. **Search & Metadata Extraction**:
   * When a user runs a playback command (e.g., `/play`), the bot processes the request using **`yt-dlp`** (wrapped in the `SONALI_MUSIC.platforms.Youtube` module).
   * It extracts the video ID, title, duration, and thumbnail of the requested content.

2. **Stream URL Resolution**:
   * The bot utilizes **`yt-dlp`** to resolve the direct streaming audio/video formats and URLs from YouTube, Spotify, or Soundcloud.

3. **High-Performance Audio/Video Pipeline**:
   * The core of the voice chat streaming is powered by **`py-tgcalls`** (configured inside `SONALI_MUSIC/core/call.py`).
   * `py-tgcalls` converts and streams the direct media links or downloaded files directly into Telegram's WebRTC-based group call/voice chat.

4. **Multi-Tenant Assistant & Load-Balancing**:
   * The streaming is executed by an Assistant account (Userbot).
   * The platform features a **multi-assistant load-balancer** (rotating across 5 standard system assistant clients to prevent group call limits) or allows premium users to supply a **custom session assistant** for their cloned bots, dynamically started and stopped via the `Sona` Py-Tgcalls wrapper.
