import json
from datetime import datetime

from src.database import db


class AuditLog(db.Model):
    """審計日誌模型"""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)  # 可能是系統操作
    action = db.Column(db.String(100), nullable=False)  # 操作類型
    resource_type = db.Column(db.String(50), nullable=True)  # 資源類型
    resource_id = db.Column(db.String(50), nullable=True)  # 資源 ID
    details = db.Column(db.Text, nullable=True)  # 詳細信息（JSON 格式）
    ip_address = db.Column(db.String(45), nullable=True)  # IP 地址
    user_agent = db.Column(db.String(500), nullable=True)  # 用戶代理
    status = db.Column(db.String(20), nullable=False, default="success")  # success, failed, error
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # 關聯到用戶
    user = db.relationship("User", backref=db.backref("audit_logs", lazy=True))

    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action}>"

    @classmethod
    def log_action(
        cls,
        action,
        user_id=None,
        resource_type=None,
        resource_id=None,
        details=None,
        ip_address=None,
        user_agent=None,
        status="success",
    ):
        """記錄操作日誌"""
        try:
            # 如果 details 是字典，轉換為 JSON 字符串
            if isinstance(details, dict):
                details = json.dumps(details, ensure_ascii=False)

            log_entry = cls(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
            )

            db.session.add(log_entry)
            db.session.commit()
            return log_entry

        except Exception as e:
            db.session.rollback()
            # 記錄審計日誌失敗不應該影響主要操作
            print(f"Failed to log audit entry: {str(e)}")
            return None

    @classmethod
    def get_user_logs(cls, user_id, limit=50, offset=0):
        """獲取用戶的操作日誌"""
        return (
            cls.query.filter_by(user_id=user_id)
            .order_by(cls.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    @classmethod
    def get_logs_by_action(cls, action, limit=50, offset=0):
        """根據操作類型獲取日誌"""
        return (
            cls.query.filter_by(action=action)
            .order_by(cls.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    @classmethod
    def get_failed_logs(cls, limit=50, offset=0):
        """獲取失敗的操作日誌"""
        return (
            cls.query.filter(cls.status.in_(["failed", "error"]))
            .order_by(cls.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    @classmethod
    def cleanup_old_logs(cls, days=90):
        """清理舊的審計日誌"""
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        old_logs = cls.query.filter(cls.created_at < cutoff_date).all()
        count = len(old_logs)

        for log in old_logs:
            db.session.delete(log)

        db.session.commit()
        return count

    def get_details_dict(self):
        """獲取詳細信息的字典格式"""
        if not self.details:
            return {}

        try:
            return json.loads(self.details)
        except (json.JSONDecodeError, TypeError):
            return {"raw": self.details}

    def to_dict(self):
        """轉換為字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.get_details_dict(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# 常用的操作類型常量
class AuditActions:
    # 認證相關
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    REGISTER = "register"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"

    # 2FA 相關
    TWO_FA_ENABLE = "2fa_enable"
    TWO_FA_DISABLE = "2fa_disable"
    TWO_FA_SETUP = "2fa_setup"
    TWO_FA_VERIFY = "2fa_verify"

    # Email 驗證相關
    EMAIL_VERIFICATION_SENT = "email_verification_sent"
    EMAIL_VERIFIED = "email_verified"

    # JWT 相關
    TOKEN_REVOKED = "token_revoked"
    TOKEN_BLACKLISTED = "token_blacklisted"

    # 用戶管理
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_STATUS_CHANGED = "user_status_changed"

    # 系統操作
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    DATABASE_MIGRATION = "database_migration"
