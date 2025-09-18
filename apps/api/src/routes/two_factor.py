import base64
import io

import qrcode
from flask import Blueprint, current_app, jsonify, request

from src.database import db
from src.decorators import token_required

two_factor_bp = Blueprint("two_factor", __name__)


@two_factor_bp.route("/auth/2fa/setup", methods=["POST"])
@token_required
def setup_2fa(current_user):
    """設置 2FA - 生成密鑰和 QR 碼"""
    try:
        # 生成 2FA 密鑰
        secret = current_user.generate_2fa_secret()

        # 獲取 TOTP URI
        uri = current_user.get_2fa_uri()

        # 生成 QR 碼
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)

        # 將 QR 碼轉換為 base64 圖片
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

        # 保存到資料庫
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "2FA 設置成功",
                    "secret": secret,
                    "qr_code": f"data:image/png;base64,{qr_code_base64}",
                    "uri": uri,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"2FA setup error: {str(e)}")
        return jsonify({"message": "2FA 設置失敗"}), 500


@two_factor_bp.route("/auth/2fa/enable", methods=["POST"])
@token_required
def enable_2fa(current_user):
    """啟用 2FA - 驗證 OTP 後啟用"""
    try:
        data = request.get_json()
        otp = data.get("otp")

        if not otp:
            return jsonify({"message": "請提供 OTP 驗證碼"}), 400

        # 驗證 OTP
        if not current_user.verify_2fa_token(otp):
            return jsonify({"message": "OTP 驗證碼錯誤"}), 400

        # 啟用 2FA
        current_user.enable_2fa()
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
