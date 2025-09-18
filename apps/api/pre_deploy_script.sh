#!/bin/bash

# 導航到 apps/api 目錄
cd /opt/render/project/src/apps/api

# 打印當前工作目錄和 Python 版本
echo "Current working directory: $(pwd)"
echo "Python version: $(python3 --version)"

# 嘗試安裝依賴
pip install -r requirements.txt

echo "Pre-deploy script finished successfully."


