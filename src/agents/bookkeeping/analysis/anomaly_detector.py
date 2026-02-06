"""
Anomaly Detector Node - LangGraph 版本（LLM + 統計混合）
先用 DB 查歷史數據計算統計值，再用 LLM 綜合判斷是否異常
"""
import json
import logging
from datetime import date, timedelta
from typing import Any, Dict, List

from ....agents.base import BookkeepingState
from ....models import get_taide_model
from ....database.connection import execute_query

logger = logging.getLogger(__name__)


# ============================================================================
# LLM Prompt
# ============================================================================

ANOMALY_PROMPT = """你是一個財務異常偵測助手，負責判斷一筆新交易是否異常。

用戶的歷史消費統計：
- 該分類過去平均單筆金額：{avg_amount} 元
- 該分類過去最高單筆金額：{max_amount} 元
- 該分類本月已消費總額：{month_total} 元
- 該分類本月已消費筆數：{month_count} 筆
- 過去30天同分類消費筆數：{recent_count} 筆

這筆新交易：
- 金額：{amount} 元
- 分類：{category_name}
- 描述：{description}
- 商家：{merchant}

請判斷這筆交易是否異常，以 JSON 格式回答，只回覆 JSON：
{{
    "is_anomaly": true 或 false,
    "anomaly_type": "異常類型（如：金額偏高、頻率異常、疑似重複、無異常）",
    "reason": "簡短說明原因（20字以內）",
    "severity": "low" 或 "medium" 或 "high"（嚴重程度）
}}"""


# ============================================================================
# 統計查詢
# ============================================================================

def get_category_stats(user_id: int, category_id: int) -> Dict[str, Any]:
    """從 DB 查詢該分類的歷史統計"""
    today = date.today()
    month_start = today.replace(day=1)
    thirty_days_ago = today - timedelta(days=30)

    # 該分類歷史平均和最高金額
    result = execute_query("""
        SELECT 
            COALESCE(AVG(amount), 0) as avg_amount,
            COALESCE(MAX(amount), 0) as max_amount
        FROM transactions
        WHERE user_id = %s AND category_id = %s
    """, (user_id, category_id), fetch=True)

    avg_amount = float(result[0]["avg_amount"]) if result else 0
    max_amount = float(result[0]["max_amount"]) if result else 0

    # 本月該分類消費總額和筆數
    result = execute_query("""
        SELECT 
            COALESCE(SUM(amount), 0) as month_total,
            COUNT(*) as month_count
        FROM transactions
        WHERE user_id = %s AND category_id = %s
          AND transaction_date >= %s
    """, (user_id, category_id, month_start), fetch=True)

    month_total = float(result[0]["month_total"]) if result else 0
    month_count = int(result[0]["month_count"]) if result else 0

    # 過去30天同分類筆數
    result = execute_query("""
        SELECT COUNT(*) as recent_count
        FROM transactions
        WHERE user_id = %s AND category_id = %s
          AND transaction_date >= %s
    """, (user_id, category_id, thirty_days_ago), fetch=True)

    recent_count = int(result[0]["recent_count"]) if result else 0

    return {
        "avg_amount": round(avg_amount, 0),
        "max_amount": round(max_amount, 0),
        "month_total": round(month_total, 0),
        "month_count": month_count,
        "recent_count": recent_count,
    }


def check_duplicate(user_id: int, amount: float, description: str) -> bool:
    """檢查是否有疑似重複交易（同天同金額同描述）"""
    result = execute_query("""
        SELECT COUNT(*) as dup_count
        FROM transactions
        WHERE user_id = %s 
          AND amount = %s
          AND description = %s
          AND transaction_date = CURRENT_DATE
    """, (user_id, amount, description), fetch=True)

    return int(result[0]["dup_count"]) > 0 if result else False


# ============================================================================
# LLM 回應解析
# ============================================================================

def parse_anomaly_response(response: str) -> Dict[str, Any]:
    """解析 LLM 的異常偵測回應"""
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
            "is_anomaly": result.get("is_anomaly", False),
            "anomaly_type": result.get("anomaly_type", "無異常"),
            "reason": result.get("reason", ""),
            "severity": result.get("severity", "low"),
        }

    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"異常偵測 JSON 解析失敗: {e}")
        return {
            "is_anomaly": False,
            "anomaly_type": "無異常",
            "reason": "解析失敗，預設為正常",
            "severity": "low",
        }


# ============================================================================
# LangGraph Node
# ============================================================================

def anomaly_detector_node(state: BookkeepingState) -> dict:
    """
    Anomaly Detector Node（LLM + 統計混合）
    1. 從 DB 查歷史統計
    2. 檢查重複交易
    3. 用 LLM 綜合判斷是否異常
    """
    # 如果前面有錯誤，跳過
    if state.get("error"):
        return {}

    user_id = state.get("user_id", 0)
    amount = state.get("amount", 0)
    category_id = state.get("category_id")
    category_name = state.get("category_name", "未分類")
    description = state.get("description", "")
    merchant = state.get("merchant", "")

    try:
        # 1. 檢查重複交易
        if check_duplicate(user_id, amount, description):
            return {
                "is_anomaly": True,
                "anomaly_reason": f"⚠️ 疑似重複記帳：今天已有一筆相同的「{description} ${amount}」",
            }

        # 2. 查歷史統計（如果有分類）
        stats = {"avg_amount": 0, "max_amount": 0, "month_total": 0, "month_count": 0, "recent_count": 0}
        if category_id:
            stats = get_category_stats(user_id, category_id)

        # 3. 如果沒有歷史資料，視為正常（新用戶）
        if stats["recent_count"] == 0 and stats["month_count"] == 0:
            return {
                "is_anomaly": False,
                "anomaly_reason": None,
            }

        # 4. 用 LLM 綜合判斷
        model = get_taide_model()
        if not model.is_loaded:
            model.load()

        prompt = ANOMALY_PROMPT.format(
            avg_amount=stats["avg_amount"],
            max_amount=stats["max_amount"],
            month_total=stats["month_total"],
            month_count=stats["month_count"],
            recent_count=stats["recent_count"],
            amount=amount,
            category_name=category_name,
            description=description,
            merchant=merchant or "無",
        )
        response = model.generate(prompt, temperature=0.1, max_new_tokens=128)

        # 5. 解析結果
        parsed = parse_anomaly_response(response)

        anomaly_reason = None
        if parsed["is_anomaly"]:
            anomaly_reason = f"⚠️ {parsed['anomaly_type']}：{parsed['reason']}"

        return {
            "is_anomaly": parsed["is_anomaly"],
            "anomaly_reason": anomaly_reason,
        }

    except Exception as e:
        logger.error(f"Anomaly Detector 錯誤: {e}")
        return {
            "is_anomaly": False,
            "anomaly_reason": None,
        }
