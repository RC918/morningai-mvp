"""
API 路由文檔化模組
為現有路由添加 Flask-RESTX 文檔支持
"""

from flask import request, jsonify
from flask_restx import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from flask_restx import fields

from src.api_docs import (
    api, auth_ns, users_ns, admin_ns, tenants_ns, 
    audit_ns, webhooks_ns, two_factor_ns,
    login_model, register_model, token_response_model,
    user_model, user_create_model, user_update_model,
    tenant_model, tenant_create_model,
    audit_log_model, webhook_model, webhook_create_model,
    two_factor_setup_model, two_factor_verify_model,
    health_model, error_model, success_model,
    paginated_model, require_auth
)

# ==================== 認證路由文檔 ====================

@auth_ns.route('/login')
class LoginResource(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.marshal_with(token_response_model, code=200)
    @auth_ns.response(400, 'Invalid credentials', error_model)
    @auth_ns.response(401, 'Authentication failed', error_model)
    @auth_ns.doc(description='用戶登入，支持雙重認證')
    def post(self):
        """用戶登入"""
        pass  # 實際實現在 routes/auth.py

@auth_ns.route('/register')
class RegisterResource(Resource):
    @auth_ns.expect(register_model)
    @auth_ns.marshal_with(success_model, code=201)
    @auth_ns.response(400, 'Validation error', error_model)
    @auth_ns.response(409, 'User already exists', error_model)
    @auth_ns.doc(description='用戶註冊')
    def post(self):
        """用戶註冊"""
        pass

@auth_ns.route('/logout')
class LogoutResource(Resource):
    @require_auth
    @auth_ns.marshal_with(success_model, code=200)
    @auth_ns.response(401, 'Unauthorized', error_model)
    @auth_ns.doc(description='用戶登出，將 JWT 加入黑名單')
    def delete(self):
        """用戶登出"""
        pass

@auth_ns.route('/refresh')
class RefreshResource(Resource):
    @require_auth
    @auth_ns.marshal_with(token_response_model, code=200)
    @auth_ns.response(401, 'Invalid token', error_model)
    @auth_ns.doc(description='刷新 JWT Token')
    def post(self):
        """刷新 Token"""
        pass

# ==================== 用戶路由文檔 ====================

@users_ns.route('/profile')
class ProfileResource(Resource):
    @require_auth
    @users_ns.marshal_with(user_model, code=200)
    @users_ns.response(401, 'Unauthorized', error_model)
    @users_ns.doc(description='獲取當前用戶資料')
    def get(self):
        """獲取用戶資料"""
        pass

    @require_auth
    @users_ns.expect(user_update_model)
    @users_ns.marshal_with(user_model, code=200)
    @users_ns.response(400, 'Validation error', error_model)
    @users_ns.response(401, 'Unauthorized', error_model)
    @users_ns.doc(description='更新當前用戶資料')
    def put(self):
        """更新用戶資料"""
        pass

@users_ns.route('/change-password')
class ChangePasswordResource(Resource):
    @require_auth
    @users_ns.expect(api.model('ChangePassword', {
        'current_password': fields.String(required=True, description='當前密碼'),
        'new_password': fields.String(required=True, description='新密碼', min_length=8),
    }))
    @users_ns.marshal_with(success_model, code=200)
    @users_ns.response(400, 'Invalid current password', error_model)
    @users_ns.response(401, 'Unauthorized', error_model)
    @users_ns.doc(description='修改密碼')
    def post(self):
        """修改密碼"""
        pass

# ==================== 管理員路由文檔 ====================

@admin_ns.route('/users')
class AdminUsersResource(Resource):
    @require_auth
    @admin_ns.marshal_with(paginated_model(user_model, 'User'), code=200)
    @admin_ns.response(401, 'Unauthorized', error_model)
    @admin_ns.response(403, 'Admin access required', error_model)
    @admin_ns.doc(description='獲取所有用戶列表（管理員專用）')
    @admin_ns.param('page', '頁碼', type=int, default=1)
    @admin_ns.param('per_page', '每頁數量', type=int, default=20)
    @admin_ns.param('search', '搜尋關鍵字', type=str)
    def get(self):
        """獲取用戶列表"""
        pass

    @require_auth
    @admin_ns.expect(user_create_model)
    @admin_ns.marshal_with(user_model, code=201)
    @admin_ns.response(400, 'Validation error', error_model)
    @admin_ns.response(401, 'Unauthorized', error_model)
    @admin_ns.response(403, 'Admin access required', error_model)
    @admin_ns.doc(description='創建新用戶（管理員專用）')
    def post(self):
        """創建用戶"""
        pass

@admin_ns.route('/users/<string:user_id>')
class AdminUserResource(Resource):
    @require_auth
    @admin_ns.marshal_with(user_model, code=200)
    @admin_ns.response(401, 'Unauthorized', error_model)
    @admin_ns.response(403, 'Admin access required', error_model)
    @admin_ns.response(404, 'User not found', error_model)
    @admin_ns.doc(description='獲取指定用戶詳情（管理員專用）')
    def get(self, user_id):
        """獲取用戶詳情"""
        pass

    @require_auth
    @admin_ns.expect(user_update_model)
    @admin_ns.marshal_with(user_model, code=200)
    @admin_ns.response(400, 'Validation error', error_model)
    @admin_ns.response(401, 'Unauthorized', error_model)
    @admin_ns.response(403, 'Admin access required', error_model)
    @admin_ns.response(404, 'User not found', error_model)
    @admin_ns.doc(description='更新指定用戶（管理員專用）')
    def put(self, user_id):
        """更新用戶"""
        pass

    @require_auth
    @admin_ns.marshal_with(success_model, code=200)
    @admin_ns.response(401, 'Unauthorized', error_model)
    @admin_ns.response(403, 'Admin access required', error_model)
    @admin_ns.response(404, 'User not found', error_model)
    @admin_ns.doc(description='刪除指定用戶（管理員專用）')
    def delete(self, user_id):
        """刪除用戶"""
        pass

# ==================== 租戶路由文檔 ====================

@tenants_ns.route('/')
class TenantsResource(Resource):
    @require_auth
    @tenants_ns.marshal_with(paginated_model(tenant_model, 'Tenant'), code=200)
    @tenants_ns.response(401, 'Unauthorized', error_model)
    @tenants_ns.doc(description='獲取租戶列表')
    @tenants_ns.param('page', '頁碼', type=int, default=1)
    @tenants_ns.param('per_page', '每頁數量', type=int, default=20)
    def get(self):
        """獲取租戶列表"""
        pass

    @require_auth
    @tenants_ns.expect(tenant_create_model)
    @tenants_ns.marshal_with(tenant_model, code=201)
    @tenants_ns.response(400, 'Validation error', error_model)
    @tenants_ns.response(401, 'Unauthorized', error_model)
    @tenants_ns.response(403, 'Admin access required', error_model)
    @tenants_ns.doc(description='創建新租戶')
    def post(self):
        """創建租戶"""
        pass

@tenants_ns.route('/<string:tenant_id>')
class TenantResource(Resource):
    @require_auth
    @tenants_ns.marshal_with(tenant_model, code=200)
    @tenants_ns.response(401, 'Unauthorized', error_model)
    @tenants_ns.response(404, 'Tenant not found', error_model)
    @tenants_ns.doc(description='獲取指定租戶詳情')
    def get(self, tenant_id):
        """獲取租戶詳情"""
        pass

# ==================== 審計日誌路由文檔 ====================

@audit_ns.route('/')
class AuditLogsResource(Resource):
    @require_auth
    @audit_ns.marshal_with(paginated_model(audit_log_model, 'AuditLog'), code=200)
    @audit_ns.response(401, 'Unauthorized', error_model)
    @audit_ns.doc(description='獲取審計日誌')
    @audit_ns.param('page', '頁碼', type=int, default=1)
    @audit_ns.param('per_page', '每頁數量', type=int, default=50)
    @audit_ns.param('action', '操作類型', type=str)
    @audit_ns.param('resource_type', '資源類型', type=str)
    @audit_ns.param('user_id', '用戶 ID', type=str)
    def get(self):
        """獲取審計日誌"""
        pass

# ==================== Webhook 路由文檔 ====================

@webhooks_ns.route('/')
class WebhooksResource(Resource):
    @require_auth
    @webhooks_ns.marshal_with(paginated_model(webhook_model, 'Webhook'), code=200)
    @webhooks_ns.response(401, 'Unauthorized', error_model)
    @webhooks_ns.doc(description='獲取 Webhook 列表')
    def get(self):
        """獲取 Webhook 列表"""
        pass

    @require_auth
    @webhooks_ns.expect(webhook_create_model)
    @webhooks_ns.marshal_with(webhook_model, code=201)
    @webhooks_ns.response(400, 'Validation error', error_model)
    @webhooks_ns.response(401, 'Unauthorized', error_model)
    @webhooks_ns.doc(description='創建新 Webhook')
    def post(self):
        """創建 Webhook"""
        pass

@webhooks_ns.route('/<string:webhook_id>')
class WebhookResource(Resource):
    @require_auth
    @webhooks_ns.marshal_with(webhook_model, code=200)
    @webhooks_ns.response(401, 'Unauthorized', error_model)
    @webhooks_ns.response(404, 'Webhook not found', error_model)
    @webhooks_ns.doc(description='獲取指定 Webhook 詳情')
    def get(self, webhook_id):
        """獲取 Webhook 詳情"""
        pass

    @require_auth
    @webhooks_ns.marshal_with(success_model, code=200)
    @webhooks_ns.response(401, 'Unauthorized', error_model)
    @webhooks_ns.response(404, 'Webhook not found', error_model)
    @webhooks_ns.doc(description='刪除指定 Webhook')
    def delete(self, webhook_id):
        """刪除 Webhook"""
        pass

# ==================== 雙重認證路由文檔 ====================

@two_factor_ns.route('/setup')
class TwoFactorSetupResource(Resource):
    @require_auth
    @two_factor_ns.marshal_with(two_factor_setup_model, code=200)
    @two_factor_ns.response(401, 'Unauthorized', error_model)
    @two_factor_ns.doc(description='設置雙重認證')
    def post(self):
        """設置雙重認證"""
        pass

@two_factor_ns.route('/verify')
class TwoFactorVerifyResource(Resource):
    @require_auth
    @two_factor_ns.expect(two_factor_verify_model)
    @two_factor_ns.marshal_with(success_model, code=200)
    @two_factor_ns.response(400, 'Invalid token', error_model)
    @two_factor_ns.response(401, 'Unauthorized', error_model)
    @two_factor_ns.doc(description='驗證雙重認證')
    def post(self):
        """驗證雙重認證"""
        pass

@two_factor_ns.route('/disable')
class TwoFactorDisableResource(Resource):
    @require_auth
    @two_factor_ns.expect(two_factor_verify_model)
    @two_factor_ns.marshal_with(success_model, code=200)
    @two_factor_ns.response(400, 'Invalid token', error_model)
    @two_factor_ns.response(401, 'Unauthorized', error_model)
    @two_factor_ns.doc(description='停用雙重認證')
    def post(self):
        """停用雙重認證"""
        pass

# ==================== 健康檢查路由文檔 ====================

@api.route('/health')
class HealthResource(Resource):
    @api.marshal_with(health_model, code=200)
    @api.doc(description='系統健康檢查')
    def get(self):
        """健康檢查"""
        pass
