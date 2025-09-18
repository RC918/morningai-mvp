#!/bin/bash

# 進入 apps/api 目錄
cd /opt/render/project/src/apps/api

# 刪除舊的資料庫文件（如果存在）
rm -f src/database/app.db

# 創建資料庫目錄
mkdir -p src/database

echo "Pre-deploy script finished: Old database removed and directory created."


