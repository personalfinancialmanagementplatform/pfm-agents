from typing import Dict, Any, List


def _format_items(items: List[Dict[str, Any]]) -> str:
    blocks = []
    for i, item in enumerate(items[:5], start=1):
        title = item.get("title") or "（無標題）"
        summary = item.get("rewrite_summary") or item.get("summary") or "（無摘要）"
        source = item.get("source") or "未知來源"

        blocks.append(
            f"{i}. {title}\n"
            f"   摘要：{summary}\n"
            f"   來源：{source}"
        )
    return "\n\n".join(blocks)


def news_present_node(state: Dict[str, Any]) -> Dict[str, Any]:
    intent = state.get("intent") or "skip"
    final_items = state.get("final_items") or []
    keywords = state.get("keywords") or []

    if intent == "skip":
        state["response_message"] = ""
        return state

    if not final_items:
        kw_text = "、".join(keywords) if keywords else "相關主題"
        state["response_message"] = f"目前沒有找到與「{kw_text}」明確相關的新聞。"
        return state

    kw_text = "、".join(keywords) if keywords else "相關主題"
    body = _format_items(final_items)

    state["response_message"] = (
        f"以下是與「{kw_text}」相關的近期新聞整理：\n\n{body}"
    )
    return state