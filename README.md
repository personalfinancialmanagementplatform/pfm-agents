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

## 📁 專案結構
```
pfm-agents/
├── config/              # 設定檔
├── data/                # 知識庫與 prompts
├── docs/                # 文件
├── src/                 # 原始碼
│   ├── agents/          # 各領域 Agent（LangGraph Nodes）
│   │   ├── base/        # State 定義與共用結構
│   │   └── bookkeeping/ # 記帳 Domain
│   │       ├── processing/     # 交易解析
│   │       ├── classification/ # 分類
│   │       └── analysis/       # 異常偵測、預算監控
│   ├── database/        # 資料庫模組
│   │   ├── connection.py       # PostgreSQL 連線
│   │   ├── crud.py             # PostgreSQL CRUD
│   │   ├── mongo_connection.py # MongoDB 連線
│   │   ├── mongo_crud.py       # MongoDB CRUD
│   │   ├── redis_connection.py # Redis 連線
│   │   └── redis_crud.py       # Redis CRUD
│   ├── mcp/             # MCP 工具
│   ├── protocols/       # A2A 協議
│   ├── models/          # TAIDE 模型
│   └── api/             # FastAPI
└── tests/               # 測試
```

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

儲存非結構化 / 半結構化資料。

| Collection | 用途 |
|------------|------|
| conversation_states | Agent 對話狀態 |
| llm_logs | LLM 解析日誌（輸入/輸出/延遲） |
| events | 事件總線（Agent 間通訊記錄） |
| financial_news | 財經新聞 |
| user_behaviors | 使用者行為記錄 |
| goal_strategies | AI 目標策略建議 |

### Redis（快取與即時數據）

即時快取，提升回應速度。

| 功能 | Key 格式 | 過期時間 |
|------|----------|----------|
| 使用者 Session | `session:{user_id}` | 30 分鐘 |
| 預算快取 | `budget:{user_id}` | 1 小時 |
| 分類快取 | `categories:all` | 24 小時 |
| Rate Limiting | `rate:{user_id}` | 1 分鐘 |
| 當日消費總額 | `daily_total:{user_id}:{date}` | 2 小時 |

### 資料庫分工原則
```
PostgreSQL：結構固定、需要 JOIN、需要交易一致性
  → 使用者、交易、預算、目標

MongoDB：結構彈性、寫入頻繁、不需 JOIN
  → 對話狀態、日誌、事件、新聞、行為分析

Redis：高速讀寫、短期暫存、即時數據
  → Session、快取、限流、當日統計
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

---

## 📒 記帳 Domain 架構（LangGraph）

使用 **LangGraph** 將各 Agent 改為 **Node**，以 **BookkeepingState** 作為共享狀態流轉。所有 Node 皆使用 **TAIDE LLM** 進行語意理解，不使用 rule-based。

### LangGraph State
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
raw_text
  ↓
transaction_parser_node（TAIDE 解析金額/商家/描述，理解錯字口語）
  ↓
category_classifier_node（TAIDE 判斷分類）
  ↓
anomaly_detector_node（DB 查歷史統計 + TAIDE 綜合判斷異常）
  ↓
budget_monitor_node（DB 查預算目標 + TAIDE 判斷歸屬 + 計算剩餘額度）
  ↓
db_save_node（儲存到 PostgreSQL）
  ↓
summary_generator_node（TAIDE 生成回覆訊息）
```

### Node 清單與開發進度

#### 📝 Processing Layer

| Node | 職責 | 方式 | 狀態 |
|------|------|------|------|
| transaction_parser_node | 自然語言 → 結構化交易資料（理解錯字、口語） | 純 TAIDE LLM | ✅ 完成 |

#### 🏷️ Classification Layer

| Node | 職責 | 方式 | 狀態 |
|------|------|------|------|
| category_classifier_node | 判斷交易所屬分類 | 純 TAIDE LLM + DB 分類表 | ✅ 完成 |

#### 📊 Analysis Layer

| Node | 職責 | 方式 | 狀態 |
|------|------|------|------|
| anomaly_detector_node | 異常消費偵測（重複/金額偏高/頻率異常） | TAIDE LLM + DB 統計 | ✅ 完成 |
| budget_monitor_node | 預算匹配、已花費計算、剩餘額度、超支提醒 | TAIDE LLM + DB 預算查詢 | ✅ 完成 |

#### 💾 Storage Layer

| Node | 職責 | 方式 | 狀態 |
|------|------|------|------|
| db_save_node | 儲存交易到 PostgreSQL | DB CRUD | 🔲 待開發 |

#### 📋 Output Layer

| Node | 職責 | 方式 | 狀態 |
|------|------|------|------|
| summary_generator_node | 生成自然語言回覆訊息 | TAIDE LLM | 🔲 待開發 |

#### 🎯 Coordinator

| 項目 | 狀態 |
|------|------|
| LangGraph Graph（串接所有 Node） | 🔲 待開發 |
| Intent Router（record/query/analyze 分流） | 🔲 待開發 |

### 跨 Domain 通訊（A2A）
```
記帳 Domain → 目標 Domain
  budget_monitor_node 計算預算使用狀況
  → A2A 傳送至目標 Domain
  → 目標 Domain 提醒使用者
```

### MCP Tools
```yaml
mcp_tools:
  - database_query    # 查詢交易紀錄
  - database_insert   # 新增交易紀錄
  - database_update   # 更新交易紀錄
```

---

## 📚 技術棧

- **LLM**: TAIDE-LX-7B
- **Agent Framework**: LangGraph
- **Agent Protocol**: Google A2A
- **Tool Protocol**: Anthropic MCP
- **Backend**: FastAPI
- **Database**: PostgreSQL + MongoDB + Redis
