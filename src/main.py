import requests
import time
import pygame
import os
import re
import json
import xml.etree.ElementTree as ET
import subprocess
from urllib.parse import urlparse, parse_qs
import html
from datetime import datetime
from curl_cffi import requests as cffi_requests
import signal

os.system('')

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GRAY = '\033[90m'
    BLUE = '\033[94m'
    END = '\033[0m'

class Config:
    DEBUG_LOGGING = False
    ENABLE_AUTO_RECORDING = True

    APP_TITLE = "--- Oshi-tracker ---"
    LOG_STARTUP = "--- Tracker Startup ---"
    LOG_SHUTDOWN = "--- Tracker Shutdown Successful ---"
    CONSOLE_SHUTDOWN = "\n--- Shutting Down System ---"
    CONSOLE_CACHE_SAVED = "Cache Saved."
    
    CONSOLE_LIVE_CYCLE = f"[{Colors.GRAY}--- Live Monitoring Cycle ---{Colors.END}]"
    CONSOLE_X_CYCLE = f"[{Colors.GRAY}--- X (RSSHub) Monitoring Cycle ---{Colors.END}]"
    CONSOLE_FOOTER = "\n{gray}({time_str} @ X:{x_interval}s / Live:{live_interval}s / Press Ctrl+C to Exit){end}"
    
    CONSOLE_LIVE_PREFIX = f"[{Colors.GREEN}● LIVE{Colors.END}]"
    CONSOLE_OFF_PREFIX = f"[{Colors.RED}■ OFF{Colors.END}]"
    CONSOLE_RSS_PREFIX = f"[{Colors.BLUE}● RSS{Colors.END}]"
    CONSOLE_RSS_PAUSED_PREFIX = f"[{Colors.GRAY}● RSS{Colors.END}]"

    STATUS_SERVICE_DISABLED = "(Disabled)"
    STATUS_X_PAUSED = "Streaming (Paused)"
    STATUS_X_MONITORING = "Monitoring ({count} posts)"
    STATUS_X_ERROR = "Error"
    
    STATUS_TITLE_UNKNOWN = "Title Unknown"
    STATUS_BODY_UNKNOWN = "Body Unknown"

    NOTIF_LIVE_START = "@everyone\n@everyone\n{name}'s {platform} stream has started!!!!!"
    NOTIF_LIVE_END = "({name}'s {platform} stream has ended.)"
    
    NOTIF_PLATFORM_TIKTOK = "TikTok"
    NOTIF_PLATFORM_NICONICO = "Nico Live"
    NOTIF_PLATFORM_YOUTUBE = "YouTube"
    NOTIF_PLATFORM_TWITCH = "Twitch"
    NOTIF_PLATFORM_OPENREC = "Openrec"
    NOTIF_PLATFORM_KICK = "Kick"
    NOTIF_PLATFORM_TWITCASTING = "TwitCasting"

    RECORDING_TARGET_PLATFORMS = [
        #NOTIF_PLATFORM_TIKTOK,
        NOTIF_PLATFORM_NICONICO,
        #NOTIF_PLATFORM_YOUTUBE,
        #NOTIF_PLATFORM_TWITCH,
        #NOTIF_PLATFORM_OPENREC,
        #NOTIF_PLATFORM_KICK,
        #NOTIF_PLATFORM_TWITCASTING
    ]

    NOTIF_POST_DELETED_TITLE = "[Deletion Detected] {title}"
    NOTIF_POST_DELETED_DESC = "This Post was deleted or made private.\n\n**▼ Original Post Body ▼**\n{desc}"
    
    LOG_X_PAUSE = "-> Pausing monitoring for {name} (@{account_id}) (Due to an ongoing live stream)"

TIKTOK_TARGET_USERNAMES = ["neymarjr"]
NICONICO_TARGET_USER_IDS = ["142120663"]
YOUTUBE_TARGET_USERNAMES = ["MrBeast"]
TWITCH_TARGET_USERNAMES = ["kun_50"]
OPENREC_TARGET_USERNAMES = ["mokouliszt_or"]
KICK_TARGET_USERNAMES = ["adinross"]
TWITCASTING_TARGET_USERNAMES = ["korekore_ch"]

X_TARGET_URLS = [
    "http://localhost:1200/twitter/user/elonmusk?limit=20&includeRts=false&includeReplies=false",
    "http://localhost:1200/twitter/user/BillGates?limit=10&includeRts=false&includeReplies=false",
]
LIVE_PAUSE_X_TARGET_IDS = ["elonmusk"]

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1234567890/xxxxxxxxxxxx_YYYYYYYYYYYYYYYYY"

X_CHECK_INTERVAL_SECONDS = 60.1
LIVE_CHECK_INTERVAL_SECONDS = 60
REQUEST_TIMEOUT_SECONDS = 15

SOUND_LIVE_START = "./sounds/live_start.mp3"
SOUND_LIVE_END = "./sounds/live_end.mp3"
SOUND_MESSAGE_DETECTED = "./sounds/message_detected.mp3"

CACHE_FILE = "./datas/tracker_cache.json"
COOKIE_FILE_PATH = "./datas/cookies.txt"
LOG_FILE = "./datas/tracker_log.txt"
RECORDING_PATH = "./datas/recordings/"

niconico_headers = {"X-Frontend-Id": "6"}
browser_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

pygame.mixer.init()
http_session = requests.Session()
http_session.headers.update(browser_headers)

recording_processes = {}

def write_log(message, debug=False):
    if debug and not Config.DEBUG_LOGGING:
        return
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except Exception as e:
        print(f"[{Colors.RED}Log Write Error{Colors.END}] {e}")

def play_sound(file_path):
    if file_path and os.path.exists(file_path):
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
        except Exception as e:
            log_msg = f"[{Colors.RED}Sound Playback Error{Colors.END}] {e}"
            print(log_msg)
            write_log(log_msg)
    elif file_path:
        log_msg = f"[{Colors.RED}Sound File Not Found{Colors.END}] {file_path}"
        print(log_msg)
        write_log(log_msg)


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log_msg = f"[{Colors.RED}Cache Load Error{Colors.END}] {e}"
        print(log_msg)
        write_log(log_msg)
        return {}

def save_cache(cache):
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4)
    except Exception as e:
        log_msg = f"[{Colors.RED}Cache Save Error{Colors.END}] {e}"
        print(log_msg)
        write_log(log_msg)

def download_media(url, is_video=False):
    downloaded_files = []
    
    if is_video:
        print(f"-> DL with yt-dlp: {url}")
        try:
            cmd = ["yt-dlp", "--cookies", COOKIE_FILE_PATH, "-o", "%(id)s.%(ext)s", url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=True, encoding='utf-8', errors='ignore')
            
            output_lines = result.stdout.splitlines()
            for line in output_lines:
                if "Merging formats into" in line or "Destination:" in line:
                    parts = line.split('"') if '"' in line else line.split(':')
                    filename = parts[-2] if '"' in line else parts[-1].strip()
                    if os.path.exists(filename) and filename not in downloaded_files:
                        downloaded_files.append(filename)
            
            if not downloaded_files:
                match = re.search(r"\[download\] (.*?) has already been downloaded", result.stdout)
                if match and os.path.exists(match.group(1)):
                    downloaded_files.append(match.group(1))

            print(f"-> yt-dlp Success: {downloaded_files}")
            
        except subprocess.CalledProcessError as e:
            log_msg = f"[{Colors.RED}yt-dlp Error{Colors.END}] {e.stderr}"
            print(log_msg)
            write_log(log_msg)
        except FileNotFoundError:
             log_msg = f"[{Colors.RED}yt-dlp Error{Colors.END}] yt-dlp is not installed."
             print(log_msg)
             write_log(log_msg)
        except Exception as e:
            log_msg = f"[{Colors.RED}yt-dlp General Error{Colors.END}] {e}"
            print(log_msg)
            write_log(log_msg)
            
    else: 
        print(f"-> Image DL: {url}")
        try:
            parsed_url = urlparse(url)
            path_filename = parsed_url.path.split('/')[-1]
            query_params = parse_qs(parsed_url.query)
            
            ext = ""
            if 'format' in query_params:
                ext = query_params['format'][0]

            if not path_filename:
                path_filename = f"image_{int(time.time())}"

            if ext:
                filename = f"{path_filename}.{ext}"
            elif '.' in path_filename:
                filename = path_filename
            else:
                filename = f"{path_filename}.jpg"

            response = http_session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            
            filepath = os.path.join(os.getcwd(), filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            downloaded_files.append(filepath)
            print(f"-> Download Success: {filepath}")
            
        except Exception as e:
            log_msg = f"[{Colors.RED}Download Error{Colors.END}] {e}"
            print(log_msg)
            write_log(log_msg)
            
    return downloaded_files

def send_live_notification(message, sound_file, url=None):
    print(f"!!! [{Colors.GREEN}{message}{Colors.END}] !!!")

    notification_message = message
    if url and isinstance(url, str) and url.startswith("http"):
        print(f"-> LiveURL: {url}")
        notification_message = f"{message}\n{url}"

    write_log(f"Live Notification: {notification_message}")
    play_sound(sound_file)
    
    if DISCORD_WEBHOOK_URL:
        try:
            http_session.post(DISCORD_WEBHOOK_URL, json={"content": notification_message}, timeout=REQUEST_TIMEOUT_SECONDS)
        except Exception as e:
            log_msg = f"[{Colors.RED}Webhook Error{Colors.END}] {e}"
            print(log_msg)
            write_log(log_msg)

def send_post_notification(account_name, post_info, files_to_attach, color_hex, mention_everyone=False):
    print(f"-> Sending Discord Notification: {account_name} - {post_info.get('title', 'N/A')}")
    play_sound(SOUND_MESSAGE_DETECTED)
    
    embed = {
        "title": post_info.get('title', 'No Title'),
        "description": post_info.get('description_text', ''),
        "url": post_info.get('link', ''),
        "color": int(color_hex, 16),
        "author": {
            "name": account_name
        },
        "footer": {
            "text": f"GUID: {post_info.get('guid', 'N/A')}"
        }
    }
    
    if post_info.get('pubDate'):
        try:
            date_str = post_info['pubDate']
            if date_str.endswith(" +0000"):
                date_str = date_str.replace(" +0000", " GMT")
            dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
            embed["timestamp"] = dt.isoformat()
        except ValueError as e:
            log_msg = f"[{Colors.RED}Date Parse Error{Colors.END}] {e} - {post_info['pubDate']}"
            print(log_msg)
            write_log(log_msg)
            pass
        
    files_payload = []
    discord_files = []
    
    try:
        payload = {}
        if mention_everyone:
            payload["content"] = "@everyone"
        
        payload["embeds"] = [embed]
        payload_json = json.dumps(payload)
        
        if files_to_attach:
            for i, filepath in enumerate(files_to_attach):
                file_handle = open(filepath, 'rb')
                discord_files.append(file_handle)
                files_payload.append((f'file{i}', (os.path.basename(filepath), file_handle)))
            
            response = requests.post(DISCORD_WEBHOOK_URL, files=files_payload, data={"payload_json": payload_json}, timeout=30)
        else:
            response = requests.post(DISCORD_WEBHOOK_URL, data={"payload_json": payload_json}, timeout=30)
        
        response.raise_for_status()
        
    except Exception as e:
        log_msg = f"[{Colors.RED}Webhook Error{Colors.END}] {e}"
        print(log_msg)
        write_log(log_msg)
    finally:
        for f in discord_files:
            f.close()
        for f in files_to_attach:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception as e:
                    log_msg = f"[{Colors.RED}File Deletion Error{Colors.END}] {e}"
                    print(log_msg)
                    write_log(log_msg)

def parse_rss_item(item):
    guid = item.find('guid').text if item.find('guid') is not None else ""
    title = item.find('title').text if item.find('title') is not None else ""
    link = item.find('link').text if item.find('link') is not None else ""
    pubDate = item.find('pubDate').text if item.find('pubDate') is not None else ""
    description_html = item.find('description').text if item.find('description') is not None else ""
    
    description_text = re.sub(r'<[^>]+>', ' ', description_html).strip()
    
    video_urls = re.findall(r'<video.*?src="(.*?)".*?>', description_html)
    img_urls = re.findall(r'<img.*?src="(.*?)".*?>', description_html)
    
    video_urls = [html.unescape(url) for url in video_urls]
    img_urls = [html.unescape(url) for url in img_urls]

    return {
        "guid": guid,
        "title": title or Config.STATUS_TITLE_UNKNOWN,
        "link": link,
        "pubDate": pubDate,
        "description_text": description_text,
        "video_urls": video_urls,
        "img_urls": img_urls
    }

def get_oldest_post_date(posts_map):
    if not posts_map:
        return None
    oldest_date = None
    for post in posts_map.values():
        if not post.get('pubDate'):
            continue
        try:
            date_str = post['pubDate']
            if date_str.endswith(" +0000"):
                date_str = date_str.replace(" +0000", " GMT")
            dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
            if oldest_date is None or dt < oldest_date:
                oldest_date = dt
        except ValueError:
            continue
    return oldest_date

def start_recording(platform, identifier, live_url):
    try:
        os.makedirs(RECORDING_PATH, exist_ok=True)
        filename = os.path.join(RECORDING_PATH, f"[{platform}]_{identifier}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
        
        cmd = ["yt-dlp", "--cookies", COOKIE_FILE_PATH, "-o", filename, live_url]
        
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        recording_processes[identifier] = process
        write_log(f"Recording Started: {identifier} ({platform}) -> {filename}", debug=True)
        
    except Exception as e:
        log_msg = f"[{Colors.RED}Recording Start Error{Colors.END}] {identifier}: {e}"
        print(log_msg)
        write_log(log_msg)

def stop_recording(identifier):
    try:
        if identifier in recording_processes:
            process = recording_processes.pop(identifier)
            process.send_signal(signal.SIGINT)
            write_log(f"Recording Stopped: {identifier}", debug=True)
    except Exception as e:
        log_msg = f"[{Colors.RED}Recording Stop Error{Colors.END}] {identifier}: {e}"
        print(log_msg)
        write_log(log_msg)

def check_tiktok_live(username):
    url = f"https://www.tiktok.com/@{username}"
    write_log(f"[TikTok DEBUG] @{username}: Starting check", debug=True)
    
    try:
        response = cffi_requests.get(url, headers=browser_headers, impersonate="chrome110", timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        html_content = response.text
        write_log(f"[TikTok DEBUG] @{username}: HTML fetched successfully (Status {response.status_code}, {len(html_content)} bytes).", debug=True)

        match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>', html_content)
        if not match:
            log_msg = f"[{Colors.RED}TikTok Error{Colors.END}] @{username}: Data (REHYDRATION) not found."
            print(log_msg)
            write_log(log_msg)
            return False, None
        
        write_log(f"[TikTok DEBUG] @{username}: JSON-LD script found.", debug=True)
        
        try:
            data = json.loads(match.group(1))
            user_info = data.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {}).get("userInfo", {}).get("user", {})
            
            display_name = user_info.get("nickname")
            live_url = False
            
            if user_info.get("roomId") and user_info.get("roomId") != "0":
                live_url = f"https://www.tiktok.com/@{username}/live"
                write_log(f"[TikTok DEBUG] @{username}: 'roomId' ({user_info.get('roomId')}) found. Assumed live.", debug=True)

            write_log(f"[TikTok DEBUG] @{username}: Check complete. live_url={live_url}, display_name='{display_name}'", debug=True)
            return live_url, display_name
            
        except json.JSONDecodeError:
            log_msg = f"[{Colors.RED}TikTok Error{Colors.END}] @{username}: JSON parsing failed."
            print(log_msg)
            write_log(log_msg)
            return False, None

    except Exception as e:
        log_msg = f"[{Colors.RED}TikTok Error{Colors.END}] {e}"
        print(log_msg)
        write_log(log_msg)
        return False, None

def check_niconico_live(user_id):
    niconico_api_url = (
        f"https://api.feed.nicovideo.jp/v1/activities/actors/users/"
        f"{user_id}/publish"
        f"?context=user_timeline_{user_id}"
    )
    write_log(f"[Nico Live DEBUG] ID:{user_id}: Starting check", debug=True)
    try:
        response = http_session.get(niconico_api_url, headers=niconico_headers, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        write_log(f"[Nico Live DEBUG] ID:{user_id}: API fetched successfully.", debug=True)

        display_name = None
        live_url = False

        if "activities" in data and len(data["activities"]) > 0:
            latest_activity = data["activities"][0]
            display_name = latest_activity.get("actor", {}).get("name", None)
            
            latest_activity_label = latest_activity.get("label", {}).get("text", "")
            if latest_activity_label == "LIVE":
                live_url_path = latest_activity.get("content", {}).get("url", "")
                live_url = live_url_path if live_url_path else True
                write_log(f"[Nico Live DEBUG] ID:{user_id}: 'LIVE' label found. Assumed live.", debug=True)
        
        write_log(f"[Nico Live DEBUG] ID:{user_id}: Check complete. live_url={live_url}, display_name='{display_name}'", debug=True)
        return live_url, display_name

    except Exception as e:
        log_msg = f"[{Colors.RED}Nico Live Error{Colors.END}] {e}"
        print(log_msg)
        write_log(log_msg)
        return False, None

def check_youtube_live(username):
    url = f"https://www.youtube.com/@{username}"
    write_log(f"[YouTube DEBUG] @{username}: Starting check", debug=True)
    try:
        response = cffi_requests.get(url, headers=browser_headers, impersonate="chrome110", timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        html_content = response.text
        write_log(f"[YouTube DEBUG] @{username}: HTML fetched successfully (Status {response.status_code}, {len(html_content)} bytes).", debug=True)

        match = re.search(r"var ytInitialData = ({.*?});</script>", html_content)
        if not match:
            log_msg = f"[{Colors.RED}YouTube Error{Colors.END}] @{username}: ytInitialData not found."
            print(log_msg)
            write_log(log_msg)
            return False, None
        
        write_log(f"[YouTube DEBUG] @{username}: 'ytInitialData' found.", debug=True)
            
        try:
            data = json.loads(match.group(1))
            display_name = None
            live_url = False
            
            try:
                display_name = data['metadata']['channelMetadataRenderer']['title']
                write_log(f"[YouTube DEBUG] @{username}: Display name '{display_name}' found.", debug=True)
            except KeyError:
                display_name = username
            
            try:
                header_vm = data['header']['pageHeaderRenderer']['content']['pageHeaderViewModel']
                avatar = header_vm['image']['decoratedAvatarViewModel']
                
                if 'liveData' in avatar:
                    video_id = avatar['rendererContext']['commandContext']['onTap']['innertubeCommand']['watchEndpoint']['videoId']
                    live_url = f"https://www.youtube.com/watch?v={video_id}"
                    write_log(f"[YouTube DEBUG] @{username}: 'liveData' found. Assumed live.", debug=True)
            except KeyError:
                pass

            write_log(f"[YouTube DEBUG] @{username}: Check complete. live_url={live_url}, display_name='{display_name}'", debug=True)
            return live_url, display_name

        except json.JSONDecodeError:
            log_msg = f"[{Colors.RED}YouTube Error{Colors.END}] @{username}: JSON parsing failed."
            print(log_msg)
            write_log(log_msg)
            return False, None
            
    except Exception as e:
        log_msg = f"[{Colors.RED}YouTube Error{Colors.END}] @{username}: Failed to fetch page. {e}"
        print(log_msg)
        write_log(log_msg)
        return False, None

def check_twitch_live(username):
    url = f"https://www.twitch.tv/{username}"
    live_url = False
    display_name = f"@{username}"
    write_log(f"[Twitch DEBUG] @{username}: Starting check", debug=True)
    
    try:
        response = cffi_requests.get(url, headers=browser_headers, impersonate="chrome110", timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        html_content = response.text
        write_log(f"[Twitch DEBUG] @{username}: HTML fetched successfully (Status {response.status_code}, {len(html_content)} bytes).", debug=True)

        match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html_content, re.DOTALL)
        if not match:
            log_msg = f"[{Colors.RED}Twitch Error{Colors.END}] @{username}: JSON-LD script not found."
            print(log_msg)
            write_log(log_msg)
            return False, display_name

        write_log(f"[Twitch DEBUG] @{username}: JSON-LD script block found.", debug=True)
        try:
            json_data_str = match.group(1)
            
            data_list = []
            if json_data_str.startswith('['):
                data_list = json.loads(json_data_str)
            else:
                data_list.append(json.loads(json_data_str))

            found_live = False
            found_name = False

            for data in data_list:
                graph = data.get("@graph", [])
                if isinstance(graph, list):
                    for item in graph:
                        if isinstance(item, dict):
                            if not found_name and item.get("@type") == "Person":
                                display_name = item.get("name", username)
                                found_name = True
                                write_log(f"[Twitch DEBUG] @{username}: Display name '{display_name}' found.", debug=True)
                            
                            publication = item.get("publication")
                            if not found_live and isinstance(publication, dict):
                                if publication.get("@type") == "BroadcastEvent" and publication.get("isLiveBroadcast") == True:
                                    live_url = url
                                    found_live = True
                                    write_log(f"[Twitch DEBUG] @{username}: 'isLiveBroadcast: true' found. Assumed live.", debug=True)
            
            write_log(f"[Twitch DEBUG] @{username}: Check complete. live_url={live_url}, display_name='{display_name}'", debug=True)
            return live_url, display_name

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            log_msg = f"[{Colors.RED}Twitch Error{Colors.END}] @{username}: JSON parsing failed. {e}"
            print(log_msg)
            write_log(log_msg)
            return False, display_name

    except Exception as e:
        log_msg = f"[{Colors.RED}Twitch Error{Colors.END}] @{username}: Failed to fetch page. {e}"
        print(log_msg)
        write_log(log_msg)
        return False, display_name

def check_openrec_live(username):
    url = f"https://public.openrec.tv/external/api/v5/channels/{username}"
    live_url = False
    display_name = f"@{username}"
    write_log(f"[Openrec DEBUG] @{username}: Starting check", debug=True)
    
    try:
        response = http_session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        write_log(f"[Openrec DEBUG] @{username}: API fetched successfully.", debug=True)
        
        display_name = data.get("nickname", username)
        
        onair_movies = data.get("onair_broadcast_movies", [])
        if onair_movies and isinstance(onair_movies, list) and len(onair_movies) > 0:
            live_id = onair_movies[0].get("id")
            if live_id:
                live_url = f"https://www.openrec.tv/live/{live_id}"
                write_log(f"[Openrec DEBUG] @{username}: 'onair_broadcast_movies' found. Assumed live.", debug=True)
        
        write_log(f"[Openrec DEBUG] @{username}: Check complete. live_url={live_url}, display_name='{display_name}'", debug=True)
        return live_url, display_name

    except Exception as e:
        log_msg = f"[{Colors.RED}Openrec Error{Colors.END}] @{username}: Failed to fetch API. {e}"
        print(log_msg)
        write_log(log_msg)
        return False, display_name

def check_kick_live(username):
    url = f"https://kick.com/{username}"
    live_url = False
    display_name = f"@{username}"
    
    write_log(f"[Kick DEBUG] @{username}: Starting check...", debug=True)
    
    try:
        response = cffi_requests.get(url, headers=browser_headers, impersonate="chrome110", timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        html_content = response.text

        write_log(f"[Kick DEBUG] @{username}: HTML fetched successfully (Status {response.status_code}, {len(html_content)} bytes).", debug=True)

        matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html_content, re.DOTALL)
        if not matches:
            log_msg = f"[{Colors.RED}Kick Error{Colors.END}] @{username}: JSON-LD script not found."
            print(log_msg)
            write_log(log_msg)
            return False, display_name

        write_log(f"[Kick DEBUG] @{username}: {len(matches)} JSON-LD script blocks found.", debug=True)
        
        found_live = False
        found_name = False

        for i, match_str in enumerate(matches):
            if found_live and found_name:
                break 

            write_log(f"[Kick DEBUG] @{username}: Parsing JSON-LD block #{i}...", debug=True)
            try:
                data = json.loads(match_str)
                
                items_to_check = []
                if isinstance(data.get("@graph"), list):
                    items_to_check.extend(data["@graph"])
                elif isinstance(data, dict):
                    items_to_check.append(data)

                for item in items_to_check:
                    if not isinstance(item, dict):
                        continue

                    item_type = item.get("@type")
                    
                    if not found_name:
                        if item_type == "Person" and item.get("@id") == "#kick-user":
                            display_name = item.get("name", username)
                            found_name = True
                            write_log(f"[Kick DEBUG] @{username}: Display name (Person) '{display_name}' found.", debug=True)
                        elif item_type == "BroadcastEvent" and item.get("@id") == "#active-stream":
                            if "publishedBy" in item and "name" in item["publishedBy"]:
                                display_name = item["publishedBy"]["name"]
                                found_name = True
                                write_log(f"[Kick DEBUG] @{username}: Display name (BroadcastEvent) '{display_name}' found.", debug=True)
                    
                    if not found_live:
                        if item_type == "BroadcastEvent" and item.get("isLiveBroadcast") == True:
                            live_url = url
                            found_live = True
                            write_log(f"[Kick DEBUG] @{username}: 'isLiveBroadcast: true' (Root) found. Assumed live.", debug=True)
                        elif item_type == "VideoObject" and "publication" in item:
                             if item["publication"].get("@type") == "BroadcastEvent" and item["publication"].get("isLiveBroadcast") == True:
                                live_url = url
                                found_live = True
                                write_log(f"[Kick DEBUG] @{username}: 'isLiveBroadcast: true' (VideoObject) found. Assumed live.", debug=True)

            except (json.JSONDecodeError, KeyError, IndexError) as e:
                write_log(f"[Kick DEBUG] @{username}: JSON parsing failed for block #{i}: {e}", debug=True)
                continue

        write_log(f"[Kick DEBUG] @{username}: Check complete. live_url={live_url}, display_name='{display_name}'", debug=True)
        return live_url, display_name

    except Exception as e:
        log_msg = f"[{Colors.RED}Kick Error{Colors.END}] @{username}: Failed to fetch page. {e}"
        print(log_msg)
        write_log(log_msg)
        return False, display_name

def check_twitcasting_live(username):
    url = f"https://twitcasting.tv/streamserver.php?target={username}&mode=client&player=pc_web"
    live_url = False
    display_name = f"@{username}"
    write_log(f"[TwitCasting DEBUG] @{username}: Starting check", debug=True)
    
    try:
        response = http_session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        write_log(f"[TwitCasting DEBUG] @{username}: API fetched successfully.", debug=True)
        
        display_name = data.get("broadcaster", {}).get("name", username)
        
        if data.get("movie", {}).get("live") == True:
            live_url = f"https://twitcasting.tv/{username}"
            write_log(f"[TwitCasting DEBUG] @{username}: 'movie.live: true' found. Assumed live.", debug=True)

        write_log(f"[TwitCasting DEBUG] @{username}: Check complete. live_url={live_url}, display_name='{display_name}'", debug=True)
        return live_url, display_name

    except Exception as e:
        log_msg = f"[{Colors.RED}TwitCasting Error{Colors.END}] @{username}: Failed to fetch API. {e}"
        print(log_msg)
        write_log(log_msg)
        return False, display_name

def process_x_feed(url, cache, is_any_streamer_live):
    account_id = ""
    try:
        account_id = url.split('/user/')[1].split('?')[0]
        limit_match = re.search(r'limit=(\d+)', url)
        feed_limit = int(limit_match.group(1)) if limit_match else 10

        response = http_session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        
        root = ET.fromstring(response.text)
        
        display_name_from_rss = root.findtext('./channel/title')
        display_name = ""
        
        if display_name_from_rss:
            display_name = display_name_from_rss.replace(" / Twitter", "").strip()
            display_name = re.sub(r"\(@.+?\)", "", display_name).strip()
            if display_name.startswith("Twitter @"):
                 display_name = display_name.replace("Twitter @", "").strip()
        else:
            display_name = f"@{account_id}" 
        
        if account_id in LIVE_PAUSE_X_TARGET_IDS and is_any_streamer_live:
            return display_name, Config.STATUS_X_PAUSED
        
        current_posts_map = {}
        for item in root.findall('./channel/item'):
            post_info = parse_rss_item(item)
            if post_info['guid']:
                current_posts_map[post_info['guid']] = post_info
        
        if not current_posts_map:
            return display_name, Config.STATUS_X_MONITORING.format(count=0)

        cached_posts_map = cache.get(account_id, {})
        
        cached_guids = set(cached_posts_map.keys())
        current_guids = set(current_posts_map.keys())
        
        new_guids = current_guids - cached_guids
        deleted_guids = cached_guids - current_guids
        
        if not cached_posts_map and current_guids:
            log_msg = f"-> Initial scan for {display_name} (@{account_id}) complete. {len(current_guids)} posts cached. (Notification skipped)"
            print(log_msg)
            write_log(f"Initial scan ({display_name} @{account_id}): {len(current_guids)} cached. Notification skipped.")
            cache[account_id] = current_posts_map
            return display_name, Config.STATUS_X_MONITORING.format(count=len(current_posts_map))

        oldest_cache_date = get_oldest_post_date(cached_posts_map)
        
        bubbled_up_guids = set()
        if oldest_cache_date:
            for guid in new_guids:
                post_info = current_posts_map[guid]
                if not post_info.get('pubDate'):
                    continue
                try:
                    date_str = post_info['pubDate']
                    if date_str.endswith(" +0000"):
                        date_str = date_str.replace(" +0000", " GMT")
                    post_date = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
                    
                    if post_date < oldest_cache_date:
                        bubbled_up_guids.add(guid)
                except ValueError:
                    continue

        real_new_guids = new_guids - bubbled_up_guids
        
        if bubbled_up_guids:
            for guid in bubbled_up_guids:
                log_msg = f"[{Colors.GRAY}Post Resurfaced{Colors.END}] {display_name} (@{account_id}): {guid} (Older than oldest cached post, skipping notification)"
                print(log_msg)
                write_log(f"Post Resurfaced ({display_name} @{account_id}): {guid}. Reason: Older than oldest cached post, skipping notification. URL: {current_posts_map[guid].get('link', 'N/A')}")

        for guid in real_new_guids:
            post_info = current_posts_map[guid]
            log_msg = f"[{Colors.GREEN}New Post Detected{Colors.END}] {display_name} (@{account_id}): {post_info['title']}"
            print(log_msg)
            write_log(f"New Post Detected ({display_name} @{account_id}): {post_info['title']}. URL: {post_info.get('link', 'N/A')}")
            
            downloaded_files = []
            if post_info['video_urls']:
                downloaded_files.extend(download_media(post_info['link'], is_video=True))
            for img_url in post_info['img_urls']:
                downloaded_files.extend(download_media(img_url, is_video=False))
                
            notification_account_name = f"{display_name} (@{account_id})"
            send_post_notification(notification_account_name, post_info, downloaded_files, "00FF00", mention_everyone=True)

        are_real_new_posts = len(real_new_guids) > 0
        is_feed_full = len(current_posts_map) == feed_limit
        
        expanded_guids = set()
        potential_push_out = is_feed_full and are_real_new_posts and deleted_guids

        if potential_push_out:
            try:
                expanded_limit = feed_limit + len(real_new_guids)
                expanded_url = re.sub(r'limit=\d+', f'limit={expanded_limit}', url)
                
                log_msg = f"-> Deletion candidate detected. Re-fetching with limit increased to {expanded_limit} ({account_id})"
                print(log_msg)
                write_log(log_msg)

                expanded_response = http_session.get(expanded_url, timeout=REQUEST_TIMEOUT_SECONDS)
                expanded_response.raise_for_status()
                expanded_root = ET.fromstring(expanded_response.text)
                
                for item in expanded_root.findall('./channel/item'):
                    guid = item.find('guid').text if item.find('guid') is not None else ""
                    if guid:
                        expanded_guids.add(guid)
            
            except Exception as e:
                log_msg = f"[{Colors.RED}Deletion Check (Refetch) Error{Colors.END}] {e}"
                print(log_msg)
                write_log(log_msg)

        for guid in deleted_guids:
            notification_account_name = f"{display_name} (@{account_id})"
            
            is_pushed_out = False
            if potential_push_out:
                if guid in expanded_guids:
                    is_pushed_out = True
                else:
                    log_msg = f"-> GUID ({guid}) not found even in expanded feed, confirming deletion."
                    print(log_msg)
                    write_log(log_msg)
            
            if is_pushed_out:
                log_msg = f"[{Colors.GRAY}Post Out of Range{Colors.END}] {display_name} (@{account_id}): {guid} (Assumed pushed out)"
                print(log_msg)
                write_log(f"Post Out of Range ({display_name} @{account_id}): {guid}. Reason: GUID found in expanded feed (limit={len(expanded_guids)}), assumed pushed out. URL: {cached_posts_map.get(guid, {}).get('link', 'N/A')}")
            else:
                log_msg = f"[{Colors.YELLOW}Post Deletion Detected{Colors.END}] {display_name} (@{account_id}): {guid}"
                print(log_msg)
                
                deleted_post_info = cached_posts_map.get(guid, {})
                
                deleted_post_info['title'] = Config.NOTIF_POST_DELETED_TITLE.format(title=deleted_post_info.get('title', Config.STATUS_TITLE_UNKNOWN))
                deleted_post_info['description_text'] = Config.NOTIF_POST_DELETED_DESC.format(desc=deleted_post_info.get('description_text', Config.STATUS_BODY_UNKNOWN))
                deleted_post_info['link'] = deleted_post_info.get('link', '') 
                
                reason = "Reason: GUID missing after expanded feed check" if potential_push_out and not is_pushed_out else "Reason: GUID missing from feed"
                write_log(f"Post Deletion Detected ({display_name} @{account_id}): {guid}. {reason}. URL: {deleted_post_info.get('link', 'N/A')}")
                send_post_notification(notification_account_name, deleted_post_info, [], "FF0000", mention_everyone=False)
        
        cache[account_id] = current_posts_map
        return display_name, Config.STATUS_X_MONITORING.format(count=len(current_posts_map))

    except Exception as e:
        account_id_str = f":{account_id}" if account_id else ""
        log_msg = f"[{Colors.RED}X{account_id_str} Error{Colors.END}] {e}"
        print(log_msg)
        write_log(log_msg)
        return f"@{account_id}" if account_id else "X:Error", Config.STATUS_X_ERROR

def main():
    cache = load_cache()
    
    tiktok_live_statuses = {}
    if TIKTOK_TARGET_USERNAMES:
        for username in TIKTOK_TARGET_USERNAMES:
            tiktok_live_statuses[username] = {"status": False, "name": f"@{username}"}
    
    niconico_live_statuses = {}
    if NICONICO_TARGET_USER_IDS:
        for user_id in NICONICO_TARGET_USER_IDS:
            niconico_live_statuses[user_id] = {"status": False, "name": user_id}
    
    youtube_live_statuses = {}
    if YOUTUBE_TARGET_USERNAMES:
        for username in YOUTUBE_TARGET_USERNAMES:
            youtube_live_statuses[username] = {"status": False, "name": f"@{username}"}

    twitch_live_statuses = {}
    if TWITCH_TARGET_USERNAMES:
        for username in TWITCH_TARGET_USERNAMES:
            twitch_live_statuses[username] = {"status": False, "name": f"@{username}"}
    
    openrec_live_statuses = {}
    if OPENREC_TARGET_USERNAMES:
        for username in OPENREC_TARGET_USERNAMES:
            openrec_live_statuses[username] = {"status": False, "name": f"@{username}"}
            
    kick_live_statuses = {}
    if KICK_TARGET_USERNAMES:
        for username in KICK_TARGET_USERNAMES:
            kick_live_statuses[username] = {"status": False, "name": f"@{username}"}
    
    twitcasting_live_statuses = {}
    if TWITCASTING_TARGET_USERNAMES:
        for username in TWITCASTING_TARGET_USERNAMES:
            twitcasting_live_statuses[username] = {"status": False, "name": f"@{username}"}

    x_accounts_status = {}
    if X_TARGET_URLS:
        for url in X_TARGET_URLS:
            account_id = url.split('/user/')[1].split('?')[0]
            x_accounts_status[account_id] = {"name": f"@{account_id}", "status": "OFFLINE", "last_status": "OFFLINE"}

    print(Config.APP_TITLE)
    write_log(Config.LOG_STARTUP)
    
    print(f"TikTok: {', '.join(TIKTOK_TARGET_USERNAMES) if TIKTOK_TARGET_USERNAMES else Config.STATUS_SERVICE_DISABLED}")
    print(f"Nico Live: {', '.join(NICONICO_TARGET_USER_IDS) if NICONICO_TARGET_USER_IDS else Config.STATUS_SERVICE_DISABLED}")
    print(f"YouTube: {', '.join(YOUTUBE_TARGET_USERNAMES) if YOUTUBE_TARGET_USERNAMES else Config.STATUS_SERVICE_DISABLED}")
    print(f"Twitch: {', '.join(TWITCH_TARGET_USERNAMES) if TWITCH_TARGET_USERNAMES else Config.STATUS_SERVICE_DISABLED}")
    print(f"Openrec: {', '.join(OPENREC_TARGET_USERNAMES) if OPENREC_TARGET_USERNAMES else Config.STATUS_SERVICE_DISABLED}")
    print(f"Kick: {', '.join(KICK_TARGET_USERNAMES) if KICK_TARGET_USERNAMES else Config.STATUS_SERVICE_DISABLED}")
    print(f"TwitCasting: {', '.join(TWITCASTING_TARGET_USERNAMES) if TWITCASTING_TARGET_USERNAMES else Config.STATUS_SERVICE_DISABLED}")
    print(f"X (RSSHub): {len(X_TARGET_URLS)} accounts" if X_TARGET_URLS else f"X (RSSHub): {Config.STATUS_SERVICE_DISABLED}")

    print(f"X Check Interval: {X_CHECK_INTERVAL_SECONDS} seconds")
    print(f"Live Check Interval: {LIVE_CHECK_INTERVAL_SECONDS} seconds")
    print(f"Cookie: {COOKIE_FILE_PATH if os.path.exists(COOKIE_FILE_PATH) else 'Not Found'}")
    print("---------------------------------")
    
    last_live_check_time = 0
    last_cache_save_time = time.time()
    
    try:
        while True:
            loop_start_time = time.time()
            
            if loop_start_time - last_live_check_time >= LIVE_CHECK_INTERVAL_SECONDS:
                print(f"\n{Config.CONSOLE_LIVE_CYCLE}")
                last_live_check_time = loop_start_time
                
                if TIKTOK_TARGET_USERNAMES:
                    for username in TIKTOK_TARGET_USERNAMES:
                        new_status, tt_name = check_tiktok_live(username)
                        old_status = tiktok_live_statuses[username]["status"]
                        if tt_name: tiktok_live_statuses[username]["name"] = tt_name
                        
                        if new_status != old_status:
                            notif_name = tiktok_live_statuses[username]["name"]
                            platform = Config.NOTIF_PLATFORM_TIKTOK
                            if new_status:
                                send_live_notification(Config.NOTIF_LIVE_START.format(name=notif_name, platform=platform), SOUND_LIVE_START, url=new_status)
                                if Config.ENABLE_AUTO_RECORDING and platform in Config.RECORDING_TARGET_PLATFORMS: start_recording(platform, username, new_status)
                            else:
                                send_live_notification(Config.NOTIF_LIVE_END.format(name=notif_name, platform=platform), SOUND_LIVE_END)
                                if Config.ENABLE_AUTO_RECORDING and platform in Config.RECORDING_TARGET_PLATFORMS: stop_recording(username)
                        tiktok_live_statuses[username]["status"] = new_status

                if NICONICO_TARGET_USER_IDS:
                    for user_id in NICONICO_TARGET_USER_IDS:
                        new_status, nn_name = check_niconico_live(user_id)
                        old_status = niconico_live_statuses[user_id]["status"]
                        if nn_name: niconico_live_statuses[user_id]["name"] = nn_name

                        if new_status != old_status:
                            notif_name = niconico_live_statuses[user_id]["name"]
                            platform = Config.NOTIF_PLATFORM_NICONICO
                            if new_status:
                                send_live_notification(Config.NOTIF_LIVE_START.format(name=notif_name, platform=platform), SOUND_LIVE_START, url=new_status)
                                if Config.ENABLE_AUTO_RECORDING and platform in Config.RECORDING_TARGET_PLATFORMS: start_recording(platform, user_id, new_status)
                            else:
                                send_live_notification(Config.NOTIF_LIVE_END.format(name=notif_name, platform=platform), SOUND_LIVE_END)
                                if Config.ENABLE_AUTO_RECORDING and platform in Config.RECORDING_TARGET_PLATFORMS: stop_recording(user_id)
                        niconico_live_statuses[user_id]["status"] = new_status

                if YOUTUBE_TARGET_USERNAMES:
                    for username in YOUTUBE_TARGET_USERNAMES:
                        new_status, yt_name = check_youtube_live(username)
                        old_status = youtube_live_statuses[username]["status"]
                        if yt_name: youtube_live_statuses[username]["name"] = yt_name
                        
                        if new_status != old_status:
                            notif_name = youtube_live_statuses[username]["name"]
                            platform = Config.NOTIF_PLATFORM_YOUTUBE
                            if new_status:
                                send_live_notification(Config.NOTIF_LIVE_START.format(name=notif_name, platform=platform), SOUND_LIVE_START, url=new_status)
                                if Config.ENABLE_AUTO_RECORDING and platform in Config.RECORDING_TARGET_PLATFORMS: start_recording(platform, username, new_status)
                            else:
                                send_live_notification(Config.NOTIF_LIVE_END.format(name=notif_name, platform=platform), SOUND_LIVE_END)
                                if Config.ENABLE_AUTO_RECORDING and platform in Config.RECORDING_TARGET_PLATFORMS: stop_recording(username)
                            youtube_live_statuses[username]["status"] = new_status
                
                if TWITCH_TARGET_USERNAMES:
                    for username in TWITCH_TARGET_USERNAMES:
                        new_status, twitch_name = check_twitch_live(username)
                        old_status = twitch_live_statuses[username]["status"]
                        if twitch_name: twitch_live_statuses[username]["name"] = twitch_name
                        
                        if new_status != old_status:
                            notif_name = twitch_live_statuses[username]["name"]
                            platform = Config.NOTIF_PLATFORM_TWITCH
                            if new_status:
                                send_live_notification(Config.NOTIF_LIVE_START.format(name=notif_name, platform=platform), SOUND_LIVE_START, url=new_status)
                                if Config.ENABLE_AUTO_RECORDING and platform in Config.RECORDING_TARGET_PLATFORMS: start_recording(platform, username, new_status)
                            else:
                                send_live_notification(Config.NOTIF_LIVE_END.format(name=notif_name, platform=platform), SOUND_LIVE_END)
                                if Config.ENABLE_AUTO_RECORDING and platform in Config.RECORDING_TARGET_PLATFORMS: stop_recording(username)
                            twitch_live_statuses[username]["status"] = new_status

                if OPENREC_TARGET_USERNAMES:
                    for username in OPENREC_TARGET_USERNAMES:
                        new_status, openrec_name = check_openrec_live(username)
                        old_status = openrec_live_statuses[username]["status"]
                        if openrec_name: openrec_live_statuses[username]["name"] = openrec_name
                        
                        if new_status != old_status:
                            notif_name = openrec_live_statuses[username]["name"]
                            platform = Config.NOTIF_PLATFORM_OPENREC
                            if new_status:
                                send_live_notification(Config.NOTIF_LIVE_START.format(name=notif_name, platform=platform), SOUND_LIVE_START, url=new_status)
                                if Config.ENABLE_AUTO_RECORDING and platform in Config.RECORDING_TARGET_PLATFORMS: start_recording(platform, username, new_status)
                            else:
                                send_live_notification(Config.NOTIF_LIVE_END.format(name=notif_name, platform=platform), SOUND_LIVE_END)
                                if Config.ENABLE_AUTO_RECORDING and platform in Config.RECORDING_TARGET_PLATFORMS: stop_recording(username)
                            openrec_live_statuses[username]["status"] = new_status

                if KICK_TARGET_USERNAMES:
                    for username in KICK_TARGET_USERNAMES:
                        new_status, kick_name = check_kick_live(username)
                        old_status = kick_live_statuses[username]["status"]
                        if kick_name: kick_live_statuses[username]["name"] = kick_name
                        
                        if new_status != old_status:
                            notif_name = kick_live_statuses[username]["name"]
                            platform = Config.NOTIF_PLATFORM_KICK
                            if new_status:
                                send_live_notification(Config.NOTIF_LIVE_START.format(name=notif_name, platform=platform), SOUND_LIVE_START, url=new_status)
                                if Config.ENABLE_AUTO_RECORDING and platform in Config.RECORDING_TARGET_PLATFORMS: start_recording(platform, username, new_status)
                            else:
                                send_live_notification(Config.NOTIF_LIVE_END.format(name=notif_name, platform=platform), SOUND_LIVE_END)
                                if Config.ENABLE_AUTO_RECORDING and platform in Config.RECORDING_TARGET_PLATFORMS: stop_recording(username)
                            kick_live_statuses[username]["status"] = new_status
                
                if TWITCASTING_TARGET_USERNAMES:
                    for username in TWITCASTING_TARGET_USERNAMES:
                        new_status, tc_name = check_twitcasting_live(username)
                        old_status = twitcasting_live_statuses[username]["status"]
                        if tc_name: twitcasting_live_statuses[username]["name"] = tc_name
                        
                        if new_status != old_status:
                            notif_name = twitcasting_live_statuses[username]["name"]
                            platform = Config.NOTIF_PLATFORM_TWITCASTING
                            if new_status:
                                send_live_notification(Config.NOTIF_LIVE_START.format(name=notif_name, platform=platform), SOUND_LIVE_START, url=new_status)
                                if Config.ENABLE_AUTO_RECORDING and platform in Config.RECORDING_TARGET_PLATFORMS: start_recording(platform, username, new_status)
                            else:
                                send_live_notification(Config.NOTIF_LIVE_END.format(name=notif_name, platform=platform), SOUND_LIVE_END)
                                if Config.ENABLE_AUTO_RECORDING and platform in Config.RECORDING_TARGET_PLATFORMS: stop_recording(username)
                            twitcasting_live_statuses[username]["status"] = new_status

            is_any_streamer_live = False
            if any(s["status"] for s in tiktok_live_statuses.values()): is_any_streamer_live = True
            if not is_any_streamer_live and any(s["status"] for s in niconico_live_statuses.values()): is_any_streamer_live = True
            if not is_any_streamer_live and any(s["status"] for s in youtube_live_statuses.values()): is_any_streamer_live = True
            if not is_any_streamer_live and any(s["status"] for s in twitch_live_statuses.values()): is_any_streamer_live = True
            if not is_any_streamer_live and any(s["status"] for s in openrec_live_statuses.values()): is_any_streamer_live = True
            if not is_any_streamer_live and any(s["status"] for s in kick_live_statuses.values()): is_any_streamer_live = True
            if not is_any_streamer_live and any(s["status"] for s in twitcasting_live_statuses.values()): is_any_streamer_live = True

            if X_TARGET_URLS:
                print(f"\n{Config.CONSOLE_X_CYCLE}")

                for url in X_TARGET_URLS:
                    account_id = url.split('/user/')[1].split('?')[0]
                    
                    name, status_str = process_x_feed(url, cache, is_any_streamer_live) 
                    
                    if status_str == Config.STATUS_X_PAUSED and x_accounts_status[account_id]["last_status"] != Config.STATUS_X_PAUSED:
                        log_msg = Config.LOG_X_PAUSE.format(name=name, account_id=account_id)
                        print(log_msg)
                        write_log(log_msg)
                    
                    x_accounts_status[account_id]["name"] = name
                    x_accounts_status[account_id]["status"] = status_str
                    x_accounts_status[account_id]["last_status"] = status_str

            if loop_start_time - last_cache_save_time >= LIVE_CHECK_INTERVAL_SECONDS:
                save_cache(cache)
                last_cache_save_time = loop_start_time
            
            os.system('cls' if os.name == 'nt' else 'clear')
            print(Config.APP_TITLE)
            
            if TIKTOK_TARGET_USERNAMES:
                for username, info in tiktok_live_statuses.items():
                    tiktok_formatted_name = f"{info['name']} (@{username})"
                    if info["status"]:
                        recording_status = ""
                        platform_name = Config.NOTIF_PLATFORM_TIKTOK
                        if (Config.ENABLE_AUTO_RECORDING and 
                            platform_name in Config.RECORDING_TARGET_PLATFORMS and 
                            username in recording_processes):
                            recording_status = f" ({Colors.RED}RECORDING{Colors.END})"
                        print(f"{Config.CONSOLE_LIVE_PREFIX} TikTok: {tiktok_formatted_name}{recording_status}")
                    else:
                        print(f"{Config.CONSOLE_OFF_PREFIX} TikTok: {tiktok_formatted_name}")

            if NICONICO_TARGET_USER_IDS:
                for user_id, info in niconico_live_statuses.items():
                    niconico_formatted_name = f"{info['name']} (ID: {user_id})"
                    if info["status"]:
                        recording_status = ""
                        platform_name = Config.NOTIF_PLATFORM_NICONICO
                        if (Config.ENABLE_AUTO_RECORDING and 
                            platform_name in Config.RECORDING_TARGET_PLATFORMS and 
                            user_id in recording_processes):
                            recording_status = f" ({Colors.RED}RECORDING{Colors.END})"
                        print(f"{Config.CONSOLE_LIVE_PREFIX} Nico Live: {niconico_formatted_name}{recording_status}")
                    else:
                        print(f"{Config.CONSOLE_OFF_PREFIX} Nico Live: {niconico_formatted_name}")
            
            if YOUTUBE_TARGET_USERNAMES:
                for username, info in youtube_live_statuses.items():
                    yt_formatted_name = f"{info['name']} (@{username})"
                    if info["status"]:
                        recording_status = ""
                        platform_name = Config.NOTIF_PLATFORM_YOUTUBE
                        if (Config.ENABLE_AUTO_RECORDING and 
                            platform_name in Config.RECORDING_TARGET_PLATFORMS and 
                            username in recording_processes):
                            recording_status = f" ({Colors.RED}RECORDING{Colors.END})"
                        print(f"{Config.CONSOLE_LIVE_PREFIX} YouTube: {yt_formatted_name}{recording_status}")
                    else:
                        print(f"{Config.CONSOLE_OFF_PREFIX} YouTube: {yt_formatted_name}")
            
            if TWITCH_TARGET_USERNAMES:
                for username, info in twitch_live_statuses.items():
                    twitch_formatted_name = f"{info['name']} (@{username})"
                    if info["status"]:
                        recording_status = ""
                        platform_name = Config.NOTIF_PLATFORM_TWITCH
                        if (Config.ENABLE_AUTO_RECORDING and 
                            platform_name in Config.RECORDING_TARGET_PLATFORMS and 
                            username in recording_processes):
                            recording_status = f" ({Colors.RED}RECORDING{Colors.END})"
                        print(f"{Config.CONSOLE_LIVE_PREFIX} Twitch: {twitch_formatted_name}{recording_status}")
                    else:
                        print(f"{Config.CONSOLE_OFF_PREFIX} Twitch: {twitch_formatted_name}")

            if OPENREC_TARGET_USERNAMES:
                for username, info in openrec_live_statuses.items():
                    openrec_formatted_name = f"{info['name']} (@{username})"
                    if info["status"]:
                        recording_status = ""
                        platform_name = Config.NOTIF_PLATFORM_OPENREC
                        if (Config.ENABLE_AUTO_RECORDING and 
                            platform_name in Config.RECORDING_TARGET_PLATFORMS and 
                            username in recording_processes):
                            recording_status = f" ({Colors.RED}RECORDING{Colors.END})"
                        print(f"{Config.CONSOLE_LIVE_PREFIX} Openrec: {openrec_formatted_name}{recording_status}")
                    else:
                        print(f"{Config.CONSOLE_OFF_PREFIX} Openrec: {openrec_formatted_name}")

            if KICK_TARGET_USERNAMES:
                for username, info in kick_live_statuses.items():
                    kick_formatted_name = f"{info['name']} (@{username})"
                    if info["status"]:
                        recording_status = ""
                        platform_name = Config.NOTIF_PLATFORM_KICK
                        if (Config.ENABLE_AUTO_RECORDING and 
                            platform_name in Config.RECORDING_TARGET_PLATFORMS and 
                            username in recording_processes):
                            recording_status = f" ({Colors.RED}RECORDING{Colors.END})"
                        print(f"{Config.CONSOLE_LIVE_PREFIX} Kick: {kick_formatted_name}{recording_status}")
                    else:
                        print(f"{Config.CONSOLE_OFF_PREFIX} Kick: {kick_formatted_name}")
            
            if TWITCASTING_TARGET_USERNAMES:
                for username, info in twitcasting_live_statuses.items():
                    twitcasting_formatted_name = f"{info['name']} (@{username})"
                    if info["status"]:
                        recording_status = ""
                        platform_name = Config.NOTIF_PLATFORM_TWITCASTING
                        if (Config.ENABLE_AUTO_RECORDING and 
                            platform_name in Config.RECORDING_TARGET_PLATFORMS and 
                            username in recording_processes):
                            recording_status = f" ({Colors.RED}RECORDING{Colors.END})"
                        print(f"{Config.CONSOLE_LIVE_PREFIX} TwitCasting: {twitcasting_formatted_name}{recording_status}")
                    else:
                        print(f"{Config.CONSOLE_OFF_PREFIX} TwitCasting: {twitcasting_formatted_name}")

            if X_TARGET_URLS:
                print("---------------------------------")
                for account_id, info in x_accounts_status.items():
                    status_color_prefix = Config.CONSOLE_RSS_PAUSED_PREFIX if "Paused" in info['status'] else Config.CONSOLE_RSS_PREFIX
                    print(f"{status_color_prefix} {info['name']} (@{account_id}) ({info['status']})")

            print(Config.CONSOLE_FOOTER.format(
                gray=Colors.GRAY,
                time_str=time.strftime('%Y-%m-%d %H:%M:%S'),
                x_interval=X_CHECK_INTERVAL_SECONDS,
                live_interval=LIVE_CHECK_INTERVAL_SECONDS,
                end=Colors.END
            ))
            
            processing_time = time.time() - loop_start_time
            sleep_time = X_CHECK_INTERVAL_SECONDS - processing_time
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print(Config.CONSOLE_SHUTDOWN)
        
        if Config.ENABLE_AUTO_RECORDING:
            print("Stopping all active recordings...")
            active_recordings = list(recording_processes.keys())
            for identifier in active_recordings:
                stop_recording(identifier)
        
        save_cache(cache)
        print(Config.CONSOLE_CACHE_SAVED)
        write_log(Config.LOG_SHUTDOWN)

if __name__ == "__main__":
    main()
