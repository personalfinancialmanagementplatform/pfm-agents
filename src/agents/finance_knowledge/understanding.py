# src/agents/finance/understanding.py
from __future__ import annotations
from typing import Any, Dict, List, Tuple
import json

from src.models.taide import get_taide_model
from .state import FinanceState


def _default_understanding(state: FinanceState) -> Dict[str, Any]:
    """
    fallback：保守抽取（至少不讓 concepts 變成空/None）
    """
    text = (state.get("raw_text") or "").strip()
    concepts: List[str] = []
    if "ETF" in text.upper():
        concepts.append("ETF")
    if "0050" in text:
        concepts.append("台股ETF")
    if "升息" in text:
        concepts.append("升息")
    need_news = any(k in text for k in ["最近", "新聞", "最新", "今天", "本週", "這幾天"])
    return {"concepts": concepts, "need_news": bool(need_news), "reason": ["fallback_keywords"]}


def _validate_understanding_json(obj: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if "concepts" not in obj:
        errors.append("missing_key:concepts")
    if "need_news" not in obj:
        errors.append("missing_key:need_news")

    if "concepts" in obj and not isinstance(obj["concepts"], list):
        errors.append("concepts_not_list")
    if "concepts" in obj and isinstance(obj["concepts"], list):
        if any(not isinstance(x, str) for x in obj["concepts"]):
            errors.append("concepts_item_not_str")

    if "need_news" in obj and not isinstance(obj["need_news"], bool):
        errors.append("need_news_not_bool")

    return (len(errors) == 0), errors


def understanding_node(state: FinanceState) -> FinanceState:
    """
    Understanding Node（LLM 抽取）
    - 抽取 concepts（關鍵概念）
    - 判斷 need_news（是否需要查近期新聞/事件）
    - 防呆：JSON parse 失敗 -> fallback
    """
    raw = (state.get("raw_text") or "").strip()

    dbg = state.get("debug") or {}
    dbg.setdefault("understanding", {})

    if not raw:
        fb = _default_understanding(state)
        state["concepts"] = fb["concepts"]
        state["need_news"] = fb["need_news"]
        dbg["understanding"] = {"mode": "fallback", "reason": ["empty_input"]}
        state["debug"] = dbg
        return state

    model = get_taide_model()
    task_name = "finance_understanding"

    prompt = (
        "你是金融多代理系統的理解模組（Understanding），只負責抽取結構化資訊，輸出 JSON，不要解釋。\n"
        "請從使用者輸入中抽取最重要的 0~5 個金融概念（concepts），並判斷是否需要近期新聞（need_news）。\n"
        "注意：\n"
        "- concepts 要用繁體中文、短詞（例如：ETF、升息、殖利率、通膨、台股ETF、0050）\n"
        "- need_news 若問題涉及『最近/最新/新聞/事件/發生了什麼』或需要事件背景，設為 true\n\n"
        "請輸出 JSON（只能輸出 JSON，不能有多餘文字）：\n"
        "{\n"
        '  "concepts": ["..."],\n'
        '  "need_news": true | false,\n'
        '  "reason": ["..."]\n'
        "}\n\n"
        f"使用者輸入：{raw}\n"
    )

    try:
        out = model.generate_task(task_name, prompt)
        parsed = json.loads(out)
        ok, errs = _validate_understanding_json(parsed)
        if not ok:
            raise ValueError("invalid_understanding_json:" + ",".join(errs))

        # concepts 防呆：最多 5 個、去空白、去重
        concepts_raw: List[str] = [x.strip() for x in parsed["concepts"] if isinstance(x, str)]
        concepts: List[str] = []
        seen = set()
        for c in concepts_raw:
            if not c or c in seen:
                continue
            seen.add(c)
            concepts.append(c)
            if len(concepts) >= 5:
                break

        state["concepts"] = concepts
        state["need_news"] = bool(parsed["need_news"])

        dbg["understanding"] = {
            "mode": "llm",
            "task": task_name,
            "raw": out,
            "concepts": concepts,
            "need_news": parsed["need_news"],
            "reason": parsed.get("reason", []),
        }
        state["debug"] = dbg
        return state

    except Exception as e:
        fb = _default_understanding(state)
        state["concepts"] = fb["concepts"]
        state["need_news"] = fb["need_news"]
        dbg["understanding"] = {"mode": "fallback", "error": str(e), "reason": fb.get("reason", [])}
        state["debug"] = dbg
        return state
