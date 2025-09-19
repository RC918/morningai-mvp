#!/usr/bin/env python3
"""
資料庫結構修復腳本
修復 users 表缺少的欄位問題
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

def get_database_connection():
    """獲取資料庫連接"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("錯誤: 未找到 DATABASE_URL 環境變數")
        sys.exit(1)
    
    # 解析 DATABASE_URL
    parsed = urlparse(database_url)
    
    try:
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # 移除開頭的 '/'
            user=parsed.username,
            password=parsed.password
        )
        return conn
    except Exception as e:
        print(f"資料庫連接失敗: {e}")
        sys.exit(1)

def check_column_exists(conn, table_name, column_name):
    """檢查欄位是否存在"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s AND column_name = %s
    """, (table_name, column_name))
    
    result = cursor.fetchone()
    cursor.close()
    return result is not None

def add_missing_columns(conn):
    """添加缺少的欄位"""
    cursor = conn.cursor()
    
    # 檢查並添加 is_active 欄位
    if not check_column_exists(conn, 'users', 'is_active'):
        print("添加 users.is_active 欄位...")
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN is_active BOOLEAN DEFAULT TRUE
        """)
        print("✅ users.is_active 欄位已添加")
    else:
        print("✅ users.is_active 欄位已存在")
    
    # 檢查並添加其他可能缺少的欄位
    missing_columns = [
        ('users', 'tokens_valid_since', 'TIMESTAMP'),
        ('users', 'is_email_verified', 'BOOLEAN DEFAULT FALSE'),
        ('users', 'two_factor_secret', 'VARCHAR(32)'),
        ('users', 'two_factor_enabled', 'BOOLEAN DEFAULT FALSE'),
        ('users', 'tenant_id', 'INTEGER'),
        ('users', 'tenant_role', 'VARCHAR(50) DEFAULT \'member\''),
        ('users', 'created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        ('users', 'updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    ]
    
    for table, column, column_type in missing_columns:
        if not check_column_exists(conn, table, column):
            print(f"添加 {table}.{column} 欄位...")
            cursor.execute(f"""
                ALTER TABLE {table} 
                ADD COLUMN {column} {column_type}
            """)
            print(f"✅ {table}.{column} 欄位已添加")
        else:
            print(f"✅ {table}.{column} 欄位已存在")
    
    conn.commit()
    cursor.close()

def main():
    """主函數"""
    print("開始修復資料庫結構...")
    
    # 獲取資料庫連接
    conn = get_database_connection()
    
    try:
        # 添加缺少的欄位
        add_missing_columns(conn)
        
        print("\n🎉 資料庫結構修復完成！")
        
    except Exception as e:
        print(f"❌ 修復過程中發生錯誤: {e}")
        conn.rollback()
        sys.exit(1)
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()
