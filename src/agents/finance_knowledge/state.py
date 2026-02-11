from typing import TypedDict, List, Optional, Dict, Any


class FinanceState(TypedDict, total=False):
    # Input
    user_id: str
    user_level: str              # beginner / normal
    user_preference: List[str]   # ["ETF", "台股"]
    raw_input: str

    # Orchestrator / Understanding
    intent: str                  # knowledge / news / mixed
    tone: str                    # simple / normal
    concepts: List[str]          # ["ETF", "升息"]
    need_news: bool

    # Coordinator decisions
    run_knowledge: bool
    run_news: bool

    # Execution outputs
    knowledge_content: Optional[str]
    news_content: Optional[str]

    # Adapter I/O for news subgraph
    news_state_in: Optional[Dict[str, Any]]
    news_state_out: Optional[Dict[str, Any]]

    # Presentation
    final_response: Optional[str]

    # Error / Debug
    error: Optional[str]
    debug: Optional[Dict[str, Any]]
