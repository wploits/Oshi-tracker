# 🚀 Oshi-tracker

**🇯🇵 [日本語](./README.ja.md)** | **🇺🇸 [English](./README.en.md)**

---

> The "Stream / X tracker" for your "推し活(Oshi-katsu)" !

Welcome to Oshi-tracker!

"Ugh, I wish there was a tool that could notify me on Discord about my Oshi's streams or new posts..."
If that's you, use this tutorial to make sure you never miss your favorite creator's latest actions! 👀

---

## ✨ Features
* Send stream notifications to Discord
* Notify new posts and *deleted* posts from X (formerly Twitter)

## 📡 Supported Platforms
* YouTube
* Twitch
* Niconico
* TikTok
* Openrec
* KICK
* Twitcasting

---

## 💻 Requirements
* Windows (10 / 11)
* [Python (3.10 or higher recommended)](https://www.python.org/downloads/)
* [Docker Desktop](https://www.docker.com/products/docker-desktop/)
* A Discord Account (to receive notifications)
* An X (formerly Twitter) Account (to get cookies)

---

## 🛠️ Setup Guide

### Step 0: Download the Source Code
1.  Click the green **`< > Code`** button on this repository's main page.
2.  Select **`Download ZIP`**.
3.  Extract the ZIP file to a location of your choice (e.g., your Desktop).
4.  **All further instructions assume you are working inside the extracted `src` folder.**

### Step 1: Install Required Libraries
Find and **double-click the `requirements.bat` file** inside the `src` folder.
This will automatically install the necessary Python libraries (`requests`, `pygame`, `curl_cffi`, `yt-dlp`).

### Step 2: Configure X (Twitter) & Launch RSSHub
To monitor X posts, you need to run a separate tool called 'RSSHub' using Docker.

**a. Get Your Cookie (Authentication Token)**
1.  Install the [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) extension for Chrome.
2.  Open X ( `https://x.com` ) and make sure you are logged in.
3.  Click the extension's icon (it might be inside the 🧩 puzzle-piece menu) and press the `Export` button to download the `cookies.txt` file.

**b. Set the Cookie for Oshi-tracker**
1.  Open the `src/datas/` folder.
2.  Open the `cookies.txt` file you just downloaded with a text editor.
3.  Copy all of its content (`Ctrl+A` -> `Ctrl+C`).
4.  Paste the content into `src/datas/cookies.txt` (overwrite any existing content) and save.

**c. Set the `auth_token` for RSSHub**
1.  Open `src/rsshub/docker-compose.yml` with a text editor.
2.  Find the line that says `TWITTER_AUTH_TOKEN=`.
3.  Look inside the `cookies.txt` file you downloaded earlier and find the line for `auth_token` (it's usually near the end).
    ```
    .x.com	TRUE	/	TRUE	[NUMBER]	auth_token	[A VERY LONG STRING OF LETTERS/NUMBERS]
    ```
4.  Copy *only* that long string of letters and numbers.
5.  Paste it after `TWITTER_AUTH_TOKEN=` in the `docker-compose.yml` file and save.
    ```yaml
    # Before
    TWITTER_AUTH_TOKEN: 
    # After (Example)
    TWITTER_AUTH_TOKEN: 012345abcdef...
    ```

**d. Launch RSSHub (The Monitoring Server)**
1.  **Make sure Docker Desktop is running.**
2.  Open the `src/rsshub/` folder.
3.  In the folder's address bar (where it shows the path), type `cmd` and press Enter.
4.  When the black terminal window opens, type the following command and press Enter:
    ```bash
    docker-compose up -d
    ```
5.  This will download and start the RSSHub server. If you see green `Done` or `started` messages, it was successful.

### Step 3: Configure Oshi-tracker (main.py)
This is the final step. We need to tell the tracker *who* to track.

Open the `main.py` file in the `src` folder with a text editor.
You will need to edit the target accounts listed at the top of the file.

**Set up the accounts you want to track.**
Leave any platform you don't want to track as an empty list (`[]`).

```python
# TikTok @usernames to track (@ not needed)
# Example: https://www.tiktok.com/@neymarjr
TIKTOK_TARGET_USERNAMES = ["neymarjr"]

# Niconico User IDs (the numbers in https://www.nicovideo.jp/user/XXXX)
# Example: https://www.nicovideo.jp/user/131666408
NICONICO_TARGET_USER_IDS = ["131666408"]

# YouTube @usernames to track (@ not needed)
# Example: https://www.youtube.com/@MrBeast
YOUTUBE_TARGET_USERNAMES = ["MrBeast"]

# Twitch usernames to track
# Example: https://www.twitch.tv/ninja
TWITCH_TARGET_USERNAMES = ["ninja"]

# Openrec usernames to track
# Example: https://www.openrec.tv/user/warabarin
OPENREC_TARGET_USERNAMES = ["warabarin"]

# Kick usernames to track
# Example: https://kick.com/adinross
KICK_TARGET_USERNAMES = ["adinross"]

# Twitcasting usernames to track
# Example: https://twitcasting.tv/korekore_ch
TWITCASTING_TARGET_USERNAMES = ["korekore_ch"]

# X RSSHub URLs to track
# "http://localhost:1200/twitter/user/X_USERNAME"
X_TARGET_URLS = [
    "http://localhost:1200/twitter/user/elonmusk?limit=20&includeRts=false&includeReplies=false",
    "http://localhost:1200/twitter/user/BillGates?limit=10&includeRts=false&includeReplies=false",
]

# X user IDs (from the URLs above) to *pause* tracking for if *any* stream is live
LIVE_PAUSE_X_TARGET_IDS = ["elonmusk"]

# Your Discord Webhook URL for notifications
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1234567890/xxxxxxxxxxxx_YYYYYYYYYYYYYYYYY"
```

#### How to get a Discord Webhook URL
1.  In your Discord server, right-click the channel you want notifications in.
2.  Go to `Edit Channel` -> `Integrations` -> `Webhooks`.
3.  Click `New Webhook`, give it a name (e.g., Oshi-tracker).
4.  Click `Copy Webhook URL` and paste it into the `DISCORD_WEBHOOK_URL` variable in `main.py`.

#### X (Twitter) URL Parameters
The URLs in `X_TARGET_URLS` have several options:
* `limit=10`: The number of recent posts to check. **10-20 is recommended.**
* `includeRts=false`: Include Retweets (Reposts) (`true` / `false`).
* `includeReplies=false`: Include Replies (`true` / `false`).

### Step 4: Launch the Tracker!
You're done!
**Double-click `main.py`** in the `src` folder (or run `python main.py` in your terminal).
A console window will open, and monitoring for all your configured accounts will begin. As long as this window is running, you will get notifications on Discord!

---

## 🔴 Automatic Stream Recording

### Enable/Disable Toggle

```python
class Config:
    DEBUG_LOGGING = False
    ENABLE_AUTO_RECORDING = False # ← Right here!!!! False = Off, True = On
```

### Target Platforms

```python
class Config:
    # (...snip...)
    RECORDING_TARGET_PLATFORMS = [
        #NOTIF_PLATFORM_TIKTOK,
        #NOTIF_PLATFORM_NICONICO,
        #NOTIF_PLATFORM_YOUTUBE,
        #NOTIF_PLATFORM_TWITCH,
        #NOTIF_PLATFORM_OPENREC,
        #NOTIF_PLATFORM_KICK,
        #NOTIF_PLATFORM_TWITCASTING
    ]
    # (...snip...)
```

Remove the # from the lines above to enable automatic recording for that platform!

(To disable it, add the # back or delete the line. If you delete a line and want to add it back later, refer to this readme to add the platform.)

---

## 🔧 Advanced Configuration (main.py)
You can fine-tune the tracker's behavior by editing the `Config` class and other global variables in `main.py`.

### Sound On/Off
To disable a local sound notification, set its path to an empty string (`""`).

```python
# Stream Start Sound
SOUND_LIVE_START = "./sounds/live_start.mp3"
# Stream End Sound (empty = disabled)
SOUND_LIVE_END = ""
# X Post Detection Sound
SOUND_MESSAGE_DETECTED = "./sounds/message_detected.mp3"
```

### Monitoring Intervals
Smaller numbers mean faster detection, but increase the risk of getting rate-limited (banned) by the platforms. **Change at your own risk.**

```python
# X (RSSHub) check interval (seconds)
X_CHECK_INTERVAL_SECONDS = 60.1
# Live stream check interval (seconds)
LIVE_CHECK_INTERVAL_SECONDS = 60
```

### Debug Logging
Whether to write detailed operational logs to `datas/tracker_log.txt`.
If `True`, you can see which platforms were checked successfully or failed.

```python
class Config:
    DEBUG_LOGGING = True  # True to enable, False to disable
```

### Notification Messages
You can change the messages sent to Discord.

```python
class Config:
    # (...omitted...)
    NOTIF_LIVE_START = "【Alert】{name} has started streaming {platform}! @everyone"
    NOTIF_LIVE_END = "({name}'s {platform} stream has ended)"
    # (...omitted...)
```

---

## 👨‍💻 For Developers
This tool uses the `curl_cffi` library to bypass TLS fingerprinting (JA3) blocks on platforms like YouTube, Twitch, Kick, and TikTok, which would normally return a 403 (Forbidden) error to standard `python-requests`. By setting `impersonate="chrome110"`, we spoof the TLS handshake to appear as a genuine Chrome browser.

---

## 👑 Credit
* **Developer:** [Your Name or Handle]
* *(Note: Some code in this tool was written with the assistance of AI.)*

## 📜 License
This project is licensed under the [MIT License](./LICENSE).
