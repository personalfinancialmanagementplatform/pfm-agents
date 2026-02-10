"""
DB Save Node - LangGraph 版本
將交易資料儲存到 PostgreSQL（目前用 Mock）
"""
import logging
import uuid
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)


# ============================================================================
# Mock DB 儲存（之後替換成真正的 PostgreSQL CRUD）
# ============================================================================

MOCK_DB = []


def mock_save_transaction(transaction: Dict) -> Dict:
    """
    Mock 儲存交易
    TODO: 之後替換成 from ...database.crud import create_transaction
    """
    record = {
        "transaction_id": str(uuid.uuid4()),
        "user_id": transaction.get("user_id"),
        "amount": transaction.get("amount"),
        "transaction_type": transaction.get("transaction_type"),
        "description": transaction.get("description"),
        "category_id": transaction.get("category_id"),
        "category_name": transaction.get("category_name"),
        "merchant": transaction.get("merchant"),
        "is_anomaly": transaction.get("is_anomaly", False),
        "anomaly_reason": transaction.get("anomaly_reason"),
        "created_at": datetime.now().isoformat(),
    }
    MOCK_DB.append(record)
    logger.info(f"[Mock DB] 儲存交易: {record['transaction_id']} - {record['description']} ${record['amount']}")
    return record


# ============================================================================
# LangGraph Node
# ============================================================================

def db_save_node(state: dict) -> dict:
    """
    DB Save Node
    從 state 讀取交易資訊，儲存到資料庫，寫回 transaction_id
    """
    if state.get("error"):
        return {
            "db_success": False,
        }

    amount = state.get("amount", 0)
    if amount <= 0:
        return {
            "db_success": False,
            "error": "金額無效，無法儲存",
        }

    try:
        transaction = {
            "user_id": state.get("user_id"),
            "amount": state.get("amount"),
            "transaction_type": state.get("transaction_type", "expense"),
            "description": state.get("description", ""),
            "category_id": state.get("category_id"),
            "category_name": state.get("category_name", "其他支出"),
            "merchant": state.get("merchant"),
            "is_anomaly": state.get("is_anomaly", False),
            "anomaly_reason": state.get("anomaly_reason"),
        }

        record = mock_save_transaction(transaction)

        return {
            "transaction_id": record["transaction_id"],
            "db_success": True,
        }

    except Exception as e:
        logger.error(f"DB Save 錯誤: {e}")
        return {
            "db_success": False,
            "error": f"儲存失敗: {str(e)}",
        }