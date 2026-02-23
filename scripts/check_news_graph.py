from src.agents.news import build_news_graph

g = build_news_graph()

# 測 digest
out = g.invoke({"user_id": "u1", "trigger": "digest", "raw_text": "推播今天熱門新聞"})
print(out["response_message"])

# 測 QA
out = g.invoke({"user_id": "u1", "trigger": "qa", "raw_text": "什麼是漲停？"})
print(out["response_message"])
