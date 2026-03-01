# scripts/demo_finance_rag.py
import os
from pprint import pprint

from src.agents.finance_knowledge.graph import build_finance_graph

def run_case(question: str):
    app = build_finance_graph()
    out = app.invoke({
        "user_id": "demo_user",
        "raw_text": question,
        "user_level": "beginner",
        "user_preference": [],
        "trigger": "qa",
    })

    print("\n" + "=" * 80)
    print("Q:", question)
    print("-" * 80)
    print("FINAL:\n", out.get("final_response"))
    print("-" * 80)
    print("DEBUG:")
    pprint(out.get("debug"))
    print("-" * 80)
    print("KB (knowledge_content):\n", out.get("knowledge_content"))
    print("-" * 80)
    print("NEWS (news_content):\n", out.get("news_content"))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    # 沒 GPU 也能跑
    os.environ.setdefault("FORCE_KB_FALLBACK", "true")
    os.environ.setdefault("USE_MOCK_MODEL", "true")

    cases = [
        "什麼是 ETF？跟共同基金差在哪？",
        "最近升息對債券價格有什麼影響？",
        "台股大盤為什麼會漲？請用白話解釋",
        "0050 跟 0056 有什麼差別？適合新手嗎？",
    ]

    for q in cases:
        run_case(q)