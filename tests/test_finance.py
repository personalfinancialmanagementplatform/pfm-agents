import os
from src.agents.finance_knowledge.graph import build_finance_graph

def run_case(app, title, raw_text, trigger="qa"):
    out = app.invoke({
        "user_id": "user_124",
        "raw_text": raw_text,   
        "trigger": trigger,
    })

    print(f"\n=== {title} ===")

    # ✅ FinanceState 的最終輸出欄位是 final_response
    print("final_response:\n", out.get("final_response"))

    # ✅ 方便你確認 knowledge / news 有沒有真的寫回 state
    print("\nknowledge_content:\n", out.get("knowledge_content"))
    print("\nnews_content:\n", out.get("news_content"))

    print("\n-- debug --")
    print(out.get("debug"))

    return out

def main():
    # 先用 Mock 跑通流程（避免卡模型/KB）
    os.environ["USE_MOCK_MODEL"] = "true"

    app = build_finance_graph()

    run_case(app, "FINANCE | KNOWLEDGE ONLY", "什麼是 ETF？")
    run_case(app, "FINANCE | NEWS ONLY", "給我今天台股大盤新聞", trigger="qa")
    run_case(app, "FINANCE | BOTH", "升息對債券 ETF 有什麼影響？也想看今天相關新聞")

if __name__ == "__main__":
    main()