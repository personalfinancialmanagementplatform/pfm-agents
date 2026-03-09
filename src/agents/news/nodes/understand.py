from typing import Dict, Any, List

try:
    from src.models.taide import get_taide_model
except Exception:
    get_taide_model = None


def _fallback_rewrite(title: str, summary: str) -> str:
    text = (summary or title or "").strip()
    if not text:
        return "目前沒有足夠新聞內容可整理。"
    return text[:180]


def news_understand_node(state: Dict[str, Any]) -> Dict[str, Any]:
    candidates = state.get("candidates") or []

    dbg = state.get("debug") or {}
    dbg.setdefault("understand", {})

    if not candidates:
        state["ir_items"] = []
        dbg["understand"] = {"count": 0}
        state["debug"] = dbg
        return state

    ir_items: List[Dict[str, Any]] = []
    model = None

    if get_taide_model is not None:
        try:
            model = get_taide_model()
        except Exception:
            model = None

    for idx, item in enumerate(candidates):
        title = item.get("title") or ""
        summary = item.get("summary") or ""
        rewrite_summary = None

        if model is not None and hasattr(model, "generate"):
            try:
                prompt = f"""
請將以下新聞用繁體中文整理成 1~2 句簡短摘要，聚焦重點，不要加入未提供資訊。

標題：
{title}

內容：
{summary}
"""
                rewrite_summary = model.generate(prompt).strip()
            except Exception:
                rewrite_summary = _fallback_rewrite(title, summary)
        else:
            rewrite_summary = _fallback_rewrite(title, summary)

        ir_items.append({
            "article_id": item.get("article_id", f"item-{idx}"),
            "title": title,
            "summary": summary,
            "rewrite_summary": rewrite_summary,
            "source": item.get("source", ""),
            "url": item.get("url", ""),
        })

    state["ir_items"] = ir_items
    dbg["understand"] = {"count": len(ir_items)}
    state["debug"] = dbg
    return state