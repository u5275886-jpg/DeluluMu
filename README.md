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

## 👑 Owner Administration & Management Commands

These commands are strictly reserved for the platform Owner (`OWNER_ID`):

### 💎 Premium Plan Management
*   `/addpremium [user_id] [duration_days]` - Grant premium privileges to a user.
*   `/removepremium [user_id]` - Revoke premium status and downgrade user to free plan limits.
*   `/set_clone_limit [user_id] [limit]` - Set a customized cloning limit for a specific user.

### 🤖 Clone & Session Admin Controls
*   `/clones_list` (or `/clones`) - Retrieve a master list of all registered cloned bots along with their IDs and statuses.
*   `/delete_clone [bot_id]` (or `/remove_clone [bot_id]`) - Forcibly stop and delete any cloned bot in the system.
*   `/clones_stats` - View real-time resource utilization (CPU, RAM) and total active/paused clones.
*   `/restart_clones` - Dynamically stop and restart all active clones in memory.
*   `/broadcast_clones [message]` - Broadcast an administrative global alert to all active cloned bots.
*   `/setfs [channel_username/none]` - Set a mandatory channel force subscription that users must join before they can clone a bot (or `/setfs none` to disable).

### 🛡️ User Moderation
*   `/clone_ban [user_id]` - Globally ban a user from accessing all cloned bots and the main bot.
*   `/clone_unban [user_id]` - Globally unban a user.

---

## 💻 Tech Stack

*   **Language:** Python 3.10+
*   **Libraries:** Pyrogram (kurigram fork), motor (MongoDB Driver), py-tgcalls
*   **Database:** MongoDB Atlas
*   **API Framework:** aiohttp (Administration REST API & SSE/WebSockets)
