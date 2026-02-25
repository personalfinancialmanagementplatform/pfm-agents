#!/bin/bash

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 Emily 的資料庫連線資訊"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 查詢 IP 和主機名稱
CURRENT_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)
HOSTNAME=$(hostname)

echo "🔍 當前網路資訊："
echo "  IP 地址: $CURRENT_IP"
echo "  主機名稱: $HOSTNAME"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "👥 給組員的設定（兩種方式）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📌 方式 1: 使用主機名稱（推薦先試這個）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat << METHOD1
DB_HOST=$HOSTNAME
MONGO_HOST=$HOSTNAME
REDIS_HOST=$HOSTNAME
METHOD1

echo ""
echo "�� 方式 2: 使用 IP 地址（如果方式 1 不行）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat << METHOD2
DB_HOST=$CURRENT_IP
MONGO_HOST=$CURRENT_IP
REDIS_HOST=$CURRENT_IP
METHOD2

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 完整的 .env 設定（複製給組員）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "# 組員請先試方式 1，不行再用方式 2"
echo ""
echo "# 方式 1: 使用主機名稱"
cat << FULLENV1
HF_TOKEN=你的token

DB_HOST=$HOSTNAME
DB_PORT=5432
DB_NAME=pfm_agents
DB_USER=emily200008
DB_PASSWORD=108306052J

MONGO_HOST=$HOSTNAME
MONGO_PORT=27017
MONGO_DB=pfm_agents

REDIS_HOST=$HOSTNAME
REDIS_PORT=6379
REDIS_DB=0
FULLENV1

echo ""
echo "# 方式 2: 使用 IP 地址"
cat << FULLENV2
HF_TOKEN=你的token

DB_HOST=$CURRENT_IP
DB_PORT=5432
DB_NAME=pfm_agents
DB_USER=emily200008
DB_PASSWORD=108306052J

MONGO_HOST=$CURRENT_IP
MONGO_PORT=27017
MONGO_DB=pfm_agents

REDIS_HOST=$CURRENT_IP
REDIS_PORT=6379
REDIS_DB=0
FULLENV2

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 更新 .env.remote（同時包含兩種方式的說明）
cat > .env.remote << ENVFILE
# 組員連線設定
# Emily 最後更新時間: $(date '+%Y-%m-%d %H:%M:%S')
# 
# 請先試方式 1（主機名稱），如果連線失敗再用方式 2（IP）

HF_TOKEN=請填入你的token

# === 方式 1: 使用主機名稱（推薦） ===
# 優點: 不會因為 IP 變動而失效
# 缺點: 需要在同一區域網路
# 
DB_HOST=$HOSTNAME
# DB_HOST=$CURRENT_IP  # 如果方式 1 不行，取消這行註解，註解上面那行

DB_PORT=5432
DB_NAME=pfm_agents
DB_USER=emily200008
DB_PASSWORD=108306052J

MONGO_HOST=$HOSTNAME
# MONGO_HOST=$CURRENT_IP  # 如果方式 1 不行，取消這行註解，註解上面那行

MONGO_PORT=27017
MONGO_DB=pfm_agents

REDIS_HOST=$HOSTNAME
# REDIS_HOST=$CURRENT_IP  # 如果方式 1 不行，取消這行註解，註解上面那行

REDIS_PORT=6379
REDIS_DB=0
ENVFILE

echo "✅ .env.remote 已更新"
echo ""
echo "📤 推送到 GitHub："
echo "   git add .env.remote"
echo "   git commit -m 'chore: update connection info'"
echo "   git push origin main"
echo ""

# 複製主機名稱版本到剪貼簿（macOS）
echo "DB_HOST=$HOSTNAME
MONGO_HOST=$HOSTNAME
REDIS_HOST=$HOSTNAME" | pbcopy 2>/dev/null && echo "✅ 方式 1（主機名稱）已複製到剪貼簿" || echo "💡 可以手動複製上面的設定"

