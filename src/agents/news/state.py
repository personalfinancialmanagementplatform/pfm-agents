from typing import TypedDict, List, Optional, Dict, Any


class NewsState(TypedDict, total=False):
    # =========================
    # Input
    # =========================
    user_id: str
    raw_text: str
    user_level: str
    user_preference: List[str]

    # Optional trigger from parent graph
    trigger: Optional[str]   # news / digest / related_news / qa

    # =========================
    # Router / Understanding
    # =========================
    intent: Optional[str]            # digest / skip
    question_type: Optional[str]     # news_query / general
    scope: Optional[str]
    need_news: Optional[bool]
    need_kb: Optional[bool]

    # extracted keywords
    keywords: Optional[List[str]]

    # =========================
    # Fetch / IR
    # =========================
    candidates: Optional[List[Dict[str, Any]]]   # fetched raw news
    ir_items: Optional[List[Dict[str, Any]]]     # summarized / understood items
    final_items: Optional[List[Dict[str, Any]]]  # ranked items

    # =========================
    # Output
    # =========================
    answer_draft: Optional[str]
    response_message: Optional[str]

    # =========================
    # Debug / Error
    # =========================
    debug: Optional[Dict[str, Any]]
    error: Optional[str]