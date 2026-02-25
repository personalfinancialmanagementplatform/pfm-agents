#!/bin/bash

echo "🚇 啟動 Ngrok 隧道..."
echo ""

# 檢查 ngrok 是否安裝
if ! command -v ngrok &> /dev/null; then
    echo "❌ Ngrok 未安裝"
    echo ""
    echo "安裝方式："
    echo "  brew install ngrok"
    echo ""
    exit 1
fi

# 檢查配置檔
if [ ! -f ngrok.yml ]; then
    echo "❌ ngrok.yml 不存在"
    echo ""
    echo "請先建立配置檔："
    echo "  cp ngrok.yml.example ngrok.yml"
    echo "  nano ngrok.yml  # 填入你的 authtoken"
    echo ""
    exit 1
fi

# 檢查 Docker 是否運行
if ! docker ps | grep -q postgres; then
    echo "⚠️  PostgreSQL 容器未運行"
    echo "正在啟動 Docker..."
    docker-compose up -d
    sleep 5
fi

echo "🚀 啟動 Ngrok 隧道..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  重要提示："
echo "  1. 請保持這個視窗開啟"
echo "  2. 按 Ctrl+C 可以停止 Ngrok"
echo "  3. 啟動後，開新終端執行："
echo "     ./scripts/get_ngrok_urls.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "正在啟動..."
sleep 2

# 啟動 ngrok
ngrok start --all --config ngrok.yml

