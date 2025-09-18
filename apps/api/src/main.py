import os

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_cors import CORS
from datetime import timedelta

# 導入資料庫和模型
from src.database import db
from src.models.user import User
from src.decorators import require_role

# 導入路由
from src.routes.auth import auth_bp
from src.routes.admin import admin_bp

app = Flask(__name__)
CORS(app)

# 配置資料庫
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 配置 JWT
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "super-secret")  # 替換為您的秘密金鑰
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

jwt = JWTManager(app)

db.init_app(app)

# 註冊藍圖
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(admin_bp, url_prefix="/api/admin")

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
        admin_user = User(email="admin@morningai.com", role="admin", is_email_verified=True)
        admin_user.set_password("admin123")
        db.session.add(admin_user)
        db.session.commit()
        print("Default admin user created: admin@morningai.com/admin123")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=os.environ.get("PORT", 5000))


