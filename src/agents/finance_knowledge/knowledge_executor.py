from typing import Any, Dict
from src.tools.kb_rag_client import kb_search
from src.models.taide import taide_generate
from .state import FinanceState

def _build_context(kb: Dict[str, Any]) -> str:
    top = kb.get("top") or {}
    payload = top.get("payload") or {}
    # 你可以改成用 top["doc"]（你 table 有 doc 欄位），或 payload["summary"] + key_points
    title = top.get("title") or payload.get("title") or ""
    summary = payload.get("summary") or ""
    key_points = payload.get("key_points") or []
    pitfalls = payload.get("pitfalls") or []
    example = payload.get("example") or ""

    kp = "\n".join([f"- {x}" for x in key_points]) if key_points else "- （無）"
    pf = "\n".join([f"- {x}" for x in pitfalls]) if pitfalls else "- （無）"

    return f"""[KB_TITLE] {title}
[KB_SUMMARY] {summary}

[KB_KEY_POINTS]
{kp}

[KB_EXAMPLE]
{example}

[KB_PITFALLS]
{pf}
""".strip()

def knowledge_executor(state: FinanceState) -> FinanceState:
    q = (state.get("raw_text") or "").strip()
    lvl = state.get("user_level") or "beginner"

    state.setdefault("debug", {})
    state["debug"]["kb_rag"] = {"query": q, "level": lvl}

    # 1) 檢索 KB
    kb = kb_search(q, top_k=5, level=lvl, include_related=True)
    top = kb.get("top")

    # 2) 檢索命中判斷（distance 越小越像；你可以訂一個閾值）
    #    這裡先記錄，後面 coordinator 也可以用它決策
    top_dist = None
    if top and "distance" in top:
        try:
            top_dist = float(top["distance"])
        except Exception:
            top_dist = None

    state["debug"]["kb_rag"].update({
        "top_id": top.get("id") if top else None,
        "top_title": top.get("title") if top else None,
        "top_distance": top_dist,
        "candidates": kb.get("candidates", []),
    })

    if not top:
        state["knowledge_content"] = "知識庫目前沒有命中相關內容，我先用一般概念說明（可能不完整），你也可以提供更具體的關鍵字。"
        return state

    context = _build_context(kb)

    prompt = f"""你是一位給新手看的理財老師。
    請依照【知識庫內容】用白話解釋，避免投資建議與保證，必要時用「可能/通常/視情況」措辭。
    若知識庫內容不足，請明確說「知識庫未提供」並只補充通用概念。

    【使用者問題】
    {q}

    【知識庫內容】
    {context}
    """

    # 3) grounded 生成
    ans = taide_generate(prompt, task_name="finance_generate")
    state["knowledge_content"] = ans

    return state