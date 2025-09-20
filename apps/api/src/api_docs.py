"""
API 文檔配置模組
使用 Flask-RESTX 提供 Swagger/OpenAPI 文檔
"""

from flask import Blueprint
from flask_restx import Api, Resource, fields

# 創建 API 文檔 Blueprint
docs_bp = Blueprint("docs", __name__)

# 配置 Flask-RESTX API
api = Api(
    docs_bp,
    version="1.0.3",
    title="MorningAI MVP API",
    description="""
    MorningAI MVP 企業級 AI SaaS 多租戶平台 API
    
    ## 認證方式
    使用 JWT Bearer Token 進行認證：
    ```
    Authorization: Bearer <your-jwt-token>
    ```
    
    ## 錯誤處理
    API 使用標準 HTTP 狀態碼，錯誤回應格式：
    ```json
    {
        "error": "錯誤描述",
        "code": "ERROR_CODE",
        "details": {}
    }
    ```
    
    ## 速率限制
    - 未認證用戶：每分鐘 60 次請求
    - 已認證用戶：每分鐘 1000 次請求
    - 管理員：無限制
    """,
    doc="/docs/",
    prefix="/api",
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'JWT Token (格式: Bearer <token>)'
        }
    },
    security='Bearer'
)

# ==================== 數據模型定義 ====================

# 用戶相關模型
user_model = api.model(
    "User",
    {
        "id": fields.String(required=True, description="用戶 UUID"),
        "username": fields.String(required=True, description="用戶名"),
        "email": fields.String(required=True, description="郵箱地址"),
        "role": fields.String(required=True, description="用戶角色", enum=["user", "admin"]),
        "is_active": fields.Boolean(description="是否啟用"),
        "is_email_verified": fields.Boolean(description="郵箱是否已驗證"),
        "two_factor_enabled": fields.Boolean(description="是否啟用雙重認證"),
        "tenant_id": fields.String(description="所屬租戶 ID"),
        "created_at": fields.DateTime(description="創建時間"),
        "updated_at": fields.DateTime(description="更新時間"),
    },
)

user_create_model = api.model(
    "UserCreate",
    {
        "username": fields.String(required=True, description="用戶名", min_length=3, max_length=50),
        "email": fields.String(required=True, description="郵箱地址"),
        "password": fields.String(required=True, description="密碼", min_length=8),
        "role": fields.String(description="用戶角色", enum=["user", "admin"], default="user"),
    },
)

user_update_model = api.model(
    "UserUpdate",
    {
        "username": fields.String(description="用戶名", min_length=3, max_length=50),
        "email": fields.String(description="郵箱地址"),
        "is_active": fields.Boolean(description="是否啟用"),
        "role": fields.String(description="用戶角色", enum=["user", "admin"]),
    },
)

# 認證相關模型
login_model = api.model(
    "Login",
    {
        "email": fields.String(required=True, description="郵箱地址"),
        "password": fields.String(required=True, description="密碼"),
        "otp": fields.String(description="雙重認證驗證碼（如果啟用）"),
    },
)

register_model = api.model(
    "Register",
    {
        "username": fields.String(required=True, description="用戶名", min_length=3, max_length=50),
        "email": fields.String(required=True, description="郵箱地址"),
        "password": fields.String(required=True, description="密碼", min_length=8),
        "confirm_password": fields.String(required=True, description="確認密碼"),
    },
)

token_response_model = api.model(
    "TokenResponse",
    {
        "access_token": fields.String(required=True, description="JWT 存取令牌"),
        "refresh_token": fields.String(description="刷新令牌"),
        "token_type": fields.String(default="Bearer", description="令牌類型"),
        "expires_in": fields.Integer(description="令牌過期時間（秒）"),
        "user": fields.Nested(user_model, description="用戶資訊"),
    },
)

# 租戶相關模型
tenant_model = api.model(
    "Tenant",
    {
        "id": fields.String(required=True, description="租戶 UUID"),
        "name": fields.String(required=True, description="租戶名稱"),
        "slug": fields.String(required=True, description="租戶標識符"),
        "domain": fields.String(description="自定義域名"),
        "description": fields.String(description="租戶描述"),
        "is_active": fields.Boolean(description="是否啟用"),
        "is_trial": fields.Boolean(description="是否試用"),
        "plan": fields.String(description="訂閱計劃", enum=["free", "basic", "premium", "enterprise"]),
        "max_users": fields.Integer(description="最大用戶數"),
        "max_storage_gb": fields.Integer(description="最大存儲空間（GB）"),
        "created_at": fields.DateTime(description="創建時間"),
        "updated_at": fields.DateTime(description="更新時間"),
    },
)

tenant_create_model = api.model(
    "TenantCreate",
    {
        "name": fields.String(required=True, description="租戶名稱", min_length=2, max_length=100),
        "slug": fields.String(required=True, description="租戶標識符", min_length=2, max_length=50),
        "domain": fields.String(description="自定義域名"),
        "description": fields.String(description="租戶描述"),
        "plan": fields.String(description="訂閱計劃", enum=["free", "basic", "premium", "enterprise"], default="free"),
    },
)

# 審計日誌模型
audit_log_model = api.model(
    "AuditLog",
    {
        "id": fields.String(required=True, description="日誌 UUID"),
        "user_id": fields.String(description="操作用戶 ID"),
        "action": fields.String(required=True, description="操作動作"),
        "resource_type": fields.String(required=True, description="資源類型"),
        "resource_id": fields.String(description="資源 ID"),
        "details": fields.Raw(description="操作詳情"),
        "ip_address": fields.String(description="IP 地址"),
        "user_agent": fields.String(description="用戶代理"),
        "status": fields.String(description="操作狀態", enum=["success", "failed", "pending"]),
        "created_at": fields.DateTime(description="創建時間"),
    },
)

# Webhook 模型
webhook_model = api.model(
    "Webhook",
    {
        "id": fields.String(required=True, description="Webhook UUID"),
        "user_id": fields.String(required=True, description="用戶 ID"),
        "url": fields.String(required=True, description="Webhook URL"),
        "event_type": fields.String(required=True, description="事件類型"),
        "secret": fields.String(description="簽名密鑰"),
        "is_active": fields.Boolean(description="是否啟用"),
        "retry_count": fields.Integer(description="重試次數"),
        "last_triggered_at": fields.DateTime(description="最後觸發時間"),
        "created_at": fields.DateTime(description="創建時間"),
        "updated_at": fields.DateTime(description="更新時間"),
    },
)

webhook_create_model = api.model(
    "WebhookCreate",
    {
        "url": fields.String(required=True, description="Webhook URL"),
        "event_type": fields.String(required=True, description="事件類型"),
        "secret": fields.String(description="簽名密鑰"),
        "is_active": fields.Boolean(description="是否啟用", default=True),
    },
)

# 雙重認證模型
two_factor_setup_model = api.model(
    "TwoFactorSetup",
    {
        "secret": fields.String(required=True, description="2FA 密鑰"),
        "qr_code": fields.String(required=True, description="QR 碼 Base64 圖片"),
        "backup_codes": fields.List(fields.String, description="備用代碼"),
    },
)

two_factor_verify_model = api.model(
    "TwoFactorVerify",
    {
        "token": fields.String(required=True, description="6位數驗證碼"),
    },
)

# 健康檢查模型
health_model = api.model(
    "Health",
    {
        "status": fields.String(required=True, description="服務狀態", enum=["ok", "error"]),
        "message": fields.String(description="狀態訊息"),
        "timestamp": fields.DateTime(description="檢查時間"),
        "version": fields.String(description="API 版本"),
        "dependencies": fields.Raw(description="依賴服務狀態"),
        "uptime": fields.String(description="運行時間"),
        "memory_usage": fields.Raw(description="記憶體使用情況"),
    },
)

# 錯誤回應模型
error_model = api.model(
    "Error",
    {
        "error": fields.String(required=True, description="錯誤描述"),
        "code": fields.String(description="錯誤代碼"),
        "details": fields.Raw(description="錯誤詳情"),
        "timestamp": fields.DateTime(description="錯誤時間"),
    },
)

# 分頁模型
pagination_model = api.model(
    "Pagination",
    {
        "page": fields.Integer(description="當前頁碼"),
        "per_page": fields.Integer(description="每頁數量"),
        "total": fields.Integer(description="總數量"),
        "pages": fields.Integer(description="總頁數"),
        "has_prev": fields.Boolean(description="是否有上一頁"),
        "has_next": fields.Boolean(description="是否有下一頁"),
    },
)

# 分頁回應模型
def paginated_model(item_model, name):
    """創建分頁回應模型"""
    return api.model(
        f"Paginated{name}",
        {
            "items": fields.List(fields.Nested(item_model), description="數據項目"),
            "pagination": fields.Nested(pagination_model, description="分頁資訊"),
        },
    )

# 常用回應模型
success_model = api.model(
    "Success",
    {
        "message": fields.String(required=True, description="成功訊息"),
        "data": fields.Raw(description="回應數據"),
    },
)

# ==================== 命名空間定義 ====================

# 認證命名空間
auth_ns = api.namespace('auth', description='認證相關操作')
users_ns = api.namespace('users', description='用戶管理')
admin_ns = api.namespace('admin', description='管理員操作')
tenants_ns = api.namespace('tenants', description='租戶管理')
audit_ns = api.namespace('audit', description='審計日誌')
webhooks_ns = api.namespace('webhooks', description='Webhook 管理')
two_factor_ns = api.namespace('2fa', description='雙重認證')

# ==================== 工具函數 ====================

def require_auth(f):
    """認證裝飾器，用於 API 文檔"""
    return api.doc(security='Bearer')(f)

def handle_validation_error(errors):
    """處理驗證錯誤"""
    return {
        'error': 'Validation failed',
        'code': 'VALIDATION_ERROR',
        'details': errors
    }, 400

def handle_not_found(resource_type="Resource"):
    """處理資源未找到錯誤"""
    return {
        'error': f'{resource_type} not found',
        'code': 'NOT_FOUND'
    }, 404

def handle_unauthorized():
    """處理未授權錯誤"""
    return {
        'error': 'Unauthorized access',
        'code': 'UNAUTHORIZED'
    }, 401

def handle_forbidden():
    """處理禁止訪問錯誤"""
    return {
        'error': 'Forbidden access',
        'code': 'FORBIDDEN'
    }, 403
