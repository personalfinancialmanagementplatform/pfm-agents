"""
Budget Monitor Node - LangGraph 版本（LLM + DB）
查詢預算目標，LLM 判斷交易歸屬，計算剩餘額度
"""
import json
import logging
from datetime import date
from typing import Any, Dict, List

from ....agents.base import BookkeepingState
from ....models import get_taide_model
from ....database.connection import execute_query

logger = logging.getLogger(__name__)


# ============================================================================
# LLM Prompt
# ============================================================================

BUDGET_MATCH_PROMPT = """你是一個預算管理助手。用戶設定了以下預算目標，請判斷這筆交易屬於哪個預算。

用戶的預算目標：
{budgets_list}

這筆新交易：
- 描述：{description}
- 分類：{category_name}
- 商家：{merchant}
- 金額：{amount} 元
- 類型：{transaction_type}

請以 JSON 格式回答，只回覆 JSON：
{{
    "matched_budget_id": 匹配的預算 ID（整數，若都不匹配則 null）,
    "matched_budget_name": "匹配的預算名稱（若不匹配則 null）",
    "reason": "簡短說明匹配原因（15字以內）"
}}"""


# ============================================================================
# DB 查詢
# ============================================================================

def get_active_budgets(user_id: int) -> List[Dict[str, Any]]:
    """查詢用戶目前有效的預算"""
    today = date.today()
    result = execute_query("""
        SELECT b.budget_id, b.amount as budget_amount, b.period,
               b.start_date, b.end_date,
               c.category_id, c.name as category_name
        FROM budgets b
        LEFT JOIN categories c ON b.category_id = c.category_id
        WHERE b.user_id = %s
          AND b.start_date <= %s
          AND b.end_date >= %s
        ORDER BY b.budget_id
    """, (user_id, today, today), fetch=True)
    return result or []


def get_budget_spent(user_id: int, category_id: int, start_date, end_date) -> float:
    """查詢某預算期間內該分類已花費金額"""
    result = execute_query("""
        SELECT COALESCE(SUM(amount), 0) as spent
        FROM transactions
        WHERE user_id = %s
          AND category_id = %s
          AND transaction_type = 'expense'
          AND transaction_date >= %s
          AND transaction_date <= %s
    """, (user_id, category_id, start_date, end_date), fetch=True)
    return float(result[0]["spent"]) if result else 0


def get_financial_goals_as_budgets(user_id: int) -> List[Dict[str, Any]]:
    """從 financial_goals 表取得儲蓄目標（轉成預算格式）"""
    result = execute_query("""
        SELECT goal_id, name, target_amount, current_amount, deadline, status
        FROM financial_goals
        WHERE user_id = %s AND status = 'active'
        ORDER BY goal_id
    """, (user_id,), fetch=True)
    return result or []


# ============================================================================
# LLM 回應解析
# ============================================================================

def parse_budget_match_response(response: str) -> Dict[str, Any]:
    """解析 LLM 的預算匹配回應"""
    try:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start != -1 and end > start:
            cleaned = cleaned[start:end]

        result = json.loads(cleaned)
        return {
            "matched_budget_id": result.get("matched_budget_id"),
            "matched_budget_name": result.get("matched_budget_name"),
            "reason": result.get("reason", ""),
        }

    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"預算匹配 JSON 解析失敗: {e}")
        return {
            "matched_budget_id": None,
            "matched_budget_name": None,
            "reason": "解析失敗",
        }


# ============================================================================
# 預算等級計算
# ============================================================================

def calculate_budget_level(spent: float, budget_amount: float, new_amount: float) -> Dict[str, Any]:
    """計算預算使用等級和警告訊息"""
    total_after = spent + new_amount
    percentage = (total_after / budget_amount * 100) if budget_amount > 0 else 0
    remaining = budget_amount - total_after

    if percentage >= 100:
        level = "exceeded"
        warning = f"🔴 已超支！預算 ${budget_amount:.0f}，已花 ${total_after:.0f}，超出 ${abs(remaining):.0f}"
    elif percentage >= 80:
        level = "high"
        warning = f"🟡 接近上限！預算 ${budget_amount:.0f}，已花 ${total_after:.0f}，剩餘 ${remaining:.0f}（{100-percentage:.0f}%）"
    elif percentage >= 50:
        level = "medium"
        warning = f"📊 已過半！預算 ${budget_amount:.0f}，已花 ${total_after:.0f}，剩餘 ${remaining:.0f}（{100-percentage:.0f}%）"
    else:
        level = "ok"
        warning = None

    return {
        "level": level,
        "percentage": round(percentage, 1),
        "spent_before": spent,
        "spent_after": total_after,
        "remaining": remaining,
        "budget_amount": budget_amount,
        "warning": warning,
    }


# ============================================================================
# LangGraph Node
# ============================================================================

def budget_monitor_node(state: BookkeepingState) -> dict:
    """
    Budget Monitor Node
    1. 查 DB 取得預算目標
    2. LLM 判斷這筆交易屬於哪個預算
    3. 計算已花費 & 剩餘額度
    4. 回傳結果給目標 Domain
    """
    # 如果前面有錯誤，跳過
    if state.get("error"):
        return {}

    # 只處理支出
    if state.get("transaction_type") != "expense":
        return {
            "budget_warning": None,
            "budget_level": "ok",
        }

    user_id = state.get("user_id", 0)
    amount = state.get("amount", 0)
    category_name = state.get("category_name", "未分類")
    description = state.get("description", "")
    merchant = state.get("merchant", "")

    try:
        # 1. 查詢有效預算
        budgets = get_active_budgets(user_id)

        # 也查 financial_goals
        goals = get_financial_goals_as_budgets(user_id)

        if not budgets and not goals:
            return {
                "budget_warning": None,
                "budget_level": "ok",
            }

        # 2. 組合預算清單給 LLM
        budgets_list_parts = []
        budget_lookup = {}

        for b in budgets:
            label = f"[預算 ID:{b['budget_id']}] {b['category_name']} - 每月 ${float(b['budget_amount']):.0f}"
            budgets_list_parts.append(label)
            budget_lookup[b["budget_id"]] = b

        for g in goals:
            label = f"[目標 ID:G{g['goal_id']}] {g['name']} - 目標 ${float(g['target_amount']):.0f}"
            budgets_list_parts.append(label)

        budgets_list = "\n".join(budgets_list_parts)

        # 3. LLM 判斷這筆屬於哪個預算
        model = get_taide_model()
        if not model.is_loaded:
            model.load()

        prompt = BUDGET_MATCH_PROMPT.format(
            budgets_list=budgets_list,
            description=description,
            category_name=category_name,
            merchant=merchant or "無",
            amount=amount,
            transaction_type="支出",
        )
        response = model.generate(prompt, temperature=0.1, max_new_tokens=128)
        parsed = parse_budget_match_response(response)

        matched_id = parsed["matched_budget_id"]

        # 4. 如果匹配到預算，計算剩餘額度
        if matched_id and matched_id in budget_lookup:
            matched_budget = budget_lookup[matched_id]
            spent = get_budget_spent(
                user_id,
                matched_budget["category_id"],
                matched_budget["start_date"],
                matched_budget["end_date"],
            )

            level_info = calculate_budget_level(spent, float(matched_budget["budget_amount"]), amount)

            return {
                "budget_warning": level_info["warning"],
                "budget_level": level_info["level"],
                "budget_detail": {
                    "budget_name": matched_budget["category_name"],
                    "budget_amount": level_info["budget_amount"],
                    "spent_before": level_info["spent_before"],
                    "spent_after": level_info["spent_after"],
                    "remaining": level_info["remaining"],
                    "percentage": level_info["percentage"],
                    "match_reason": parsed["reason"],
                },
            }

        # 沒匹配到任何預算
        return {
            "budget_warning": None,
            "budget_level": "ok",
        }

    except Exception as e:
        logger.error(f"Budget Monitor 錯誤: {e}")
        return {
            "budget_warning": None,
            "budget_level": "ok",
        }
