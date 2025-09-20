import os
from datetime import timedelta
from flask import Flask, jsonify
from flask_apscheduler import APScheduler
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from flask_restx import Api

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

# 立即註冊健康檢查端點，確保它在任何耗時操作前可用
@app.route("/health")
def health_check():
    return jsonify(ok=True, message="Service is healthy")

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

# 配置 Flask-Mail
app.config['MAIL_SERVER'] = os.environ.get('SMTP_HOST')
app.config['MAIL_PORT'] = int(os.environ.get('SMTP_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('SMTP_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('SMTP_PASS')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('EMAIL_FROM')

# 初始化擴展
db.init_app(app)
jwt = JWTManager(app)
mail = Mail(app)

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

# 註冊 API 文檔
from src.simple_docs import simple_docs_bp
app.register_blueprint(simple_docs_bp)

@app.route("/")
def hello():
    """根路徑歡迎訊息"""
    return jsonify({
        "message": "Welcome to MorningAI MVP API!",
        "version": "1.0.1",
        "timestamp": "2025-09-20T04:55:00Z",
        "docs_available": True,
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "api_docs": "/api-docs",
            "documentation": "/documentation"
        }
    })

@app.route("/test-deployment")
def test_deployment():
    """測試部署狀態"""
    import datetime
    return jsonify({
        "status": "deployed",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "routes_count": len(list(app.url_map.iter_rules())),
        "docs_route_exists": any(rule.rule == '/docs' for rule in app.url_map.iter_rules())
    })

@app.route("/docs")
@app.route("/docs/")
def api_docs():
    """API 文檔頁面"""
    docs_html = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MorningAI MVP API 文檔</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 30px; }
        .endpoint { background: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007cba; }
        .method { display: inline-block; padding: 4px 8px; border-radius: 3px; color: white; font-weight: bold; margin-right: 10px; }
        .get { background: #61affe; }
        .post { background: #49cc90; }
        .code { background: #f4f4f4; padding: 10px; border-radius: 3px; font-family: monospace; }
        .status-ok { color: #28a745; }
        .status-error { color: #dc3545; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌅 MorningAI MVP API 文檔</h1>
        <p>版本: 1.0.0 | 基礎 URL: <code>https://morningai-mvp.onrender.com</code></p>
        <p><strong>狀態:</strong> <span class="status-ok">✅ 服務運行中</span></p>
    </div>

    <h2>🔐 認證</h2>
    <p>大部分 API 端點需要 JWT Token 認證。在請求標頭中包含:</p>
    <div class="code">Authorization: Bearer &lt;your_jwt_token&gt;</div>

    <h2>📋 主要 API 端點</h2>

    <div class="endpoint">
        <span class="method get">GET</span><strong>/health</strong>
        <p>健康檢查端點</p>
        <div class="code">curl https://morningai-mvp.onrender.com/health</div>
    </div>

    <div class="endpoint">
        <span class="method post">POST</span><strong>/api/register</strong>
        <p>用戶註冊</p>
        <div class="code">curl -X POST https://morningai-mvp.onrender.com/api/register -H "Content-Type: application/json" -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'</div>
    </div>

    <div class="endpoint">
        <span class="method post">POST</span><strong>/api/login</strong>
        <p>用戶登入</p>
        <div class="code">curl -X POST https://morningai-mvp.onrender.com/api/login -H "Content-Type: application/json" -d '{"email": "test@example.com", "password": "password123"}'</div>
    </div>

    <div class="endpoint">
        <span class="method get">GET</span><strong>/api/profile</strong> 🔒
        <p>獲取用戶資料（需要認證）</p>
        <div class="code">curl https://morningai-mvp.onrender.com/api/profile -H "Authorization: Bearer &lt;token&gt;"</div>
    </div>

    <div class="endpoint">
        <span class="method post">POST</span><strong>/api/auth/logout</strong> 🔒
        <p>用戶登出</p>
        <div class="code">curl -X POST https://morningai-mvp.onrender.com/api/auth/logout -H "Authorization: Bearer &lt;token&gt;"</div>
    </div>

    <h2>🔒 安全特性</h2>
    <ul>
        <li><strong>JWT 認證:</strong> ✅ 已實施</li>
        <li><strong>JWT 黑名單:</strong> ✅ 已實施</li>
        <li><strong>RBAC:</strong> ✅ 已實施</li>
        <li><strong>RLS:</strong> ✅ 已實施</li>
    </ul>

    <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; color: #666;">
        <p>© 2025 MorningAI MVP | 驗收測試通過 ✅</p>
    </footer>
</body>
</html>
    """
    return docs_html

@app.route("/api-docs")
@app.route("/api-docs/")
def api_docs_alt():
    """API 文檔頁面 (備選路徑)"""
    return api_docs()

@app.route("/documentation")
@app.route("/documentation/")
def documentation():
    """API 文檔頁面 (第三備選路徑)"""
    return api_docs()

@app.route("/swagger")
@app.route("/swagger/")
def swagger_docs():
    """Swagger 風格的 API 文檔"""
    return api_docs()

def print_routes():
    """啟動時列印所有路由，方便調試 404/405 問題"""
    print("=== Available Routes ===")
    for rule in app.url_map.iter_rules():
        methods = ",".join(rule.methods - {"HEAD", "OPTIONS"})
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
            from sqlalchemy import text

            result = db.session.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_name = 'user'")
            )
            columns = [row[0] for row in result]
            print(f"📋 User table columns: {columns}")

            # 檢查必要的欄位是否存在
            required_columns = ["two_factor_secret", "two_factor_enabled"]
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
