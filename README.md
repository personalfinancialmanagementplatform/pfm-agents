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
│   ├── database/    # 資料庫模組（PostgreSQL + MongoDB）
│   ├── mcp/         # MCP 工具
│   ├── protocols/   # A2A 協議
│   ├── models/      # TAIDE 模型
│   └── api/         # FastAPI
└── tests/           # 測試
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

### 資料庫分工原則
```
PostgreSQL：結構固定、需要 JOIN、需要交易一致性
  → 使用者、交易、預算、目標

MongoDB：結構彈性、寫入頻繁、不需 JOIN
  → 對話狀態、日誌、事件、新聞、行為分析
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

## 📒 記帳 Domain 架構

### 整體流程
```
輸入: 用戶原始輸入 + 上下文
        ⬇️
Bookkeeping Coordinator Agent（主協調器）
        ⬇️ 分派任務
Intent Recognizer（意圖識別）
        ⬇️
   ┌────┴────┬────────────┐
   ▼         ▼            ▼
record    query       analyze
   ⬇️         ⬇️            ⬇️
[記帳流程] [查詢流程]   [分析流程]
```

### 處理流程
```
用戶輸入 → Intent Recognizer（判斷意圖）→ Coordinator 分派任務
│
├── intent="record"（記帳）
│   → Transaction Parser（解析金額/時間/描述）
│   → Merchant Recognizer（識別商家）
│   → Category Classifier → Sub-Agent（分類）
│   → Anomaly Detector（檢查異常）
│   → Budget Monitor（更新預算狀態）
│   → Database（儲存，透過 MCP Tool: database_insert）
│   → Summary Generator（回覆確認訊息）
│
├── intent="query"（查詢）
│   → Summary Generator（生成摘要回覆）
│   → Report Formatter（格式化輸出）
│
└── intent="analyze"（分析）
    → Spending Analyzer（消費模式分析）
    → Anomaly Detector（異常趨勢）
    → Report Formatter（產出報表）
```

### Agent 清單

#### 🎯 Coordinator Layer

| Agent | 職責 | 模型 |
|-------|------|------|
| Bookkeeping Coordinator | 接收請求、分派任務、彙整結果 | TAIDE + Rule |

#### 📝 Input Processing Layer

| Agent | 職責 | 模型 |
|-------|------|------|
| Transaction Parser | 自然語言 → 結構化資料（金額/時間/描述） | TAIDE + Regex |
| Intent Recognizer | 識別用戶意圖（record/query/analyze） | Rule + TAIDE |

#### 🏷️ Classification Layer

| Agent | 職責 | 模型 |
|-------|------|------|
| Category Classifier | 交易主類別分類 | Rule + ML + TAIDE |
| Merchant Recognizer | 商家識別與學習 | NER + Rule |
| Food Sub-Agent | 飲食細分（早餐/午餐/晚餐/飲料/聚餐） | Rule |
| Transport Sub-Agent | 交通細分（捷運/公車/計程車/加油） | Rule |
| Entertainment Sub-Agent | 娛樂細分（電影/遊戲/串流/KTV） | Rule |
| Shopping Sub-Agent | 購物細分（日用品/服飾/3C/網購） | Rule |
| Medical Sub-Agent | 醫療細分（看診/藥品/保險） | Rule |
| Fixed Expense Sub-Agent | 固定支出細分（房租/水電/電信/訂閱） | Rule |

#### 📊 Analysis Layer

| Agent | 職責 | 模型 |
|-------|------|------|
| Anomaly Detector | 異常消費偵測（單筆異常/頻率異常/重複交易） | Rule（統計） |
| Budget Monitor | 預算設定、追蹤、提醒（50%/80%/100%） | Rule + TAIDE |

#### 📋 Output Layer

| Agent | 職責 | 模型 |
|-------|------|------|
| Summary Generator | 自然語言摘要（日/週/月/類別摘要） | TAIDE |
| Report Formatter | 格式化輸出（JSON/Markdown/圖表數據） | Template |

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
- **Agent Protocol**: Google A2A
- **Tool Protocol**: Anthropic MCP
- **Backend**: FastAPI
- **Database**: PostgreSQL + MongoDB