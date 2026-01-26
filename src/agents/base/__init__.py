"""
Base Agent 類別
所有 Agent 的基礎類別
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid


class TaskStatus(str, Enum):
    """A2A Task 狀態"""
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentCard:
    """A2A Agent Card - Agent 的能力宣告"""
    name: str
    description: str
    capabilities: List[str]
    version: str = "1.0.0"
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "version": self.version,
            "dependencies": self.dependencies,
        }


@dataclass
class Task:
    """A2A Task"""
    id: str
    input: Dict[str, Any]
    status: TaskStatus = TaskStatus.SUBMITTED
    session_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    @classmethod
    def create(cls, input_data: Dict[str, Any], session_id: Optional[str] = None) -> "Task":
        return cls(
            id=str(uuid.uuid4()),
            input=input_data,
            session_id=session_id,
        )


@dataclass
class Artifact:
    """A2A Artifact - Task 的輸出結果"""
    type: str
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Agent 基礎類別"""
    
    def __init__(self):
        self._agent_card: Optional[AgentCard] = None
    
    @property
    @abstractmethod
    def agent_card(self) -> AgentCard:
        """回傳 Agent Card"""
        pass
    
    @abstractmethod
    async def process(self, task: Task) -> Artifact:
        """處理 Task，回傳 Artifact"""
        pass
    
    async def execute(self, task: Task) -> Task:
        """執行 Task 完整流程"""
        try:
            task.status = TaskStatus.WORKING
            artifact = await self.process(task)
            task.status = TaskStatus.COMPLETED
            task.result = {
                "artifact": {
                    "type": artifact.type,
                    "data": artifact.data,
                    "metadata": artifact.metadata,
                }
            }
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
        
        return task
