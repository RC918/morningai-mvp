from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import json
import hashlib
import hmac

from src.database import db

class Webhook(db.Model):
    """
    Webhook 配置模型
    """
    __tablename__ = 'webhooks'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=True)  # 租戶特定的 webhook
    
    # Webhook 基本資訊
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(255), nullable=True)  # 用於簽名驗證
    
    # 觸發條件
    events = Column(JSON, nullable=False)  # 監聽的事件類型列表
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 重試設定
    max_retries = Column(Integer, default=3, nullable=False)
    retry_delay = Column(Integer, default=60, nullable=False)  # 秒
    
    # 時間戳記
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    
    # 統計資訊
    total_calls = Column(Integer, default=0, nullable=False)
    successful_calls = Column(Integer, default=0, nullable=False)
    failed_calls = Column(Integer, default=0, nullable=False)
    
    # 關聯
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Webhook {self.name} ({self.url})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'url': self.url,
            'events': self.events,
            'is_active': self.is_active,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_triggered_at': self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            'total_calls': self.total_calls,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'success_rate': self.get_success_rate()
        }
    
    def get_success_rate(self):
        """計算成功率"""
        if self.total_calls == 0:
            return 0
        return round((self.successful_calls / self.total_calls) * 100, 2)
    
    def should_trigger_for_event(self, event_type):
        """檢查是否應該為特定事件觸發"""
        return self.is_active and event_type in self.events
    
    def generate_signature(self, payload):
        """生成 webhook 簽名"""
        if not self.secret:
            return None
        
        signature = hmac.new(
            self.secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f'sha256={signature}'


class WebhookDelivery(db.Model):
    """
    Webhook 傳送記錄模型
    """
    __tablename__ = 'webhook_deliveries'
    
    id = Column(Integer, primary_key=True)
    webhook_id = Column(Integer, ForeignKey('webhooks.id'), nullable=False)
    
    # 傳送資訊
    event_type = Column(String(100), nullable=False)
    payload = Column(Text, nullable=False)  # JSON payload
    
    # 請求資訊
    request_headers = Column(JSON, nullable=True)
    request_method = Column(String(10), default='POST', nullable=False)
    
    # 回應資訊
    response_status_code = Column(Integer, nullable=True)
    response_headers = Column(JSON, nullable=True)
    response_body = Column(Text, nullable=True)
    
    # 狀態
    status = Column(String(20), default='pending', nullable=False)  # pending, success, failed, retrying
    error_message = Column(Text, nullable=True)
    
    # 重試資訊
    attempt_count = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # 時間戳記
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 關聯
    webhook = relationship("Webhook", back_populates="deliveries")
    
    def __repr__(self):
        return f'<WebhookDelivery {self.id} ({self.event_type})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'webhook_id': self.webhook_id,
            'event_type': self.event_type,
            'status': self.status,
            'response_status_code': self.response_status_code,
            'error_message': self.error_message,
            'attempt_count': self.attempt_count,
            'max_attempts': self.max_attempts,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None,
            'next_retry_at': self.next_retry_at.isoformat() if self.next_retry_at else None
        }
    
    def can_retry(self):
        """檢查是否可以重試"""
        return (self.status in ['failed', 'retrying'] and 
                self.attempt_count < self.max_attempts and
                (self.next_retry_at is None or self.next_retry_at <= datetime.utcnow()))
    
    def mark_as_success(self, response_status_code, response_headers=None, response_body=None):
        """標記為成功"""
        self.status = 'success'
        self.response_status_code = response_status_code
        self.response_headers = response_headers
        self.response_body = response_body
        self.delivered_at = datetime.utcnow()
        self.error_message = None
        
        # 更新 webhook 統計
        self.webhook.successful_calls += 1
        self.webhook.last_triggered_at = datetime.utcnow()
    
    def mark_as_failed(self, error_message, response_status_code=None, response_headers=None, response_body=None):
        """標記為失敗"""
        self.status = 'failed'
        self.error_message = error_message
        self.response_status_code = response_status_code
        self.response_headers = response_headers
        self.response_body = response_body
        self.failed_at = datetime.utcnow()
        
        # 更新 webhook 統計
        self.webhook.failed_calls += 1
    
    def schedule_retry(self, delay_seconds=None):
        """安排重試"""
        if self.attempt_count >= self.max_attempts:
            self.mark_as_failed("Maximum retry attempts exceeded")
            return False
        
        self.status = 'retrying'
        self.attempt_count += 1
        
        if delay_seconds is None:
            delay_seconds = self.webhook.retry_delay * (2 ** (self.attempt_count - 1))  # 指數退避
        
        self.next_retry_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
        return True


class WebhookEvent(db.Model):
    """
    Webhook 事件模型 - 記錄系統中發生的事件
    """
    __tablename__ = 'webhook_events'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=True)
    
    # 事件資訊
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON, nullable=False)
    
    # 觸發資訊
    triggered_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    source = Column(String(100), nullable=True)  # 事件來源
    
    # 時間戳記
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 關聯
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    triggered_by = relationship("User", foreign_keys=[triggered_by_user_id])
    
    def __repr__(self):
        return f'<WebhookEvent {self.event_type} ({self.id})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'event_type': self.event_type,
            'event_data': self.event_data,
            'triggered_by_user_id': self.triggered_by_user_id,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }


# 預定義的事件類型
WEBHOOK_EVENTS = {
    # 使用者事件
    'user.created': '使用者建立',
    'user.updated': '使用者更新',
    'user.deleted': '使用者刪除',
    'user.login': '使用者登入',
    'user.logout': '使用者登出',
    'user.password_changed': '密碼變更',
    'user.email_verified': '電子郵件驗證',
    'user.2fa_enabled': '2FA 啟用',
    'user.2fa_disabled': '2FA 停用',
    
    # 租戶事件
    'tenant.created': '租戶建立',
    'tenant.updated': '租戶更新',
    'tenant.deleted': '租戶刪除',
    'tenant.member_added': '成員加入',
    'tenant.member_removed': '成員移除',
    'tenant.member_role_changed': '成員角色變更',
    'tenant.plan_changed': '方案變更',
    
    # 系統事件
    'system.maintenance_start': '維護開始',
    'system.maintenance_end': '維護結束',
    'system.backup_completed': '備份完成',
    'system.backup_failed': '備份失敗',
    
    # 安全事件
    'security.login_failed': '登入失敗',
    'security.suspicious_activity': '可疑活動',
    'security.token_revoked': 'Token 撤銷',
}
