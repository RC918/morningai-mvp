from datetime import datetime

from src.database import db


class JWTBlacklist(db.Model):
    """JWT 黑名單模型"""

    __tablename__ = "jwt_blacklist"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), unique=True, nullable=False, index=True)  # JWT ID
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    token_type = db.Column(db.String(20), nullable=False, default="access")  # access, refresh
    expires_at = db.Column(db.DateTime, nullable=False, index=True)  # 索引用於清理查詢
    blacklisted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reason = db.Column(
        db.String(100), nullable=True
    )  # logout, password_change, security_breach, etc.

    # 關聯到用戶
    user = db.relationship("User", backref=db.backref("blacklisted_tokens", lazy=True))

    def __repr__(self):
        return f"<JWTBlacklist {self.jti}>"

    @classmethod
    def is_blacklisted(cls, jti):
        """檢查 JWT 是否在黑名單中"""
        if not jti:
            return False

        token = cls.query.filter_by(jti=jti).first()
        if not token:
            return False

        # 如果 token 已過期，從黑名單中移除
        if token.expires_at < datetime.utcnow():
            db.session.delete(token)
            db.session.commit()
            return False

        return True

    @classmethod
    def add_to_blacklist(cls, jti, user_id, expires_at, token_type="access", reason=None):
        """將 JWT 添加到黑名單"""
        if not jti:
            return None

        try:
            # 檢查是否已存在
            existing = cls.query.filter_by(jti=jti).first()
            if existing:
                return existing

            blacklisted_token = cls(
                jti=jti,
                user_id=user_id,
                token_type=token_type,
                expires_at=expires_at,
                reason=reason,
            )
            db.session.add(blacklisted_token)
            db.session.commit()
            return blacklisted_token
        except Exception as e:
            db.session.rollback()
            print(f"Error adding token to blacklist: {e}")
            return None

    @classmethod
    def cleanup_expired_tokens(cls):
        """清理已過期的黑名單 token"""
        try:
            expired_tokens = cls.query.filter(cls.expires_at < datetime.utcnow()).all()
            count = len(expired_tokens)

            for token in expired_tokens:
                db.session.delete(token)

            db.session.commit()
            return count
        except Exception as e:
            db.session.rollback()
            print(f"Error cleaning up expired tokens: {e}")
            return 0

    def to_dict(self):
        """轉換為字典"""
        return {
            "id": self.id,
            "jti": self.jti,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "blacklisted_at": self.blacklisted_at.isoformat() if self.blacklisted_at else None,
            "reason": self.reason,
        }
