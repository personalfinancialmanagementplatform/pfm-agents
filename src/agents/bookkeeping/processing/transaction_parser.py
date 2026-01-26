"""
Transaction Parser Agent
交易解析 Agent - 將自然語言轉為結構化交易資料
"""
import json
import re
from typing import Any, Dict, Optional
from dataclasses import dataclass

from ..base import BaseAgent, AgentCard, Task, Artifact
from ...models import get_taide_model


@dataclass
class ParsedTransaction:
    """解析後的交易"""
    amount: float
    transaction_type: str  # expense / income
    description: str
    time_hint: Optional[str] = None
    merchant: Optional[str] = None


PARSE_PROMPT = """你是一個記帳助手，專門解析用戶的記帳輸入。

請解析以下記帳內容，提取交易資訊。

用戶輸入：{user_input}

請以 JSON 格式回答，包含以下欄位：
- amount: 金額（純數字）
- transaction_type: "expense" 或 "income"
- description: 簡短描述（2-10字）
- time_hint: 時間提示（如「今天」「午餐」，若無則 null）
- merchant: 商家名稱（若無則 null）

只回覆 JSON，不要其他文字。"""


class TransactionParserAgent(BaseAgent):
    """交易解析 Agent"""
    
    @property
    def agent_card(self) -> AgentCard:
        return AgentCard(
            name="transaction_parser",
            description="解析自然語言記帳輸入，提取交易資訊",
            capabilities=["parse_transaction"],
        )
    
    async def process(self, task: Task) -> Artifact:
        """解析交易"""
        text = task.input.get("text", "")
        
        if not text:
            return Artifact(
                type="error",
                data={"message": "No input text provided"},
            )
        
        # 先嘗試規則解析
        rule_result = self._rule_based_parse(text)
        if rule_result:
            return Artifact(
                type="parsed_transaction",
                data=rule_result.__dict__,
                metadata={"method": "rule_based"},
            )
        
        # 使用 LLM 解析
        llm_result = await self._llm_parse(text)
        return Artifact(
            type="parsed_transaction",
            data=llm_result,
            metadata={"method": "llm"},
        )
    
    def _rule_based_parse(self, text: str) -> Optional[ParsedTransaction]:
        """規則解析 - 處理簡單格式"""
        # 匹配: "午餐 150" 或 "150 午餐" 或 "午餐花了150"
        patterns = [
            r"(.+?)\s*(\d+(?:\.\d+)?)\s*元?$",
            r"(\d+(?:\.\d+)?)\s*元?\s*(.+)$",
            r"(.+?)花了?\s*(\d+(?:\.\d+)?)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                try:
                    # 判斷哪個是金額
                    if groups[0].replace(".", "").isdigit():
                        amount = float(groups[0])
                        desc = groups[1].strip()
                    else:
                        amount = float(groups[1])
                        desc = groups[0].strip()
                    
                    return ParsedTransaction(
                        amount=amount,
                        transaction_type="expense",
                        description=desc[:10],
                    )
                except ValueError:
                    continue
        
        return None
    
    async def _llm_parse(self, text: str) -> Dict[str, Any]:
        """LLM 解析"""
        model = get_taide_model()
        prompt = PARSE_PROMPT.format(user_input=text)
        
        response = model.generate(prompt, temperature=0.1)
        
        # 嘗試解析 JSON
        try:
            # 清理可能的 markdown 格式
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "amount": 0,
                "transaction_type": "expense",
                "description": text[:10],
                "time_hint": None,
                "merchant": None,
                "raw_response": response,
            }
