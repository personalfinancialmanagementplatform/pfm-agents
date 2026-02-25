from src.database import get_goals
from .utils import calculate_goal_metrics, judge_lagging_status

def goal_manager_node(state: dict):
    user_id = state.get("user_id")
    goals = get_goals(user_id)
    
    if not goals:
        return {
            "metrics": {"completion_rate": 0, "gap": 0, "daily_needed": 0, "days_left": 0},
            "is_lagging": False,
            "goal_name": None,
            "response_message": "目前還沒看到您的財務目標喔！"
        }

    latest_goal = goals[0]
    
    metrics = calculate_goal_metrics(
        target_amount=float(latest_goal['target_amount']),
        current_amount=float(latest_goal['current_amount']),
        deadline=latest_goal['deadline'].strftime("%Y-%m-%d")
    )
    
    is_lagging = judge_lagging_status(
        metrics, 
        start_date=latest_goal['created_at'].strftime("%Y-%m-%d")
    )
    
    # --- 確保這下面這一塊有縮進 (前面有 4 個空格) ---
    return {
        "goal_id": latest_goal['goal_id'], 
        "goal_name": latest_goal['name'],
        "metrics": metrics,
        "is_lagging": is_lagging
    }