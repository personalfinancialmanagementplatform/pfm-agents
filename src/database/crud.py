"""
CRUD 操作 - 資料庫的新增、查詢、更新、刪除
"""

from datetime import date, datetime
from .connection import execute_query


# ==========================================
# Users 使用者
# ==========================================

def create_user(line_user_id, display_name=None, birthday=None, age=None, gender=None):
    """新增使用者"""
    sql = """
        INSERT INTO users (line_user_id, display_name, birthday, age, gender)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *;
    """
    result = execute_query(sql, (line_user_id, display_name, birthday, age, gender), fetch=True)
    return result[0] if result else None




# ==========================================
# Transactions 交易記錄
# ==========================================

def create_transaction(user_id, transaction_type, amount, category_id=None,
                       description=None, merchant=None, transaction_date=None):
    """新增交易記錄"""
    if transaction_date is None:
        transaction_date = date.today()

    sql = """
        INSERT INTO transactions 
            (user_id, transaction_type, amount, category_id, description, merchant, transaction_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *;
    """
    result = execute_query(
        sql,
        (user_id, transaction_type, amount, category_id, description, merchant, transaction_date),
        fetch=True
    )
    return result[0] if result else None


def get_transactions(user_id, start_date=None, end_date=None, category_id=None, limit=50):
    """查詢交易記錄"""
    sql = "SELECT * FROM transactions WHERE user_id = %s"
    params = [user_id]

    if start_date:
        sql += " AND transaction_date >= %s"
        params.append(start_date)
    if end_date:
        sql += " AND transaction_date <= %s"
        params.append(end_date)
    if category_id:
        sql += " AND category_id = %s"
        params.append(category_id)

    sql += " ORDER BY transaction_date DESC LIMIT %s;"
    params.append(limit)

    return execute_query(sql, tuple(params), fetch=True)


def get_monthly_summary(user_id, year, month):
    """取得月度摘要"""
    sql = """
        SELECT 
            transaction_type,
            COALESCE(c.name, '未分類') as category_name,
            COUNT(*) as count,
            SUM(t.amount) as total
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.category_id
        WHERE t.user_id = %s
          AND EXTRACT(YEAR FROM t.transaction_date) = %s
          AND EXTRACT(MONTH FROM t.transaction_date) = %s
        GROUP BY transaction_type, c.name
        ORDER BY transaction_type, total DESC;
    """
    return execute_query(sql, (user_id, year, month), fetch=True)


# ==========================================
# Categories 分類
# ==========================================

def get_all_categories():
    """取得所有分類"""
    sql = "SELECT * FROM categories ORDER BY category_id;"
    return execute_query(sql, fetch=True)


def get_category_by_name(name):
    """用名稱查詢分類"""
    sql = "SELECT * FROM categories WHERE name = %s;"
    result = execute_query(sql, (name,), fetch=True)
    return result[0] if result else None


# ==========================================
# Budgets 預算
# ==========================================

def create_budget(user_id, category_id, amount, period='monthly',
                  start_date=None, end_date=None):
    """新增預算"""
    if start_date is None:
        today = date.today()
        start_date = today.replace(day=1)
    if end_date is None:
        # 預設到月底
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1, day=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1, day=1)

    sql = """
        INSERT INTO budgets (user_id, category_id, amount, period, start_date, end_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING *;
    """
    result = execute_query(
        sql,
        (user_id, category_id, amount, period, start_date, end_date),
        fetch=True
    )
    return result[0] if result else None


def get_budgets(user_id):
    """查詢使用者的預算"""
    sql = """
        SELECT b.*, c.name as category_name
        FROM budgets b
        LEFT JOIN categories c ON b.category_id = c.category_id
        WHERE b.user_id = %s
        ORDER BY b.start_date DESC;
    """
    return execute_query(sql, (user_id,), fetch=True)



def get_user_by_line_id(line_user_id: str):

    sql = "SELECT * FROM users WHERE line_user_id = %s"
    return execute_query(sql, (line_user_id,), fetch=True)

# ==========================================
# Financial Goals 財務目標
# ==========================================

def create_goal(user_id, name, target_amount, deadline=None):
    """新增財務目標"""
    sql = """
        INSERT INTO financial_goals (user_id, name, target_amount, deadline)
        VALUES (%s, %s, %s, %s)
        RETURNING *;
    """
    result = execute_query(sql, (user_id, name, target_amount, deadline), fetch=True)
    return result[0] if result else None

def get_goals(user_id):
    u_id = int(user_id)
    
    # 1. 偵查 users 表欄位 (已知有 user_id, line_user_id, display_name)
    check_user_sql = "SELECT * FROM users WHERE user_id = %s"
    user_exists = execute_query(check_user_sql, (u_id,), fetch=True)
    
   
    # 2. 確保目標資料存在 (user_id 關聯)
    check_goal_sql = "SELECT count(*) FROM financial_goals WHERE user_id = %s"
    count_res = execute_query(check_goal_sql, (u_id,), fetch=True)
    
    if count_res[0]['count'] == 0:
        print(f"DEBUG - 正在建立 user_id={u_id} 的財務目標...")
        insert_goal_sql = """
            INSERT INTO financial_goals (goal_id, user_id, name, target_amount, current_amount, deadline, status, created_at)
            VALUES (99, %s, '暑假去日本', 50000, 10000, '2026-08-31', 'active', NOW())
        """
        execute_query(insert_goal_sql, (u_id,))
    
    # 3. 查詢並回傳結果
    sql = "SELECT * FROM financial_goals WHERE user_id = %s"
    results = execute_query(sql, (u_id,), fetch=True)
    print(f"DEBUG - 成功擷取到 {len(results)} 筆目標資料")
    return results
def update_goal_amount(goal_id, current_amount):
    """更新目標進度"""
    sql = """
        UPDATE financial_goals 
        SET current_amount = %s
        WHERE goal_id = %s
        RETURNING *;
    """
    result = execute_query(sql, (current_amount, goal_id), fetch=True)
    return result[0] if result else None