# 組員快速設定指南

## 🚀 三步驟開始

### 1. Clone 專案
```bash
git clone https://github.com/personalfinancialmanagementplatform/pfm-agents.git
cd pfm-agents
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 設定 .env
```bash
cp .env.example .env
nano .env
```

**改成這樣（重要！）：**
```env
HF_TOKEN=你的token

# 用學校網路的 IP
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
```

### 3. 測試連線
```bash
python3 scripts/test_connection.py
```

看到三個 ✅ 就成功了！

---

## ⚠️ 注意事項

1. **必須在學校網路**（同一個 Wi-Fi）
2. **Emily 的電腦必須開著並執行 Docker**
3. **Emily 的 IP**: `10.234.166.5`

---

## ❓ 常見問題

**Q: 連線失敗？**
- 確認在學校 Wi-Fi
- 確認 Emily 的 Docker 在運行
- 問 Emily 😊

**Q: IP 變了？**
- 問 Emily 新的 IP
- 更新 .env 檔案

---

## 📞 需要幫助
找 Emily 🙋‍♀️
