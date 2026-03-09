from typing import Dict, Any


def news_knowledge_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compatibility fallback.
    目前 news agent 不再主打金融 QA，這個 node 只保留相容性。
    """
    raw_text = (state.get("raw_text") or "").strip()

    state["answer_draft"] = (
        f"目前 News Agent 已簡化為新聞抓取與摘要流程；"
        f"若是金融知識問答，建議由 Finance Knowledge Agent 回答。\n\n"
        f"原始問題：{raw_text}"
    )
    return state