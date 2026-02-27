import os
import sys
from dotenv import load_dotenv

# --- 1. 環境變數載入與路徑設定 ---
# 取得目前檔案的絕對路徑，確保能正確找到專案根目錄下的 .env 檔案
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root) 

dotenv_path = os.path.join(project_root, ".env")
# 強制載入 .env 並覆蓋系統環境變數，確保 DATABASE_URL 指向 PostgreSQL
load_dotenv(dotenv_path=dotenv_path, override=True)

# 偵錯用：確認載入的資料庫路徑是否正確
print(f"DEBUG - .env 路徑: {dotenv_path}")
print(f"DEBUG - 檔案是否存在: {os.path.exists(dotenv_path)}")
print(f"DEBUG - 讀取的 URL: {os.getenv('DATABASE_URL')}")

# --- 2. 導入 Agent 應用程式 ---
# 從 coordinator 導入編排好的 LangGraph 應用
from src.agents.goals.coordinator import goals_app 

# --- 3. 準備測試數據 ---
# 這裡的 user_id 必須與你在 PostgreSQL 中 INSERT 的資料對齊
test_state = {
    "user_id": 13,          # 必須是整數 13，對應剛才 pgAdmin 確認的 ID
    "raw_text": "查詢進度",  # 模擬使用者的輸入指令
    "is_lagging": False,
    "advice_options": []
}

# --- 4. 執行測試流程 ---
if __name__ == "__main__":
    print("\n" + "="*30)
    print("🚀 開始執行目標 Agent 整合測試")
    print("="*30)
    
    try:
        # 使用 invoke 啟動 LangGraph 工作流
        # 流程會經過 goal_manager -> savings_advisor (若進度落後) -> notifier
        final_state = goals_app.invoke(test_state)
        
        print("\n--- Agent 最終回覆 ---")
        # 從最終狀態中擷取回傳訊息
        print(final_state.get("response_message", "❌ 無法取得回覆訊息"))
        print("="*30)
        
    except Exception as e:
        print(f"\n❌ 執行過程中發生錯誤: {e}")