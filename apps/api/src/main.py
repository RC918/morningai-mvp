import os
import sys

# 確保 Python 能夠找到 src 包
# 將 apps/api 的父目錄添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print(f"DEBUG: sys.path at startup: {sys.path}") # 添加這行來打印 sys.path

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db, User
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.admin import admin_bp # 導入 admin_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')

# 啟用 CORS
CORS(app, origins="*")

# 註冊藍圖
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin') # 註冊 admin_bp

# 資料庫配置
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# 在應用啟動時初始化資料庫和創建默認管理員用戶
with app.app_context():
    db.create_all()
    
    # 檢查是否已存在管理員用戶
    admin_user = User.query.filter_by(email='admin@morningai.com').first()
    if not admin_user:
        # 創建默認管理員用戶
        admin_user = User(
            email='admin@morningai.com',
            role='admin',
            is_email_verified=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        print("默認管理員用戶已創建: admin@morningai.com/admin123")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404
            

@app.route('/health')
def health_check():
    return {"ok": True}, 200
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


