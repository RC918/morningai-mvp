"""
資料庫遷移腳本
用於安全地添加缺失的欄位到現有的資料庫表中
"""

import logging

from sqlalchemy import inspect, text

from src.database import db

logger = logging.getLogger(__name__)


def check_column_exists(table_name, column_name):
    """檢查表格中是否存在指定的欄位"""
    try:
        inspector = inspect(db.engine)
        columns = inspector.get_columns(table_name)
        return any(col["name"] == column_name for col in columns)
    except Exception as e:
        logger.error(f"Error checking column {column_name} in table {table_name}: {e}")
        return False


def add_column_if_not_exists(table_name, column_name, column_definition):
    """如果欄位不存在，則添加到表格中"""
    try:
        if not check_column_exists(table_name, column_name):
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
            # 使用新的 SQLAlchemy 語法
            with db.engine.connect() as connection:
                connection.execute(text(sql))
                connection.commit()
            logger.info(f"Added column {column_name} to table {table_name}")
            return True
        else:
            logger.info(f"Column {column_name} already exists in table {table_name}")
            return False
    except Exception as e:
        logger.error(f"Error adding column {column_name} to table {table_name}: {e}")
        raise


def migrate_user_table():
    """遷移 user 表格，添加 2FA 相關欄位"""
    logger.info("Starting user table migration...")

    migrations_applied = []

    # 添加 two_factor_secret 欄位
    if add_column_if_not_exists("user", "two_factor_secret", "VARCHAR(32)"):
        migrations_applied.append("two_factor_secret")

    # 添加 two_factor_enabled 欄位
    if add_column_if_not_exists("user", "two_factor_enabled", "BOOLEAN DEFAULT FALSE"):
        migrations_applied.append("two_factor_enabled")

    if migrations_applied:
        logger.info(
            f"User table migration completed. Added columns: {', '.join(migrations_applied)}"
        )
    else:
        logger.info("User table migration completed. No changes needed.")

    return migrations_applied


def run_all_migrations():
    """執行所有資料庫遷移"""
    logger = logging.getLogger(__name__)
    results = []

    try:
        # 確保資料庫連接正常
        logger.info("Testing database connection...")
        db.session.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")

        # 檢查當前資料庫狀態
        logger.info("Checking current database schema...")

        # 執行所有遷移
        logger.info("Starting two-factor authentication column migration...")
        migration_result = migrate_user_table()
        results.append(migration_result)
        logger.info(f"✅ Two-factor migration result: {migration_result}")

        # 提交所有變更
        db.session.commit()
        logger.info("✅ All migrations completed successfully")

        return results

    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        try:
            db.session.rollback()
            logger.info("Database session rolled back")
        except Exception as rollback_error:
            logger.error(f"Rollback failed: {rollback_error}")

        # 不要重新拋出異常，讓應用程式繼續運行
        logger.warning("Migration failed, but continuing application startup...")
        return [f"FAILED: {str(e)}"]


if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO)

    # 執行遷移
    from src.main import app

    with app.app_context():
        results = run_all_migrations()
        print(f"Migration results: {results}")
