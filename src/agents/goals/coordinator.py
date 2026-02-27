from langgraph.graph import StateGraph, END
from .goal_manager import goal_manager_node
from .savings_advisor import savings_advisor_node
from .progress_notifier import progress_notifier_node

def create_goals_graph():
    workflow = StateGraph(dict) # 這裡簡化使用 dict 測試
    
    workflow.add_node("manager", goal_manager_node)
    workflow.add_node("advisor", savings_advisor_node)
    workflow.add_node("notifier", progress_notifier_node)

    workflow.set_entry_point("manager")

    # 路由邏輯：落後則去建議節點，否則直接通知
    def router(state):
        if not state.get("goal_name"):
            return "notifier"
        return "advisor" if state.get("is_lagging") else "notifier"

    workflow.add_conditional_edges("manager", router, {
        "advisor": "advisor",
        "notifier": "notifier"
    })
    
    workflow.add_edge("advisor", "notifier")
    workflow.add_edge("notifier", END)

    return workflow.compile()

goals_app = create_goals_graph()