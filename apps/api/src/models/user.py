from datetime import datetime
import pyotp
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.orm import relationship

from src.database import db


class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="user")  # 'admin' or 'user'
    is_active = db.Column(db.Boolean, default=True)
    is_email_verified = db.Column(db.Boolean, default=False)
    # 2FA 相關欄位
    two_factor_secret = db.Column(db.String(32), nullable=True)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    
    # 多租戶相關欄位
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)
    tenant_role = db.Column(db.String(50), default='member', nullable=False)  # owner, admin, member
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    tenant = relationship("Tenant", back_populates="users")

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        """設置密碼哈希"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """檢查密碼"""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """檢查是否為管理員"""
        return self.role == "admin"

    def generate_2fa_secret(self):
        """生成 2FA 密鑰"""
        if not self.two_factor_secret:
            self.two_factor_secret = pyotp.random_base32()
        return self.two_factor_secret

    def get_2fa_uri(self, issuer_name="MorningAI"):
        """獲取 2FA URI 用於生成 QR 碼"""
        if not self.two_factor_secret:
            self.generate_2fa_secret()

        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.provisioning_uri(name=self.email, issuer_name=issuer_name)

    def verify_2fa_token(self, token):
        """驗證 2FA token"""
        if not self.two_factor_secret:
            return False

        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.verify(token, valid_window=1)

    def enable_2fa(self):
        """啟用 2FA"""
        self.two_factor_enabled = True

    def disable_2fa(self):
        """停用 2FA"""
        self.two_factor_enabled = False
        self.two_factor_secret = None

    def to_dict(self, include_sensitive=False):
        """轉換為字典，可選擇是否包含敏感信息"""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "is_email_verified": self.is_email_verified,
            "two_factor_enabled": self.two_factor_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_sensitive:
            data["password_hash"] = self.password_hash
            data["two_factor_secret"] = self.two_factor_secret

        return data


    tokens_valid_since = db.Column(db.DateTime, nullable=True)



    def invalidate_all_tokens(self):
        """使所有舊 token 失效"""
        self.tokens_valid_since = datetime.utcnow()

