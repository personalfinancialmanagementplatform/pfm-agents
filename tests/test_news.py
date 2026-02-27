from src.agents.news.graph import build_news_graph

def main():
    app = build_news_graph()

    # 1) QA 測試（走 router -> knowledge -> present）
    out = app.invoke({
        "user_id": "user_124",
        "raw_text": "什麼是 ETF？",
        "trigger": "qa",
    })
    print("\n=== QA ===")
    print(out.get("response_message"))
    print("debug:", out.get("debug"))

    # 2) Digest 測試（走 router -> fetch -> understand -> rank -> present）
    out2 = app.invoke({
        "user_id": "user_124",
        "raw_text": "給我今天的新聞",
        "trigger": "digest",
    })
    print("\n=== DIGEST ===")
    print(out2.get("response_message"))
    print("debug:", out2.get("debug"))

if __name__ == "__main__":
    main()