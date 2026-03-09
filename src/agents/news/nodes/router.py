from typing import Dict, Any, List


NEWS_TRIGGER_KEYWORDS = [
    "新聞",
    "最新消息",
    "近期消息",
    "最近消息",
    "相關新聞",
    "有沒有新聞",
    "最近怎麼了",
    "最近發生什麼",
    "近期發生什麼",
    "最新發展",
    "最新動態",
]


def _extract_keywords(text: str) -> List[str]:
    text = (text or "").strip()
    keywords: List[str] = []

    # 極簡但穩定的關鍵字抽取
    candidates = [
        "ETF", "0050", "0056", "00878", "00919", "台股", "美股",
        "科技股", "半導體", "AI", "台積電", "聯發科", "高股息", "升息", "降息"
    ]

    for c in candidates:
        if c in text and c not in keywords:
            keywords.append(c)

    return keywords


def news_router_node(state: Dict[str, Any]) -> Dict[str, Any]:
    raw_text = (state.get("raw_text") or "").strip()
    trigger = (state.get("trigger") or "").strip().lower()

    dbg = state.get("debug") or {}
    dbg.setdefault("router", {})

    if not raw_text:
        state["intent"] = "skip"
        state["question_type"] = "general"
        state["need_news"] = False
        state["need_kb"] = False
        state["keywords"] = []
        dbg["router"] = {"mode": "empty_input"}
        state["debug"] = dbg
        return state

    # parent graph 明確要求新聞
    explicit_trigger = trigger in {"news", "digest", "related_news"}

    # 使用者語句明確提到新聞/消息
    explicit_news_query = any(k in raw_text for k in NEWS_TRIGGER_KEYWORDS)

    if explicit_trigger or explicit_news_query:
        state["intent"] = "digest"
        state["question_type"] = "news_query"
        state["scope"] = "related_news"
        state["need_news"] = True
        state["need_kb"] = False
        state["keywords"] = _extract_keywords(raw_text)

        dbg["router"] = {
            "mode": "explicit_news",
            "trigger": trigger,
            "keywords": state["keywords"],
        }
        state["debug"] = dbg
        return state

    # 預設不處理，直接交還 parent graph
    state["intent"] = "skip"
    state["question_type"] = "general"
    state["scope"] = "general"
    state["need_news"] = False
    state["need_kb"] = False
    state["keywords"] = _extract_keywords(raw_text)

    dbg["router"] = {
        "mode": "skip",
        "trigger": trigger,
        "keywords": state["keywords"],
    }
    state["debug"] = dbg
    return state