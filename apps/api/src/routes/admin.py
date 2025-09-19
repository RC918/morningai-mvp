from flask import Blueprint, jsonify, request

from src.models.jwt_blacklist import JWTBlacklist
from src.models.user import User, db
from src.routes.auth import admin_required, token_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/users", methods=["GET"])
@token_required
@admin_required
def get_all_users(current_user):
    """
    獲取所有用戶列表（僅管理員）

    Headers:
        Authorization: Bearer <admin_token>

    Returns:
        JSON: 用戶列表
    """
    try:
        users = User.query.all()
        return (
            jsonify({"users": [user.to_dict() for user in users], "total": len(users)}),
            200,
        )

    except Exception as e:
        return jsonify({"error": "Failed to get users", "details": str(e)}), 500


@admin_bp.route("/users/<int:user_id>", methods=["GET"])
@token_required
@admin_required
def get_user_by_id(current_user, user_id):
    """
    根據 ID 獲取用戶信息（僅管理員）

    Args:
        user_id (int): 用戶 ID

    Headers:
        Authorization: Bearer <admin_token>

    Returns:
        JSON: 用戶信息
    """
    try:
        user = User.query.get_or_404(user_id)

        return jsonify({"user": user.to_dict()}), 200

    except Exception as e:
        return jsonify({"error": "Failed to get user", "details": str(e)}), 500


@admin_bp.route("/users/<int:user_id>/role", methods=["PUT"])
@token_required
@admin_required
def update_user_role(current_user, user_id):
    """
    更新用戶角色（僅管理員）

    Args:
        user_id (int): 用戶 ID

    Request Body:
        {
            "role": "admin" | "user"
        }

    Headers:
        Authorization: Bearer <admin_token>

    Returns:
        JSON: 更新後的用戶信息
    """
    try:
        data = request.get_json()
        new_role = data.get("role")

        if new_role not in ["admin", "user"]:
            return jsonify({"error": 'Invalid role. Must be "admin" or "user"'}), 400

        user = User.query.get_or_404(user_id)

        user.role = new_role
        db.session.commit()

        return (
            jsonify({"message": "User role updated successfully", "user": user.to_dict()}),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update user role", "details": str(e)}), 500


@admin_bp.route("/users/<int:user_id>/status", methods=["PUT"])
@token_required
@admin_required
def update_user_status(current_user, user_id):
    """
    更新用戶狀態（僅管理員）

    Args:
        user_id (int): 用戶 ID

    Request Body:
        {
            "is_active": true | false
        }

    Headers:
        Authorization: Bearer <admin_token>

    Returns:
        JSON: 更新後的用戶信息
    """
    try:
        data = request.get_json()
        is_active = data.get("is_active")

        if is_active is None:
            return jsonify({"error": "is_active field is required"}), 400

        user = User.query.get_or_404(user_id)

        user.is_active = bool(is_active)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "User status updated successfully",
                    "user": user.to_dict(),
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"error": "Failed to update user status", "details": str(e)}),
            500,
        )


@admin_bp.route("/blacklist", methods=["GET"])
@token_required
@admin_required
def get_blacklist(current_user):
    """獲取黑名單列表（僅管理員）"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        # 清理過期的 token
        JWTBlacklist.cleanup_expired_tokens()

        # 分頁查詢
        blacklist = JWTBlacklist.query.order_by(JWTBlacklist.blacklisted_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return (
            jsonify(
                {
                    "blacklist": [token.to_dict() for token in blacklist.items],
                    "total": blacklist.total,
                    "pages": blacklist.pages,
                    "current_page": page,
                    "per_page": per_page,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"message": "獲取黑名單失敗", "error": str(e)}), 500


@admin_bp.route("/blacklist/cleanup", methods=["POST"])
@token_required
@admin_required
def cleanup_blacklist(current_user):
    """清理過期的黑名單 token（僅管理員）"""
    try:
        cleaned_count = JWTBlacklist.cleanup_expired_tokens()
        return (
            jsonify(
                {"message": f"已清理 {cleaned_count} 個過期 token", "cleaned_count": cleaned_count}
            ),
            200,
        )

    except Exception as e:
        return jsonify({"message": "清理黑名單失敗", "error": str(e)}), 500
