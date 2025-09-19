#!/bin/bash
# Phase-DB.2: Migration 文件清理腳本

set -e

echo "=== Migration 文件清理開始 ==="

# 備份現有的 migration 文件
echo "1. 備份現有 migration 文件..."
mkdir -p ../../ops/db/backups/legacy_migrations
cp -r apps/api/migrations/* ../../ops/db/backups/legacy_migrations/ 2>/dev/null || echo "No legacy migrations to backup"

# 檢查 Alembic 版本目錄
echo "2. 檢查 Alembic 版本目錄..."
ls -la apps/api/alembic/versions/

# 驗證新的整合 migration
echo "3. 驗證新的整合 migration..."
if [ -f "apps/api/alembic/versions/20250920_001_initial_schema.py" ]; then
    echo "✓ 整合 migration 文件存在"
else
    echo "✗ 整合 migration 文件不存在"
    exit 1
fi

# 標記舊的 migration 文件為已棄用
echo "4. 標記舊的 migration 文件..."
for file in apps/api/migrations/*.sql; do
    if [ -f "$file" ]; then
        echo "-- DEPRECATED: This file has been consolidated into Alembic migration 20250920_001" > "${file}.deprecated"
        cat "$file" >> "${file}.deprecated"
        echo "標記為已棄用: $file"
    fi
done

echo "=== Migration 文件清理完成 ==="
echo "注意: 舊的 SQL migration 文件已標記為 deprecated，但未刪除以確保安全"
