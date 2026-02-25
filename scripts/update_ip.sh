#!/bin/bash

OLD_IP="172.20.10.4"
NEW_IP="10.234.166.5"

echo "�� 更新 IP: $OLD_IP → $NEW_IP"
echo ""

# 更新 .env.remote
echo "📝 更新 .env.remote..."
cat > .env.remote << 'ENVFILE'
HF_TOKEN=請填入你的_huggingface_token

DB_HOST=10.234.166.5
DB_PORT=5432
DB_NAME=pfm_agents
DB_USER=emily200008
DB_PASSWORD=108306052J

MONGO_HOST=10.234.166.5
MONGO_PORT=27017
MONGO_DB=pfm_agents

REDIS_HOST=10.234.166.5
REDIS_PORT=6379
REDIS_DB=0
ENVFILE

# 更新文件
echo "📝 更新文件中的 IP..."
for file in DOCKER_GUIDE.md DOCKER_SETUP.md QUICK_START.md SETUP_DIAGRAM.md REMOTE_SETUP.md README.md; do
    if [ -f "$file" ]; then
        sed -i '' "s/$OLD_IP/$NEW_IP/g" "$file"
        echo "  ✅ $file"
    fi
done

echo ""
echo "✅ 更新完成！"
echo ""
echo "📊 檢查結果:"
grep -l "$NEW_IP" *.md .env.remote 2>/dev/null | sed 's/^/  ✓ /'

echo ""
echo "📋 下一步:"
echo "1. 檢查文件內容: cat .env.remote"
echo "2. 提交變更: git add . && git commit -m 'docs: update IP to school network'"
echo "3. 推送: git push origin main"

