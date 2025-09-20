# apps/api/src/routes/email_verification.py
from flask import Blueprint, current_app, jsonify, request
from itsdangerous import BadTimeSignature, SignatureExpired, URLSafeTimedSerializer

from src.decorators import token_required
from src.models.user import User, db
from src.services.email_service import send_email

# from src.audit_log import audit_log, AuditActions

email_verification_bp = Blueprint("email_verification", __name__)


def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(
        email, salt=current_app.config.get("SECURITY_PASSWORD_SALT", "email-confirm")
    )


def confirm_verification_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(
            token,
            salt=current_app.config.get("SECURITY_PASSWORD_SALT", "email-confirm"),
            max_age=expiration,
        )
        return email
    except SignatureExpired:
        raise SignatureExpired("Verification token expired")
    except BadTimeSignature:
        raise BadTimeSignature("Invalid verification token")


@email_verification_bp.route("/auth/send-verification", methods=["POST"])
@token_required
def send_verification_email(current_user):
    if current_user.is_email_verified:
        return jsonify({"message": "Email is already verified."}), 400

    token = generate_verification_token(current_user.email)

    # 發送驗證郵件
    verification_url = (
        f"https://morningai-mvp.onrender.com/api/auth/email/verify/{token}"
    )

    # 使用 EmailService 發送郵件
    success = send_email(current_user.email, verification_url)

    if not success:
        return jsonify({"message": "Failed to send verification email."}), 500

    return jsonify({"message": "Verification email sent."}), 200


@email_verification_bp.route("/auth/verify/<token>", methods=["GET"])
def verify_email(token):
    try:
        email = confirm_verification_token(token)
    except SignatureExpired:
        return jsonify({"message": "Verification token expired"}), 400
    except BadTimeSignature:
        return jsonify({"message": "Invalid verification token"}), 400
    except Exception:
        return jsonify({"message": "Invalid verification token"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found."}), 404

    if user.is_email_verified:
        return jsonify({"message": "Email is already verified."}), 400

    user.is_email_verified = True
    db.session.commit()

    return jsonify({"message": "Email verified successfully."}), 200


@email_verification_bp.route("/auth/verify", methods=["GET"])
def verify_email_status():
    """檢查 Email 驗證狀態"""
    token = request.args.get("token")
    if not token:
        return jsonify({"message": "Missing verification token"}), 400

    email = confirm_verification_token(token)
    if not email:
        return (
            jsonify({"message": "The verification link is invalid or has expired."}),
            400,
        )

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found."}), 404

    if user.is_email_verified:
        return jsonify({"message": "Email is already verified."}), 400

    user.is_email_verified = True
    db.session.commit()

    return jsonify({"message": "Email verified successfully."}), 200


@email_verification_bp.route("/auth/email-status", methods=["GET"])
@token_required
def get_email_status(current_user):
    """獲取當前用戶的 Email 驗證狀態"""
    return (
        jsonify(
            {"email": current_user.email, "is_verified": current_user.is_email_verified}
        ),
        200,
    )
