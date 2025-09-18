#!/bin/bash

# 設置 PYTHONPATH 以確保 Python 能夠找到 src 包
export PYTHONPATH="/opt/render/project/src/apps/api/src:$PYTHONPATH"

# 進入 apps/api 目錄
cd /opt/render/project/src/apps/api

# 刪除舊的資料庫文件 (如果存在)
rm -f src/database/app.db

# 創建資料庫目錄 (如果不存在)
mkdir -p src/database

# 運行 seed 腳本來創建默認管理員用戶
python scripts/seed_admin.py

# 打印路由表 (用於調試)
python -c "
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from main import app

print(\"--- Registered Routes ---\")
for r in app.url_map.iter_rules():
    print(r.rule, list(r.methods))
print(\"-----------------------\")
"

