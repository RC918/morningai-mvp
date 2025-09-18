from flask import Blueprint, jsonify, request
from src.models.user import User, db
import jwt
import datetime
import os
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# JWT 配置
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-here')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

def token_required(f):
    """JWT 令牌驗證裝飾器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 從 Authorization header 獲取令牌
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'message': '令牌格式無效'}), 401
        
        if not token:
            return jsonify({'message': '缺少令牌'}), 401
        
        try:
            # 解碼令牌
            data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            current_user = User.query.filter_by(id=data['user_id']).first()
            
            if not current_user or not current_user.is_active:
                return jsonify({'message': '用戶不存在或已被禁用'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': '令牌已過期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': '令牌無效'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def admin_required(f):
    """管理員權限驗證裝飾器"""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if not current_user.is_admin():
            return jsonify({'message': '需要管理員權限'}), 403
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    """用戶註冊"""
    try:
        data = request.get_json()
        
        # 驗證必要字段
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'缺少必要字段: {field}'}), 400
        
        username = data['username']
        email = data['email']
        password = data['password']
        role = data.get('role', 'user')  # 默認為普通用戶
        
        # 檢查用戶名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({'message': '用戶名已存在'}), 409
        
        # 檢查郵箱是否已存在
        if User.query.filter_by(email=email).first():
            return jsonify({'message': '郵箱已存在'}), 409
        
        # 驗證角色
        if role not in ['user', 'admin']:
            return jsonify({'message': '無效的角色'}), 400
        
        # 創建新用戶
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': '用戶註冊成功',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'註冊失敗: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用戶登錄"""
    try:
        data = request.get_json()
        print(f"DEBUG: Login request data: {data}") # 調試打印
        
        email = data.get('email') # 改為 email
        password = data.get('password')
        print(f"DEBUG: Email: {email}, Password: {password}") # 調試打印
        
        if not email or not password:
            return jsonify({'message': '郵箱和密碼不能為空'}), 400 # 錯誤信息也改為郵箱
        
        # 查找用戶
        user = User.query.filter_by(email=email).first() # 改為 email 查找
        
        if not user or not user.check_password(password):
            return jsonify({'message': '郵箱或密碼錯誤'}), 401 # 錯誤信息也改為郵箱
        
        if not user.is_active:
            return jsonify({'message': '帳戶已被禁用'}), 401
        
        # 生成 JWT 令牌
        payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return jsonify({
            'message': '登錄成功',
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'登錄失敗: {str(e)}'}), 500

@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    """驗證令牌有效性"""
    return jsonify({
        'message': '令牌有效',
        'user': current_user.to_dict()
    }), 200

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """獲取用戶資料"""
    return jsonify({
        'user': current_user.to_dict()
    }), 200

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """更新用戶資料"""
    try:
        data = request.get_json()
        
        # 更新允許的字段
        if 'email' in data:
            # 檢查新郵箱是否已被其他用戶使用
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != current_user.id:
                return jsonify({'message': '郵箱已被其他用戶使用'}), 409
            current_user.email = data['email']
            current_user.is_email_verified = False  # 需要重新驗證郵箱
        
        if 'password' in data:
            current_user.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'message': '資料更新成功',
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'更新失敗: {str(e)}'}), 500

@auth_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_all_users(current_user):
    """獲取所有用戶（僅管理員）"""
    try:
        users = User.query.all()
        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200
    except Exception as e:
        return jsonify({'message': f'獲取用戶列表失敗: {str(e)}'}), 500

@auth_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@token_required
@admin_required
def update_user_role(current_user, user_id):
    """更新用戶角色（僅管理員）"""
    try:
        data = request.get_json()
        new_role = data.get('role')
        
        if new_role not in ['user', 'admin']:
            return jsonify({'message': '無效的角色'}), 400
        
        user = User.query.get_or_404(user_id)
        
        # 防止管理員移除自己的管理員權限
        if user.id == current_user.id and new_role != 'admin':
            return jsonify({'message': '不能移除自己的管理員權限'}), 400
        
        user.role = new_role
        db.session.commit()
        
        return jsonify({
            'message': '角色更新成功',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'角色更新失敗: {str(e)}'}), 500

@auth_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@token_required
@admin_required
def update_user_status(current_user, user_id):
    """更新用戶狀態（僅管理員）"""
    try:
        data = request.get_json()
        is_active = data.get('is_active')
        
        if is_active is None:
            return jsonify({'message': '缺少 is_active 字段'}), 400
        
        user = User.query.get_or_404(user_id)
        
        # 防止管理員禁用自己
        if user.id == current_user.id and not is_active:
            return jsonify({'message': '不能禁用自己的帳戶'}), 400
        
        user.is_active = is_active
        db.session.commit()
        
        return jsonify({
            'message': '用戶狀態更新成功',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'狀態更新失敗: {str(e)}'}), 500





