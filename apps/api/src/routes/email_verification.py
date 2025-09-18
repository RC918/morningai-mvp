from flask import Blueprint, jsonify, request, url_for, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from src.database import db
from src.models.user import User
from datetime import datetime, timedelta
import os

email_verification_bp = Blueprint("email_verification", __name__)

# 初始化 URLSafeTimedSerializer
# 確保在應用上下文中初始化，因為它需要 SECRET_KEY
def get_serializer():
    # 使用 JWT_SECRET_KEY 作為其 SECRET_KEY
    return URLSafeTimedSerializer(current_app.config["JWT_SECRET_KEY"])

# 郵件發送函數 (簡化版，實際應使用郵件服務)
def send_verification_email(user_email, verification_link):
    print(f"Sending verification email to {user_email} with link: {verification_link}")
    # 實際應用中，這裡會調用郵件服務 API
    # 例如：
    # from flask_mail import Message, Mail
    # mail = Mail(current_app)
    # msg = Message("Verify Your Email Address", sender="noreply@morningai.com", recipients=[user_email])
    # msg.body = f"Please click the link to verify your email: {verification_link}"
    # mail.send(msg)

@email_verification_bp.route("/auth/send-verification", methods=["POST"])
@jwt_required()
def send_verification():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify(message="User not found"), 404

    if user.is_email_verified:
        return jsonify(message="Email already verified"), 200

    # 生成驗證 token
    serializer = get_serializer()
    # 使用 WEB_URL 作為基礎 URL
    web_url = os.environ.get("WEB_URL", "http://localhost:3000") # 替換為您的前端 URL
    token = serializer.dumps(user.email, salt="email-verification")
    verification_link = f"{web_url}/verify-email?token={token}"

    send_verification_email(user.email, verification_link)

    return jsonify(message="Verification email sent"), 200

@email_verification_bp.route("/auth/verify", methods=["GET"])
def verify_email():
    token = request.args.get("token")

    if not token:
        return jsonify(message="Missing verification token"), 400

    try:
        serializer = get_serializer()
        email = serializer.loads(token, salt="email-verification", max_age=3600) # Token 有效期 1 小時
    except SignatureExpired:
        return jsonify(message="Verification token expired"), 400
    except BadTimeSignature:
        return jsonify(message="Invalid verification token"), 400
    except Exception as e:
        return jsonify(message=f"Verification failed: {str(e)}"), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify(message="User not found"), 404

    if user.is_email_verified:
        return jsonify(message="Email already verified"), 200

    user.is_email_verified = True
    user.email_verified_at = datetime.utcnow()
    db.session.commit()

    return jsonify(message="Email verified successfully"), 200


