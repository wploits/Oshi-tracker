# 🚀 Oshi-tracker (推しトラッカー)

**🇯🇵 [日本語](./README.ja.md)** | **🇺🇸 [English](./README.en.md)**

---

> The "Stream / X tracker" for your "推し活(Oshi-katsu)" !

ようこそ！推しトラッカーへ！

「あーなんか推しの配信とか最新のポストをDiscordに通知してくれるツールがあればいいのになー！！！」
と思ったそこのあなた！！！！
このチュートリアルを使って、貴方の推しがした最新の行動を見逃さないようにしましょう 👀

## ✨ 機能

* 配信の通知をDiscordに飛ばす

* X(旧Twitter)の新しいポスト及び削除されたポストの通知

## 📡 サポートされている配信サイト

* YouTube

* Twitch

* ニコニコ(ニコ生)

* TikTok

* Openrec

* KICK

## 💻 必要なもの

* Windows (10 / 11)

* [Python (3.10以上を推奨)](https://www.python.org/downloads/)

* [Docker Desktop](https://www.docker.com/products/docker-desktop/)

* Discordアカウント (通知を受け取るため)

* X (旧Twitter) アカウント (Cookieを取得するため)

## 🛠️ 導入・設定方法

### 0. ソースコードをダウンロードする

このリポジトリの「Code」ボタンから `Download ZIP` を選択し、フルソースコードをダウンロード・解凍します。
(ここからの話はすべて解凍した`src`フォルダーの中を見ている前提で話します)

### 1. 必要なライブラリをインストールする

`src`フォルダの中にある `requirements.bat` をダブルクリックして実行します。
必要なPythonライブラリ (`requests`, `pygame`, `curl_cffi`, `yt-dlp`) が自動でインストールされます。

### 2. X (Twitter) の設定とRSSHubの起動

Xのポストを監視するには、`RSSHub`という別のツールをDockerで起動する必要があります。

**a. Cookieを取得する**

1. Chromeブラウザで [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) 拡張機能をインストールします。

2. X ( `https://x.com` ) を開き、ログインしていることを確認します。

3. 拡張機能のアイコンをクリックし、`Export` ボタンを押して `cookies.txt` ファイルをダウンロードします。

**b. Oshi-trackerにCookieを設定する**

1. `src/datas/` フォルダを開きます。

2. ダウンロードした `cookies.txt` の中身を**すべてコピー**し、`src/datas/cookies.txt` に**貼り付けて保存**します。（既にある内容は上書きしてください）

**c. RSSHubに `auth_token` を設定する**

1. `src/rsshub/` フォルダにある `docker-compose.yml` をメモ帳などで開きます。

2. `TWITTER_AUTH_TOKEN=` という行を探します。

3. `b.`で使ったダウンロード済みの `cookies.txt` の中から、`auth_token` と書かれている行を探します。

   ```
   .x.com	TRUE	/	TRUE	[数字]	auth_token	[ここに書かれている長い英数字]
   ```

4. この `[ここに書かれている長い英数字]` の部分だけをコピーし、`docker-compose.yml` の `TWITTER_AUTH_TOKEN=` の**後ろに貼り付けて保存**します。

   ```
   # 変更前
   TWITTER_AUTH_TOKEN: 
   # 変更後 (例)
   TWITTER_AUTH_TOKEN: 012345abcdef...
   ```

**d. RSSHubを起動する**

1. **Docker Desktopを起動**しておきます。

2. `src/rsshub/` フォルダのアドレスバーに `cmd` と入力してコマンドプロンプトを開きます。

3. `docker-compose up -d` と入力し、Enterキーを押します。

4. 緑色の `Done` や `started` という文字が出れば成功です。

### 3. Oshi-tracker (main.py) を設定する

`src`フォルダにある `main.py` をメモ帳やVSCodeなどのエディタで開きます。
このファイルの上部にある設定を、あなた用に書き換える必要があります。

**監視したい推しのアカウントを設定してください。**
監視しないプラットフォームは、`[]`（空のリスト）のままにしてください。

```python
# 監視したいTikTokの@ユーザー名（@は不要）
TIKTOK_TARGET_USERNAMES = ["neymarjr"]

# 監視したいニコ生のユーザーID ([https://www.nicovideo.jp/user/XXXX](https://www.nicovideo.jp/user/XXXX) の数字)
NICONICO_TARGET_USER_IDS = ["131666408"]

# 監視したいYouTubeの@ユーザー名（@は不要）
YOUTUBE_TARGET_USERNAMES = ["MrBeast"]

# 監視したいTwitchのユーザー名
TWITCH_TARGET_USERNAMES = ["ninja"]

# 監視したいOpenrecのユーザー名
OPENREC_TARGET_USERNAMES = ["warabarin"]

# 監視したいKickのユーザー名
KICK_TARGET_USERNAMES = ["adinross"]

# 監視したいXのRSSHub URL
X_TARGET_URLS = [
    "http://localhost:1200/twitter/user/elonmusk?limit=20&includeRts=false&includeReplies=false",
    "http://localhost:1200/twitter/user/BillGates?limit=10&includeRts=false&includeReplies=false",
]

# 誰かが配信中の時に監視を「停止」したいXのID (上のURLの "elonmusk" や "BillGates" の部分)
LIVE_PAUSE_X_TARGET_IDS = ["elonmusk"]

# 通知を飛ばしたいDiscordのWebhook URL
DISCORD_WEBHOOK_URL = "[https://discord.com/api/webhooks/1234567890/xxxxxxxxxxxx_YYYYYYYYYYYYYYYYY](https://discord.com/api/webhooks/1234567890/xxxxxxxxxxxx_YYYYYYYYYYYYYYYYY)"
```

#### X (Twitter) URLのパラメータ設定

`X_TARGET_URLS` のURLには、いくつかオプションがあります。

* `limit=10`: 一度にチェックする最新ポストの件数。**10〜20を推奨**します。

* `includeRts=false`: リツイート（リポスト）を通知に含めるか (`true` / `false`)。

* `includeReplies=false`: リプライ（返信）を通知に含めるか (`true` / `false`)。

### 4. トラッカーを起動する

`src`フォルダにある `main.py` をダブルクリック、または `python main.py` で実行します。
コンソールが起動し、設定した全アカウントの監視が開始されます。

## 🔧 詳細設定 (main.py)

`main.py` の中盤にある`Config`クラスや、その他のグローバル変数を変更することで、動作を細かく調整できます。

### サウンドのオン/オフ

通知音を消したい場合は、パスを空（`""`）にしてください。

```python
# 配信開始音
SOUND_LIVE_START = "./sounds/live_start.mp3"
# 配信終了音 (空にすると鳴らない)
SOUND_LIVE_END = ""
# Xのポスト検知音
SOUND_MESSAGE_DETECTED = "./sounds/message_detected.mp3"
```

### 監視間隔の調整

数値を小さくすると検知が早くなりますが、API制限（BAN）のリスクが上がります。

```python
# X (RSSHub) のチェック間隔 (秒)
X_CHECK_INTERVAL_SECONDS = 60.1
# ライブ配信のチェック間隔 (秒)
LIVE_CHECK_INTERVAL_SECONDS = 60
```

### デバッグログ

`datas/tracker_log.txt` に詳細な動作ログを残すかどうか。

```python
class Config:
    DEBUG_LOGGING = True  # Trueで有効, Falseで無効
```

### 通知メッセージの変更

Discordに飛ぶメッセージを変更できます。

```python
class Config:
    # (...省略...)
    NOTIF_LIVE_START = "【速報】{name}が{platform}配信を開始！ @everyone"
    NOTIF_LIVE_END = "({name} の{platform}配信が終わりました)"
    # (...省略...)
```

## 👨‍💻 開発者向け (For Developers)

このツールは、`python-requests`ではTLSフィンガープリント（JA3）によってブロックされるプラットフォーム（YouTube, Twitch, Kick, TikTok）に対応するため、`curl_cffi`ライブラリを使用しています。
これにより、`impersonate="chrome110"`を指定し、TLSハンドシェイクをChromeブラウザに偽装することで、403 (Forbidden) エラーを回避しています。

## 👑 クレジット (Credit)

* **Developer:** \[Your Name or Handle\]

* *(Note: Some code in this tool was written with the assistance of AI.)*

## 📜 ライセンス (License)

This project is licensed under the [MIT License](./LICENSE).
