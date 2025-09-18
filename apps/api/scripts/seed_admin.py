#!/usr/bin/env python3
"""
管理員種子腳本
用於創建默認管理員帳戶以解除 RBAC 驗收卡點
"""

import sys
import os

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask
from models.user import User, db

def create_admin_user():
    """創建默認管理員用戶"""
    
    # 創建 Flask 應用實例
    app = Flask(__name__)
    
    # 配置數據庫
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 
        'sqlite:///database/app.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化數據庫
    db.init_app(app)
    
    with app.app_context():
        try:
            # 創建所有表
            db.create_all()
            
            # 檢查管理員是否已存在
            admin_email = 'admin@example.com'
            existing_admin = User.query.filter_by(email=admin_email).first()
            
            if existing_admin:
                print(f"管理員用戶已存在: {admin_email}")
                print(f"角色: {existing_admin.role}")
                print(f"狀態: {'活躍' if existing_admin.is_active else '非活躍'}")
                return existing_admin
            
            # 創建新的管理員用戶
            admin_user = User(
                username='admin',  # 保持向後兼容
                email=admin_email,
                role='admin',
                is_active=True,
                is_email_verified=True
            )
            admin_user.set_password('admin123')
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("✅ 管理員用戶創建成功!")
            print(f"郵箱: {admin_user.email}")
            print(f"用戶名: {admin_user.username}")
            print(f"密碼: admin123")
            print(f"角色: {admin_user.role}")
            print(f"ID: {admin_user.id}")
            
            return admin_user
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 創建管理員用戶失敗: {str(e)}")
            raise e

def main():
    """主函數"""
    print("🚀 開始創建管理員種子數據...")
    
    try:
        admin_user = create_admin_user()
        print("\n📋 管理員帳戶信息:")
        print(f"   郵箱: {admin_user.email}")
        print(f"   用戶名: {admin_user.username}")
        print(f"   密碼: admin123")
        print(f"   角色: {admin_user.role}")
        print("\n🎯 可用於 RBAC 驗收測試")
        
    except Exception as e:
        print(f"\n💥 種子腳本執行失敗: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()

