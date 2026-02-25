# src/agents/finance/orchestrator.py
from __future__ import annotations
from typing import Any, Dict, List, Literal, Tuple
import json

from src.models.taide import get_taide_model
from .state import FinanceState

Intent = Literal["knowledge", "news", "mixed"]
Tone = Literal["simple", "normal"]


def _default_router(state: FinanceState) -> Dict[str, Any]:
    """
    極保守 fallback：不中斷流程，避免整個 graph 掛掉。
    """
    user_level = (state.get("user_level") or "beginner").strip()
    tone: Tone = "simple" if user_level == "beginner" else "normal"

    return {
        "intent": "mixed",
        "need_knowledge": True,
        "need_news": True,
        "tone": tone,
        "reason": ["fallback_default"],
    }


def _validate_router_json(obj: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    for k in ["intent", "need_knowledge", "need_news", "tone"]:
        if k not in obj:
            errors.append(f"missing_key:{k}")

    if "intent" in obj and obj["intent"] not in ("knowledge", "news", "mixed"):
        errors.append("bad_intent")
    if "tone" in obj and obj["tone"] not in ("simple", "normal"):
        errors.append("bad_tone")

    if "need_knowledge" in obj and not isinstance(obj["need_knowledge"], bool):
        errors.append("need_knowledge_not_bool")
    if "need_news" in obj and not isinstance(obj["need_news"], bool):
        errors.append("need_news_not_bool")

    return (len(errors) == 0), errors


def unified_orchestrator(state: FinanceState) -> FinanceState:
    """
    F0: Unified Orchestrator（LLM Router）
    - 不做內容回答，只做 routing decision
    - 輸出：intent / tone / (need_knowledge, need_news)
    - 防呆：JSON parse 失敗或欄位不完整 -> fallback
    """
    raw = (state.get("raw_input") or "").strip()
    user_level = (state.get("user_level") or "beginner").strip()
    prefs = state.get("user_preference") or []

    # 初始化 debug
    dbg = state.get("debug") or {}
    dbg.setdefault("orchestrator", {})

    # 空輸入：直接 fallback
    if not raw:
        fb = _default_router(state)
        state["intent"] = fb["intent"]
        state["tone"] = fb["tone"]
        # 給 coordinator 用（你 finance graph 會用 intent 產 run flags）
        dbg["orchestrator"] = {"mode": "fallback", "reason": ["empty_input"]}
        state["debug"] = dbg
        return state

    model = get_taide_model()

    # 你可以把這個 task_name 加進 TAIDE 的 task_configs（建議）
    task_name = "finance_router"

    prompt = (
        "你是多代理系統的路由器（Router），只負責輸出 JSON，不要解釋。\n"
        "請根據使用者輸入判斷要走哪種路徑：\n"
        "- knowledge：偏概念解釋/名詞/機制\n"
        "- news：偏近期事件/最新消息/新聞摘要\n"
        "- mixed：兩者都需要（先解釋概念再串新聞，或先新聞再概念）\n\n"
        "請輸出 JSON（只能輸出 JSON，不能有多餘文字）：\n"
        "{\n"
        '  "intent": "knowledge" | "news" | "mixed",\n'
        '  "need_knowledge": true | false,\n'
        '  "need_news": true | false,\n'
        '  "tone": "simple" | "normal",\n'
        '  "reason": ["..."]\n'
        "}\n\n"
        f"使用者程度：{user_level}\n"
        f"使用者偏好：{prefs}\n"
        f"使用者輸入：{raw}\n"
    )

    try:
        out = model.generate_task(task_name, prompt)
        parsed = json.loads(out)

        ok, errs = _validate_router_json(parsed)
        if not ok:
            raise ValueError("invalid_router_json:" + ",".join(errs))

        # 填回 state（注意：FinanceState 原本沒有 need_knowledge 欄位，但不影響存放；
        # coordinator 仍以 intent 產生 run_knowledge/run_news）
        state["intent"] = parsed["intent"]
        state["tone"] = parsed["tone"]
        state["need_news"] = bool(parsed["need_news"])  # 你 FinanceState 有 need_news

        dbg["orchestrator"] = {
            "mode": "llm",
            "task": task_name,
            "raw": out,
            "intent": parsed["intent"],
            "need_knowledge": parsed["need_knowledge"],
            "need_news": parsed["need_news"],
            "tone": parsed["tone"],
            "reason": parsed.get("reason", []),
        }
        state["debug"] = dbg
        return state

    except Exception as e:
        fb = _default_router(state)
        state["intent"] = fb["intent"]
        state["tone"] = fb["tone"]
        state["need_news"] = True  # 保守：fallback 時仍嘗試新聞

        dbg["orchestrator"] = {
            "mode": "fallback",
            "error": str(e),
            "reason": fb.get("reason", []),
        }
        state["debug"] = dbg
        return state
