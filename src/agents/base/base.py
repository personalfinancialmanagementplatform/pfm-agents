# src/agents/base.py
from typing import TypedDict, List, Optional, Dict, Any

class BookkeepingState(TypedDict):
    # --- 基礎資訊 ---
    user_id: int
    raw_text: str           # 使用者輸入的原話
    
    # --- 記帳 Agent 解析出的結果 ---
    amount: float           # 解析出的金額
    transaction_type: str   # 'income' (存錢) 或 'expense' (花錢)
    category_name: str      # 分類名稱
    description: str        # 交易描述
    
    # --- 目標 Agent 判斷後的狀態 (協作關鍵) ---
    is_lagging: bool        # 進度是否落後
    target_goal_id: Optional[int] # 匹配到的財務目標 ID
    
    # --- 最終輸出 ---
    response_message: str   # 要回給使用者的話
    error: Optional[str]    # 錯誤訊息