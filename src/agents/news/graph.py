from __future__ import annotations
from typing import Literal

from langgraph.graph import StateGraph, END

from .state import NewsState
from .nodes.router import news_router_node
from .nodes.fetch import news_fetch_node
from .nodes.understand import news_understand_node
from .rank import news_rank_node
from .nodes.present import news_present_node


def _route_after_router(state: NewsState) -> Literal["digest_flow", "skip"]:
    intent = state.get("intent") or "skip"
    return "digest_flow" if intent == "digest" else "skip"


def build_news_graph():
    g = StateGraph(NewsState)

    g.add_node("router", news_router_node)
    g.add_node("fetch", news_fetch_node)
    g.add_node("understand", news_understand_node)
    g.add_node("rank", news_rank_node)
    g.add_node("present", news_present_node)

    g.set_entry_point("router")

    g.add_conditional_edges(
        "router",
        _route_after_router,
        {
            "digest_flow": "fetch",
            "skip": "present",
        },
    )

    g.add_edge("fetch", "understand")
    g.add_edge("understand", "rank")
    g.add_edge("rank", "present")
    g.add_edge("present", END)

    return g.compile()


# 方便外部直接呼叫
_news_graph = None


def run_news_graph(state: NewsState) -> NewsState:
    global _news_graph
    if _news_graph is None:
        _news_graph = build_news_graph()
    return _news_graph.invoke(state)