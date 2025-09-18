#!/bin/bash

# 導航到 apps/api 目錄
cd /opt/render/project/src/apps/api

# 設置 PYTHONPATH 以確保 Python 能夠找到應用模塊
export PYTHONPATH=$PYTHONPATH:/opt/render/project/src/apps/api

# 打印 PYTHONPATH 以供調試
echo "PYTHONPATH: $PYTHONPATH"

# 打印當前工作目錄和 Python 版本
echo "Current working directory: $(pwd)"
echo "Python version: $(python3 --version)"

# 安裝 API 作為可編輯包
pip install -e .

# 執行資料庫初始化和管理員用戶創建
# 這裡我們直接調用 main.py 中的邏輯來初始化資料庫和創建管理員用戶
python3 -c "from src.main import app, db, User; with app.app_context(): db.create_all(); admin_user = User.query.filter_by(email=\'admin@morningai.com\').first(); print(f\"Admin user check: {admin_user}\"); if not admin_user: admin_user = User(email=\'admin@morningai.com\', role=\'admin\', is_email_verified=True); admin_user.set_password(\'admin123\'); db.session.add(admin_user); db.session.commit(); print(\'Default admin user created: admin@morningai.com/admin123\')"

echo "Pre-deploy script finished successfully."


