from functools import wraps
from flask import request, jsonify, current_app
import jwt
from models.user import User

def require_role(required_role):
    """
    權限檢查裝飾器
    
    Args:
        required_role (str): 需要的角色 ('admin' 或 'user')
    
    Returns:
        decorator: 裝飾器函數
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 獲取 Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'error': 'Missing authorization header'}), 401
            
            # 檢查 Bearer token 格式
            try:
                token_type, token = auth_header.split(' ')
                if token_type.lower() != 'bearer':
                    return jsonify({'error': 'Invalid authorization header format'}), 401
            except ValueError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
            
            try:
                # 解碼 JWT
                payload = jwt.decode(
                    token, 
                    current_app.config['JWT_SECRET_KEY'], 
                    algorithms=['HS256']
                )
                
                # 獲取用戶角色
                user_role = payload.get('role')
                user_id = payload.get('sub')
                
                if not user_role or not user_id:
                    return jsonify({'error': 'Invalid token payload'}), 401
                
                # 檢查角色權限
                if required_role == 'admin' and user_role != 'admin':
                    return jsonify({'error': 'forbidden'}), 403
                
                # 將用戶信息添加到請求上下文
                request.current_user = {
                    'id': user_id,
                    'role': user_role
                }
                
                return f(*args, **kwargs)
                
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401
            except Exception as e:
                return jsonify({'error': 'Token validation failed'}), 401
        
        return decorated_function
    return decorator

def get_current_user():
    """
    獲取當前登錄用戶信息
    
    Returns:
        dict: 用戶信息字典，包含 id 和 role
    """
    return getattr(request, 'current_user', None)

