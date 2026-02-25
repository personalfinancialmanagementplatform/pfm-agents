# Docker 資料庫環境快速指南

## 📋 目錄
- [環境資訊](#環境資訊)
- [快速開始](#快速開始)
- [常用指令](#常用指令)
- [容器管理](#容器管理)
- [資料庫操作](#資料庫操作)
- [遠端連線設定](#遠端連線設定)
- [故障排除](#故障排除)
- [備份與還原](#備份與還原)

---

## 環境資訊

### 主機配置
```
📍 IP: 172.20.10.4 (可能會變動)
🐳 Docker Desktop: 必須保持運行
```

### 資料庫服務
| 服務 | 容器名稱 | 映像檔 | 端口 | 版本 |
|------|---------|--------|------|------|
| PostgreSQL | postgresql-pgvector-db-1 | pgvector/pgvector:pg18-trixie | 5432 | 18.1 |
| MongoDB | pfm-mongodb | mongo:7 | 27017 | 7.0.30 |
| Redis | pfm-redis | redis:7-alpine | 6379 | 7.4.8 |

### 資料庫連線資訊
```
PostgreSQL:
- Database: pfm_agents
- User: emily200008
- Password: 108306052J

MongoDB:
- Database: pfm_agents
- 無需認證（開發環境）

Redis:
- DB: 0
- 無密碼（開發環境）
```

---

## 快速開始

### 1. 啟動所有服務
```bash
# 啟動 MongoDB 和 Redis
docker-compose up -d

# 查看狀態
docker ps
```

### 2. 測試連線
```bash
# 執行連線測試
python3 scripts/test_connection.py

# 預期輸出：
# ✅ PostgreSQL 連線成功
# ✅ MongoDB 連線成功
# ✅ Redis 連線成功
```

### 3. 停止服務
```bash
# 停止 MongoDB 和 Redis
docker-compose down

# 停止所有容器（包括 PostgreSQL）
docker stop postgresql-pgvector-db-1 pfm-mongodb pfm-redis
```

---

## 常用指令

### 查看容器狀態
```bash
# 查看所有運行中的容器
docker ps

# 查看所有容器（包括停止的）
docker ps -a

# 格式化輸出
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
```

### 查看容器日誌
```bash
# 查看 PostgreSQL 日誌
docker logs postgresql-pgvector-db-1

# 查看 MongoDB 日誌
docker logs pfm-mongodb

# 查看 Redis 日誌
docker logs pfm-redis

# 即時追蹤日誌（Ctrl+C 退出）
docker logs -f pfm-mongodb

# 查看最後 100 行
docker logs --tail 100 pfm-redis
```

### Docker Compose 指令
```bash
# 啟動服務（背景執行）
docker-compose up -d

# 啟動並查看日誌
docker-compose up

# 停止服務
docker-compose down

# 停止並刪除資料卷（⚠️ 會刪除所有資料）
docker-compose down -v

# 重啟服務
docker-compose restart

# 重啟特定服務
docker-compose restart mongodb

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

---

## 容器管理

### 啟動/停止容器
```bash
# 啟動容器
docker start postgresql-pgvector-db-1
docker start pfm-mongodb
docker start pfm-redis

# 停止容器
docker stop postgresql-pgvector-db-1
docker stop pfm-mongodb
docker stop pfm-redis

# 重啟容器
docker restart pfm-mongodb

# 強制停止容器
docker kill pfm-redis
```

### 進入容器 Shell
```bash
# 進入 PostgreSQL 容器
docker exec -it postgresql-pgvector-db-1 bash

# 進入 MongoDB 容器
docker exec -it pfm-mongodb bash

# 進入 Redis 容器
docker exec -it pfm-redis sh
```

### 查看容器資源使用
```bash
# 查看所有容器資源使用
docker stats

# 查看特定容器
docker stats pfm-mongodb
```

### 清理無用資源
```bash
# 清理停止的容器
docker container prune

# 清理無用的映像檔
docker image prune

# 清理無用的資料卷
docker volume prune

# 清理所有無用資源（⚠️ 小心使用）
docker system prune -a
```

---

## 資料庫操作

### PostgreSQL

#### 進入 psql
```bash
# 以 emily200008 使用者登入
docker exec -it postgresql-pgvector-db-1 psql -U emily200008 -d pfm_agents

# 以 postgres 超級使用者登入
docker exec -it postgresql-pgvector-db-1 psql -U postgres
```

#### 常用 SQL 指令（在 psql 中執行）
```sql
-- 列出所有資料庫
\l

-- 切換資料庫
\c pfm_agents

-- 列出所有資料表
\dt

-- 查看資料表結構
\d users

-- 查看資料表資料
SELECT * FROM users LIMIT 10;

-- 查看資料庫大小
SELECT pg_size_pretty(pg_database_size('pfm_agents'));

-- 離開 psql
\q
```

#### 直接執行 SQL
```bash
# 執行單行 SQL
docker exec -it postgresql-pgvector-db-1 psql -U emily200008 -d pfm_agents -c "SELECT COUNT(*) FROM users;"

# 執行 SQL 檔案
docker exec -i postgresql-pgvector-db-1 psql -U emily200008 -d pfm_agents < script.sql
```

### MongoDB

#### 進入 mongosh
```bash
# 進入 MongoDB Shell
docker exec -it pfm-mongodb mongosh pfm_agents
```

#### 常用指令（在 mongosh 中執行）
```javascript
// 顯示所有集合
show collections

// 查詢資料
db.users.find().limit(10)

// 統計文件數量
db.users.countDocuments()

// 插入資料
db.users.insertOne({name: "Test", email: "test@example.com"})

// 刪除資料
db.users.deleteOne({name: "Test"})

// 離開 mongosh
exit
```

#### 直接執行指令
```bash
# 執行單行指令
docker exec -it pfm-mongodb mongosh pfm_agents --eval "db.users.countDocuments()"

# 匯出資料
docker exec pfm-mongodb mongodump --db pfm_agents --out /tmp/backup
```

### Redis

#### 進入 redis-cli
```bash
# 進入 Redis CLI
docker exec -it pfm-redis redis-cli
```

#### 常用指令（在 redis-cli 中執行）
```bash
# 測試連線
PING

# 查看所有 key
KEYS *

# 取得 key 的值
GET mykey

# 設定 key
SET mykey "Hello World"

# 刪除 key
DEL mykey

# 查看資料庫大小
DBSIZE

# 清空當前資料庫
FLUSHDB

# 離開 redis-cli
exit
```

#### 直接執行指令
```bash
# 執行單行指令
docker exec pfm-redis redis-cli PING

# 查看所有 key
docker exec pfm-redis redis-cli KEYS '*'
```

---

## 遠端連線設定

### 查詢主機 IP
```bash
# macOS/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}'

# 或
ipconfig getifaddr en0  # Wi-Fi
ipconfig getifaddr en1  # 有線網路
```

### 本機配置 (.env)
```env
DB_HOST=localhost
MONGO_HOST=localhost
REDIS_HOST=localhost
```

### 遠端配置 (.env.remote)
```env
DB_HOST=172.20.10.4
MONGO_HOST=172.20.10.4
REDIS_HOST=172.20.10.4
```

### 其他電腦設定步驟

1. **複製專案**
```bash
git clone <repository-url>
cd pfm-agents
```

2. **安裝依賴**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **設定環境變數**
```bash
# 方法 1: 複製遠端配置
cp .env.remote .env

# 方法 2: 手動建立 .env
# 將所有 HOST 改為主機 IP (172.20.10.4)
```

4. **測試連線**
```bash
python3 scripts/test_connection.py
```

### 防火牆設定（如果連線失敗）

#### macOS
```bash
# 查看防火牆狀態
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# 允許 Docker 通過防火牆
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /Applications/Docker.app/Contents/MacOS/Docker
```

---

## 故障排除

### 問題 1: 容器無法啟動

**症狀：**
```
Error response from daemon: Conflict. The container name "..." is already in use
```

**解決方法：**
```bash
# 查看衝突的容器
docker ps -a | grep pfm

# 停止並刪除舊容器
docker stop pfm-mongodb pfm-redis
docker rm pfm-mongodb pfm-redis

# 重新啟動
docker-compose up -d
```

### 問題 2: 端口被占用

**症狀：**
```
Error starting userland proxy: listen tcp4 0.0.0.0:5432: bind: address already in use
```

**解決方法：**
```bash
# 查看占用端口的程序
lsof -i :5432
lsof -i :27017
lsof -i :6379

# 停止本機資料庫服務
brew services stop postgresql@15
brew services stop mongodb-community
brew services stop redis

# 或修改 docker-compose.yml 使用不同端口
ports:
  - "5433:5432"  # 本機使用 5433 連接
```

### 問題 3: Docker 無法連線

**症狀：**
```
Cannot connect to the Docker daemon. Is the docker daemon running?
```

**解決方法：**
```bash
# 啟動 Docker Desktop
open -a Docker

# 等待 30 秒讓 Docker 完全啟動
sleep 30

# 驗證 Docker 運行
docker info
```

### 問題 4: 網路連線失敗（從其他電腦）

**症狀：**
```
pymongo.errors.ServerSelectionTimeoutError: connection refused
```

**排查步驟：**

1. **確認主機 IP**
```bash
# 在主機執行
ifconfig | grep "inet "
```

2. **確認容器運行**
```bash
# 在主機執行
docker ps
```

3. **測試網路連通性**
```bash
# 從其他電腦執行
ping 172.20.10.4

# 測試端口
nc -zv 172.20.10.4 5432
nc -zv 172.20.10.4 27017
nc -zv 172.20.10.4 6379
```

4. **檢查防火牆**
```bash
# macOS - 查看防火牆狀態
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

### 問題 5: 資料遺失

**症狀：**
所有資料都不見了

**原因：**
執行了 `docker-compose down -v` 刪除了資料卷

**預防：**
```bash
# 永遠不要使用 -v 參數（除非你確定要刪除資料）
docker-compose down  # ✅ 正確

docker-compose down -v  # ❌ 會刪除所有資料
```

**資料恢復：**
如果有備份，參考[備份與還原](#備份與還原)章節

### 問題 6: 容器健康檢查失敗

**症狀：**
```
docker ps 顯示 (unhealthy)
```

**解決方法：**
```bash
# 查看詳細錯誤
docker inspect pfm-mongodb | grep -A 10 Health

# 查看日誌
docker logs pfm-mongodb

# 重啟容器
docker restart pfm-mongodb

# 如果仍失敗，重新建立
docker-compose down
docker-compose up -d
```

### 問題 7: 磁碟空間不足

**症狀：**
```
no space left on device
```

**解決方法：**
```bash
# 查看 Docker 磁碟使用
docker system df

# 清理未使用的資源
docker system prune

# 清理舊映像檔
docker image prune -a

# 清理未使用的資料卷（⚠️ 小心）
docker volume prune
```

---

## 備份與還原

### PostgreSQL 備份

#### 完整備份
```bash
# 備份整個資料庫
docker exec postgresql-pgvector-db-1 pg_dump -U emily200008 pfm_agents > backup_$(date +%Y%m%d).sql

# 壓縮備份
docker exec postgresql-pgvector-db-1 pg_dump -U emily200008 pfm_agents | gzip > backup_$(date +%Y%m%d).sql.gz
```

#### 還原
```bash
# 從備份還原
docker exec -i postgresql-pgvector-db-1 psql -U emily200008 -d pfm_agents < backup_20260225.sql

# 從壓縮檔還原
gunzip < backup_20260225.sql.gz | docker exec -i postgresql-pgvector-db-1 psql -U emily200008 -d pfm_agents
```

#### 備份特定資料表
```bash
# 備份單一資料表
docker exec postgresql-pgvector-db-1 pg_dump -U emily200008 -d pfm_agents -t users > users_backup.sql

# 還原
docker exec -i postgresql-pgvector-db-1 psql -U emily200008 -d pfm_agents < users_backup.sql
```

### MongoDB 備份

#### 完整備份
```bash
# 備份到容器內
docker exec pfm-mongodb mongodump --db pfm_agents --out /tmp/backup

# 複製到本機
docker cp pfm-mongodb:/tmp/backup ./mongodb_backup_$(date +%Y%m%d)

# 一步完成（推薦）
docker exec pfm-mongodb mongodump --db pfm_agents --archive | gzip > mongodb_backup_$(date +%Y%m%d).gz
```

#### 還原
```bash
# 從本機還原
gunzip < mongodb_backup_20260225.gz | docker exec -i pfm-mongodb mongorestore --archive --db pfm_agents

# 從目錄還原
docker cp ./mongodb_backup pfm-mongodb:/tmp/
docker exec pfm-mongodb mongorestore --db pfm_agents /tmp/mongodb_backup/pfm_agents
```

### Redis 備份

#### RDB 備份（快照）
```bash
# 觸發立即備份
docker exec pfm-redis redis-cli BGSAVE

# 等待完成
docker exec pfm-redis redis-cli LASTSAVE

# 複製 RDB 檔案
docker cp pfm-redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

#### 還原
```bash
# 停止 Redis
docker stop pfm-redis

# 複製備份檔案
docker cp redis_backup_20260225.rdb pfm-redis:/data/dump.rdb

# 啟動 Redis
docker start pfm-redis
```

### 自動備份腳本

建立 `scripts/backup_all.sh`：
```bash
#!/bin/bash

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "🗄️  開始備份所有資料庫..."

# PostgreSQL
echo "📊 備份 PostgreSQL..."
docker exec postgresql-pgvector-db-1 pg_dump -U emily200008 pfm_agents | gzip > $BACKUP_DIR/postgres.sql.gz

# MongoDB
echo "📊 備份 MongoDB..."
docker exec pfm-mongodb mongodump --db pfm_agents --archive | gzip > $BACKUP_DIR/mongodb.gz

# Redis
echo "📊 備份 Redis..."
docker exec pfm-redis redis-cli BGSAVE
sleep 2
docker cp pfm-redis:/data/dump.rdb $BACKUP_DIR/redis.rdb

echo "✅ 備份完成: $BACKUP_DIR"
ls -lh $BACKUP_DIR
```

使用方法：
```bash
chmod +x scripts/backup_all.sh
./scripts/backup_all.sh
```

### 定期備份（Cron）
```bash
# 編輯 crontab
crontab -e

# 每天凌晨 2 點備份
0 2 * * * cd /path/to/pfm-agents && ./scripts/backup_all.sh
```

---

## 附錄

### 快速命令速查表
```bash
# 啟動
docker-compose up -d

# 停止
docker-compose down

# 查看狀態
docker ps

# 查看日誌
docker-compose logs -f

# 測試連線
python3 scripts/test_connection.py

# 進入 PostgreSQL
docker exec -it postgresql-pgvector-db-1 psql -U emily200008 -d pfm_agents

# 進入 MongoDB
docker exec -it pfm-mongodb mongosh pfm_agents

# 進入 Redis
docker exec -it pfm-redis redis-cli

# 備份所有資料庫
./scripts/backup_all.sh
```

### 資料卷位置
```bash
# 查看所有資料卷
docker volume ls

# 查看資料卷詳細資訊
docker volume inspect pfm-agents_postgres_data
docker volume inspect pfm-agents_mongodb_data
docker volume inspect pfm-agents_redis_data

# 資料實際位置（macOS）
# ~/Library/Containers/com.docker.docker/Data/vms/0/data/docker/volumes/
```

### 有用的資源

- [Docker 官方文件](https://docs.docker.com/)
- [Docker Compose 文件](https://docs.docker.com/compose/)
- [PostgreSQL 文件](https://www.postgresql.org/docs/)
- [MongoDB 文件](https://www.mongodb.com/docs/)
- [Redis 文件](https://redis.io/docs/)

---

## 更新記錄

- 2026-02-25: 初始版本建立
- IP: 172.20.10.4 (可能變動)
- PostgreSQL 18.1, MongoDB 7.0.30, Redis 7.4.8

