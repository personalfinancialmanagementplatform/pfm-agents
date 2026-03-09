from typing import Dict, Any, List


def _score_item(item: Dict[str, Any], keywords: List[str]) -> float:
    title = (item.get("title") or "").lower()
    summary = (item.get("rewrite_summary") or item.get("summary") or "").lower()
    source = (item.get("source") or "").lower()

    text = f"{title} {summary}"

    # 基礎分數
    score = 0.0

    # 關鍵字命中
    for k in keywords:
        k = (k or "").lower().strip()
        if not k:
            continue
        if k in title:
            score += 3.0
        elif k in text:
            score += 1.5

    # 粗略信任來源加權
    trusted_sources = ["cnyes", "moneydj", "工商時報", "經濟日報", "鉅亨", "udn"]
    if any(s.lower() in source for s in trusted_sources):
        score += 1.0

    return score


def news_rank_node(state: Dict[str, Any]) -> Dict[str, Any]:
    ir_items = state.get("ir_items") or []
    keywords = state.get("keywords") or []

    dbg = state.get("debug") or {}
    dbg.setdefault("rank", {})

    if not ir_items:
        state["final_items"] = []
        dbg["rank"] = {"count": 0}
        state["debug"] = dbg
        return state

    ranked = sorted(
        ir_items,
        key=lambda x: _score_item(x, keywords),
        reverse=True,
    )

    # 保留前 5 則
    final_items = ranked[:5]
    state["final_items"] = final_items

    dbg["rank"] = {
        "count": len(final_items),
        "keywords": keywords,
        "top_titles": [x.get("title") for x in final_items[:3]],
    }
    state["debug"] = dbg
    return state