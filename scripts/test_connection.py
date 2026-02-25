import os
from dotenv import load_dotenv
import psycopg2
from pymongo import MongoClient
import redis

load_dotenv()

def test_postgres():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print("✅ PostgreSQL 連線成功")
        print(f"   Host: {os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}")
        print(f"   Database: {os.getenv('DB_NAME')}")
        print(f"   Version: {version[:50]}...")
        conn.close()
    except Exception as e:
        print(f"❌ PostgreSQL 連線失敗: {e}")

def test_mongodb():
    try:
        client = MongoClient(
            host=os.getenv("MONGO_HOST"),
            port=int(os.getenv("MONGO_PORT"))
        )
        client.admin.command('ping')
        server_info = client.server_info()
        print("✅ MongoDB 連線成功")
        print(f"   Host: {os.getenv('MONGO_HOST')}:{os.getenv('MONGO_PORT')}")
        print(f"   Version: {server_info['version']}")
    except Exception as e:
        print(f"❌ MongoDB 連線失敗: {e}")

def test_redis():
    try:
        r = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT")),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )
        r.ping()
        info = r.info()
        print("✅ Redis 連線成功")
        print(f"   Host: {os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}")
        print(f"   Version: {info['redis_version']}")
    except Exception as e:
        print(f"❌ Redis 連線失敗: {e}")

if __name__ == "__main__":
    print("🔍 開始測試資料庫連線...\n")
    test_postgres()
    print()
    test_mongodb()
    print()
    test_redis()
