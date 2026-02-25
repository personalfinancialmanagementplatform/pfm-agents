#!/bin/bash

echo "🔍 查詢 Ngrok 隧道資訊..."
echo ""

# 檢查 Ngrok 是否運行
if ! curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
    echo "❌ 無法連接到 Ngrok API"
    echo ""
    echo "請確認："
    echo "  1. Ngrok 是否正在運行？"
    echo "     執行: ./scripts/ngrok_start.sh"
    echo ""
    echo "  2. 是否在另一個終端視窗運行？"
    echo ""
    exit 1
fi

# 從 Ngrok API 取得隧道資訊
TUNNELS=$(curl -s http://localhost:4040/api/tunnels)

# 解析各個隧道的 URL
POSTGRES_URL=$(echo "$TUNNELS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        if tunnel.get('name') == 'postgres':
            url = tunnel.get('public_url', '')
            print(url.replace('tcp://', ''))
            break
except:
    pass
")

MONGODB_URL=$(echo "$TUNNELS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        if tunnel.get('name') == 'mongodb':
            url = tunnel.get('public_url', '')
            print(url.replace('tcp://', ''))
            break
except:
    pass
")

REDIS_URL=$(echo "$TUNNELS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        if tunnel.get('name') == 'redis':
            url = tunnel.get('public_url', '')
            print(url.replace('tcp://', ''))
            break
except:
    pass
")

if [ -z "$POSTGRES_URL" ] || [ -z "$MONGODB_URL" ] || [ -z "$REDIS_URL" ]; then
    echo "❌ 無法取得完整的隧道資訊"
    echo ""
    echo "請檢查 Ngrok 是否正確啟動"
    echo "或訪問: http://localhost:4040"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 Ngrok 隧道資訊"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "PostgreSQL: $POSTGRES_URL"
echo "MongoDB:    $MONGODB_URL"
echo "Redis:      $REDIS_URL"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "👥 組員的 .env 設定"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 分離主機和端口
PG_HOST=$(echo $POSTGRES_URL | cut -d':' -f1)
PG_PORT=$(echo $POSTGRES_URL | cut -d':' -f2)
MONGO_HOST=$(echo $MONGODB_URL | cut -d':' -f1)
MONGO_PORT=$(echo $MONGODB_URL | cut -d':' -f2)
REDIS_HOST=$(echo $REDIS_URL | cut -d':' -f1)
REDIS_PORT=$(echo $REDIS_URL | cut -d':' -f2)

# 顯示設定
cat << ENVCONFIG
HF_TOKEN=你的token

DB_HOST=$PG_HOST
DB_PORT=$PG_PORT
DB_NAME=pfm_agents
DB_USER=emily200008
DB_PASSWORD=108306052J

MONGO_HOST=$MONGO_HOST
MONGO_PORT=$MONGO_PORT
MONGO_DB=pfm_agents

REDIS_HOST=$REDIS_HOST
REDIS_PORT=$REDIS_PORT
REDIS_DB=0
ENVCONFIG

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 更新 .env.remote
cat > .env.remote << REMOTENV
# Ngrok 隧道設定
# 更新時間: $(date '+%Y-%m-%d %H:%M:%S')
# 
# ⚠️ 注意: Ngrok 免費版每次重啟網址會變
# Emily 重啟 Ngrok 後，請重新執行此腳本並推送更新

HF_TOKEN=請填入你的token

DB_HOST=$PG_HOST
DB_PORT=$PG_PORT
DB_NAME=pfm_agents
DB_USER=emily200008
DB_PASSWORD=108306052J

MONGO_HOST=$MONGO_HOST
MONGO_PORT=$MONGO_PORT
MONGO_DB=pfm_agents

REDIS_HOST=$REDIS_HOST
REDIS_PORT=$REDIS_PORT
REDIS_DB=0
REMOTENV

echo "✅ .env.remote 已更新"
echo ""
echo "📤 下一步: 推送到 GitHub"
echo "   git add .env.remote"
echo "   git commit -m 'chore: update Ngrok URLs ($(date +%Y-%m-%d))'"
echo "   git push origin main"
echo ""

# 複製到剪貼簿（macOS）
echo "DB_HOST=$PG_HOST
DB_PORT=$PG_PORT
MONGO_HOST=$MONGO_HOST
MONGO_PORT=$MONGO_PORT
REDIS_HOST=$REDIS_HOST
REDIS_PORT=$REDIS_PORT" | pbcopy 2>/dev/null && echo "✅ 連線資訊已複製到剪貼簿" || true

