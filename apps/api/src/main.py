import os

# 導入 JWT 相關庫
from datetime import timedelta

from flask import Flask, jsonify

# 導入 APScheduler
from flask_apscheduler import APScheduler
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# 導入資料庫和模型
from src.database import db
from src.models.user import User
from src.routes.admin import admin_bp

# 導入路由
from src.routes.auth import auth_bp
from src.routes.jwt_blacklist import jwt_blacklist_bp
from src.routes.two_factor import two_factor_bp
from src.routes.email_verification import email_verification_bp
from src.routes.tenant import tenant_bp
from src.routes.webhook import webhook_bp

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",
    "http://localhost:5173", 
    "https://morningai-mvp-web.vercel.app",
    "https://morningai-mvp-*.vercel.app"
], allow_headers=["Content-Type", "Authorization"], allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# 配置資料庫
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 配置 JWT
app.config["JWT_SECRET_KEY"] = os.environ.get(
    "JWT_SECRET_KEY", "super-secret"
)  # 替換為您的秘密金鑰
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_HEADER_NAME"] = "Authorization"
app.config["JWT_HEADER_TYPE"] = "Bearer"

db.init_app(app)
jwt = JWTManager(app)

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
app.register_blueprint(email_verification_bp, url_prefix="/api")
app.register_blueprint(tenant_bp, url_prefix="/api")
app.register_blueprint(webhook_bp, url_prefix="/api")


@app.route("/")
def home():
    return jsonify(message="Welcome to MorningAI MVP API!")


@app.route("/health")
def health_check():
    import subprocess
    try:
        # 獲取 git commit hash
        git_sha = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], 
                                        cwd='/opt/render/project/src', 
                                        stderr=subprocess.DEVNULL).decode().strip()
    except:
        git_sha = "unknown"
    
    return jsonify(ok=True, version=git_sha)


# 添加路由列印功能（用於調試）
def print_routes():
    """啟動時列印所有路由，方便調試 404/405 問題"""
    print("=== Available Routes ===")
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
        print(f"{rule.endpoint:30s} {methods:20s} {rule.rule}")
    print("========================")


# 在應用上下文中安全地初始化資料庫表和管理員用戶
with app.app_context():
    try:
        # 執行資料庫遷移，確保所有表格和欄位都存在
        print("🔄 Running database migrations...")
        from src.database_migration import run_all_migrations
        migration_results = run_all_migrations()
        print(f"✅ Database migrations completed: {migration_results}")
        
        # 檢查遷移是否失敗，如果失敗則使用 create_all 作為後備
        if any("FAILED" in str(result) for result in migration_results):
            print("⚠️ Some migrations failed, attempting fallback with db.create_all()...")
            db.create_all()
            print("✅ Fallback database creation completed")
        
        # 驗證表格結構是否正確
        print("🔍 Verifying database schema...")
        try:
            # 嘗試查詢用戶表的所有欄位
            result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'user'"))
            columns = [row[0] for row in result]
            print(f"📋 User table columns: {columns}")
            
            # 檢查必要的欄位是否存在
            required_columns = ['two_factor_secret', 'two_factor_enabled']
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                print(f"❌ Missing columns: {missing_columns}")
                # 強制重新創建表格
                print("🔄 Recreating tables with correct schema...")
                db.drop_all()
                db.create_all()
                print("✅ Tables recreated successfully")
            else:
                print("✅ All required columns present")
                
        except Exception as schema_error:
            print(f"⚠️ Schema verification failed: {schema_error}")
            print("🔄 Attempting full table recreation...")
            try:
                db.drop_all()
                db.create_all()
                print("✅ Full table recreation completed")
            except Exception as recreation_error:
                print(f"❌ Table recreation failed: {recreation_error}")
            
        # 檢查並創建默認管理員用戶
        try:
            admin_user = User.query.filter_by(email="admin@morningai.com").first()
        except Exception as query_error:
            print(f"❌ User query failed: {query_error}")
            print("🔄 Attempting to recreate tables one more time...")
            db.drop_all()
            db.create_all()
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
                    is_email_verified=True,
                )
                admin_user.set_password("admin123")
                db.session.add(admin_user)
                db.session.commit()
                print("Default admin user created: admin@morningai.com/admin123")
            else:
                print("Admin user already exists with username 'admin'")
        else:
            print("Admin user already exists with email 'admin@morningai.com'")
            
    except Exception as e:
        print(f"Database initialization error: {e}")
        # 如果資料庫初始化失敗，嘗試繼續運行（可能表格已存在）


# 在應用啟動時列印路由（用於調試）
print_routes()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)


# 配置 Flask-Mail
app.config['MAIL_SERVER'] = os.environ.get('SMTP_HOST')
app.config['MAIL_PORT'] = int(os.environ.get('SMTP_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('SMTP_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('SMTP_PASS')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('EMAIL_FROM')

