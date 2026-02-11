def progress_notifier_node(state: dict):
    metrics = state.get("metrics", {})
    goal_name = state.get("goal_name")
    
    if not goal_name:
        return {"response_message": state.get("response_message", "找不到目標資料。")}

    res = f"【{goal_name}】進度報告：\n"
    res += f"達成率 {metrics.get('completion_rate')}%，還差 ${int(metrics.get('gap', 0)):,} 就能達標！\n"
    
    if state.get("is_lagging"):
        res += "\n⚠️ 目前稍微落後，教練建議：\n"
        for i, opt in enumerate(state.get("advice_options", [])):
            res += f"{i+1}. {opt}\n"
    else:
        res += "\n進度很棒，繼續保持！✨"
        
    return {"response_message": res}