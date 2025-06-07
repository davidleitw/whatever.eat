# LINE Bot - Whatever Eat

最小化的 LINE Bot 實作，支援 .env 配置管理和容器化部署。

## 🚀 快速開始

### 1. 設定環境變數

複製範例檔案並填入您的 LINE Bot 憑證：
```bash
cp env.example .env
# 編輯 .env 檔案，填入真實的 token 和 secret
```

### 2. 本地開發

```bash
# 安裝依賴
uv sync

# 啟動服務
uv run main.py
```

### 3. 容器化部署

```bash
# 使用 Docker Compose
docker-compose up -d

# 或使用 Docker
docker build -t linebot .
docker run -p 5000:5000 --env-file .env linebot
```

## 📋 端點說明

- `/` - 健康檢查
- `/callback` - LINE Webhook 端點
- `/config` - 配置狀態檢查

## 🔧 配置說明

在 `.env` 檔案中設定：

```env
LINE_CHANNEL_ACCESS_TOKEN=your_token
LINE_CHANNEL_SECRET=your_secret
PORT=5000
HOST=0.0.0.0
DEBUG=True
```

## 🌐 Webhook 設定

設定 LINE Developers Console 的 Webhook URL：
```
https://your-domain.com/callback
```

## 📦 專案結構

```
├── app.py              # Flask 應用程式
├── config.py           # 配置管理
├── main.py             # 啟動入口
├── Dockerfile          # 容器化配置
├── docker-compose.yml  # Docker Compose 配置
├── .env               # 環境變數 (需自行建立)
└── env.example        # 環境變數範例
```

## 使用

1. 設定 Webhook URL: `http://your-domain/callback`
2. 傳送訊息給 Bot
3. Bot 會回覆 "Hello! You said: [你的訊息]"
