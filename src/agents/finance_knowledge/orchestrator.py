def unified_orchestrator(state: dict) -> dict:
    """
    判斷任務型態與回覆風格
    """
    text = state["raw_input"]

    # 非 LLM，快速 routing（降低成本）
    if any(k in text for k in ["是什麼", "怎麼", "意思"]):
        state["intent"] = "knowledge"
    elif any(k in text for k in ["新聞", "發生", "最近"]):
        state["intent"] = "news"
    else:
        state["intent"] = "mixed"

    # 回覆模式（規則式個人化）
    if state.get("user_level") == "beginner":
        state["tone"] = "simple"
    else:
        state["tone"] = "normal"

    return state
