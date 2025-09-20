from datetime import datetime
from flask import Blueprint, current_app, jsonify, request

from src.database import db
from src.decorators import token_required
from src.models.audit_log import AuditActions, AuditLog

audit_log_bp = Blueprint("audit_log", __name__)


def get_client_info(request):
    """獲取客戶端信息"""
    return {
        "ip_address": request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr),
        "user_agent": request.headers.get("User-Agent", "")[:500],  # 限制長度
    }


@audit_log_bp.route("/admin/audit-logs", methods=["GET"])
@token_required
def get_audit_logs(current_user):
    """獲取審計日誌（僅管理員）"""
    if not current_user.is_admin():
        return jsonify({"message": "需要管理員權限"}), 403

    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        action = request.args.get("action")
        user_id = request.args.get("user_id", type=int)
        status = request.args.get("status")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        # 構建查詢
        query = AuditLog.query

        if action:
            query = query.filter(AuditLog.action == action)

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        if status:
            query = query.filter(AuditLog.status == status)

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                query = query.filter(AuditLog.created_at >= start_dt)
            except ValueError:
                return jsonify({"message": "開始日期格式無效"}), 400

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                query = query.filter(AuditLog.created_at <= end_dt)
            except ValueError:
                return jsonify({"message": "結束日期格式無效"}), 400

        # 分頁查詢
        logs = query.order_by(AuditLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return (
            jsonify(
                {
                    "logs": [log.to_dict() for log in logs.items],
                    "total": logs.total,
                    "pages": logs.pages,
                    "current_page": page,
                    "per_page": per_page,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Get audit logs error: {str(e)}")
        return jsonify({"message": "獲取審計日誌失敗"}), 500


@audit_log_bp.route("/audit-logs/my", methods=["GET"])
@token_required
def get_my_audit_logs(current_user):
    """獲取當前用戶的審計日誌"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        action = request.args.get("action")

        # 構建查詢
        query = AuditLog.query.filter(AuditLog.user_id == current_user.id)

        if action:
            query = query.filter(AuditLog.action == action)

        # 分頁查詢
        logs = query.order_by(AuditLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return (
            jsonify(
                {
                    "logs": [log.to_dict() for log in logs.items],
                    "total": logs.total,
                    "pages": logs.pages,
                    "current_page": page,
                    "per_page": per_page,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Get my audit logs error: {str(e)}")
        return jsonify({"message": "獲取審計日誌失敗"}), 500


@audit_log_bp.route("/admin/audit-logs/stats", methods=["GET"])
@token_required
def get_audit_stats(current_user):
    """獲取審計日誌統計（僅管理員）"""
    if not current_user.is_admin():
        return jsonify({"message": "需要管理員權限"}), 403

    try:
        # 獲取時間範圍
        days = request.args.get("days", 7, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)

        # 總日誌數
        total_logs = AuditLog.query.filter(AuditLog.created_at >= start_date).count()

        # 失敗操作數
        failed_logs = AuditLog.query.filter(
            AuditLog.created_at >= start_date, AuditLog.status.in_(["failed", "error"])
        ).count()

        # 按操作類型統計
        from sqlalchemy import func

        action_stats = (
            db.session.query(AuditLog.action, func.count(AuditLog.id).label("count"))
            .filter(AuditLog.created_at >= start_date)
            .group_by(AuditLog.action)
            .all()
        )

        # 按狀態統計
        status_stats = (
            db.session.query(AuditLog.status, func.count(AuditLog.id).label("count"))
            .filter(AuditLog.created_at >= start_date)
            .group_by(AuditLog.status)
            .all()
        )

        # 活躍用戶統計
        active_users = (
            db.session.query(func.count(func.distinct(AuditLog.user_id)).label("count"))
            .filter(AuditLog.created_at >= start_date, AuditLog.user_id.isnot(None))
            .scalar()
        )

        return (
            jsonify(
                {
                    "period_days": days,
                    "total_logs": total_logs,
                    "failed_logs": failed_logs,
                    "success_rate": (
                        round((total_logs - failed_logs) / total_logs * 100, 2)
                        if total_logs > 0
                        else 100
                    ),
                    "active_users": active_users,
                    "action_stats": [
                        {"action": action, "count": count} for action, count in action_stats
                    ],
                    "status_stats": [
                        {"status": status, "count": count} for status, count in status_stats
                    ],
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Get audit stats error: {str(e)}")
        return jsonify({"message": "獲取統計數據失敗"}), 500


@audit_log_bp.route("/admin/audit-logs/cleanup", methods=["POST"])
@token_required
def cleanup_audit_logs(current_user):
    """清理舊的審計日誌（僅管理員）"""
    if not current_user.is_admin():
        return jsonify({"message": "需要管理員權限"}), 403

    try:
        data = request.get_json()
        days = data.get("days", 90)  # 默認清理 90 天前的日誌

        if days < 30:
            return jsonify({"message": "保留天數不能少於 30 天"}), 400

        # 記錄清理操作
        client_info = get_client_info(request)
        AuditLog.log_action(
            action=AuditActions.SYSTEM_STARTUP,  # 使用系統操作類型
            user_id=current_user.id,
            details={"operation": "audit_log_cleanup", "days": days},
            **client_info,
        )

        # 執行清理
        cleaned_count = AuditLog.cleanup_old_logs(days)

        return (
            jsonify(
                {
                    "message": f"已清理 {cleaned_count} 條舊日誌",
                    "cleaned_count": cleaned_count,
                    "retention_days": days,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Cleanup audit logs error: {str(e)}")
        return jsonify({"message": "清理審計日誌失敗"}), 500


@audit_log_bp.route("/admin/audit-logs/export", methods=["POST"])
@token_required
def export_audit_logs(current_user):
    """導出審計日誌（僅管理員）"""
    if not current_user.is_admin():
        return jsonify({"message": "需要管理員權限"}), 403

    try:
        data = request.get_json()
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        format_type = data.get("format", "json")  # json, csv

        # 構建查詢
        query = AuditLog.query

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.filter(AuditLog.created_at >= start_dt)

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.filter(AuditLog.created_at <= end_dt)

        logs = query.order_by(AuditLog.created_at.desc()).limit(10000).all()  # 限制導出數量

        # 記錄導出操作
        client_info = get_client_info(request)
        AuditLog.log_action(
            action="audit_log_export",
            user_id=current_user.id,
            details={
                "format": format_type,
                "count": len(logs),
                "start_date": start_date,
                "end_date": end_date,
            },
            **client_info,
        )

        if format_type == "csv":
            # 生成 CSV 格式
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # 寫入標題行
            writer.writerow(
                [
                    "ID",
                    "User ID",
                    "Username",
                    "Action",
                    "Resource Type",
                    "Resource ID",
                    "Status",
                    "IP Address",
                    "Created At",
                    "Details",
                ]
            )

            # 寫入數據行
            for log in logs:
                writer.writerow(
                    [
                        log.id,
                        log.user_id,
                        log.user.username if log.user else "",
                        log.action,
                        log.resource_type or "",
                        log.resource_id or "",
                        log.status,
                        log.ip_address or "",
                        log.created_at.isoformat() if log.created_at else "",
                        log.details or "",
                    ]
                )

            csv_content = output.getvalue()
            output.close()

            return (
                jsonify(
                    {
                        "message": "導出成功",
                        "format": "csv",
                        "content": csv_content,
                        "count": len(logs),
                    }
                ),
                200,
            )

        else:
            # 默認 JSON 格式
            return (
                jsonify(
                    {
                        "message": "導出成功",
                        "format": "json",
                        "logs": [log.to_dict() for log in logs],
                        "count": len(logs),
                    }
                ),
                200,
            )

    except Exception as e:
        current_app.logger.error(f"Export audit logs error: {str(e)}")
        return jsonify({"message": "導出審計日誌失敗"}), 500
