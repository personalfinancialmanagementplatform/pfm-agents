from typing import TypedDict, List, Optional


class FinanceState(TypedDict):
    # Input
    user_id: str
    user_level: str              # beginner / normal
    user_preference: List[str]   # ["ETF", "台股"]
    raw_input: str

    # Understanding
    intent: str                  # knowledge / news / mixed
    concepts: List[str]          # ["ETF", "升息"]
    need_news: bool

    # Execution
    knowledge_content: Optional[str]
    news_content: Optional[str]

    # Presentation
    tone: str                    # simple / normal
    final_response: Optional[str]

    # Error
    error: Optional[str]
