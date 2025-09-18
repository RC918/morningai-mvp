import os

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

# 導入 JWT 相關庫
import jwt
from datetime import datetime, timedelta

from flask_cors import CORS

# 導入資料庫和模型
from src.database import db
from src.models.user import User
from src.models.jwt_blacklist import JWTBlacklist
from src.decorators import require_role

# 導入路由
from src.routes.auth import auth_bp
from src.routes.admin import admin_bp
from src.routes.two_factor import two_factor_bp
from src.routes.jwt_blacklist import jwt_blacklist_bp

app = Flask(__name__)
CORS(app)

# 配置資料庫
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 配置 JWT
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "super-secret")  # 替換為您的秘密金鑰
app.config["JWT_ACCESS_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

db.init_app(app)

# 配置和初始化 APScheduler
app.config["SCHEDULER_API_ENABLED"] = True
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# 添加定時任務：每小時清理一次過期的 JWT 黑名單
@scheduler.task("interval", id="cleanup_jwt_blacklist", hours=1, misfire_grace_time=900)
def cleanup_jwt_blacklist_job():
    with app.app_context():
        from src.models.jwt_blacklist import JWTBlacklist
        cleaned_count = JWTBlacklist.cleanup_expired_tokens()
        print(f"清理了 {cleaned_count} 個過期的 JWT 黑名單 token")

# 註冊藍圖
app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(admin_bp, url_prefix="/api/admin")
app.register_blueprint(two_factor_bp, url_prefix="/api")
app.register_blueprint(jwt_blacklist_bp, url_prefix="/api")

@app.route("/")
def home():
    return jsonify(message="Welcome to MorningAI MVP API!")

@app.route("/health")
def health_check():
    return jsonify(status="ok", message="API is healthy")

# 在應用上下文中創建資料庫表和管理員用戶
with app.app_context():
    db.create_all()
    # 檢查並創建默認管理員用戶
    admin_user = User.query.filter_by(email="admin@morningai.com").first()
    if not admin_user:
        # 也檢查是否已經有 username='admin' 的用戶
        existing_admin = User.query.filter_by(username="admin").first()
        if not existing_admin:
            admin_user = User(
                username="admin", 
                email="admin@morningai.com", 
                role="admin", 
                is_active=True,
                is_email_verified=True
            )
            admin_user.set_password("admin123")
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created: admin@morningai.com/admin123")
        else:
            print("Admin user already exists with username 'admin'")
    else:
        print("Admin user already exists with email 'admin@morningai.com'")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=os.environ.get("PORT", 5000))


