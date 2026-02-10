"""
Summary Generator Node - LangGraph 版本
彙整記帳流程所有結果，用 TAIDE 生成友善的回覆訊息
"""
import json
import logging
from typing import Dict

from ....models import get_taide_model

logger = logging.getLogger(__name__)


# ============================================================================
# LLM Prompt
# ============================================================================

SUMMARY_PROMPT = """你是一個友善的記帳助手。根據以下記帳結果，生成一段簡短、口語化的回覆訊息給用戶。

記帳結果：
- 描述：{description}
- 金額：${amount}
- 類型：{transaction_type}
- 分類：{category_name}
- 商家：{merchant}
- 是否異常：{is_anomaly}
- 異常原因：{anomaly_reason}
- 預算狀態：{budget_level}
- 預算提醒：{budget_warning}
- 預算使用：{budget_usage_pct}%
- 預算剩餘：${budget_remaining}
- 儲存成功：{db_success}

請生成一段回覆訊息，要求：
1. 第一行用 ✅ 確認記帳成功（包含金額、分類）
2. 如果有異常，用 ⚠️ 提醒
3. 如果預算狀態是 warning/critical/exceeded，用 🟡/🔴 提醒預算
4. 語氣友善、簡潔，像朋友聊天
5. 總共不超過 3 行

只回覆訊息本身，不要 JSON，不要額外說明。"""

SUMMARY_PROMPT_ERROR = """你是一個友善的記帳助手。記帳過程發生錯誤，請生成一段簡短的錯誤提示。

錯誤資訊：{error}

請用友善的語氣告訴用戶記帳失敗，並建議重新輸入。不超過 2 行。
只回覆訊息本身，不要 JSON，不要額外說明。"""


# ============================================================================
# Fallback（如果 LLM 失敗，用規則生成）
# ============================================================================

def generate_fallback_summary(state: dict) -> str:
    """當 LLM 失敗時，用簡單規則生成回覆"""
    amount = state.get("amount", 0)
    category = state.get("category_name", "其他")
    description = state.get("description", "消費")
    tx_type = state.get("transaction_type", "expense")
    is_anomaly = state.get("is_anomaly", False)
    budget_level = state.get("budget_level", "")
    budget_usage_pct = state.get("budget_usage_pct", 0)

    # 基本確認
    if tx_type == "income":
        msg = f"✅ 已記錄收入：{description} +${amount}（{category}）"
    else:
        msg = f"✅ 已記錄：{description} ${amount}（{category}）"

    # 異常提醒
    if is_anomaly:
        reason = state.get("anomaly_reason", "金額偏高")
        msg += f"\n⚠️ 注意：{reason}"

    # 預算提醒
    if budget_level == "exceeded":
        msg += f"\n🔴 本月{category}預算已超支！已使用 {budget_usage_pct}%"
    elif budget_level == "critical":
        msg += f"\n🔴 本月{category}預算即將用完！已使用 {budget_usage_pct}%"
    elif budget_level == "warning":
        msg += f"\n🟡 本月{category}預算已使用 {budget_usage_pct}%，注意控制"

    return msg


# ============================================================================
# LangGraph Node
# ============================================================================

def summary_generator_node(state: dict) -> dict:
    """
    Summary Generator Node（TAIDE LLM）
    彙整所有記帳結果，生成友善的回覆訊息
    """
    # 如果有錯誤，生成錯誤訊息
    if state.get("error"):
        try:
            model = get_taide_model()
            if not model.is_loaded:
                model.load()
            prompt = SUMMARY_PROMPT_ERROR.format(error=state["error"])
            response = model.generate(prompt, temperature=0.3, max_new_tokens=128)
            return {"response_message": response.strip()}
        except Exception:
            return {"response_message": f"❌ 記帳失敗：{state['error']}，請重新輸入"}

    # 如果 DB 儲存失敗
    if not state.get("db_success", False):
        return {"response_message": "❌ 記帳儲存失敗，請稍後再試"}

    try:
        model = get_taide_model()
        if not model.is_loaded:
            model.load()

        prompt = SUMMARY_PROMPT.format(
            description=state.get("description", "消費"),
            amount=state.get("amount", 0),
            transaction_type="收入" if state.get("transaction_type") == "income" else "支出",
            category_name=state.get("category_name", "其他"),
            merchant=state.get("merchant", "未知"),
            is_anomaly="是" if state.get("is_anomaly") else "否",
            anomaly_reason=state.get("anomaly_reason", "無"),
            budget_level=state.get("budget_level", "無預算"),
            budget_warning=state.get("budget_warning", "無"),
            budget_usage_pct=state.get("budget_usage_pct", 0),
            budget_remaining=state.get("budget_remaining", 0),
            db_success="是" if state.get("db_success") else "否",
        )

        response = model.generate(prompt, temperature=0.3, max_new_tokens=256)
        message = response.strip()

    #如果 LLM 回覆太短、太長、或不像 JSON，用 fallback
        if len(message) < 5 or len(message) > 200 or message.startswith("{"):
            message = generate_fallback_summary(state)

        return {"response_message": message}

    except Exception as e:
        logger.error(f"Summary Generator 錯誤: {e}")
        return {"response_message": generate_fallback_summary(state)}