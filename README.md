# PFM-Agents 個人財務管理多代理人系統

基於 **TAIDE 模型** + **A2A Protocol** + **MCP** 的個人財務管理多代理人系統。

## 🚀 快速開始

```bash
# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
cp .env.example .env

# 啟動
uvicorn src.api.main:app --reload --port 8000
```

## 📁 專案結構

```
pfm-agents/
├── config/          # 設定檔
├── data/            # 知識庫與 prompts
├── docs/            # 文件
├── src/             # 原始碼
│   ├── agents/      # 各領域 Agent
│   ├── mcp/         # MCP 工具
│   ├── protocols/   # A2A 協議
│   ├── models/      # TAIDE 模型
│   └── api/         # FastAPI
└── tests/           # 測試
```

## 🤖 Agent 架構

| Domain | 主要功能 |
|--------|----------|
| 記帳 Bookkeeping | 交易解析、分類、異常偵測 |
| 目標 Goals | 目標追蹤、進度預測 |
| 投資 Investment | ETF/股票分析 |
| 新聞 News | 財經新聞摘要 |
| 報告 Reports | 財務報告生成 |
| 陪伴 Companion | 主動洞察、互動對話 |

## 📚 技術棧

- **LLM**: TAIDE-LX-7B
- **Agent Protocol**: Google A2A
- **Tool Protocol**: Anthropic MCP
- **Backend**: FastAPI
