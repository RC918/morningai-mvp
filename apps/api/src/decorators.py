"""
認證和授權裝飾器模組
"""

import jwt
from functools import wraps
from flask import current_app, jsonify, request

from src.models.jwt_blacklist import JWTBlacklist
from src.models.user import User


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
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return jsonify({"error": "token is missing"}), 401

            # 檢查 Bearer token 格式
            try:
                token_type, token = auth_header.split(" ")
                if token_type.lower() != "bearer":
                    return (
                        jsonify({"error": "token is missing"}),
                        401,
                    )
            except ValueError:
                return jsonify({"error": "token is missing"}), 401

            try:
                # 解碼 JWT
                payload = jwt.decode(
                    token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
                )

                # 檢查 JWT 是否在黑名單中
                jti = payload.get("jti")
                if jti and JWTBlacklist.is_blacklisted(jti):
                    return jsonify({"error": "token is invalid"}), 401

                # 檢查用戶是否存在
                user_id = payload.get("user_id")
                if not user_id:
                    return jsonify({"error": "token is invalid"}), 401

                user = User.query.get(user_id)
                if not user:
                    return jsonify({"error": "token is invalid"}), 401

                # 檢查用戶是否啟用
                if not user.is_active:
                    return jsonify({"error": "user is inactive"}), 401

                # 檢查權限
                if required_role == "admin" and user.role != "admin":
                    return jsonify({"error": "admin access required"}), 403

                # 將用戶資訊添加到 request 中
                request.current_user = user

                return f(*args, **kwargs)

            except jwt.ExpiredSignatureError:
                return jsonify({"error": "token is invalid"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "token is invalid"}), 401
            except Exception as e:
                return jsonify({"error": "token is invalid"}), 401

        return decorated_function

    return decorator


def token_required(f):
    """
    JWT Token 驗證裝飾器
    
    Args:
        f: 被裝飾的函數
        
    Returns:
        decorated_function: 裝飾後的函數
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 獲取 Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "token is missing"}), 401

        # 檢查 Bearer token 格式
        try:
            token_type, token = auth_header.split(" ")
            if token_type.lower() != "bearer":
                return jsonify({"error": "token is missing"}), 401
        except ValueError:
            return jsonify({"error": "token is missing"}), 401

        try:
            # 解碼 JWT
            payload = jwt.decode(
                token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
            )

            # 檢查 JWT 是否在黑名單中
            jti = payload.get("jti")
            if jti and JWTBlacklist.is_blacklisted(jti):
                return jsonify({"error": "token is invalid"}), 401

            # 檢查用戶是否存在
            user_id = payload.get("user_id")
            if not user_id:
                return jsonify({"error": "token is invalid"}), 401

            user = User.query.get(user_id)
            if not user:
                return jsonify({"error": "token is invalid"}), 401

            # 檢查用戶是否啟用
            if not user.is_active:
                return jsonify({"error": "user is inactive"}), 401

            # 將用戶資訊添加到 request 中
            request.current_user = user

            return f(*args, **kwargs)

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "token is invalid"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "token is invalid"}), 401
        except Exception as e:
            return jsonify({"error": "token is invalid"}), 401

    return decorated_function


def admin_required(f):
    """
    管理員權限裝飾器
    
    Args:
        f: 被裝飾的函數
        
    Returns:
        decorated_function: 裝飾後的函數
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 獲取 Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "token is missing"}), 401

        # 檢查 Bearer token 格式
        try:
            token_type, token = auth_header.split(" ")
            if token_type.lower() != "bearer":
                return jsonify({"error": "token is missing"}), 401
        except ValueError:
            return jsonify({"error": "token is missing"}), 401

        try:
            # 解碼 JWT
            payload = jwt.decode(
                token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
            )

            # 檢查 JWT 是否在黑名單中
            jti = payload.get("jti")
            if jti and JWTBlacklist.is_blacklisted(jti):
                return jsonify({"error": "token is invalid"}), 401

            # 檢查用戶是否存在
            user_id = payload.get("user_id")
            if not user_id:
                return jsonify({"error": "token is invalid"}), 401

            user = User.query.get(user_id)
            if not user:
                return jsonify({"error": "token is invalid"}), 401

            # 檢查用戶是否啟用
            if not user.is_active:
                return jsonify({"error": "user is inactive"}), 401

            # 檢查管理員權限
            if user.role != "admin":
                return jsonify({"error": "admin access required"}), 403

            # 將用戶資訊添加到 request 中
            request.current_user = user

            return f(*args, **kwargs)

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "token is invalid"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "token is invalid"}), 401
        except Exception as e:
            return jsonify({"error": "token is invalid"}), 401

    return decorated_function
