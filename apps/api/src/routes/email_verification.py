# apps/api/src/routes/email_verification.py
from flask import Blueprint, request, jsonify, current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from src.models.user import User, db
from src.decorators import token_required
from src.audit_log import audit_log, AuditActions

email_verification_bp = Blueprint("email_verification", __name__)


def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt=current_app.config["SECURITY_PASSWORD_SALT"])


def confirm_verification_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(
            token, salt=current_app.config["SECURITY_PASSWORD_SALT"], max_age=expiration
        )
    except (SignatureExpired, BadTimeSignature):
        return None
    return email


@email_verification_bp.route("/auth/email/send-verification", methods=['POST'])
@token_required
@audit_log(action=AuditActions.EMAIL_VERIFICATION_SENT, resource_type="user")
def send_verification_email(current_user):
    if current_user.is_email_verified:
        return jsonify({"message": "Email is already verified."}), 400

    token = generate_verification_token(current_user.email)
    # This is a placeholder for sending the email. In a real application, you would use a library like Flask-Mail to send the email.
    print(f"Verification token for {current_user.email}: {token}")

    return jsonify({"message": "Verification email sent."}), 200


@email_verification_bp.route("/auth/email/verify/<token>", methods=['GET'])
@audit_log(action=AuditActions.EMAIL_VERIFIED, resource_type="user")
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

