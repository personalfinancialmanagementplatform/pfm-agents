#!/bin/bash

echo "🔑 Ngrok 設定助手"
echo ""

# 檢查是否已安裝 ngrok
if ! command -v ngrok &> /dev/null; then
    echo "❌ Ngrok 未安裝"
    echo "請先安裝: brew install ngrok"
    exit 1
fi

# 檢查是否已有 authtoken
EXISTING_TOKEN=$(cat ~/.config/ngrok/ngrok.yml 2>/dev/null | grep "authtoken:" | awk '{print $2}')

if [ -n "$EXISTING_TOKEN" ]; then
    echo "✅ 發現已設定的 authtoken"
    echo ""
    read -p "是否使用現有的 token? (y/n): " USE_EXISTING
    
    if [ "$USE_EXISTING" = "y" ]; then
        AUTHTOKEN=$EXISTING_TOKEN
    else
        echo ""
        echo "請輸入新的 authtoken:"
        read AUTHTOKEN
    fi
else
    echo "請輸入你的 Ngrok authtoken:"
    echo ""
    echo "💡 如果還沒有 token:"
    echo "   1. 前往 https://dashboard.ngrok.com/signup 註冊"
    echo "   2. 前往 https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "   3. 複製 token"
    echo ""
    read -p "Authtoken: " AUTHTOKEN
fi

# 建立 ngrok.yml
cat > ngrok.yml << NGROKCONFIG
version: "2"
authtoken: $AUTHTOKEN

tunnels:
  postgres:
    proto: tcp
    addr: 5432
  
  mongodb:
    proto: tcp
    addr: 27017
  
  redis:
    proto: tcp
    addr: 6379
NGROKCONFIG

echo ""
echo "✅ ngrok.yml 已建立"
echo ""

# 驗證配置
echo "🔍 驗證配置..."
if grep -q "YOUR_AUTHTOKEN_HERE" ngrok.yml; then
    echo "❌ Token 未正確設定"
    exit 1
else
    echo "✅ 配置驗證通過"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 下一步:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. 確保 Docker 運行:"
echo "   docker-compose up -d"
echo ""
echo "2. 啟動 Ngrok:"
echo "   ./scripts/ngrok_start.sh"
echo ""
echo "3. 開新終端，取得網址:"
echo "   ./scripts/get_ngrok_urls.sh"
echo ""

