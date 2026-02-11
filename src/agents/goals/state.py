from typing import TypedDict, Optional, List, Dict, Any

class GoalState(TypedDict):
    user_id: str
    goal_name: Optional[str]
    metrics: Dict[str, Any]      #
    is_lagging: bool
    advice_options: List[str]
    response_message: str
    error: Optional[str]