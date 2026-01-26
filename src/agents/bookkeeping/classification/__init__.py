"""
Category Classifier Agent
類別分類 Agent
"""
import json
from typing import Any, Dict, List, Optional
from ..base import BaseAgent, AgentCard, Task, Artifact
from ...models import get_taide_model


# 預設分類
CATEGORIES = {
    "food": {
        "name": "飲食",
        "sub_categories": ["breakfast", "lunch", "dinner", "drinks", "snacks"],
        "keywords": ["吃", "餐", "飯", "麵", "便當", "早餐", "午餐", "晚餐", "咖啡", "飲料", "茶"],
    },
    "transport": {
        "name": "交通",
        "sub_categories": ["public", "taxi", "parking", "fuel"],
        "keywords": ["捷運", "公車", "uber", "計程車", "停車", "加油", "高鐵", "火車"],
    },
    "entertainment": {
        "name": "娛樂",
        "sub_categories": ["movies", "games", "sports", "travel"],
        "keywords": ["電影", "遊戲", "KTV", "唱歌", "旅遊", "門票"],
    },
    "shopping": {
        "name": "購物",
        "sub_categories": ["clothes", "electronics", "daily", "gifts"],
        "keywords": ["買", "購", "衣服", "3C", "日用品", "禮物"],
    },
    "medical": {
        "name": "醫療",
        "sub_categories": ["hospital", "medicine", "insurance"],
        "keywords": ["看診", "醫院", "藥", "掛號", "保險"],
    },
    "fixed": {
        "name": "固定支出",
        "sub_categories": ["rent", "utilities", "subscription"],
        "keywords": ["房租", "水電", "電話", "網路", "訂閱", "月租"],
    },
}


class CategoryClassifierAgent(BaseAgent):
    """類別分類 Agent"""
    
    @property
    def agent_card(self) -> AgentCard:
        return AgentCard(
            name="category_classifier",
            description="將交易分類到適當的類別",
            capabilities=["classify_transaction", "suggest_category"],
        )
    
    async def process(self, task: Task) -> Artifact:
        """分類交易"""
        description = task.input.get("description", "")
        merchant = task.input.get("merchant")
        amount = task.input.get("amount", 0)
        
        # 先嘗試規則分類
        rule_result = self._rule_based_classify(description, merchant)
        if rule_result["confidence"] > 0.7:
            return Artifact(
                type="classification",
                data=rule_result,
                metadata={"method": "rule_based"},
            )
        
        # 使用 LLM 分類
        llm_result = await self._llm_classify(description, merchant, amount)
        return Artifact(
            type="classification",
            data=llm_result,
            metadata={"method": "llm"},
        )
    
    def _rule_based_classify(
        self, 
        description: str, 
        merchant: Optional[str] = None
    ) -> Dict[str, Any]:
        """規則分類"""
        text = f"{description} {merchant or ''}".lower()
        
        best_match = None
        best_score = 0
        
        for cat_id, cat_info in CATEGORIES.items():
            score = 0
            for keyword in cat_info["keywords"]:
                if keyword in text:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = cat_id
        
        if best_match and best_score > 0:
            confidence = min(0.5 + (best_score * 0.15), 0.95)
            return {
                "category": best_match,
                "category_name": CATEGORIES[best_match]["name"],
                "confidence": confidence,
            }
        
        return {
            "category": "other",
            "category_name": "其他",
            "confidence": 0.3,
        }
    
    async def _llm_classify(
        self,
        description: str,
        merchant: Optional[str],
        amount: float,
    ) -> Dict[str, Any]:
        """LLM 分類"""
        model = get_taide_model()
        
        categories_str = ", ".join([
            f"{k}({v['name']})" for k, v in CATEGORIES.items()
        ])
        
        prompt = f"""請將以下消費分類：

描述：{description}
商家：{merchant or '未知'}
金額：{amount}

可用分類：{categories_str}, other(其他)

請回覆 JSON 格式：
{{"category": "分類ID", "confidence": 0.0-1.0, "reason": "原因"}}

只回覆 JSON。"""
        
        response = model.generate(prompt, temperature=0.1)
        
        try:
            result = json.loads(response.strip())
            cat_id = result.get("category", "other")
            return {
                "category": cat_id,
                "category_name": CATEGORIES.get(cat_id, {}).get("name", "其他"),
                "confidence": result.get("confidence", 0.5),
                "reason": result.get("reason", ""),
            }
        except json.JSONDecodeError:
            return {
                "category": "other",
                "category_name": "其他",
                "confidence": 0.3,
            }
