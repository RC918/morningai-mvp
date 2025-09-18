#!/bin/bash

# 進入 apps/api 目錄
cd /opt/render/project/src/apps/api

# 設置 PYTHONPATH，確保 Python 能夠找到 src 包
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "Current working directory: $(pwd)"
echo "PYTHONPATH: $PYTHONPATH"

# 刪除舊的資料庫文件（如果存在）
rm -f src/database/app.db

# 創建資料庫目錄
mkdir -p src/database

# 執行資料庫初始化
python3.11 -c "import sys; import os; sys.path.insert(0, os.getcwd()); from src.database import Base, engine; Base.metadata.create_all(engine)"

# 檢查資料庫初始化是否成功
if [ $? -eq 0 ]; then
  echo "資料庫初始化成功"
else
  echo "資料庫初始化失敗"
  exit 1
fi


