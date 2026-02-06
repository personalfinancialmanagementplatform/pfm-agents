"""
PostgreSQL 資料庫連線管理
使用 psycopg2 純 SQL 操作
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# 載入 .env
load_dotenv()

# 資料庫設定
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "pfm_agents"),
    "user": os.getenv("DB_USER", "emily200008"),
    "password": os.getenv("DB_PASSWORD", "108306052J"),
}


def get_connection():
    """
    取得資料庫連線
    回傳 psycopg2 connection 物件
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"❌ 資料庫連線失敗: {e}")
        raise


def close_connection(conn):
    """關閉資料庫連線"""
    if conn and not conn.closed:
        conn.close()


def execute_query(sql, params=None, fetch=False):
    """
    執行 SQL 查詢的通用函數
    
    參數:
        sql: SQL 語句
        params: SQL 參數 (tuple)
        fetch: 是否回傳查詢結果
    
    回傳:
        fetch=True 時回傳查詢結果 (list of dict)
        fetch=False 時回傳 None
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if fetch:
                result = cur.fetchall()
            else:
                result = None
            conn.commit()
            return result
    except psycopg2.Error as e:
        conn.rollback()
        print(f"❌ SQL 執行失敗: {e}")
        raise
    finally:
        close_connection(conn)


# 測試連線
if __name__ == "__main__":
    try:
        conn = get_connection()
        print(f"✅ 成功連線到: {DB_CONFIG['database']}")
        close_connection(conn)
    except Exception as e:
        print(f"❌ 連線失敗: {e}")