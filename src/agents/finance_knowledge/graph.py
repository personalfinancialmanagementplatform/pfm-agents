from langgraph.graph import StateGraph
from .state import FinanceState
from .orchestrator import unified_orchestrator
from .understanding import understanding_node
from .coordinator import domain_coordinator
from .knowledge_executor import knowledge_executor
from .news_executor import news_executor
from .presentation import presentation_node


def build_finance_graph():
    graph = StateGraph(FinanceState)

    graph.add_node("orchestrator", unified_orchestrator)
    graph.add_node("understanding", understanding_node)
    graph.add_node("coordinator", domain_coordinator)
    graph.add_node("knowledge", knowledge_executor)
    graph.add_node("news", news_executor)
    graph.add_node("presentation", presentation_node)

    graph.set_entry_point("orchestrator")
    graph.add_edge("orchestrator", "understanding")
    graph.add_edge("understanding", "coordinator")
    graph.add_edge("coordinator", "knowledge")
    graph.add_edge("knowledge", "news")
    graph.add_edge("news", "presentation")

    return graph.compile()
