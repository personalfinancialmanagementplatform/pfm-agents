from .state import FinanceState


def domain_coordinator(state: FinanceState) -> FinanceState:
    """
    決定要不要跑 Knowledge / News
    """
    intent = state.get("intent", "mixed")

    state["run_knowledge"] = intent in ["knowledge", "mixed"]
    state["run_news"] = intent in ["news", "mixed"]

    dbg = state.get("debug") or {}
    dbg["coordinator"] = {
        "intent": intent,
        "run_knowledge": state["run_knowledge"],
        "run_news": state["run_news"],
    }
    state["debug"] = dbg

    return state
