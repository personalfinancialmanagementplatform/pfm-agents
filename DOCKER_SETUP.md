# Docker 環境快速設定指南

## 📋 給組員的簡易說明

### 第一次設定（只需做一次）

#### 1. 安裝 Docker Desktop
- 下載：https://www.docker.com/products/docker-desktop
- 安裝後啟動 Docker Desktop
- 等待右上角 Docker 圖示變成綠色

#### 2. Clone 專案
```bash
git clone https://github.com/personalfinancialmanagementplatform/pfm-agents.git
cd pfm-agents
```

#### 3. 建立虛擬環境
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 4. 設定環境變數
```bash
cp .env.example .env
```

**編輯 `.env` 檔案：**
- 如果在**主機電腦**（Emily 的電腦）：
```env
  DB_HOST=localhost
  MONGO_HOST=localhost
  REDIS_HOST=localhost
```

- 如果在**其他電腦**：
```env
  DB_HOST=172.20.10.4  # Emily 的 IP
  MONGO_HOST=172.20.10.4
  REDIS_HOST=172.20.10.4
```

#### 5. 啟動資料庫
```bash
# 如果是主機電腦（Emily）
docker-compose up -d

# 等待 10 秒讓服務啟動
sleep 10
```

#### 6. 測試連線
```bash
python3 scripts/test_connection.py
```

看到三個 ✅ 就成功了！

---

## 🔄 日常使用

### 每天開始工作
```bash
# 1. 啟動 Docker Desktop（如果還沒開）
open -a Docker  # macOS
# 或手動開啟 Docker Desktop

# 2. 啟動資料庫（只有主機需要）
docker-compose up -d

# 3. 啟動虛擬環境
source venv/bin/activate

# 4. 開始開發
```

### 結束工作
```bash
# 停止資料庫（可選，也可以一直開著）
docker-compose down
```

---

## �� 常見問題

### Q1: 測試連線失敗怎麼辦？

**如果是主機電腦（Emily）：**
```bash
# 檢查容器是否在運行
docker ps

# 應該看到 3 個容器：
# - postgresql-pgvector-db-1
# - pfm-mongodb
# - pfm-redis

# 如果沒有，重新啟動
docker-compose down
docker-compose up -d
```

**如果是其他電腦：**
1. 確認主機（Emily）的 Docker 容器在運行
2. 確認 `.env` 的 IP 設定正確（`172.20.10.4`）
3. 確認在同一個 Wi-Fi 網路

### Q2: IP 變了怎麼辦？

Emily 的電腦重新連 Wi-Fi 後 IP 可能會變。

**Emily 查詢新 IP：**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}'
```

**組員更新 `.env`：**
```env
# 改成新的 IP
DB_HOST=新的IP
MONGO_HOST=新的IP
REDIS_HOST=新的IP
```

### Q3: Docker Desktop 沒啟動

看到這個錯誤：
```
Cannot connect to the Docker daemon
```

**解決：**
```bash
# macOS
open -a Docker

# Windows
# 從開始選單啟動 Docker Desktop

# 等待 30 秒讓 Docker 完全啟動
```

### Q4: 端口被占用

看到這個錯誤：
```
port is already allocated
```

**解決：**
```bash
# 停止本機的資料庫服務
brew services stop postgresql@15
brew services stop mongodb-community
brew services stop redis

# 重新啟動 Docker
docker-compose down
docker-compose up -d
```

---

## 📞 需要幫助？

- 詳細文件：[DOCKER_GUIDE.md](DOCKER_GUIDE.md)
- 問 Emily 🙋‍♀️

---

## ⚡ 快速指令參考
```bash
# 啟動資料庫
docker-compose up -d

# 停止資料庫
docker-compose down

# 查看容器狀態
docker ps

# 查看日誌
docker-compose logs -f

# 測試連線
python3 scripts/test_connection.py

# 重新啟動
docker-compose restart
```

---

## 🏗️ 資料庫資訊

| 服務 | 端口 | 用途 |
|------|------|------|
| PostgreSQL | 5432 | 主要資料（用戶、交易、預算） |
| MongoDB | 27017 | 彈性資料（對話、日誌） |
| Redis | 6379 | 快取 |

**連線資訊：**
- Database: `pfm_agents`
- User: `emily200008`
- Password: 在 `.env` 檔案中

