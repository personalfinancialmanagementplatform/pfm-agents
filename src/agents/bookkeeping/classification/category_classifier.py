"""
Category Classifier Node - LangGraph 版本（純 LLM）
使用 TAIDE 模型判斷交易分類
"""
import json
import logging
from typing import Any, Dict

from ....agents.base import BookkeepingState
from ....models import get_taide_model
from ....database.crud import get_all_categories, get_category_by_name

logger = logging.getLogger(__name__)


# ============================================================================
# LLM Prompt
# ============================================================================

CLASSIFY_PROMPT = """你是一個專業的記帳分類助手。根據交易描述和商家資訊，判斷這筆交易屬於哪個分類。

可用的分類如下：
{categories_list}

交易資訊：
- 描述：{description}
- 商家：{merchant}
- 金額：{amount}
- 類型：{transaction_type}

請以 JSON 格式回答，只回覆 JSON，不要任何其他文字：
{{
    "category_name": "最適合的分類名稱（必須是上面列表中的其中一個）",
    "sub_category_name": "子分類名稱（如果有的話，否則 null）",
    "reason": "簡短說明分類原因（10字以內）"
}}"""


# ============================================================================
# LLM 回應解析
# ============================================================================

def parse_classify_response(response: str) -> Dict[str, Any]:
    """解析 LLM 的分類回應"""
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
            "category_name": result.get("category_name", "其他支出"),
            "sub_category_name": result.get("sub_category_name"),
            "reason": result.get("reason", ""),
        }

    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"分類 JSON 解析失敗: {e}")
        return {
            "category_name": "其他支出",
            "sub_category_name": None,
            "reason": "解析失敗，使用預設分類",
        }


# ============================================================================
# LangGraph Node
# ============================================================================

def category_classifier_node(state: BookkeepingState) -> dict:
    """
    Category Classifier Node（純 LLM 版）
    根據 state 中的交易資訊，用 TAIDE 判斷分類
    """
    description = state.get("description", "")
    merchant = state.get("merchant", "")
    amount = state.get("amount", 0)
    transaction_type = state.get("transaction_type", "expense")

    # 如果有錯誤，跳過分類
    if state.get("error"):
        return {}

    try:
        # 取得所有分類
        categories = get_all_categories()
        categories_list = "\n".join(
            [f"- {c['name']}（{c['parent_category'] or '主分類'}）" for c in categories]
        )

        # 取得模型
        model = get_taide_model()
        if not model.is_loaded:
            model.load()

        # 呼叫 LLM
        prompt = CLASSIFY_PROMPT.format(
            categories_list=categories_list,
            description=description,
            merchant=merchant or "無",
            amount=amount,
            transaction_type="支出" if transaction_type == "expense" else "收入",
        )
        response = model.generate(prompt, temperature=0.1, max_new_tokens=128)

        # 解析回應
        parsed = parse_classify_response(response)
        category_name = parsed["category_name"]

        # 優先用子分類，找不到再用主分類
        sub = parsed.get("sub_category_name")
        category = None
        if sub:
            category = get_category_by_name(sub)
        if not category:
            category = get_category_by_name(category_name)

        if category:
            return {
                "category_id": category["category_id"],
                "category_name": category["name"],
            }
        else:
            # 找不到對應分類，用「其他支出」或「其他收入」
            fallback = "其他收入" if transaction_type == "income" else "其他支出"
            fallback_cat = get_category_by_name(fallback)
            return {
                "category_id": fallback_cat["category_id"] if fallback_cat else None,
                "category_name": fallback,
            }

    except Exception as e:
        logger.error(f"Category Classifier 錯誤: {e}")
        return {
            "category_name": "其他支出",
            "category_id": None,
        }
