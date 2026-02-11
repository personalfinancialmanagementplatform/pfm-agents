"""
Transaction Parser 測試腳本
測試交易解析功能
"""
import asyncio
from src.agents.bookkeeping import TransactionParserAgent
from src.agents.base import Task


async def test_parser():
    """測試 Transaction Parser"""
    
    # 建立 Parser
    parser = TransactionParserAgent()
    
    # 測試案例
    test_cases = [
        "午餐 150",
        "今天午餐吃麥當勞 180",
        "星巴克咖啡 135",
        "昨天晚餐花了 350",
        "繳電費 1200",
        "薪水入帳 45000",
        "在鼎泰豐吃了 850",
        "買了杯 50嵐 55元",
        "uber 計程車 280",
        "全聯買菜 467",
    ]
    
    print("=" * 60)
    print("Transaction Parser 測試")
    print("=" * 60)
    
    for text in test_cases:
        # 建立任務
        task = Task(input={"text": text})
        
        # 解析
        result = await parser.process(task)
        
        # 顯示結果
        print(f"\n📝 輸入: {text}")
        print(f"   金額: {result.data.get('amount')}")
        print(f"   類型: {result.data.get('transaction_type')}")
        print(f"   描述: {result.data.get('description')}")
        print(f"   商家: {result.data.get('merchant')}")
        print(f"   時間: {result.data.get('time_hint')}")
        print(f"   信心度: {result.data.get('confidence')}")
        print(f"   方法: {result.metadata.get('method')}")
    
    print("\n" + "=" * 60)
    print("✅ 測試完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_parser())