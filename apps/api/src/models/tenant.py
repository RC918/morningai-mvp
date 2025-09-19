from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import db

class Tenant(db.Model):
    """
    多租戶模型 - 支援 SaaS 多租戶架構
    """
    __tablename__ = 'tenants'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    domain = Column(String(100), unique=True, nullable=True)  # 自訂網域
    description = Column(Text, nullable=True)
    
    # 租戶狀態
    is_active = Column(Boolean, default=True, nullable=False)
    is_trial = Column(Boolean, default=True, nullable=False)
    
    # 訂閱資訊
    plan = Column(String(50), default='free', nullable=False)  # free, basic, premium, enterprise
    max_users = Column(Integer, default=5, nullable=False)
    max_storage_gb = Column(Integer, default=1, nullable=False)
    
    # 時間戳記
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    
    # 設定 JSON 欄位 (儲存租戶特定設定)
    settings = Column(Text, nullable=True)  # JSON string
    
    # 關聯
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Tenant {self.name} ({self.slug})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'domain': self.domain,
            'description': self.description,
            'is_active': self.is_active,
            'is_trial': self.is_trial,
            'plan': self.plan,
            'max_users': self.max_users,
            'max_storage_gb': self.max_storage_gb,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'trial_ends_at': self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            'user_count': len(self.users) if self.users else 0
        }
    
    @classmethod
    def get_by_slug(cls, slug):
        """根據 slug 取得租戶"""
        return cls.query.filter_by(slug=slug, is_active=True).first()
    
    @classmethod
    def get_by_domain(cls, domain):
        """根據自訂網域取得租戶"""
        return cls.query.filter_by(domain=domain, is_active=True).first()
    
    def can_add_user(self):
        """檢查是否可以新增使用者"""
        current_user_count = len(self.users) if self.users else 0
        return current_user_count < self.max_users
    
    def get_usage_stats(self):
        """取得租戶使用統計"""
        return {
            'users': {
                'current': len(self.users) if self.users else 0,
                'limit': self.max_users,
                'percentage': (len(self.users) / self.max_users * 100) if self.max_users > 0 else 0
            },
            'storage': {
                'current_gb': 0,  # TODO: 實作儲存空間計算
                'limit_gb': self.max_storage_gb,
                'percentage': 0
            }
        }


class TenantInvitation(db.Model):
    """
    租戶邀請模型 - 管理使用者邀請加入租戶
    """
    __tablename__ = 'tenant_invitations'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    email = Column(String(120), nullable=False)
    role = Column(String(50), default='user', nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    
    # 邀請狀態
    is_accepted = Column(Boolean, default=False, nullable=False)
    is_expired = Column(Boolean, default=False, nullable=False)
    
    # 邀請者資訊
    invited_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # 時間戳記
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    # 關聯
    tenant = relationship("Tenant")
    invited_by = relationship("User", foreign_keys=[invited_by_user_id])
    
    def __repr__(self):
        return f'<TenantInvitation {self.email} to {self.tenant.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'tenant_name': self.tenant.name if self.tenant else None,
            'email': self.email,
            'role': self.role,
            'token': self.token,
            'is_accepted': self.is_accepted,
            'is_expired': self.is_expired,
            'invited_by': self.invited_by.username if self.invited_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None
        }
    
    @classmethod
    def get_by_token(cls, token):
        """根據 token 取得邀請"""
        return cls.query.filter_by(token=token, is_accepted=False, is_expired=False).first()
    
    def is_valid(self):
        """檢查邀請是否有效"""
        from datetime import datetime
        return (not self.is_accepted and 
                not self.is_expired and 
                self.expires_at > datetime.utcnow())
