"""
Agent 基礎類別定義
定義所有 Agent 共用的基礎結構
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid


# ============================================================================
# 資料結構定義
# ============================================================================

class TaskStatus(str, Enum):
    """任務狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentCard:
    """
    A2A Agent Card - Agent 能力宣告
    
    用於描述 Agent 的基本資訊和能力，
    讓其他 Agent 或協調器知道如何與它互動。
    """
    name: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)
    mcp_tools: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "version": self.version,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "dependencies": self.dependencies,
            "mcp_tools": self.mcp_tools,
        }


@dataclass
class Task:
    """
    任務定義
    
    代表一個要交給 Agent 處理的任務。
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    input: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "id": self.id,
            "input": self.input,
            "context": self.context,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Artifact:
    """
    Agent 輸出產物
    
    代表 Agent 處理完任務後產生的結果。
    """
    type: str  # parsed_transaction, classification, summary, error, etc.
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "type": self.type,
            "data": self.data,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }
    
    @property
    def is_error(self) -> bool:
        """是否為錯誤結果"""
        return self.type == "error"


@dataclass
class AgentResult:
    """
    Agent 執行結果（擴展版）
    
    包含成功/失敗狀態、訊息、資料，以及可能的下一步動作。
    """
    success: bool
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    next_action: Optional[str] = None  # 建議的下一步動作
    artifacts: List[Artifact] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "next_action": self.next_action,
            "artifacts": [a.to_dict() for a in self.artifacts],
        }


# ============================================================================
# 基礎 Agent 類別
# ============================================================================

class BaseAgent(ABC):
    """
    Agent 基礎類別
    
    所有 Agent 都應該繼承這個類別，並實作：
    - agent_card: 定義 Agent 的能力宣告
    - process: 處理任務的主要邏輯
    
    使用範例：
        class MyAgent(BaseAgent):
            @property
            def agent_card(self) -> AgentCard:
                return AgentCard(
                    name="my_agent",
                    description="我的 Agent",
                    capabilities=["do_something"],
                )
            
            async def process(self, task: Task) -> Artifact:
                # 處理邏輯
                return Artifact(type="result", data={...})
    """
    
    def __init__(self):
        """初始化 Agent"""
        self._initialized = False
    
    @property
    @abstractmethod
    def agent_card(self) -> AgentCard:
        """
        Agent 能力宣告
        
        Returns:
            AgentCard: Agent 的能力描述
        """
        pass
    
    @abstractmethod
    async def process(self, task: Task) -> Artifact:
        """
        處理任務
        
        Args:
            task: 要處理的任務
            
        Returns:
            Artifact: 處理結果
        """
        pass
    
    async def initialize(self) -> None:
        """
        初始化 Agent（可選覆寫）
        
        用於載入模型、建立連線等初始化工作。
        """
        self._initialized = True
    
    async def shutdown(self) -> None:
        """
        關閉 Agent（可選覆寫）
        
        用於釋放資源、關閉連線等清理工作。
        """
        self._initialized = False
    
    @property
    def name(self) -> str:
        """Agent 名稱"""
        return self.agent_card.name
    
    @property
    def capabilities(self) -> List[str]:
        """Agent 能力列表"""
        return self.agent_card.capabilities
    
    def can_handle(self, capability: str) -> bool:
        """
        檢查是否支援某能力
        
        Args:
            capability: 能力名稱
            
        Returns:
            bool: 是否支援
        """
        return capability in self.capabilities
    
    async def __call__(self, task: Task) -> Artifact:
        """
        讓 Agent 可以直接被呼叫
        
        使用方式：
            result = await agent(task)
        """
        if not self._initialized:
            await self.initialize()
        return await self.process(task)
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name})>"


# ============================================================================
# 匯出
# ============================================================================

__all__ = [
    "TaskStatus",
    "AgentCard",
    "Task",
    "Artifact",
    "AgentResult",
    "BaseAgent",
]