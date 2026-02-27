"""
Agent 基礎定義 - LangGraph 版本
使用 TypedDict 作為 State，搭配 LangGraph 建構流程
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict
from enum import Enum
import uuid


# ============================================================================
# State 定義（LangGraph 核心）
# ============================================================================

class BookkeepingState(TypedDict, total=False):
    """記帳流程的共享狀態，所有 Node 都讀寫這個 State"""
    # 輸入
    user_id: int
    raw_text: str
    intent: str  # record / query / analyze

    # Transaction Parser 輸出
    amount: float
    transaction_type: str  # expense / income
    description: str
    time_hint: Optional[str]
    merchant: Optional[str]
    parse_confidence: float
    parse_method: str  # rule_based / llm

    # Category Classifier 輸出
    category_id: Optional[int]
    category_name: Optional[str]

    # Anomaly Detector 輸出
    is_anomaly: bool
    anomaly_reason: Optional[str]

    # Budget Monitor 輸出
    budget_warning: Optional[str]
    budget_level: Optional[str]  # ok / high / exceeded

    # DB 儲存結果
    transaction_id: Optional[int]
    db_success: bool

    # 最終輸出
    response_message: str
    error: Optional[str]


# ============================================================================
# 舊有資料結構（保留向下相容）
# ============================================================================

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentCard:
    """A2A Agent Card - Agent 能力宣告"""
    name: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)
    mcp_tools: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "version": self.version,
            "dependencies": self.dependencies,
            "mcp_tools": self.mcp_tools,
        }


@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    input: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "input": self.input,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Artifact:
    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "data": self.data,
            "metadata": self.metadata,
        }

    @property
    def is_error(self) -> bool:
        return self.type == "error"


@dataclass
class AgentResult:
    success: bool
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    next_action: Optional[str] = None
    artifacts: List[Artifact] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "next_action": self.next_action,
        }


# ============================================================================
# 匯出
# ============================================================================

__all__ = [
    # LangGraph State
    "BookkeepingState",
    # 舊有結構（向下相容）
    "TaskStatus",
    "AgentCard",
    "Task",
    "Artifact",
    "AgentResult",
]