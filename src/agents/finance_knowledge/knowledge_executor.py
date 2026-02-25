from src.models.taide import taide_generate


def knowledge_executor(state: dict) -> dict:
    if not state.get("run_knowledge"):
        return state

    prompt = f"""
        你是一位給新手看的理財老師。
        請用白話解釋以下概念：
        {', '.join(state['concepts'])}

        避免專業術語，多用生活化例子。
        """

    state["knowledge_content"] = taide_generate(prompt)
    return state
