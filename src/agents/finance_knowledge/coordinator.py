def domain_coordinator(state: dict) -> dict:
    """
    決定要不要同時跑 Knowledge / News
    """
    intent = state["intent"]

    state["run_knowledge"] = intent in ["knowledge", "mixed"]
    state["run_news"] = intent in ["news", "mixed"]

    return state
