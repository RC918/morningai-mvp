import unittest
from src.main import app, db
from src.models.user import User
import json

class AuthRoutesTest(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            # 清除所有現有用戶以避免 UNIQUE 約束失敗
            User.query.delete()
            db.session.commit()

            # 創建一個管理員用戶和一個普通用戶用於測試
            admin_user = User(username="admin", email="admin@example.com", role="admin")
            admin_user.set_password("adminpassword")
            self.admin_user = admin_user

            test_user = User(username="testuser", email="test@example.com", role="user")
            test_user.set_password("testpassword")
            self.test_user = test_user

            db.session.add(admin_user)
            db.session.add(test_user)
            db.session.commit()

            # 登錄管理員並獲取 token
            response = self.app.post("/api/auth/login", json={"username": "admin", "password": "adminpassword"})
            self.admin_token = json.loads(response.data)["token"]

            # 登錄普通用戶並獲取 token
            response = self.app.post("/api/auth/login", json={"username": "testuser", "password": "testpassword"})
            self.user_token = json.loads(response.data)["token"]

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_register_user(self):
        response = self.app.post("/api/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword"
        })
        self.assertEqual(response.status_code, 201)

    def test_login_user(self):
        response = self.app.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpassword"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", json.loads(response.data))

    def test_get_profile(self):
        response = self.app.get("/api/auth/profile", headers={"Authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data)["user"]["username"], "testuser")

    def test_get_all_users_admin_only(self):
        response = self.app.get("/api/admin/users", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(json.loads(response.data)["users"], list)

    def test_get_all_users_not_admin(self):
        response = self.app.get("/api/admin/users", headers={"Authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 403)

    def test_update_user_role_admin_only(self):
        response = self.app.put(
            f"/api/admin/users/{self.test_user.id}/role",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={"role": "admin"}
        )
        self.assertEqual(response.status_code, 200)

    def test_update_user_status_admin_only(self):
        response = self.app.put(
            f"/api/admin/users/{self.test_user.id}/status",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={"is_active": False}
        )
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()


