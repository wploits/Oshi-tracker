# 🚀 Oshi-tracker (推しトラッカー)

**🇯🇵 [日本語](./README.ja.md)** | **🇺🇸 [English](./README.en.md)**

---

> The "Stream / X tracker" for your "推し活(Oshi-katsu)" !

## 📖 はじめに - このツールがやること

ようこそ！推しトラッカーへ！

「あーなんか推しの配信とか最新のポストをDiscordに通知してくれるツールがあればいいのになー！！！」
と思ったそこのあなた！

このツールは、あなたの「推し」の活動を24時間監視し、新しい動きがあった瞬間にあなたのDiscordサーバーへ通知を送る、**全自動「推し活」支援ボット**です。

### ✨ 主な機能
* **ライブ配信の自動通知**
  * 推しが配信を開始・終了した瞬間にDiscordへ通知します。
* **X (旧Twitter) のポスト通知**
  * 新しいポスト（ツイート）を通知します。
* **X (旧Twitter) の削除検知**
  * 推しがポストを削除（または非公開）にした場合、**その内容をDiscordに通知します。**

### 📡 サポートされているプラットフォーム
* **ライブ配信**: YouTube, Twitch, ニコニコ(ニコ生), TikTok, Openrec, KICK, ツイキャス
* **ポスト**: X (旧Twitter)

---

## 💻 必要なもの（インストールガイド）

このツールを動かすには、いくつかの「部品」が必要です。順番に準備しましょう。

### 1. Windows PC
* Windows 10 または Windows 11 が搭載されたPC。

### 2. Python (プログラミング言語)
* このツールを動かすための「エンジン」です。
* [Python公式サイトから 3.10.x をダウンロード](https://www.python.org/downloads/windows/)
* **最重要:** インストーラーを実行するとき、**必ず「Add Python 3.10 to PATH」というチェックボックスにチェックを入れてください。** これを忘れると動きません。
    * 

### 3. Docker Desktop (X監視サーバー)
* X (Twitter) は監視が厳しいため、このツール内で「監視用の小さなサーバー（RSSHub）」を動かす必要があります。そのための「実行環境」です。
* [Docker Desktop 公式サイトからダウンロード](https://www.docker.com/products/docker-desktop/)
* インストールが完了したら、一度Docker Desktopを起動しておいてください（クジラのアイコンがタスクトレイにあればOK）。

### 4. Discord アカウント
* 通知を受け取りたいあなたのDiscordサーバーが必要です。

### 5. X (Twitter) アカウント
* 監視サーバー（RSSHub）を動かすために、あなたのアカウントの「認証情報（Cookie）」が必要になります。

---

## 🛠️ 導入・設定ステップ

すべての「必要なもの」が揃ったら、いよいよ設定です。

### Step 0: ソースコードをダウンロードする
1.  このリポジトリ（Oshi-tracker）のトップページに行きます。
2.  緑色の**`< > Code`**ボタンをクリックします。
3.  **`Download ZIP`** を選択します。
4.  ダウンロードしたZIPファイルを、好きな場所（デスクトップなど）に解凍します。
5.  これ以降の説明は、すべてこの解凍したフォルダの中にある **`src` フォルダ** を基準に進めます。

### Step 1: 必要なライブラリをインストールする
`src`フォルダの中にある `requirements.bat` を見つけてください。
これを**ダブルクリックして実行**します。

黒い画面（コマンドプロンプト）が開き、必要なライブラリ（`requests`, `pygame`, `curl_cffi`, `yt-dlp`）が自動でインストールされます。

### Step 2: X (Twitter) 監視サーバー (RSSHub) を設定する
ここが一番の山場です。Xのポストを監視するための「監視サーバー」をあなたのPC内で起動します。

**a. Cookie（認証情報）を取得する**
1.  Chromeブラウザで [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) 拡張機能をインストールします。
2.  X ( `https://x.com` ) を開き、自分のアカウントにログインしていることを確認します。
3.  ブラウザの右上にある「パズルのピース🧩」のような拡張機能アイコンをクリックし、「Get cookies.txt LOCALLY」を選択します。
4.  開いたウィンドウで `Export` ボタンを押すと、`cookies.txt` という名前のファイルがダウンロードされます。
    * 

**b. Oshi-trackerにCookieを設定する**
1.  `src/datas/` フォルダを開きます。
2.  ダウンロードした `cookies.txt` をメモ帳などで開きます。
3.  中身を**すべてコピー**（`Ctrl+A` → `Ctrl+C`）します。
4.  `src/datas/cookies.txt` に**貼り付けて保存**します。（既にある内容は消して、上書きしてください）

**c. RSSHubに `auth_token` を設定する**
1.  `src/rsshub/` フォルダにある `docker-compose.yml` をメモ帳などで開きます。
2.  `TWITTER_AUTH_TOKEN=` という行を探します。
3.  さきほどダウンロードした `cookies.txt` の中から、`auth_token` と書かれている行を探します。（ファイルの後ろの方にあります）
    ```
    .x.com	TRUE	/	TRUE	[数字]	auth_token	[ここに書かれている長い英数字]
    ```
4.  この `[ここに書かれている長い英数字]` の部分だけをコピーし、`docker-compose.yml` の `TWITTER_AUTH_TOKEN=` の**後ろに貼り付けて保存**します。
    ```yaml
    # 変更前
    TWITTER_AUTH_TOKEN: 
    # 変更後 (例)
    TWITTER_AUTH_TOKEN: 012345abcdef...
    ```

**d. RSSHub（監視サーバー）を起動する**
1.  **Docker Desktopが起動していること**を必ず確認してください。（PC起動時に自動で起動するはずです）
2.  `src/rsshub/` フォルダを開きます。
3.  ウィンドウ上部のアドレスバー（`C:\Users\...\Oshi-tracker\src\rsshub` と表示されている場所）をクリックし、`cmd` と入力してEnterキーを押します。
    * 
4.  黒い画面（コマンドプロンプト）が開いたら、以下の呪文を入力してEnterキーを押します。
    ```bash
    docker-compose up -d
    ```
5.  イメージのダウンロードとビルドが始まります。緑色の `Done` や `started` という文字が出れば成功です。

### Step 3: Oshi-tracker (main.py) を設定する
いよいよ最後の設定です。どの「推し」を監視するかをトラッカーに教えます。

`src`フォルダにある `main.py` をメモ帳やVSCodeなどのエディタで開きます。
ファイルの上部にある`TIKTOK_TARGET_USERNAMES`から`DISCORD_WEBHOOK_URL`までが設定項目です。

**監視しないプラットフォームは、`[]`（空のリスト）のままにしてください。**

```python
# 監視したいTikTokの@ユーザー名（@は不要）
# 例: https://www.tiktok.com/@neymarjr の場合
TIKTOK_TARGET_USERNAMES = ["neymarjr"]

# 監視したいニコ生のユーザーID (https://www.nicovideo.jp/user/XXXX の数字)
# 例: https://www.nicovideo.jp/user/131666408 の場合
NICONICO_TARGET_USER_IDS = ["131666408"]

# 監視したいYouTubeの@ユーザー名（@は不要）
# 例: https://www.youtube.com/@MrBeast の場合
YOUTUBE_TARGET_USERNAMES = ["MrBeast"]

# 監視したいTwitchのユーザー名
# 例: https://www.twitch.tv/ninja の場合
TWITCH_TARGET_USERNAMES = ["ninja"]

# 監視したいOpenrecのユーザー名
# 例: https://www.openrec.tv/user/warabarin の場合
OPENREC_TARGET_USERNAMES = ["warabarin"]

# 監視したいKickのユーザー名
# 例: https://kick.com/adinross の場合
KICK_TARGET_USERNAMES = ["adinross"]

# 監視したいXのRSSHub URL
# "http://localhost:1200/twitter/user/Xのユーザー名"
X_TARGET_URLS = [
    "http://localhost:1200/twitter/user/elonmusk?limit=20&includeRts=false&includeReplies=false",
    "http://localhost:1200/twitter/user/BillGates?limit=10&includeRts=false&includeReplies=false",
]

# 誰かが配信中の時に監視を「停止」したいXのID (上のURLの "elonmusk" や "BillGates" の部分)
LIVE_PAUSE_X_TARGET_IDS = ["elonmusk"]

# 通知を飛ばしたいDiscordのWebhook URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1234567890/xxxxxxxxxxxx_YYYYYYYYYYYYYYYYY"
```

#### Discord Webhook URLの取得方法
1.  通知を送りたいDiscordサーバーを開きます。
2.  チャンネルを右クリックし、「チャンネルの編集」→「連携サービス」→「ウェブフック」を選択します。
3.  「新しいウェブフック」ボタンを押し、名前（例: 推しトラッカー）を付けます。
4.  「ウェブフックURLをコピー」を押し、`main.py`の`DISCORD_WEBHOOK_URL = "..."`の部分に貼り付けます。

#### X (Twitter) URLのパラメータ設定
`X_TARGET_URLS` のURLには、いくつかオプションがあります。
* `limit=10`: 一度にチェックする最新ポストの件数。**10〜20を推奨**します。
* `includeRts=false`: リツイート（リポスト）を通知に含めるか (`true` / `false`)。
* `includeReplies=false`: リプライ（返信）を通知に含めるか (`true` / `false`)。

### Step 4: トラッカーを起動する
お疲れ様でした！
`src`フォルダにある `main.py` を**ダブルクリックして実行**します。

黒い画面（コンソール）が起動し、設定した全アカウントの監視が開始されます。
あとはこの画面を開いたままにしておけば、推しが活動するたびにDiscordに通知が届きます！

---

## 🔴 配信の自動録画機能

`main.py` の中盤にある`Config`クラスにすべて詰まっています :)

### オンオフトグル

```python
class Config:
    DEBUG_LOGGING = False
    ENABLE_AUTO_RECORDING = False # ← ここ！！！！ Falseでオフ、Trueでオン
```

### 録画対象設定

```python
class Config:
    # (...省略...)
    RECORDING_TARGET_PLATFORMS = [
        #NOTIF_PLATFORM_TIKTOK,
        #NOTIF_PLATFORM_NICONICO,
        #NOTIF_PLATFORM_YOUTUBE,
        #NOTIF_PLATFORM_TWITCH,
        #NOTIF_PLATFORM_OPENREC,
        #NOTIF_PLATFORM_KICK,
        #NOTIF_PLATFORM_TWITCASTING
    ]
    # (...省略...)
```

上記の部分(RECORDING_TARGET_PLATFORMSの中)にある#を消すとそのプラットフォームの自動録画をオンにします！

(オフにしたい場合は、#を付けなおす または その行を削除する。行を削除してからもう一度追加したい場合は、このreadmeを参考にしてプラットフォームを追加する。)

---

---

## 🔧 詳細設定 (上級者向け)

`main.py` の中盤にある`Config`クラスや、その他のグローバル変数を変更することで、動作を細かく調整できます。

### サウンドのオン/オフ
PC本体から通知音を鳴らしたくない場合は、パスを空（`""`）にしてください。

```python
# 配信開始音
SOUND_LIVE_START = "./sounds/live_start.mp3"
# 配信終了音 (空にすると鳴らない)
SOUND_LIVE_END = ""
# Xのポスト検知音
SOUND_MESSAGE_DETECTED = "./sounds/message_detected.mp3"
```

### 監視間隔の調整
数値を小さくすると検知が早くなりますが、各プラットフォームからブロック（BAN）されるリスクが上がります。**自己責任で変更してください。**

```python
# X (RSSHub) のチェック間隔 (秒)
X_CHECK_INTERVAL_SECONDS = 60.1
# ライブ配信のチェック間隔 (秒)
LIVE_CHECK_INTERVAL_SECONDS = 60
```

### デバッグログ
`datas/tracker_log.txt` に詳細な動作ログを残すかどうか。
`True` にすると、どのプラットフォームのチェックに成功/失敗したかなどの記録が残ります。

```python
class Config:
    DEBUG_LOGGING = True  # Trueで有効, Falseで無効
```

### 通知メッセージの変更
Discordに飛ぶメッセージを自由に変更できます。

```python
class Config:
    # (...省略...)
    NOTIF_LIVE_START = "【速報】{name}が{platform}配信を開始！ @everyone"
    NOTIF_LIVE_END = "({name} の{platform}配信が終わりました)"
    # (...省略...)
```

---

## 🤔 トラブルシューティング (FAQ)

**Q. `python` や `pip` コマンドが見つからないと言われる。**
**A.** Pythonのインストール時に「Add Python to PATH」にチェックを入れ忘れています。Pythonを一度アンインストールし、再度インストールして**必ずチェックを入れてください。**

**Q. `docker-compose up -d` がエラーになる。**
**A.** Docker Desktopが起動していない可能性が高いです。PCを再起動するか、Docker Desktopアプリを手動で起動してから、もう一度コマンドを実行してください。

**Q. X (Twitter) の通知だけが来ない。**
**A.** `auth_token` が古いか、`docker-compose.yml`への貼り付けに失敗しています。`Step 2-c`の手順をもう一度確認してください。

**Q. YouTube / Twitch / Kick / TikTok の通知が来ない。**
**A.** `curl_cffi`ライブラリのインストールに失敗しているか、相手側のサイト構造が変更された可能性があります。`requirements.bat`を再実行するか、`Config.DEBUG_LOGGING = True`にして`datas/tracker_log.txt`を確認してください。

---

## 👨‍💻 開発者向け (For Developers)
このツールは、`python-requests`ではTLSフィンガープリント（JA3）によってブロックされるプラットフォーム（YouTube, Twitch, Kick, TikTok）に対応するため、`curl_cffi`ライブラリを使用しています。
これにより、`impersonate="chrome110"`を指定し、TLSハンドシェイクをChromeブラウザに偽装することで、403 (Forbidden) エラーを回避しています。

---

## 👑 クレジット (Credit)
* **Developer:** [Your Name or Handle]
* *(Note: Some code in this tool was written with the assistance of AI.)*

## 📜 ライセンス (License)
This project is licensed under the [MIT License](./LICENSE).
