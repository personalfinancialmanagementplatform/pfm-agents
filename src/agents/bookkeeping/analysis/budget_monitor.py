
"""
Budget Monitor Node - LangGraph 版本（LLM + 預算規則）
1. 查詢用戶該分類的月預算和已花費（目前用 Mock）
2. 計算使用百分比和剩餘額度
3. LLM 判斷預算狀態並生成提醒
"""
import json
import logging
from typing import Any, Dict, Optional

from ....models import get_taide_model

logger = logging.getLogger(__name__)


# ============================================================================
# Mock 預算數據（之後替換成 DB 查詢）
# ============================================================================

MOCK_BUDGETS = {
    "午餐": {"monthly_budget": 3000, "spent": 2500},
    "晚餐": {"monthly_budget": 4000, "spent": 2800},
    "早餐": {"monthly_budget": 1500, "spent": 900},
    "飲料": {"monthly_budget": 1000, "spent": 750},
    "交通": {"monthly_budget": 2000, "spent": 1200},
    "購物": {"monthly_budget": 3000, "spent": 1500},
    "娛樂": {"monthly_budget": 2000, "spent": 1800},
    "醫療": {"monthly_budget": 2000, "spent": 300},
    "其他支出": {"monthly_budget": 3000, "spent": 1000},
}

# 整體月預算
MOCK_TOTAL_BUDGET = {
    "monthly_budget": 25000,
    "total_spent": 13750,
}


def get_budget_info(category_name: str) -> Optional[Dict]:
    """
    取得該分類的預算資訊
    TODO: 之後改成從 PostgreSQL 查詢
    """
    if category_name in MOCK_BUDGETS:
        return MOCK_BUDGETS[category_name]

    for key, budget in MOCK_BUDGETS.items():
        if key in category_name or category_name in key:
            return budget

    return None


def get_total_budget() -> Dict:
    """
    取得整體月預算
    TODO: 之後改成從 PostgreSQL 查詢
    """
    return MOCK_TOTAL_BUDGET


# ============================================================================
# 預算計算
# ============================================================================

def calculate_budget_status(budget_info: Dict, new_amount: float) -> Dict:
    """
    計算加上這筆消費後的預算狀態
    """
    monthly_budget = budget_info["monthly_budget"]
    already_spent = budget_info["spent"]
    after_spent = already_spent + new_amount
    remaining = monthly_budget - after_spent
    usage_pct = round(after_spent / monthly_budget * 100, 1) if monthly_budget > 0 else 0

    # 判斷等級
    if usage_pct >= 100:
        level = "exceeded"
    elif usage_pct >= 90:
        level = "critical"
    elif usage_pct >= 75:
        level = "warning"
    elif usage_pct >= 50:
        level = "normal"
    else:
        level = "healthy"

    return {
        "monthly_budget": monthly_budget,
        "already_spent": already_spent,
        "after_spent": after_spent,
        "remaining": remaining,
        "usage_pct": usage_pct,
        "level": level,
    }


# ============================================================================
# LLM Prompt
# ============================================================================

BUDGET_PROMPT = """你是一個專業的預算監控助手。根據以下預算狀況，給用戶簡短的提醒。

這筆交易：
- 描述：{description}
- 金額：${amount}
- 分類：{category}

該分類預算狀況：
- 月預算：${monthly_budget}
- 記帳前已花費：${already_spent}
- 記帳後已花費：${after_spent}
- 剩餘額度：${remaining}
- 使用百分比：{usage_pct}%
- 狀態：{level}

整體月預算：
- 總月預算：${total_budget}
- 總已花費：${total_spent}
- 總剩餘：${total_remaining}

請以 JSON 格式回答，只回覆 JSON：
{{
    "budget_warning": "給用戶的預算提醒（30字以內，friendly 語氣。如果 healthy 則為 null）",
    "budget_level": "{level}",
    "saving_tip": "省錢小建議（20字以內，如果不需要則為 null）"
}}"""

BUDGET_PROMPT_NO_BUDGET = """你是一個專業的預算監控助手。這個分類目前沒有設定預算。

這筆交易：
- 描述：{description}
- 金額：${amount}
- 分類：{category}

請以 JSON 格式回答，只回覆 JSON：
{{
    "budget_warning": null,
    "budget_level": "no_budget",
    "saving_tip": "建議為「{category}」設定每月預算，更好掌握開銷"
}}"""


# ============================================================================
# LLM 回應解析
# ============================================================================

def parse_llm_response(response: str) -> Dict:
    """解析 LLM 回應的 JSON"""
    try:
        text = response.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        result = json.loads(text.strip())
        return {
            "budget_warning": result.get("budget_warning"),
            "budget_level": result.get("budget_level", "unknown"),
            "saving_tip": result.get("saving_tip"),
        }
    except Exception as e:
        logger.warning(f"LLM 回應解析失敗: {e}, 原始回應: {response[:200]}")
        return {
            "budget_warning": None,
            "budget_level": "unknown",
            "saving_tip": None,
        }


# ============================================================================
# LangGraph Node
# ============================================================================

def budget_monitor_node(state: dict) -> dict:
    """
    Budget Monitor Node（LLM + 預算規則）
    從 state 讀取交易資訊，檢查預算狀態，寫回 state
    """
    if state.get("error"):
        return {}

    amount = state.get("amount", 0)
    category = state.get("category_name", "其他支出")
    description = state.get("description", "")

    if amount <= 0:
        return {
            "budget_warning": None,
            "budget_level": "skip",
        }

    # 只有支出才需要檢查預算
    if state.get("transaction_type") == "income":
        return {
            "budget_warning": None,
            "budget_level": "income",
        }

    try:
        # Step 1: 查預算
        budget_info = get_budget_info(category)
        total_budget = get_total_budget()

        # Step 2: 取得模型
        model = get_taide_model()
        if not model.is_loaded:
            model.load()

        # Step 3: 組合 prompt
        if budget_info:
            status = calculate_budget_status(budget_info, amount)
            total_remaining = total_budget["monthly_budget"] - total_budget["total_spent"]

            prompt = BUDGET_PROMPT.format(
                description=description,
                amount=amount,
                category=category,
                monthly_budget=status["monthly_budget"],
                already_spent=status["already_spent"],
                after_spent=status["after_spent"],
                remaining=status["remaining"],
                usage_pct=status["usage_pct"],
                level=status["level"],
                total_budget=total_budget["monthly_budget"],
                total_spent=total_budget["total_spent"],
                total_remaining=total_remaining,
            )
        else:
            status = {"level": "no_budget", "usage_pct": 0, "remaining": 0}
            prompt = BUDGET_PROMPT_NO_BUDGET.format(
                description=description,
                amount=amount,
                category=category,
            )

        # Step 4: LLM 判斷
        response = model.generate(prompt, temperature=0.1, max_new_tokens=256)
        llm_result = parse_llm_response(response)

        return {
            "budget_warning": llm_result["budget_warning"],
            "budget_level": status["level"],
            "budget_usage_pct": status.get("usage_pct", 0),
            "budget_remaining": status.get("remaining", 0),
            "budget_method": "llm+rules" if budget_info else "llm_only",
        }

    except Exception as e:
        logger.error(f"Budget Monitor 錯誤: {e}")
        return {
            "budget_warning": None,
            "budget_level": "error",
            "budget_method": "error",
        }

