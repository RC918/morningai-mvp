from functools import wraps

import jwt
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
                return jsonify({"error": "Missing authorization header"}), 401

            # 檢查 Bearer token 格式
            try:
                token_type, token = auth_header.split(" ")
                if token_type.lower() != "bearer":
                    return jsonify({"error": "Invalid authorization header format"}), 401
            except ValueError:
                return jsonify({"error": "Invalid authorization header format"}), 401

            try:
                # 解碼 JWT
                payload = jwt.decode(
                    token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
                )

                # 檢查 JWT 是否在黑名單中
                jti = payload.get("jti")
                if jti and JWTBlacklist.is_blacklisted(jti):
                    return jsonify({"error": "Token has been revoked"}), 401

                # 獲取用戶角色
                user_role = payload.get("role")
                user_id = payload.get("sub") or payload.get("user_id")
                if isinstance(user_id, str):
                    user_id = int(user_id)  # 轉換字符串為整數

                if not user_role or not user_id:
                    return jsonify({"error": "Invalid token payload"}), 401

                # 檢查角色權限
                if required_role == "admin" and user_role != "admin":
                    return jsonify({"error": "forbidden"}), 403

                # 將用戶信息添加到請求上下文
                request.current_user = User.query.get(user_id)
                if not request.current_user:
                    return jsonify({"error": "User not found"}), 401

                return f(request.current_user, *args, **kwargs)

            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token has expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401
            except Exception as e:
                current_app.logger.error(f"Role validation error: {str(e)}")
                return jsonify({"error": f"Token validation failed: {str(e)}"}), 401

        return decorated_function

    return decorator


def token_required(f):
    """
    JWT Token 驗證裝飾器（包含黑名單檢查）
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Missing authorization header"}), 401

        try:
            token_type, token = auth_header.split(" ")
            if token_type.lower() != "bearer":
                return jsonify({"error": "Invalid authorization header format"}), 401
        except ValueError:
            return jsonify({"error": "Invalid authorization header format"}), 401

        try:
            payload = jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])

            user_id = payload.get("sub") or payload.get("user_id")
            if isinstance(user_id, str):
                user_id = int(user_id)  # 轉換字符串為整數
            jti = payload.get("jti")

            if not user_id:
                return jsonify({"error": "Invalid token payload"}), 401

            # 檢查 JWT 是否在黑名單中
            print(f"[TOKEN_REQUIRED] Checking blacklist for JTI: {jti}")
            if jti and JWTBlacklist.is_blacklisted(jti):
                print(f"[TOKEN_REQUIRED] Token revoked: {jti}")
                return jsonify({"error": "Token has been revoked"}), 401
            elif not jti:
                print(f"[TOKEN_REQUIRED] Warning: Token has no JTI")
            else:
                print(f"[TOKEN_REQUIRED] Token is valid: {jti}")

            # 將用戶信息添加到請求上下文
            request.current_user = User.query.get(user_id)
            if not request.current_user:
                return jsonify({"error": "User not found"}), 401

            return f(request.current_user, *args, **kwargs)

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            current_app.logger.error(f"Token validation error: {str(e)}")
            return jsonify({"error": f"Token validation failed: {str(e)}"}), 401

    return decorated_function


def get_current_user():
    """
    獲取當前登錄用戶信息

    Returns:
        User: 用戶對象
    """
    return getattr(request, "current_user", None)
