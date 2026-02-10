"""
Anomaly Detector Node - LangGraph 版本（LLM + 統計規則混合）
1. 統計規則：查歷史數據算平均和標準差（目前用 Mock）
2. LLM 判斷：把統計結果 + 交易資訊丟給 TAIDE 綜合判斷
"""
import json
import logging
from typing import Any, Dict, Optional

from ....models import get_taide_model

logger = logging.getLogger(__name__)


# ============================================================================
# Mock 歷史數據（之後替換成 DB 查詢）
# ============================================================================

MOCK_HISTORY = {
    "午餐": {"avg": 120, "std": 40, "max": 250, "count": 30},
    "晚餐": {"avg": 200, "std": 60, "max": 450, "count": 25},
    "早餐": {"avg": 65, "std": 20, "max": 120, "count": 20},
    "飲料": {"avg": 55, "std": 15, "max": 100, "count": 40},
    "交通": {"avg": 80, "std": 30, "max": 200, "count": 15},
    "購物": {"avg": 500, "std": 300, "max": 2000, "count": 10},
    "娛樂": {"avg": 350, "std": 150, "max": 800, "count": 8},
    "醫療": {"avg": 300, "std": 200, "max": 1000, "count": 5},
    "其他支出": {"avg": 200, "std": 150, "max": 800, "count": 20},
}


def get_category_stats(category_name: str) -> Optional[Dict]:
    """
    取得該分類的歷史統計資料
    TODO: 之後改成從 PostgreSQL 查詢
    """
    # 嘗試精確匹配
    if category_name in MOCK_HISTORY:
        return MOCK_HISTORY[category_name]

    # 嘗試模糊匹配
    for key, stats in MOCK_HISTORY.items():
        if key in category_name or category_name in key:
            return stats

    # 沒有歷史資料，回傳 None
    return None


# ============================================================================
# 統計規則判斷
# ============================================================================

def stat_check(amount: float, stats: Dict) -> Dict:
    """
    用統計規則初步判斷是否異常
    - 超過 平均 + 2倍標準差 → 可能異常
    - 超過歷史最大值 → 高度異常
    """
    avg = stats["avg"]
    std = stats["std"]
    historical_max = stats["max"]

    threshold_2std = avg + 2 * std
    threshold_3std = avg + 3 * std

    if amount > historical_max:
        return {
            "stat_flag": "high",
            "reason": f"超過歷史最高 ${historical_max}",
            "avg": avg,
            "std": std,
            "deviation": round((amount - avg) / std, 1) if std > 0 else 0,
        }
    elif amount > threshold_3std:
        return {
            "stat_flag": "high",
            "reason": f"超過平均值 3 倍標準差（平均 ${avg}）",
            "avg": avg,
            "std": std,
            "deviation": round((amount - avg) / std, 1),
        }
    elif amount > threshold_2std:
        return {
            "stat_flag": "medium",
            "reason": f"超過平均值 2 倍標準差（平均 ${avg}）",
            "avg": avg,
            "std": std,
            "deviation": round((amount - avg) / std, 1),
        }
    else:
        return {
            "stat_flag": "normal",
            "reason": "在正常範圍內",
            "avg": avg,
            "std": std,
            "deviation": round((amount - avg) / std, 1) if std > 0 else 0,
        }


# ============================================================================
# LLM Prompt
# ============================================================================

ANOMALY_PROMPT = """你是一個專業的財務異常偵測助手。根據以下交易資訊和歷史統計數據，判斷這筆交易是否異常。

交易資訊：
- 描述：{description}
- 金額：${amount}
- 分類：{category}
- 商家：{merchant}

歷史統計（同分類）：
- 平均消費：${avg}
- 標準差：${std}
- 歷史最高：${max}
- 交易次數：{count}
- 統計判斷：{stat_flag}（{stat_reason}）
- 偏離程度：{deviation} 個標準差

請綜合判斷這筆交易是否異常。考慮：
1. 金額是否明顯偏離歷史平均
2. 該消費在該分類下是否合理
3. 是否可能是特殊情況（如聚餐、節日、一次性消費）

請以 JSON 格式回答，只回覆 JSON：
{{
    "is_anomaly": true 或 false,
    "severity": "none" 或 "low" 或 "medium" 或 "high",
    "reason": "簡短說明原因（20字以內）",
    "suggestion": "給用戶的建議（20字以內，如果正常則為 null）"
}}"""

ANOMALY_PROMPT_NO_HISTORY = """你是一個專業的財務異常偵測助手。這筆交易沒有歷史數據可以比對，請根據常識判斷是否異常。

交易資訊：
- 描述：{description}
- 金額：${amount}
- 分類：{category}
- 商家：{merchant}

請以 JSON 格式回答，只回覆 JSON：
{{
    "is_anomaly": true 或 false,
    "severity": "none" 或 "low" 或 "medium" 或 "high",
    "reason": "簡短說明原因（20字以內）",
    "suggestion": "給用戶的建議（20字以內，如果正常則為 null）"
}}"""


# ============================================================================
# LLM 回應解析
# ============================================================================

def parse_llm_response(response: str) -> Dict:
    """解析 LLM 回應的 JSON"""
    try:
        text = response.strip()
        # 移除可能的 markdown 標記
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        result = json.loads(text.strip())
        return {
            "is_anomaly": bool(result.get("is_anomaly", False)),
            "severity": result.get("severity", "none"),
            "reason": result.get("reason", ""),
            "suggestion": result.get("suggestion"),
        }
    except Exception as e:
        logger.warning(f"LLM 回應解析失敗: {e}, 原始回應: {response[:200]}")
        return {
            "is_anomaly": False,
            "severity": "none",
            "reason": "無法判斷",
            "suggestion": None,
        }


# ============================================================================
# LangGraph Node
# ============================================================================

def anomaly_detector_node(state: dict) -> dict:
    """
    Anomaly Detector Node（LLM + 統計規則混合）
    從 state 讀取交易資訊，判斷是否異常，寫回 state
    """
    # 如果前面的 node 有錯誤，跳過
    if state.get("error"):
        return {}

    amount = state.get("amount", 0)
    category = state.get("category_name", "其他支出")
    description = state.get("description", "")
    merchant = state.get("merchant", "未知")

    if amount <= 0:
        return {
            "is_anomaly": False,
            "anomaly_reason": "金額無效，跳過異常偵測",
        }

    try:
        # Step 1: 查歷史統計
        stats = get_category_stats(category)

        # Step 2: 取得模型
        model = get_taide_model()
        if not model.is_loaded:
            model.load()

        # Step 3: 組合 prompt
        if stats:
            stat_result = stat_check(amount, stats)
            prompt = ANOMALY_PROMPT.format(
                description=description,
                amount=amount,
                category=category,
                merchant=merchant or "未知",
                avg=stats["avg"],
                std=stats["std"],
                max=stats["max"],
                count=stats["count"],
                stat_flag=stat_result["stat_flag"],
                stat_reason=stat_result["reason"],
                deviation=stat_result["deviation"],
            )
        else:
            stat_result = {"stat_flag": "unknown"}
            prompt = ANOMALY_PROMPT_NO_HISTORY.format(
                description=description,
                amount=amount,
                category=category,
                merchant=merchant or "未知",
            )

        # Step 4: LLM 判斷
        response = model.generate(prompt, temperature=0.1, max_new_tokens=256)
        llm_result = parse_llm_response(response)

        return {
            "is_anomaly": llm_result["is_anomaly"],
            "anomaly_reason": llm_result["reason"],
            "anomaly_severity": llm_result["severity"],
            "anomaly_suggestion": llm_result["suggestion"],
            "anomaly_stat_flag": stat_result["stat_flag"],
            "anomaly_method": "llm+stats" if stats else "llm_only",
        }

    except Exception as e:
        logger.error(f"Anomaly Detector 錯誤: {e}")
        return {
            "is_anomaly": False,
            "anomaly_reason": f"異常偵測失敗: {str(e)}",
            "anomaly_method": "error",
        }
