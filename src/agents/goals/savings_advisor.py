from src.database.mongo_crud import save_strategy

def savings_advisor_node(state: dict):
    metrics = state.get("metrics", {})
    daily = int(metrics.get("daily_needed", 0))
    
    # 生活化二選一建議
    opt1 = f"方案一：接下來每天省下 ${daily} 元（大約是一份外送或兩杯手搖飲）"
    opt2 = f"方案二：將目標「{state.get('goal_name')}」的時間延後，讓壓力小一點"
    
    advice = [opt1, opt2]
    
    # 存入 MongoDB 紀錄
    if state.get("goal_name"):
        save_strategy(state["user_id"], state["goal_name"], "lagging_recovery", advice)
    
    return {"advice_options": advice}