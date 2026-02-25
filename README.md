# PFM-Agents 個人財務管理多代理人系統

基於 **TAIDE 模型** + **LangGraph** + **A2A Protocol** + **MCP** 的個人財務管理多代理人系統。

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

## ▶️ Demo：記帳流程
```bash
# Mock 模式測試完整記帳流程
USE_MOCK_MODEL=true python -c "
from src.agents.bookkeeping.graph import run_bookkeeping
result = run_bookkeeping('今天吃麥當勞150', user_id=1)
print('回覆:', result['response_message'])
"
```

## 📁 專案結構
```
pfm-agents/
├── config/                      # 設定檔
│   └── model/
│       └── taide.yaml           # TAIDE 模型配置
├── data/                        # 知識庫與 prompts
│   ├── knowledge/               # 類別/商家知識庫
│   └── prompts/                 # Prompt 模板
├── docs/                        # 架構文件
├── scripts/                     # 工具腳本
│   └── download_model.py        # TAIDE 模型下載
├── src/                         # 原始碼
│   ├── agents/                  # 各領域 Agent（LangGraph Nodes）
│   │   ├── base/                # BookkeepingState 定義與共用結構
│   │   └── bookkeeping/         # 記帳 Domain
│   │       ├── graph.py                #  LangGraph 流程串接
│   │       ├── coordinator.py          # Bookkeeping Coordinator
│   │       ├── processing/             # Input Processing Layer
│   │       │   └── transaction_parser.py   # 交易解析（純 LLM）
│   │       ├── classification/         # Classification Layer
│   │       │   └── category_classifier.py  # 分類（純 LLM）
│   │       ├── analysis/               # Analysis Layer
│   │       │   ├── anomaly_detector.py     # 異常偵測（LLM + 統計規則）
│   │       │   └── budget_monitor.py       # 預算監控（LLM + 預算規則）
│   │       ├── storage/                # Storage Layer
│   │       │   └── db_save.py              # DB 儲存（Mock → PostgreSQL）
│   │       └── output/                 # Output Layer
│   │           └── summary_generator.py    # 回覆訊息生成（LLM + Fallback）
│   ├── database/                # 資料庫模組
│   │   ├── connection.py               # PostgreSQL 連線
│   │   ├── create_tables.py            # 建表腳本
│   │   ├── crud.py                     # PostgreSQL CRUD
│   │   ├── mongo_connection.py         # MongoDB 連線
│   │   ├── mongo_crud.py              # MongoDB CRUD
│   │   ├── redis_connection.py         # Redis 連線
│   │   └── redis_crud.py              # Redis CRUD
│   ├── models/                  # TAIDE 模型載入器
│   │   └── taide.py
│   ├── mcp/                     # MCP 工具
│   ├── protocols/               # A2A 協議
│   └── api/                     # FastAPI
│       ├── main.py
│       └── routes/
│           ├── bookkeeping.py
│           └── health.py
├── tests/                       # 測試
│   └── test_transaction_parser.py
├── models/                      # TAIDE-LX-7B 模型檔案（本地）
├── .env.example
├── requirements.txt
└── README.md
```

## 🔧 技術架構

### 核心技術
| 技術 | 用途 | 說明 |
|------|------|------|
| **TAIDE-LX-7B** | LLM | 繁體中文語言模型，用於所有語意理解任務 |
| **LangGraph** | Agent 框架 | 將 Agent 設計為 Node，透過 State 流轉資料 |
| **A2A Protocol** | Agent 間通訊 | 跨 Domain Agent 協作（如記帳→目標追蹤） |
| **MCP** | 工具協議 | Agent 呼叫外部工具（DB 查詢、寫入等） |
| **FastAPI** | 後端 | API 服務 |
| **PostgreSQL** | 主資料庫 | 使用者、交易、預算、目標 |
| **MongoDB** | 彈性儲存 | 對話狀態、日誌、事件、新聞 |
| **Redis** | 快取 | Session、預算快取、限流 |

### 設計原則
- 所有 Node 皆使用 **TAIDE LLM** 進行語意理解，不使用 rule-based
- 各 Node 透過 **BookkeepingState** 共享狀態流轉
- 跨 Domain 通訊採用 **A2A Protocol**，各 Domain 獨立開發
- DB 尚未連上的 Node 使用 **Mock 數據**，之後替換

## 💾 資料庫架構

### PostgreSQL（結構化數據）

儲存核心業務資料，使用純 SQL + psycopg2 操作。

| 資料表 | 用途 |
|--------|------|
| users | 使用者資料（LINE ID、姓名、生日、性別） |
| categories | 消費分類（17 個預設分類含子分類） |
| transactions | 交易記錄（收入/支出） |
| budgets | 預算管理 |
| financial_goals | 財務目標追蹤 |

### MongoDB（彈性數據）

| Collection | 用途 |
|------------|------|
| conversation_states | Agent 對話狀態 |
| llm_logs | LLM 解析日誌 |
| events | 事件總線（Agent 間通訊記錄） |
| financial_news | 財經新聞 |
| user_behaviors | 使用者行為記錄 |

### Redis（快取與即時數據）

| 功能 | Key 格式 | 過期時間 |
|------|----------|----------|
| 使用者 Session | `session:{user_id}` | 30 分鐘 |
| 預算快取 | `budget:{user_id}` | 1 小時 |
| 分類快取 | `categories:all` | 24 小時 |
| 當日消費總額 | `daily_total:{user_id}:{date}` | 2 小時 |

## 🤖 Agent 架構

| Domain | 主要功能 |
|--------|----------|
| 記帳 Bookkeeping | 交易解析、分類、異常偵測、預算監控 |
| 金融知識 Finance Knowledge | ETF/指數/基金知識問答 |
| 目標 Goals | 目標追蹤、進度預測 |
| 投資 Investment | ETF/股票分析 |
| 新聞 News | 財經新聞摘要 |
| 報告 Reports | 財務報告生成 |
| 陪伴 Companion | 主動洞察、互動對話 |

## 📒 記帳 Domain（LangGraph）

使用 **LangGraph** 將各 Agent 改為 **Node**，以 **BookkeepingState** 作為共享狀態流轉。所有 Node 皆使用 **TAIDE LLM** 進行語意理解。

### BookkeepingState
```python
class BookkeepingState(TypedDict):
    # 輸入
    user_id, raw_text, intent
    # Parser 輸出
    amount, transaction_type, description, time_hint, merchant
    # Classifier 輸出
    category_id, category_name
    # Anomaly 輸出
    is_anomaly, anomaly_reason
    # Budget 輸出
    budget_warning, budget_level
    # DB 結果
    transaction_id, db_success
    # 最終輸出
    response_message, error
```

### Record 流程（LangGraph Graph）
```
用戶輸入 raw_text
  ↓
transaction_parser_node（TAIDE 解析金額/商家/描述，理解錯字口語）
  ↓ 解析失敗 → 直接跳到 summary（錯誤處理）
category_classifier_node（TAIDE 判斷分類）
  ↓
anomaly_detector_node（統計規則初篩 + TAIDE 綜合判斷異常）
  ↓
budget_monitor_node（預算規則計算 + TAIDE 生成提醒）
  ↓
db_save_node（儲存到 PostgreSQL）
  ↓
summary_generator_node（TAIDE 生成回覆 / Fallback 規則生成）
  ↓
回覆用戶
```

### 開發進度

| Layer | Node | 方式 | 狀態 |
|-------|------|------|------|
| Processing | transaction_parser_node | 純 TAIDE LLM |  完成 |
| Classification | category_classifier_node | 純 TAIDE LLM + DB 分類表 |  完成 |
| Analysis | anomaly_detector_node | TAIDE LLM + 統計規則（Mock） |  完成 |
| Analysis | budget_monitor_node | TAIDE LLM + 預算規則（Mock） |  完成 |
| Storage | db_save_node | DB CRUD（Mock） |  完成 |
| Output | summary_generator_node | TAIDE LLM + Fallback |  完成 |
| Coordinator | LangGraph Graph 串接 | LangGraph |  完成 |
| Coordinator | Intent Router（record/query/analyze） | TAIDE LLM | 待開發 |

### 跨 Domain 通訊（A2A）
```
記帳完成 → A2A → 目標 Domain：「用戶花了 $150，請更新儲蓄目標進度」
異常消費 → A2A → 陪伴 Domain：「偵測到異常消費，請斟酌提醒時機」
投資支出 → A2A → 投資 Domain：「用戶購買 0050，請記錄投資交易」
月底統計 → A2A → 報告 Domain：「請求記帳數據以生成月度報告」
```

### MCP Tools
```yaml
mcp_tools:
  - database_query    # 查詢交易紀錄
  - database_insert   # 新增交易紀錄
  - database_update   # 更新交易紀錄
```

## 🌿 Branch 說明

| Branch | 內容 | 狀態 |
|--------|------|------|
| `main` | 穩定版本，各 branch 完成後 merge | — |
| `bookkeeping` | 記帳 Domain 完整 LangGraph 流程 | 開發中 |
| `finance-knowledge` | 金融知識 Agent（ETF/指數/基金知識庫） | PR 審核中 |

## 📚 技術棧

- **LLM**: TAIDE-LX-7B
- **Agent Framework**: LangGraph
- **Agent Protocol**: Google A2A
- **Tool Protocol**: Anthropic MCP
- **Backend**: FastAPI
- **Database**: PostgreSQL + MongoDB + Redis


## 🐳 Docker 環境設定

詳見 [DOCKER_GUIDE.md](DOCKER_GUIDE.md)

### 快速啟動
```bash
# 啟動資料庫
docker-compose up -d

# 測試連線
python3 scripts/test_connection.py
```

## 📚 文件
- [Docker 使用指南](DOCKER_GUIDE.md)
- [遠端連線設定](REMOTE_SETUP.md)