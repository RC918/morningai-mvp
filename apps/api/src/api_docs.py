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
    version="1.0",
    title="MorningAI MVP API",
    description="MorningAI MVP 後端 API 文檔",
    doc="/docs/",
    prefix="/api",
)

# 定義常用的數據模型
user_model = api.model(
    "User",
    {
        "id": fields.Integer(required=True, description="用戶 ID"),
        "username": fields.String(required=True, description="用戶名"),
        "email": fields.String(required=True, description="郵箱"),
        "role": fields.String(required=True, description="角色"),
        "is_active": fields.Boolean(description="是否啟用"),
        "is_email_verified": fields.Boolean(description="郵箱是否已驗證"),
        "two_factor_enabled": fields.Boolean(description="是否啟用 2FA"),
        "created_at": fields.DateTime(description="創建時間"),
        "updated_at": fields.DateTime(description="更新時間"),
    },
)

login_model = api.model(
    "Login",
    {
        "email": fields.String(required=True, description="郵箱"),
        "password": fields.String(required=True, description="密碼"),
        "otp": fields.String(description="2FA 驗證碼（如果啟用）"),
    },
)

register_model = api.model(
    "Register",
    {
        "username": fields.String(required=True, description="用戶名"),
        "email": fields.String(required=True, description="郵箱"),
        "password": fields.String(required=True, description="密碼"),
    },
)

token_response_model = api.model(
    "TokenResponse",
    {
        "message": fields.String(description="回應訊息"),
        "token": fields.String(description="JWT Token"),
        "user": fields.Nested(user_model, description="用戶資訊"),
    },
)

error_model = api.model(
    "Error",
    {
        "message": fields.String(description="錯誤訊息"),
        "error": fields.String(description="錯誤詳情"),
    },
)


# 健康檢查端點
@api.route("/health")
class HealthCheck(Resource):
    @api.doc("health_check")
    @api.marshal_with(
        api.model(
            "Health",
            {
                "ok": fields.Boolean(description="服務狀態"),
                "message": fields.String(description="狀態訊息"),
            },
        )
    )
    def get(self):
        """健康檢查"""
        return {"ok": True, "message": "Service is healthy"}


# 認證相關端點
auth_ns = api.namespace("auth", description="認證相關操作")


@auth_ns.route("/register")
class Register(Resource):
    @api.doc("register_user")
    @api.expect(register_model)
    @api.marshal_with(token_response_model, code=200)
    @api.marshal_with(error_model, code=400)
    def post(self):
        """用戶註冊"""
        pass


@auth_ns.route("/login")
class Login(Resource):
    @api.doc("login_user")
    @api.expect(login_model)
    @api.marshal_with(token_response_model, code=200)
    @api.marshal_with(error_model, code=401)
    def post(self):
        """用戶登入"""
        pass


@auth_ns.route("/logout")
class Logout(Resource):
    @api.doc("logout_user")
    @api.doc(security="Bearer")
    @api.marshal_with(
        api.model("LogoutResponse", {"message": fields.String(description="登出訊息")}),
        code=200,
    )
    @api.marshal_with(error_model, code=401)
    def post(self):
        """用戶登出"""
        pass


@auth_ns.route("/profile")
class Profile(Resource):
    @api.doc("get_profile")
    @api.doc(security="Bearer")
    @api.marshal_with(
        api.model(
            "ProfileResponse",
            {"user": fields.Nested(user_model, description="用戶資訊")},
        ),
        code=200,
    )
    @api.marshal_with(error_model, code=401)
    def get(self):
        """獲取用戶資料"""
        pass


# 管理員相關端點
admin_ns = api.namespace("admin", description="管理員操作")


@admin_ns.route("/users")
class AdminUsers(Resource):
    @api.doc("list_users")
    @api.doc(security="Bearer")
    @api.marshal_with(
        api.model(
            "UsersResponse",
            {"users": fields.List(fields.Nested(user_model), description="用戶列表")},
        ),
        code=200,
    )
    @api.marshal_with(error_model, code=403)
    def get(self):
        """獲取用戶列表（管理員）"""
        pass


# 配置安全認證
authorizations = {
    "Bearer": {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization",
        "description": "JWT Token 認證，格式: Bearer <token>",
    }
}

api.authorizations = authorizations
