# apps/api/src/routes/email_verification.py
from flask import Blueprint, request, jsonify, current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from src.models.user import User, db
from src.decorators import token_required
# from src.audit_log import audit_log, AuditActions

email_verification_bp = Blueprint("email_verification", __name__)


def send_email(to_email, subject, body):
    """發送郵件的函數（可被測試 mock）"""
    # 這是一個佔位符函數，實際應用中會使用 Flask-Mail 發送郵件
    print(f"Sending email to {to_email}: {subject}")
    print(f"Body: {body}")
    return True


def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt=current_app.config["SECURITY_PASSWORD_SALT"])


def confirm_verification_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(
            token, salt=current_app.config["SECURITY_PASSWORD_SALT"], max_age=expiration
        )
        return email
    except SignatureExpired:
        # Token 已過期
        return None
    except BadTimeSignature:
        # Token 無效
        return None


@email_verification_bp.route("/auth/email/send-verification", methods=['POST'])
@token_required
def send_verification_email(current_user):
    if current_user.is_email_verified:
        return jsonify({"message": "Email is already verified."}), 400

    token = generate_verification_token(current_user.email)
    
    # 發送驗證郵件
    verification_url = f"https://morningai-mvp.onrender.com/api/auth/verify?token={token}"
    subject = "Email Verification - MorningAI"
    body = f"Please click the following link to verify your email: {verification_url}"
    
    send_email(current_user.email, subject, body)
    
    return jsonify({"message": "Verification email sent."}), 200


@email_verification_bp.route("/auth/email/verify/<token>", methods=['GET'])
def verify_email(token):
    email = confirm_verification_token(token)
    if not email:
        return jsonify({"message": "The verification link is invalid or has expired."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found."}), 404

    if user.is_email_verified:
        return jsonify({"message": "Email is already verified."}), 400

    user.is_email_verified = True
    db.session.commit()

    return jsonify({"message": "Email verified successfully."}), 200


@email_verification_bp.route("/auth/verify", methods=['GET'])
def verify_email_status():
    """檢查 Email 驗證狀態"""
    token = request.args.get('token')
    if not token:
        return jsonify({"message": "Missing verification token"}), 400
    
    email = confirm_verification_token(token)
    if not email:
        return jsonify({"message": "The verification link is invalid or has expired."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found."}), 404

    if user.is_email_verified:
        return jsonify({"message": "Email is already verified."}), 400

    user.is_email_verified = True
    db.session.commit()

    return jsonify({"message": "Email verified successfully."}), 200


@email_verification_bp.route("/auth/email-status", methods=['GET'])
@token_required
def get_email_status(current_user):
    """獲取當前用戶的 Email 驗證狀態"""
    return jsonify({
        "email": current_user.email,
        "is_verified": current_user.is_email_verified
    }), 200

