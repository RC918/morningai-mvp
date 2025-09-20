import json
import unittest

from flask import Flask

from src.database import db
from src.main import app
from src.models.audit_log import AuditLog
from src.models.jwt_blacklist import JWTBlacklist
from src.models.tenant import Tenant, TenantInvitation

# Explicitly import all models to ensure SQLAlchemy metadata is populated
from src.models.user import User
from src.models.webhook import Webhook, WebhookDelivery, WebhookEvent


class IntegrationTest(unittest.TestCase):
    def setUp(self):
        """設定測試環境"""
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        """清理測試環境"""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_full_flow(self):
        """測試完整的註冊、登入、建立租戶、邀請使用者流程"""
        with app.app_context():
            # 1. 註冊新使用者
            register_response = self.app.post(
                "/api/register",
                json={
                    "username": "testuser",
                    "email": "test@example.com",
                    "password": "password123",
                },
            )
            self.assertEqual(register_response.status_code, 201)

            # 2. 登入
            login_response = self.app.post(
                "/api/login",
                json={"email": "test@example.com", "password": "password123"},
            )
            self.assertEqual(login_response.status_code, 200)
            access_token = json.loads(login_response.data)["token"]

            # 3. 建立租戶
            create_tenant_response = self.app.post(
                "/api/tenants",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"name": "Test Tenant", "slug": "test-tenant"},
            )
            self.assertEqual(create_tenant_response.status_code, 201)
            tenant_id = json.loads(create_tenant_response.data)["tenant"]["id"]

            # 4. 邀請新使用者
            invite_response = self.app.post(
                f"/api/tenants/{tenant_id}/invite",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"email": "invited@example.com", "role": "member"},
            )
            self.assertEqual(invite_response.status_code, 201)
            invitation_token = json.loads(invite_response.data)["invitation"]["token"]

            # 5. 註冊被邀請的使用者
            register_invited_response = self.app.post(
                "/api/register",
                json={
                    "username": "inviteduser",
                    "email": "invited@example.com",
                    "password": "password123",
                },
            )
            self.assertEqual(register_invited_response.status_code, 201)

            # 6. 登入被邀請的使用者
            login_invited_response = self.app.post(
                "/api/login",
                json={"email": "invited@example.com", "password": "password123"},
            )
            self.assertEqual(login_invited_response.status_code, 200)
            invited_access_token = json.loads(login_invited_response.data)["token"]

            # 7. 接受邀請
            accept_response = self.app.post(
                f"/api/tenants/invitations/{invitation_token}/accept",
                headers={"Authorization": f"Bearer {invited_access_token}"},
            )
            self.assertEqual(accept_response.status_code, 200)

            # 8. 驗證成員已加入租戶
            members_response = self.app.get(
                f"/api/tenants/{tenant_id}/members",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            self.assertEqual(members_response.status_code, 200)
            members = json.loads(members_response.data)["members"]
            self.assertEqual(len(members), 2)
            self.assertIn("invited@example.com", [m["email"] for m in members])


if __name__ == "__main__":
    unittest.main()
