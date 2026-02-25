# 組員快速開始（Ngrok 版本）

## 🚀 三步驟連線

### 1. 拉取最新設定
```bash
git pull origin main
```

### 2. 複製並編輯 .env
```bash
cp .env.remote .env
nano .env
```

**填入你的 HF_TOKEN：**
```env
HF_TOKEN=你的實際token  # 從 https://huggingface.co/settings/tokens 取得
```

其他設定保持不變，已經配置好 Ngrok 網址。

### 3. 測試連線
```bash
python3 scripts/test_connection.py
```

看到三個 ✅ 就成功了！

---

## 🌍 優點

- ✅ 在家也能連線
- ✅ 不需要在同一網路
- ✅ 不受 IP 變動影響

---

## 📡 當前連線資訊
```
PostgreSQL: 0.tcp.jp.ngrok.io:10850
MongoDB:    0.tcp.jp.ngrok.io:15892
Redis:      0.tcp.jp.ngrok.io:11692
```

⚠️ **注意**: Emily 重啟 Ngrok 後網址會變，請重新 `git pull`

---

## ❓ 連線失敗？

1. 確認 `.env` 有填入你的 HF_TOKEN
2. 執行 `git pull` 確保有最新網址
3. 問 Emily 確認 Ngrok 是否在運行

