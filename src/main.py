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

    APP_TITLE = "--- Oshi-tracker ---"
    LOG_STARTUP = "--- トラッカー 起動 ---"
    LOG_SHUTDOWN = "--- トラッカー 正常終了 ---"
    CONSOLE_SHUTDOWN = "\n--- システムを終了します ---"
    CONSOLE_CACHE_SAVED = "キャッシュを保存しました。"
    
    CONSOLE_LIVE_CYCLE = f"[{Colors.GRAY}--- Live 監視サイクル ---{Colors.END}]"
    CONSOLE_X_CYCLE = f"[{Colors.GRAY}--- X (RSSHub) 監視サイクル ---{Colors.END}]"
    CONSOLE_FOOTER = "\n{gray}({time_str} @ X:{x_interval}s / Live:{live_interval}s / Ctrl+Cで終了){end}"
    
    CONSOLE_LIVE_PREFIX = f"[{Colors.GREEN}● LIVE{Colors.END}]"
    CONSOLE_OFF_PREFIX = f"[{Colors.RED}■ OFF{Colors.END}]"
    CONSOLE_RSS_PREFIX = f"[{Colors.BLUE}● RSS{Colors.END}]"
    CONSOLE_RSS_PAUSED_PREFIX = f"[{Colors.GRAY}● RSS{Colors.END}]"

    STATUS_SERVICE_DISABLED = "(無効)"
    STATUS_X_PAUSED = "配信中 (停止)"
    STATUS_X_MONITORING = "監視中 ({count}件)"
    STATUS_X_ERROR = "エラー"
    
    STATUS_TITLE_UNKNOWN = "タイトル不明"
    STATUS_BODY_UNKNOWN = "本文不明"

    NOTIF_LIVE_START = "@everyone\n@everyone\n{name} の{platform}配信が始まった！！！！！"
    NOTIF_LIVE_END = "({name} の{platform}配信が終わった。)"
    
    NOTIF_PLATFORM_TIKTOK = "TikTok"
    NOTIF_PLATFORM_NICONICO = "ニコ生"
    NOTIF_PLATFORM_YOUTUBE = "YouTube"
    NOTIF_PLATFORM_TWITCH = "Twitch"
    NOTIF_PLATFORM_OPENREC = "Openrec"
    NOTIF_PLATFORM_KICK = "Kick"

    NOTIF_POST_DELETED_TITLE = "【削除検知】{title}"
    NOTIF_POST_DELETED_DESC = "このPostは削除されたか、非公開になりました。\n\n**▼ 削除前の本文 ▼**\n{desc}"
    
    LOG_X_PAUSE = "-> {name} (@{account_id}) の監視を一時停止 (いずれかの配信中のため)"

TIKTOK_TARGET_USERNAMES = ["neymarjr"]
NICONICO_TARGET_USER_IDS = ["131666408"]
YOUTUBE_TARGET_USERNAMES = ["MrBeast"]
TWITCH_TARGET_USERNAMES = ["ninja"]
OPENREC_TARGET_USERNAMES = ["warabarin"]
KICK_TARGET_USERNAMES = ["adinross"]

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

niconico_headers = {"X-Frontend-Id": "6"}
browser_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9"
}

pygame.mixer.init()
http_session = requests.Session()
http_session.headers.update(browser_headers)

def write_log(message, debug=False):
    if debug and not Config.DEBUG_LOGGING:
        return
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except Exception as e:
        print(f"[{Colors.RED}ログ書き込みエラー{Colors.END}] {e}")

def play_sound(file_path):
    if file_path and os.path.exists(file_path):
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
        except Exception as e:
            log_msg = f"[{Colors.RED}音再生エラー{Colors.END}] {e}"
            print(log_msg)
            write_log(log_msg)
    elif file_path:
        log_msg = f"[{Colors.RED}音声ファイルが見つかりませんでした{Colors.END}] {file_path}"
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
        log_msg = f"[{Colors.RED}キャッシュロードエラー{Colors.END}] {e}"
        print(log_msg)
        write_log(log_msg)
        return {}

def save_cache(cache):
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4)
    except Exception as e:
        log_msg = f"[{Colors.RED}キャッシュ保存エラー{Colors.END}] {e}"
        print(log_msg)
        write_log(log_msg)

def download_media(url, is_video=False):
    downloaded_files = []
    
    if is_video:
        print(f"-> yt-dlpでDL: {url}")
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

            print(f"-> yt-dlp成功: {downloaded_files}")
            
        except subprocess.CalledProcessError as e:
            log_msg = f"[{Colors.RED}yt-dlpエラー{Colors.END}] {e.stderr}"
            print(log_msg)
            write_log(log_msg)
        except FileNotFoundError:
             log_msg = f"[{Colors.RED}yt-dlpエラー{Colors.END}] yt-dlpがインストールされていません。"
             print(log_msg)
             write_log(log_msg)
        except Exception as e:
            log_msg = f"[{Colors.RED}yt-dlp汎用エラー{Colors.END}] {e}"
            print(log_msg)
            write_log(log_msg)
            
    else: 
        print(f"-> 画像DL: {url}")
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
            print(f"-> ダウンロード成功: {filepath}")
            
        except Exception as e:
            log_msg = f"[{Colors.RED}ダウンロードエラー{Colors.END}] {e}"
            print(log_msg)
            write_log(log_msg)
            
    return downloaded_files

def send_live_notification(message, sound_file, url=None):
    print(f"!!! [{Colors.GREEN}{message}{Colors.END}] !!!")

    notification_message = message
    if url and isinstance(url, str) and url.startswith("http"):
        print(f"-> LiveURL: {url}")
        notification_message = f"{message}\n{url}"

    write_log(f"ライブ通知: {notification_message}")
    play_sound(sound_file)
    
    if DISCORD_WEBHOOK_URL:
        try:
            http_session.post(DISCORD_WEBHOOK_URL, json={"content": notification_message}, timeout=REQUEST_TIMEOUT_SECONDS)
        except Exception as e:
            log_msg = f"[{Colors.RED}Webhookエラー{Colors.END}] {e}"
            print(log_msg)
            write_log(log_msg)

def send_post_notification(account_name, post_info, files_to_attach, color_hex, mention_everyone=False):
    print(f"-> Discord通知送信: {account_name} - {post_info.get('title', 'N/A')}")
    play_sound(SOUND_MESSAGE_DETECTED)
    
    embed = {
        "title": post_info.get('title', 'タイトルなし'),
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
            log_msg = f"[{Colors.RED}日付parseエラー{Colors.END}] {e} - {post_info['pubDate']}"
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
        log_msg = f"[{Colors.RED}Webhookエラー{Colors.END}] {e}"
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
                    log_msg = f"[{Colors.RED}ファイル削除エラー{Colors.END}] {e}"
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

def check_tiktok_live(username):
    url = f"https://www.tiktok.com/@{username}"
    write_log(f"[TikTok DEBUG] @{username}: チェック開始", debug=True)
    
    try:
        response = cffi_requests.get(url, headers=browser_headers, impersonate="chrome110", timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        html_content = response.text
        write_log(f"[TikTok DEBUG] @{username}: HTML取得成功 (ステータス {response.status_code}, {len(html_content)} bytes)。", debug=True)

        match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>', html_content)
        if not match:
            log_msg = f"[{Colors.RED}TikTokエラー{Colors.END}] @{username}: データ(REHYDRATION)が見つかりません。"
            print(log_msg)
            write_log(log_msg)
            return False, None
        
        write_log(f"[TikTok DEBUG] @{username}: JSON-LD scriptを発見。", debug=True)
        
        try:
            data = json.loads(match.group(1))
            user_info = data.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {}).get("userInfo", {}).get("user", {})
            
            display_name = user_info.get("nickname")
            live_url = False
            
            if user_info.get("roomId") and user_info.get("roomId") != "0":
                live_url = f"https://www.tiktok.com/@{username}/live"
                write_log(f"[TikTok DEBUG] @{username}: 'roomId' ({user_info.get('roomId')}) を発見。ライブ中と判断。", debug=True)

            write_log(f"[TikTok DEBUG] @{username}: チェック完了。 live_url={live_url}, display_name='{display_name}'", debug=True)
            return live_url, display_name
            
        except json.JSONDecodeError:
            log_msg = f"[{Colors.RED}TikTokエラー{Colors.END}] @{username}: JSON解析に失敗しました。"
            print(log_msg)
            write_log(log_msg)
            return False, None

    except Exception as e:
        log_msg = f"[{Colors.RED}TikTokエラー{Colors.END}] {e}"
        print(log_msg)
        write_log(log_msg)
        return False, None

def check_niconico_live(user_id):
    niconico_api_url = (
        f"https://api.feed.nicovideo.jp/v1/activities/actors/users/"
        f"{user_id}/publish"
        f"?context=user_timeline_{user_id}"
    )
    write_log(f"[Niconico DEBUG] ID:{user_id}: チェック開始", debug=True)
    try:
        response = http_session.get(niconico_api_url, headers=niconico_headers, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        write_log(f"[Niconico DEBUG] ID:{user_id}: API取得成功。", debug=True)

        display_name = None
        live_url = False

        if "activities" in data and len(data["activities"]) > 0:
            latest_activity = data["activities"][0]
            display_name = latest_activity.get("actor", {}).get("name", None)
            
            latest_activity_label = latest_activity.get("label", {}).get("text", "")
            if latest_activity_label == "LIVE":
                live_url_path = latest_activity.get("content", {}).get("url", "")
                live_url = live_url_path if live_url_path else True
                write_log(f"[Niconico DEBUG] ID:{user_id}: 'LIVE' ラベルを発見。ライブ中と判断。", debug=True)
        
        write_log(f"[Niconico DEBUG] ID:{user_id}: チェック完了。 live_url={live_url}, display_name='{display_name}'", debug=True)
        return live_url, display_name

    except Exception as e:
        log_msg = f"[{Colors.RED}ニコ生エラー{Colors.END}] {e}"
        print(log_msg)
        write_log(log_msg)
        return False, None

def check_youtube_live(username):
    url = f"https://www.youtube.com/@{username}"
    write_log(f"[YouTube DEBUG] @{username}: チェック開始", debug=True)
    try:
        response = cffi_requests.get(url, headers=browser_headers, impersonate="chrome110", timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        html_content = response.text
        write_log(f"[YouTube DEBUG] @{username}: HTML取得成功 (ステータス {response.status_code}, {len(html_content)} bytes)。", debug=True)

        match = re.search(r"var ytInitialData = ({.*?});</script>", html_content)
        if not match:
            log_msg = f"[{Colors.RED}YouTubeエラー{Colors.END}] @{username}: ytInitialDataが見つかりません。"
            print(log_msg)
            write_log(log_msg)
            return False, None
        
        write_log(f"[YouTube DEBUG] @{username}: 'ytInitialData' を発見。", debug=True)
            
        try:
            data = json.loads(match.group(1))
            display_name = None
            live_url = False
            
            try:
                display_name = data['metadata']['channelMetadataRenderer']['title']
                write_log(f"[YouTube DEBUG] @{username}: 表示名 '{display_name}' を発見。", debug=True)
            except KeyError:
                display_name = username
            
            try:
                header_vm = data['header']['pageHeaderRenderer']['content']['pageHeaderViewModel']
                avatar = header_vm['image']['decoratedAvatarViewModel']
                
                if 'liveData' in avatar:
                    video_id = avatar['rendererContext']['commandContext']['onTap']['innertubeCommand']['watchEndpoint']['videoId']
                    live_url = f"https://www.youtube.com/watch?v={video_id}"
                    write_log(f"[YouTube DEBUG] @{username}: 'liveData' を発見。ライブ中と判断。", debug=True)
            except KeyError:
                pass

            write_log(f"[YouTube DEBUG] @{username}: チェック完了。 live_url={live_url}, display_name='{display_name}'", debug=True)
            return live_url, display_name

        except json.JSONDecodeError:
            log_msg = f"[{Colors.RED}YouTubeエラー{Colors.END}] @{username}: JSON解析に失敗しました。"
            print(log_msg)
            write_log(log_msg)
            return False, None
            
    except Exception as e:
        log_msg = f"[{Colors.RED}YouTubeエラー{Colors.END}] @{username}: ページ取得に失敗しました。 {e}"
        print(log_msg)
        write_log(log_msg)
        return False, None

def check_twitch_live(username):
    url = f"https://www.twitch.tv/{username}"
    live_url = False
    display_name = f"@{username}"
    write_log(f"[Twitch DEBUG] @{username}: チェック開始", debug=True)
    
    try:
        response = cffi_requests.get(url, headers=browser_headers, impersonate="chrome110", timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        html_content = response.text
        write_log(f"[Twitch DEBUG] @{username}: HTML取得成功 (ステータス {response.status_code}, {len(html_content)} bytes)。", debug=True)

        match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html_content, re.DOTALL)
        if not match:
            log_msg = f"[{Colors.RED}Twitchエラー{Colors.END}] @{username}: JSON-LD scriptが見つかりません。"
            print(log_msg)
            write_log(log_msg)
            return False, display_name

        write_log(f"[Twitch DEBUG] @{username}: JSON-LD scriptブロックを発見。", debug=True)
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
                                write_log(f"[Twitch DEBUG] @{username}: 表示名 '{display_name}' を発見。", debug=True)
                            
                            publication = item.get("publication")
                            if not found_live and isinstance(publication, dict):
                                if publication.get("@type") == "BroadcastEvent" and publication.get("isLiveBroadcast") == True:
                                    live_url = url
                                    found_live = True
                                    write_log(f"[Twitch DEBUG] @{username}: 'isLiveBroadcast: true' を発見。ライブ中と判断。", debug=True)
            
            write_log(f"[Twitch DEBUG] @{username}: チェック完了。 live_url={live_url}, display_name='{display_name}'", debug=True)
            return live_url, display_name

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            log_msg = f"[{Colors.RED}Twitchエラー{Colors.END}] @{username}: JSON解析に失敗しました。 {e}"
            print(log_msg)
            write_log(log_msg)
            return False, display_name

    except Exception as e:
        log_msg = f"[{Colors.RED}Twitchエラー{Colors.END}] @{username}: ページ取得に失敗しました。 {e}"
        print(log_msg)
        write_log(log_msg)
        return False, display_name

def check_openrec_live(username):
    url = f"https://public.openrec.tv/external/api/v5/channels/{username}"
    live_url = False
    display_name = f"@{username}"
    write_log(f"[Openrec DEBUG] @{username}: チェック開始", debug=True)
    
    try:
        response = http_session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        write_log(f"[Openrec DEBUG] @{username}: API取得成功。", debug=True)
        
        display_name = data.get("nickname", username)
        
        onair_movies = data.get("onair_broadcast_movies", [])
        if onair_movies and isinstance(onair_movies, list) and len(onair_movies) > 0:
            live_id = onair_movies[0].get("id")
            if live_id:
                live_url = f"https://www.openrec.tv/live/{live_id}"
                write_log(f"[Openrec DEBUG] @{username}: 'onair_broadcast_movies' を発見。ライブ中と判断。", debug=True)
        
        write_log(f"[Openrec DEBUG] @{username}: チェック完了。 live_url={live_url}, display_name='{display_name}'", debug=True)
        return live_url, display_name

    except Exception as e:
        log_msg = f"[{Colors.RED}Openrecエラー{Colors.END}] @{username}: API取得に失敗しました。 {e}"
        print(log_msg)
        write_log(log_msg)
        return False, display_name

def check_kick_live(username):
    url = f"https://kick.com/{username}"
    live_url = False
    display_name = f"@{username}"
    
    write_log(f"[Kick DEBUG] @{username}: チェック開始...", debug=True)
    
    try:
        response = cffi_requests.get(url, headers=browser_headers, impersonate="chrome110", timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        html_content = response.text

        write_log(f"[Kick DEBUG] @{username}: HTML取得成功 (ステータス {response.status_code}, {len(html_content)} bytes)。", debug=True)

        matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html_content, re.DOTALL)
        if not matches:
            log_msg = f"[{Colors.RED}Kickエラー{Colors.END}] @{username}: JSON-LD scriptが見つかりません。"
            print(log_msg)
            write_log(log_msg)
            return False, display_name

        write_log(f"[Kick DEBUG] @{username}: {len(matches)}件のJSON-LD scriptブロックを発見。", debug=True)
        
        found_live = False
        found_name = False

        for i, match_str in enumerate(matches):
            if found_live and found_name:
                break 

            write_log(f"[Kick DEBUG] @{username}: JSON-LDブロック #{i} を解析中...", debug=True)
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
                            write_log(f"[Kick DEBUG] @{username}: 表示名 (Person) '{display_name}' を発見。", debug=True)
                        elif item_type == "BroadcastEvent" and item.get("@id") == "#active-stream":
                            if "publishedBy" in item and "name" in item["publishedBy"]:
                                display_name = item["publishedBy"]["name"]
                                found_name = True
                                write_log(f"[Kick DEBUG] @{username}: 表示名 (BroadcastEvent) '{display_name}' を発見。", debug=True)
                    
                    if not found_live:
                        if item_type == "BroadcastEvent" and item.get("isLiveBroadcast") == True:
                            live_url = url
                            found_live = True
                            write_log(f"[Kick DEBUG] @{username}: 'isLiveBroadcast: true' (ルート) を発見。ライブ中と判断。", debug=True)
                        elif item_type == "VideoObject" and "publication" in item:
                             if item["publication"].get("@type") == "BroadcastEvent" and item["publication"].get("isLiveBroadcast") == True:
                                live_url = url
                                found_live = True
                                write_log(f"[Kick DEBUG] @{username}: 'isLiveBroadcast: true' (VideoObject) を発見。ライブ中と判断。", debug=True)

            except (json.JSONDecodeError, KeyError, IndexError) as e:
                write_log(f"[Kick DEBUG] @{username}: ブロック #{i} のJSON解析に失敗: {e}", debug=True)
                continue

        write_log(f"[Kick DEBUG] @{username}: チェック完了。 live_url={live_url}, display_name='{display_name}'", debug=True)
        return live_url, display_name

    except Exception as e:
        log_msg = f"[{Colors.RED}Kickエラー{Colors.END}] @{username}: ページ取得に失敗しました。 {e}"
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
            log_msg = f"-> {display_name} (@{account_id}) の初回スキャン完了。{len(current_guids)}件のPostをキャッシュ。 (通知スキップ)"
            print(log_msg)
            write_log(f"初回スキャン ({display_name} @{account_id}): {len(current_guids)}件キャッシュ。通知スキップ。")
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
                log_msg = f"[{Colors.GRAY}Post 浮上検知{Colors.END}] {display_name} (@{account_id}): {guid} (キャッシュの最古Postより古いため、通知をスキップ)"
                print(log_msg)
                write_log(f"Post 浮上検知 ({display_name} @{account_id}): {guid}. 理由: キャッシュの最古Postより古いため通知スキップ. URL: {current_posts_map[guid].get('link', 'N/A')}")

        for guid in real_new_guids:
            post_info = current_posts_map[guid]
            log_msg = f"[{Colors.GREEN}新規Post検知{Colors.END}] {display_name} (@{account_id}): {post_info['title']}"
            print(log_msg)
            write_log(f"新規Post検知 ({display_name} @{account_id}): {post_info['title']}. URL: {post_info.get('link', 'N/A')}")
            
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
                
                log_msg = f"-> 削除候補検知。Limitを{expanded_limit}に増やして再取得 ({account_id})"
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
                log_msg = f"[{Colors.RED}削除確認（再取得）エラー{Colors.END}] {e}"
                print(log_msg)
                write_log(log_msg)

        for guid in deleted_guids:
            notification_account_name = f"{display_name} (@{account_id})"
            
            is_pushed_out = False
            if potential_push_out:
                if guid in expanded_guids:
                    is_pushed_out = True
                else:
                    log_msg = f"-> 拡張フィードにもGUID ({guid}) が見つからないため、削除と判断。"
                    print(log_msg)
                    write_log(log_msg)
            
            if is_pushed_out:
                log_msg = f"[{Colors.GRAY}Post 範囲外{Colors.END}] {display_name} (@{account_id}): {guid} (プッシュアウトと判断)"
                print(log_msg)
                write_log(f"Post 範囲外 ({display_name} @{account_id}): {guid}. 理由: 拡張フィード(limit={len(expanded_guids)})でGUIDが発見されたためプッシュアウトと判断. URL: {cached_posts_map.get(guid, {}).get('link', 'N/A')}")
            else:
                log_msg = f"[{Colors.YELLOW}削除Post検知{Colors.END}] {display_name} (@{account_id}): {guid}"
                print(log_msg)
                
                deleted_post_info = cached_posts_map.get(guid, {})
                
                deleted_post_info['title'] = Config.NOTIF_POST_DELETED_TITLE.format(title=deleted_post_info.get('title', Config.STATUS_TITLE_UNKNOWN))
                deleted_post_info['description_text'] = Config.NOTIF_POST_DELETED_DESC.format(desc=deleted_post_info.get('description_text', Config.STATUS_BODY_UNKNOWN))
                deleted_post_info['link'] = deleted_post_info.get('link', '') 
                
                reason = "拡張フィードで確認したがGUIDが消失" if potential_push_out else "フィードからGUIDが消失"
                write_log(f"削除Post検知 ({display_name} @{account_id}): {guid}. V{reason}. URL: {deleted_post_info.get('link', 'N/A')}")
                send_post_notification(notification_account_name, deleted_post_info, [], "FF0000", mention_everyone=False)
        
        cache[account_id] = current_posts_map
        return display_name, Config.STATUS_X_MONITORING.format(count=len(current_posts_map))

    except Exception as e:
        account_id_str = f":{account_id}" if account_id else ""
        log_msg = f"[{Colors.RED}X{account_id_str}エラー{Colors.END}] {e}"
        print(log_msg)
        write_log(log_msg)
        return f"@{account_id}" if account_id else "X:エラー", Config.STATUS_X_ERROR

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

    x_accounts_status = {}
    if X_TARGET_URLS:
        for url in X_TARGET_URLS:
            account_id = url.split('/user/')[1].split('?')[0]
            x_accounts_status[account_id] = {"name": f"@{account_id}", "status": "OFFLINE", "last_status": "OFFLINE"}

    print(Config.APP_TITLE)
    write_log(Config.LOG_STARTUP)
    
    print(f"TikTok: {', '.join(TIKTOK_TARGET_USERNAMES) if TIKTOK_TARGET_USERNAMES else Config.STATUS_SERVICE_DISABLED}")
    print(f"ニコ生: {', '.join(NICONICO_TARGET_USER_IDS) if NICONICO_TARGET_USER_IDS else Config.STATUS_SERVICE_DISABLED}")
    print(f"YouTube: {', '.join(YOUTUBE_TARGET_USERNAMES) if YOUTUBE_TARGET_USERNAMES else Config.STATUS_SERVICE_DISABLED}")
    print(f"Twitch: {', '.join(TWITCH_TARGET_USERNAMES) if TWITCH_TARGET_USERNAMES else Config.STATUS_SERVICE_DISABLED}")
    print(f"Openrec: {', '.join(OPENREC_TARGET_USERNAMES) if OPENREC_TARGET_USERNAMES else Config.STATUS_SERVICE_DISABLED}")
    print(f"Kick: {', '.join(KICK_TARGET_USERNAMES) if KICK_TARGET_USERNAMES else Config.STATUS_SERVICE_DISABLED}")
    print(f"X (RSSHub): {len(X_TARGET_URLS)} アカウント" if X_TARGET_URLS else f"X (RSSHub): {Config.STATUS_SERVICE_DISABLED}")

    print(f"X チェック間隔: {X_CHECK_INTERVAL_SECONDS} 秒")
    print(f"Live チェック間隔: {LIVE_CHECK_INTERVAL_SECONDS} 秒")
    print(f"Cookie: {COOKIE_FILE_PATH if os.path.exists(COOKIE_FILE_PATH) else '未検出'}")
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
                        new_tiktok_status, tt_name = check_tiktok_live(username)
                        old_tiktok_status = tiktok_live_statuses[username]["status"]
                        if tt_name:
                            tiktok_live_statuses[username]["name"] = tt_name
                        
                        if new_tiktok_status != old_tiktok_status:
                            notif_name = tiktok_live_statuses[username]["name"]
                            if new_tiktok_status:
                                send_live_notification(Config.NOTIF_LIVE_START.format(name=notif_name, platform=Config.NOTIF_PLATFORM_TIKTOK), SOUND_LIVE_START, url=new_tiktok_status)
                            else:
                                send_live_notification(Config.NOTIF_LIVE_END.format(name=notif_name, platform=Config.NOTIF_PLATFORM_TIKTOK), SOUND_LIVE_END)
                        tiktok_live_statuses[username]["status"] = new_tiktok_status

                if NICONICO_TARGET_USER_IDS:
                    for user_id in NICONICO_TARGET_USER_IDS:
                        new_niconico_status, nn_name = check_niconico_live(user_id)
                        old_niconico_status = niconico_live_statuses[user_id]["status"]
                        if nn_name:
                            niconico_live_statuses[user_id]["name"] = nn_name

                        if new_niconico_status != old_niconico_status:
                            notif_name = niconico_live_statuses[user_id]["name"]
                            if new_niconico_status:
                                send_live_notification(Config.NOTIF_LIVE_START.format(name=notif_name, platform=Config.NOTIF_PLATFORM_NICONICO), SOUND_LIVE_START, url=new_niconico_status)
                            else:
                                send_live_notification(Config.NOTIF_LIVE_END.format(name=notif_name, platform=Config.NOTIF_PLATFORM_NICONICO), SOUND_LIVE_END)
                        niconico_live_statuses[user_id]["status"] = new_niconico_status

                if YOUTUBE_TARGET_USERNAMES:
                    for username in YOUTUBE_TARGET_USERNAMES:
                        new_youtube_status, yt_name = check_youtube_live(username)
                        old_youtube_status = youtube_live_statuses[username]["status"]
                        
                        if yt_name:
                            youtube_live_statuses[username]["name"] = yt_name
                        
                        if new_youtube_status != old_youtube_status:
                            notif_name = youtube_live_statuses[username]["name"]
                            if new_youtube_status:
                                send_live_notification(Config.NOTIF_LIVE_START.format(name=notif_name, platform=Config.NOTIF_PLATFORM_YOUTUBE), SOUND_LIVE_START, url=new_youtube_status)
                            else:
                                send_live_notification(Config.NOTIF_LIVE_END.format(name=notif_name, platform=Config.NOTIF_PLATFORM_YOUTUBE), SOUND_LIVE_END)
                            youtube_live_statuses[username]["status"] = new_youtube_status
                
                if TWITCH_TARGET_USERNAMES:
                    for username in TWITCH_TARGET_USERNAMES:
                        new_twitch_status, twitch_name = check_twitch_live(username)
                        old_twitch_status = twitch_live_statuses[username]["status"]
                        
                        if twitch_name:
                            twitch_live_statuses[username]["name"] = twitch_name
                        
                        if new_twitch_status != old_twitch_status:
                            notif_name = twitch_live_statuses[username]["name"]
                            if new_twitch_status:
                                send_live_notification(Config.NOTIF_LIVE_START.format(name=notif_name, platform=Config.NOTIF_PLATFORM_TWITCH), SOUND_LIVE_START, url=new_twitch_status)
                            else:
                                send_live_notification(Config.NOTIF_LIVE_END.format(name=notif_name, platform=Config.NOTIF_PLATFORM_TWITCH), SOUND_LIVE_END)
                            twitch_live_statuses[username]["status"] = new_twitch_status

                if OPENREC_TARGET_USERNAMES:
                    for username in OPENREC_TARGET_USERNAMES:
                        new_openrec_status, openrec_name = check_openrec_live(username)
                        old_openrec_status = openrec_live_statuses[username]["status"]
                        
                        if openrec_name:
                            openrec_live_statuses[username]["name"] = openrec_name
                        
                        if new_openrec_status != old_openrec_status:
                            notif_name = openrec_live_statuses[username]["name"]
                            if new_openrec_status:
                                send_live_notification(Config.NOTIF_LIVE_START.format(name=notif_name, platform=Config.NOTIF_PLATFORM_OPENREC), SOUND_LIVE_START, url=new_openrec_status)
                            else:
                                send_live_notification(Config.NOTIF_LIVE_END.format(name=notif_name, platform=Config.NOTIF_PLATFORM_OPENREC), SOUND_LIVE_END)
                            openrec_live_statuses[username]["status"] = new_openrec_status

                if KICK_TARGET_USERNAMES:
                    for username in KICK_TARGET_USERNAMES:
                        new_kick_status, kick_name = check_kick_live(username)
                        old_kick_status = kick_live_statuses[username]["status"]
                        
                        if kick_name:
                            kick_live_statuses[username]["name"] = kick_name
                        
                        if new_kick_status != old_kick_status:
                            notif_name = kick_live_statuses[username]["name"]
                            if new_kick_status:
                                send_live_notification(Config.NOTIF_LIVE_START.format(name=notif_name, platform=Config.NOTIF_PLATFORM_KICK), SOUND_LIVE_START, url=new_kick_status)
                            else:
                                send_live_notification(Config.NOTIF_LIVE_END.format(name=notif_name, platform=Config.NOTIF_PLATFORM_KICK), SOUND_LIVE_END)
                            kick_live_statuses[username]["status"] = new_kick_status

            is_any_streamer_live = False
            if any(s["status"] for s in tiktok_live_statuses.values()): is_any_streamer_live = True
            if not is_any_streamer_live and any(s["status"] for s in niconico_live_statuses.values()): is_any_streamer_live = True
            if not is_any_streamer_live and any(s["status"] for s in youtube_live_statuses.values()): is_any_streamer_live = True
            if not is_any_streamer_live and any(s["status"] for s in twitch_live_statuses.values()): is_any_streamer_live = True
            if not is_any_streamer_live and any(s["status"] for s in openrec_live_statuses.values()): is_any_streamer_live = True
            if not is_any_streamer_live and any(s["status"] for s in kick_live_statuses.values()): is_any_streamer_live = True

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
                        print(f"{Config.CONSOLE_LIVE_PREFIX} TikTok: {tiktok_formatted_name}")
                    else:
                        print(f"{Config.CONSOLE_OFF_PREFIX} TikTok: {tiktok_formatted_name}")

            if NICONICO_TARGET_USER_IDS:
                for user_id, info in niconico_live_statuses.items():
                    niconico_formatted_name = f"{info['name']} (ID: {user_id})"
                    if info["status"]:
                        print(f"{Config.CONSOLE_LIVE_PREFIX} ニコ生: {niconico_formatted_name}")
                    else:
                        print(f"{Config.CONSOLE_OFF_PREFIX} ニコ生: {niconico_formatted_name}")
            
            if YOUTUBE_TARGET_USERNAMES:
                for username, info in youtube_live_statuses.items():
                    yt_formatted_name = f"{info['name']} (@{username})"
                    if info["status"]:
                        print(f"{Config.CONSOLE_LIVE_PREFIX} YouTube: {yt_formatted_name}")
                    else:
                        print(f"{Config.CONSOLE_OFF_PREFIX} YouTube: {yt_formatted_name}")
            
            if TWITCH_TARGET_USERNAMES:
                for username, info in twitch_live_statuses.items():
                    twitch_formatted_name = f"{info['name']} (@{username})"
                    if info["status"]:
                        print(f"{Config.CONSOLE_LIVE_PREFIX} Twitch: {twitch_formatted_name}")
                    else:
                        print(f"{Config.CONSOLE_OFF_PREFIX} Twitch: {twitch_formatted_name}")

            if OPENREC_TARGET_USERNAMES:
                for username, info in openrec_live_statuses.items():
                    openrec_formatted_name = f"{info['name']} (@{username})"
                    if info["status"]:
                        print(f"{Config.CONSOLE_LIVE_PREFIX} Openrec: {openrec_formatted_name}")
                    else:
                        print(f"{Config.CONSOLE_OFF_PREFIX} Openrec: {openrec_formatted_name}")

            if KICK_TARGET_USERNAMES:
                for username, info in kick_live_statuses.items():
                    kick_formatted_name = f"{info['name']} (@{username})"
                    if info["status"]:
                        print(f"{Config.CONSOLE_LIVE_PREFIX} Kick: {kick_formatted_name}")
                    else:
                        print(f"{Config.CONSOLE_OFF_PREFIX} Kick: {kick_formatted_name}")

            if X_TARGET_URLS:
                print("---------------------------------")
                for account_id, info in x_accounts_status.items():
                    status_color_prefix = Config.CONSOLE_RSS_PAUSED_PREFIX if "停止" in info['status'] else Config.CONSOLE_RSS_PREFIX
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
        save_cache(cache)
        print(Config.CONSOLE_CACHE_SAVED)
        write_log(Config.LOG_SHUTDOWN)

if __name__ == "__main__":
    main()
