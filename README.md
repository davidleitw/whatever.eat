# Whatever Eat - LINE Bot 美食推薦機器人 🍽️

一個智能的 LINE Bot 機器人，專門為吃貨提供位置基礎的隨機餐廳推薦服務。使用者只需分享位置，機器人就會自動尋找附近的餐廳並推薦一家給你，解決「今天要吃什麼」的千古難題！

## ✨ 功能特色

- 📍 **位置基礎推薦**：基於使用者分享的位置，搜尋附近餐廳
- 🎲 **智能推薦系統**：從附近餐廳中智能選擇，增加探索樂趣
- 🛡️ **防重複推薦**：5 次抽獎內不會推薦相同餐廳，確保多樣性
- 💾 **Session 管理**：30 分鐘位置記憶，無需重複分享位置
- 🕒 **營業時間過濾**：優先推薦目前營業中的餐廳
- ⭐ **詳細資訊**：提供餐廳評分、地址、價位、營業時間等完整資訊
- 📊 **推薦統計**：追蹤推薦次數和歷史記錄
- 🗺️ **Google Maps 整合**：直接提供 Google Maps 連結
- 🎯 **指令式操作**：支援多種指令進行互動
- 🤖 **AI 對話功能**：整合 OpenAI GPT-4 提供智能對話（可選）
- 🐳 **容器化部署**：支援 Docker 和 Docker Compose
- 🛠️ **自動化工具**：提供 Makefile 快速管理開發流程

## 🏗️ 專案架構

```
whatever.eat/
├── src/                          # 核心程式碼
│   ├── app.py                   # Flask 主應用程式
│   ├── config/
│   │   └── settings.py          # 環境變數與配置管理
│   ├── line_bot/
│   │   ├── manager.py           # LINE Bot 核心邏輯
│   │   └── state.py             # LangGraph 聊天機器人狀態管理
│   └── map/
│       └── client.py            # Google Maps Places API 客戶端
├── main.py                      # 程式進入點（LangGraph 範例）
├── Dockerfile                   # Docker 容器化配置
├── docker-compose.yml           # Docker Compose 編排
├── Makefile                     # 開發自動化工具
├── pyproject.toml               # Python 專案依賴配置
└── uv.lock                      # UV 套件管理器鎖定檔案
```

## 🚀 快速開始

### 前置需求

1. **Python 3.10+**
2. **UV 套件管理器** (推薦) 或 pip
3. **ngrok 帳號** (免費)：用於本地開發時暴露服務
4. **LINE Bot 頻道** (必要)：需要在 LINE Developers Console 建立
5. **Google Maps API** (必要)：需要在 Google Cloud Console 啟用 Places API
6. **OpenAI API** (可選)：用於 AI 對話功能

### 📋 API 服務申請指南

#### 🔶 LINE Bot API 申請 (2024年新流程)

**申請步驟：**
1. 前往 [LINE 官方帳號申請頁面](https://entry.line.biz/form/entry/unverified)
2. 使用手機號碼進行簡訊驗證 📱
3. 填寫頻道相關資訊（帳號名稱、類別等）
4. 前往 [Official Account Manager](https://manager.line.biz/) 啟動 Messaging API
5. 進入 [LINE Developers Console](https://developers.line.biz/)
6. 在 Basic settings 頁面取得 **Channel Secret**
7. 在 Messaging API 頁面點擊 Issue 取得 **Channel Access Token**

**重要設定：**
- 在 Messaging API 設定中，將「自動回應訊息」和「加入好友的歡迎訊息」設為 **停用**
- 確保 Webhook 設定為 **啟用**

#### 🔶 Google Maps Places API 申請

**申請步驟：**
1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 登入 Google 帳號並建立新專案
3. 啟用計費帳戶（需綁定信用卡，但有每月 $200 免費額度）
4. 在 API 資料庫中搜尋並啟用「**Places API**」
5. 前往「憑證」頁面 → 建立憑證 → API 金鑰
6. 設定 API 金鑰限制（建議限制 HTTP 引用者或 IP 位址）

**費用說明：**
- Google 提供每月 $200 免費額度
- 大約可支援 28,000 次 Places API 查詢
- 超出免費額度才會收費

#### 🔶 OpenAI API 申請 (可選)

**申請步驟：**
1. 前往 [OpenAI Platform](https://platform.openai.com/)
2. 註冊帳號並完成電話號碼驗證
3. 進入 Dashboard → API keys → Create new secret key
4. 設定 API 金鑰權限（一般選擇 "All"）
5. **重要：** 需要購買 API 使用額度（$5-100，2024年已無免費額度）

#### 🔶 ngrok 設定 (本地開發)

**申請步驟：**
1. 前往 [ngrok 官網](https://ngrok.com/) 註冊免費帳號
2. 下載並安裝 ngrok CLI
3. 登入後取得免費的靜態域名（每個帳號可申請一個）
4. 在專案 `.env` 中設定 `NGROK_URL`

**免費方案限制：**
- 每月 1GB 流量限制
- 1 個免費靜態域名
- 適合開發和測試使用

### 安裝與設定

#### 1. 複製專案並安裝依賴

```bash
git clone <repository-url>
cd whatever.eat

# 使用 UV (推薦)
uv sync

# 或使用 pip
pip install -r requirements.txt
```

#### 2. 設定環境變數

複製範例檔案並建立 `.env` 檔案：

```bash
# 複製範例檔案
cp .env.example .env
```

編輯 `.env` 檔案並填入你申請到的 API 金鑰：

```env
# LINE Bot 設定 (必要)
LINE_CHANNEL_ACCESS_TOKEN=你的_LINE_Channel_Access_Token
LINE_CHANNEL_SECRET=你的_LINE_Channel_Secret

# Google Maps API 設定 (必要)
GOOGLE_MAP_API_TOKEN=你的_Google_Maps_API_Key

# OpenAI API 設定 (可選，用於 AI 對話功能)
OPENAI_API_KEY=你的_OpenAI_API_Key

# 伺服器設定
PORT=5000
HOST=0.0.0.0
DEBUG=True

# ngrok 設定 (本地開發)
NGROK_URL=你的_ngrok_靜態域名.ngrok-free.app
```

#### 3. 啟動應用程式

**本地開發模式：**
```bash
# 使用 UV
uv run src/app.py

# 或直接執行
python src/app.py
```

**使用 Makefile (推薦用於開發)：**
```bash
# 啟動伺服器和 ngrok (會自動讀取 .env 中的 NGROK_URL)
make start

# 或手動指定 ngrok URL
make start NGROK_URL=your-ngrok-url.ngrok-free.app

# 查看服務狀態
make status

# 查看伺服器日誌
make logs

# 重啟伺服器（保持 ngrok 運行）
make restart

# 停止所有服務
make stop

# 查看所有可用指令
make help
```

**容器化部署：**
```bash
# Docker Compose (推薦)
docker-compose up -d

# 或使用 Docker
docker build -t whatever-eat .
docker run -p 5000:5000 --env-file .env whatever-eat
```

### 4. 設定 LINE Bot Webhook

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 選擇你的 Bot 頻道
3. 在 Messaging API 設定中，設定 Webhook URL：
   ```
   https://your-domain.com/callback
   ```
4. 啟用 Webhook 並驗證連接

## 📱 使用方式

### 🚀 快速開始
1. **加入好友**：掃描 LINE Bot 的 QR Code 或搜尋 Bot ID
2. **設定位置**：分享您的位置給機器人（位置會記住 30 分鐘）
3. **開始抽獎**：輸入「抽餐廳」、「推薦」或相關指令
4. **享受美食**：查看詳細餐廳資訊並前往用餐
5. **重複抽取**：想換一家？再次輸入指令即可

### 🎯 互動指令

**餐廳推薦指令：**
- `抽餐廳` / `推薦` / `吃什麼` - 推薦附近餐廳
- `來一家` / `換一家` / `再抽` - 重新推薦
- `recommend` / `random` / `pick` - 英文指令

**管理指令：**
- `狀態` / `status` - 查看當前位置和推薦統計
- `清除` / `clear` - 清除位置和推薦記錄
- `幫助` / `help` - 顯示完整指令說明

### 🛡️ 防重複機制
- **智能避重**：5 次推薦內不會重複相同餐廳
- **自動重置**：當所有附近餐廳都推薦過時自動重置
- **統計追蹤**：即時顯示推薦次數和防重複狀態

### 推薦結果範例

**位置設定回應：**
```
✅ 已設置您的位置！

📍 台北101
📮 台北市信義區信義路五段7號

🕒 位置有效期：30 分鐘

現在您可以使用以下指令：
• 輸入「抽餐廳」或「推薦」開始抽獎
• 輸入「幫助」查看所有指令

💡 在位置有效期內，您可以重複抽取不同的餐廳！
```

**餐廳推薦回應：**
```
🍽️ 為您推薦餐廳！

📍 您的位置：台北101
📊 推薦統計：第 3 次推薦
🛡️ 防重複：🔄 防重複推薦 (5次內不重複)

🎲 智能推薦餐廳

🍴 鼎泰豐 (101店)
⭐ 評分：4.2
📍 地址：台北市信義區市府路45號B1
🏷️ 類型：restaurant, food, establishment
💰 價位：3

🕒 目前營業中

📅 營業時間：
   Monday: 11:00 AM – 9:30 PM
   Tuesday: 11:00 AM – 9:30 PM
   ...

🔗 Google Maps 導航

💡 想要換一家？再輸入「抽餐廳」即可！
🎯 已記錄此推薦，近 5 次內不會重複推薦此餐廳
```

## 🔧 API 端點

| 端點 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 健康檢查端點 |
| `/callback` | POST | LINE Webhook 接收端點 |
| `/config` | GET | 顯示當前配置狀態 |

## 🛠️ 開發工具

### Makefile 指令

```bash
make help        # 顯示所有可用指令
make start       # 啟動伺服器和 ngrok
make stop        # 停止所有服務
make restart     # 重啟伺服器（保持 ngrok 運行）
make status      # 檢查服務狀態
make logs        # 查看伺服器日誌
make clean       # 清理臨時檔案
make dev         # 開發模式（檔案變更自動重啟）
```

### 除錯

1. **檢查配置**：造訪 `http://localhost:5000/config`
2. **查看日誌**：使用 `make logs` 或檢查 `server.log`
3. **驗證 API 金鑰**：確認所有環境變數正確設定
4. **測試 Webhook**：使用 LINE Developers Console 的測試功能

## 📦 依賴套件

核心依賴包括：

- **Flask 3.1.1+** - Web 框架
- **line-bot-sdk 3.17.1+** - LINE Bot SDK
- **google-maps-places 0.2.1+** - Google Maps Places API
- **cachetools 5.3.0+** - TTL 快取和 Session 管理
- **langchain[openai] 0.3.25+** - AI 對話功能
- **langgraph 0.4.8+** - 對話狀態管理
- **python-dotenv 1.1.0+** - 環境變數管理

完整依賴清單請參考 `pyproject.toml`。

## 🔮 未來功能規劃

### 近期計畫
- [ ] **美食類型篩選**：讓使用者選擇特定料理類型（中式、日式、西式等）
- [ ] **價位範圍過濾**：根據預算篩選餐廳
- [ ] **評分門檻設定**：只推薦高評分餐廳
- [ ] **歷史記錄功能**：避免重複推薦最近去過的餐廳

### 中期計畫
- [ ] **智能推薦演算法**：根據使用者偏好學習推薦
- [ ] **群組功能**：支援多人位置聚合推薦
- [ ] **餐廳收藏功能**：讓使用者收藏喜歡的餐廳
- [ ] **用餐時間優化**：根據當前時間推薦適合的餐廳類型

### 長期計畫
- [ ] **多語言支援**：支援英文、日文等多國語言
- [ ] **個人化推薦系統**：基於機器學習的個人化推薦
- [ ] **社交功能**：分享推薦結果到社群媒體
- [ ] **營養資訊整合**：提供餐廳營養資訊
- [ ] **預約功能整合**：直接透過 Bot 預約餐廳

### 技術優化
- [ ] **Redis 快取系統**：提升 API 回應速度
- [ ] **資料庫整合**：儲存使用者偏好和歷史記錄
- [ ] **監控和分析**：加入使用統計和效能監控
- [ ] **A/B 測試框架**：優化推薦演算法效果

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！在貢獻之前，請確保：

1. 程式碼符合 PEP 8 標準
2. 新功能包含相應的測試
3. 更新相關文件
4. 提交前執行所有測試

## 📄 授權條款

此專案採用 MIT 授權條款，詳細內容請參考 [LICENSE](LICENSE) 檔案。

---

**Enjoy your meal! 🍽️✨**