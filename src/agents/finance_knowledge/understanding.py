def understanding_node(state: dict) -> dict:
    """
    抽取概念 & 是否需要新聞
    """
    text = state["raw_input"]

    concepts = []
    if "ETF" in text:
        concepts.append("ETF")
    if "0050" in text:
        concepts.append("台股ETF")
    if "升息" in text:
        concepts.append("升息")

    state["concepts"] = concepts
    state["need_news"] = "最近" in text or "新聞" in text

    return state
