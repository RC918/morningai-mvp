import base64
import io

import qrcode
from flask import Blueprint, current_app, jsonify, request

from src.database import db
from src.decorators import token_required
from src.services.two_factor_service import get_two_factor_service
# from src.audit_log import audit_log, AuditActions

two_factor_bp = Blueprint("two_factor", __name__)


@two_factor_bp.route("/auth/2fa/setup", methods=["POST"])
@token_required
def setup_2fa(current_user):
    """設置 2FA - 生成密鑰和 QR 碼"""
    try:
        two_factor_service = get_two_factor_service()
        
        # 生成 2FA 密鑰
        if not current_user.two_factor_secret:
            secret = two_factor_service.generate_secret()
            current_user.two_factor_secret = secret
            db.session.commit()
        else:
            secret = current_user.two_factor_secret

        # 生成 QR 碼
        qr_code = two_factor_service.generate_qr_code(secret, current_user.username)
        
        # 生成 TOTP URI
        import pyotp
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=current_user.username,
            issuer_name="MorningAI"
        )

        return jsonify({
            "message": "2FA 設置成功",
            "secret": secret,
            "qr_code": qr_code,
            "uri": uri,
        }), 200

    except Exception as e:
        current_app.logger.error(f"2FA setup error: {str(e)}")
        return jsonify({"message": "2FA 設置失敗"}), 500


@two_factor_bp.route("/auth/2fa/enable", methods=["POST"])
@token_required
def enable_2fa(current_user):
    """啟用 2FA - 驗證 OTP 後啟用"""
    try:
        two_factor_service = get_two_factor_service()
        data = request.get_json()
        otp = data.get("otp")

        if not otp:
            return jsonify({"message": "請提供 OTP 驗證碼"}), 400

        if not current_user.two_factor_secret:
            return jsonify({"message": "請先設置 2FA"}), 400

        # 驗證 OTP
        if not two_factor_service.verify_otp(current_user.two_factor_secret, otp):
            return jsonify({"message": "OTP 驗證碼錯誤"}), 400

        # 啟用 2FA
        current_user.two_factor_enabled = True
        db.session.commit()

        return jsonify({"message": "2FA 已成功啟用", "two_factor_enabled": True}), 200

    except Exception as e:
        current_app.logger.error(f"2FA enable error: {str(e)}")
        return jsonify({"message": "2FA 啟用失敗"}), 500


@two_factor_bp.route("/auth/2fa/disable", methods=["POST"])
@token_required

def disable_2fa(current_user):
    """停用 2FA"""
    try:
        data = request.get_json()
        otp = data.get("otp")

        if not otp:
            return jsonify({"message": "請提供 OTP 驗證碼以停用 2FA"}), 400

        # 驗證 OTP
        if not current_user.verify_2fa_token(otp):
            return jsonify({"message": "OTP 驗證碼錯誤"}), 400

        # 停用 2FA
        current_user.disable_2fa()
        db.session.commit()

        return jsonify({"message": "2FA 已成功停用", "two_factor_enabled": False}), 200

    except Exception as e:
        current_app.logger.error(f"2FA disable error: {str(e)}")
        return jsonify({"message": "2FA 停用失敗"}), 500


@two_factor_bp.route("/auth/2fa/status", methods=["GET"])
@token_required
def get_2fa_status(current_user):
    """獲取 2FA 狀態"""
    return (
        jsonify(
            {
                "two_factor_enabled": current_user.two_factor_enabled,
                "has_secret": bool(current_user.two_factor_secret),
            }
        ),
        200,
    )



@two_factor_bp.route("/auth/2fa/backup-codes", methods=["GET"])
@token_required
def get_backup_codes(current_user):
    """獲取備份碼"""
    if not current_user.two_factor_enabled:
        return jsonify({"message": "2FA is not enabled"}), 400

    two_factor_service = get_two_factor_service()
    codes = two_factor_service.generate_backup_codes()
    hashed_codes = [two_factor_service.hash_backup_code(code) for code in codes]
    current_user.two_factor_backup_codes = ",".join(hashed_codes)
    db.session.commit()

    return jsonify({"backup_codes": codes}), 200
