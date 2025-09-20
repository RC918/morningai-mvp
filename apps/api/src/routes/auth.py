import datetime
import os
from functools import wraps

import jwt
from flask import Blueprint, current_app, jsonify, request

from src.audit_log import AuditActions, audit_log
from src.decorators import token_required
from src.models.audit_log import AuditLog
from src.models.user import User, db

auth_bp = Blueprint("auth", __name__)
# JWT 配置
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def admin_required(f):
    """管理員權限驗證裝飾器"""

    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if not current_user.is_admin():
            return jsonify({"error": "forbidden"}), 403
        return f(current_user, *args, **kwargs)

    return decorated


@auth_bp.route("/register", methods=["POST"])
@audit_log(action=AuditActions.REGISTER, resource_type="user")
def register():
    """用戶註冊"""
    try:
        data = request.get_json()

        # 驗證必要字段
        required_fields = ["username", "email", "password"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"message": f"缺少必要字段: {field}"}), 400

        username = data["username"]
        email = data["email"]
        password = data["password"]
        role = data.get("role", "user")  # 默認為普通用戶

        # 檢查用戶名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({"message": "用戶名已存在"}), 409

        # 檢查郵箱是否已存在
        if User.query.filter_by(email=email).first():
            return jsonify({"message": "郵箱已存在"}), 409

        # 驗證角色
        if role not in ["user", "admin"]:
            return jsonify({"message": "無效的角色"}), 400

        # 創建新用戶
        user = User(username=username, email=email, role=role)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return jsonify({"message": "用戶註冊成功", "user": user.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"註冊失敗: {str(e)}"}), 500


@auth_bp.route("/login", methods=["POST"])
@audit_log(action=AuditActions.LOGIN, resource_type="user")
def login():
    """用戶登錄"""
    try:
        data = request.get_json()

        # 支持 email 或 username 登入
        email = data.get("email")
        username = data.get("username")
        password = data.get("password")
        otp = data.get("otp")  # 2FA OTP 驗證碼

        if not (email or username) or not password:
            return jsonify({"message": "郵箱/用戶名和密碼不能為空"}), 400

        # 查找用戶 - 優先使用 email，其次使用 username
        user = None
        if email:
            user = User.query.filter_by(email=email).first()
        elif username:
            user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            # 記錄登入失敗的審計日誌
            AuditLog.log_action(
                action=AuditActions.LOGIN_FAILED,
                user_id=user.id if user else None,
                ip_address=request.environ.get(
                    "HTTP_X_FORWARDED_FOR", request.remote_addr
                ),
                user_agent=request.headers.get("User-Agent", "")[:500],
                details={
                    "reason": "invalid_credentials",
                    "attempted_email": email,
                    "attempted_username": username,
                    "username": user.username if user else (email or username),
                },
                status="failed",
            )
            return jsonify({"message": "郵箱/用戶名或密碼錯誤"}), 401

        if not user.is_active:
            return jsonify({"message": "帳戶已被禁用"}), 401

        # 檢查 2FA
        if user.two_factor_enabled:
            if not otp:
                return (
                    jsonify(
                        {
                            "message": "此帳戶已啟用 2FA，請提供 OTP 驗證碼",
                            "requires_2fa": True,
                        }
                    ),
                    401,
                )

            if not user.verify_2fa_token(otp):
                return jsonify({"message": "OTP 驗證碼錯誤"}), 401

        # 生成 JWT 令牌（包含 JTI）
        import uuid

        jti = str(uuid.uuid4())  # 生成唯一的 JWT ID

        payload = {
            "user_id": user.id,
            "sub": str(user.id),  # 標準的 subject 聲明（必須是字符串）
            "username": user.username,
            "role": user.role,
            "jti": jti,  # JWT ID，用於黑名單管理
            "iat": datetime.datetime.utcnow(),
            "exp": datetime.datetime.utcnow()
            + datetime.timedelta(hours=JWT_EXPIRATION_HOURS),
        }

        token = jwt.encode(
            payload, current_app.config["JWT_SECRET_KEY"], algorithm=JWT_ALGORITHM
        )

        # 記錄成功登入的審計日誌
        response_data = {"message": "登錄成功", "token": token, "user": user.to_dict()}
        AuditLog.log_action(
            action=AuditActions.LOGIN,
            user_id=user.id,
            ip_address=request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr),
            user_agent=request.headers.get("User-Agent", "")[:500],
            details={
                "request_json": data,
                "request_args": dict(request.args),
                "response_data": response_data,
                "status_code": 200,
                "username": user.username,
            },
        )

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"message": f"登錄失敗: {str(e)}"}), 500


@auth_bp.route("/verify", methods=["GET"])
@token_required
def verify_token(current_user):
    """驗證令牌有效性"""
    return jsonify({"message": "令牌有效", "user": current_user.to_dict()}), 200


@auth_bp.route("/profile", methods=["GET"])
@token_required
def get_profile(current_user):
    """獲取用戶資料"""
    return jsonify({"user": current_user.to_dict()}), 200


@auth_bp.route("/profile", methods=["PUT"])
@token_required
@audit_log(action=AuditActions.USER_UPDATED, resource_type="user")
def update_profile(current_user):
    """更新用戶資料"""
    try:
        data = request.get_json()

        # 更新允許的字段
        if "email" in data:
            # 檢查新郵箱是否已被其他用戶使用
            existing_user = User.query.filter_by(email=data["email"]).first()
            if existing_user and existing_user.id != current_user.id:
                return jsonify({"message": "郵箱已被其他用戶使用"}), 409
            current_user.email = data["email"]
            current_user.is_email_verified = False  # 需要重新驗證郵箱

        if "password" in data:
            current_user.set_password(data["password"])

        db.session.commit()

        return jsonify({"message": "資料更新成功", "user": current_user.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"更新失敗: {str(e)}"}), 500


@auth_bp.route("/users/<int:user_id>/status", methods=["PUT"])
@token_required
@admin_required
@audit_log(action=AuditActions.USER_STATUS_CHANGED, resource_type="user")
def update_user_status(current_user, user_id):
    """更新用戶狀態（僅管理員）"""
    try:
        data = request.get_json()
        is_active = data.get("is_active")

        if is_active is None:
            return jsonify({"message": "缺少 is_active 字段"}), 400

        user = User.query.get_or_404(user_id)

        # 防止管理員禁用自己
        if user.id == current_user.id and not is_active:
            return jsonify({"message": "不能禁用自己的帳戶"}), 400

        user.is_active = is_active
        db.session.commit()

        return jsonify({"message": "用戶狀態更新成功", "user": user.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"狀態更新失敗: {str(e)}"}), 500
