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
from src.routes.two_factor import two_factor_bp

app = Flask(__name__)
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "https://morningai-mvp.vercel.app,https://morningai-an9nof.manus.space").split(",")
CORS(app, origins=CORS_ORIGINS, supports_credentials=True)

@app.before_request
def handle_options_request():
    if request.method == "OPTIONS":
        return '', 200

# 配置資料庫
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 配置 JWT
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "super-secret")  # 替換為您的秘密金鑰
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

jwt = JWTManager(app)

db.init_app(app)

# 註冊藍圖
app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(admin_bp, url_prefix="/api/admin")
app.register_blueprint(two_factor_bp, url_prefix="/api")

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
        # 也檢查是否已經有 username=\'admin\' 的用戶
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
            print("Admin user already exists with username \'admin\'")
    else:
        print("Admin user already exists with email \'admin@morningai.com\'")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=os.environ.get("PORT", 5000))


