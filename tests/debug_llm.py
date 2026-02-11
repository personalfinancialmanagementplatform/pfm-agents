"""
Transaction Parser Debug 測試
看看 LLM 實際回傳什麼
"""
import asyncio
import sys
import os

# 加入專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import get_taide_model

# 從 transaction_parser.py 複製的 prompt
PARSE_PROMPT = """你是一個交易解析助手。請從以下用戶輸入中提取交易資訊。

用戶輸入：{user_input}

請以 JSON 格式回應，包含以下欄位：
- amount: 金額（數字）
- transaction_type: 交易類型（"expense" 或 "income"）
- description: 描述
- merchant: 商家名稱（如果有）
- time_hint: 時間提示（如果有）

只回應 JSON，不要其他文字。

回應："""


async def debug_llm():
    """Debug LLM 回應"""
    
    # 載入模型
    print("🔄 載入 TAIDE 模型...")
    model = get_taide_model()
    model.load()
    print("✅ 模型載入完成\n")
    
    # 測試案例（信心度 < 0.8 的）
    test_cases = [
        "午餐 150",           # 0.8 (有時間)
        "繳電費 1200",        # 0.7 (沒商家沒時間)
        "薪水入帳 45000",     # 0.7
        "uber 計程車 280",    # 0.7
    ]
    
    print("=" * 60)
    print("LLM Debug 測試 - 查看原始回應")
    print("=" * 60)
    
    for text in test_cases:
        print(f"\n📝 輸入: {text}")
        print("-" * 40)
        
        # 組合 prompt
        prompt = PARSE_PROMPT.format(user_input=text)
        
        # 呼叫 LLM
        print(f"📥 LLM 原始回應:")
        try:
            response = model.generate(prompt, temperature=0.1, max_new_tokens=256)
            print(f"'''\n{response}\n'''")
            
            # 嘗試解析 JSON
            import json
            import re
            
            # 嘗試提取 JSON
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                print(f"\n🔍 提取的 JSON: {json_str}")
                try:
                    parsed = json.loads(json_str)
                    print(f"✅ 解析成功: {parsed}")
                    print(f"   金額: {parsed.get('amount', 'N/A')}")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 解析失敗: {e}")
            else:
                print("❌ 找不到 JSON 格式")
                
        except Exception as e:
            print(f"❌ LLM 呼叫失敗: {e}")
        
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("✅ Debug 完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(debug_llm())