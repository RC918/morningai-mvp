# apps/api/src/tests/test_security.py
import unittest
from src.main import app, db
from src.models.user import User
from src.models.audit_log import AuditLog, AuditActions

class SecurityTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_audit_log_login(self):
        with app.app_context():
            user = User(username="testuser", email="test@example.com", password_hash="test")
            db.session.add(user)
            db.session.commit()

            AuditLog.log_action(
                action=AuditActions.LOGIN,
                user_id=user.id,
                status="success"
            )

            log = AuditLog.query.filter_by(user_id=user.id, action=AuditActions.LOGIN).first()
            self.assertIsNotNone(log)
            self.assertEqual(log.status, "success")

if __name__ == "__main__":
    unittest.main()



    def test_email_verification(self):
        with app.app_context():
            # 1. Create a user
            user = User(username="verifyuser", email="verify@example.com")
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()

            # 2. Login to get a token
            login_res = self.app.post("/api/login", json={"email": "verify@example.com", "password": "password123"})
            self.assertEqual(login_res.status_code, 200)
            token = login_res.get_json()["token"]

            # 3. Request a verification email
            headers = {"Authorization": f"Bearer {token}"}
            send_res = self.app.post("/api/auth/email/send-verification", headers=headers)
            self.assertEqual(send_res.status_code, 200)
            self.assertIn("Verification email sent", send_res.get_json()["message"])

            # 4. Verify the email (we need to get the token from the print statement for now)
            # In a real test, you'd mock the email sending and capture the token.
            # For this test, we'll assume we can generate a token and use it.
            from src.routes.email_verification import generate_verification_token, confirm_verification_token
            verification_token = generate_verification_token(user.email)

            verify_res = self.app.get(f"/api/auth/email/verify/{verification_token}")
            self.assertEqual(verify_res.status_code, 200)
            self.assertIn("Email verified successfully", verify_res.get_json()["message"])

            # 5. Check that the user's status is updated
            updated_user = User.query.filter_by(email="verify@example.com").first()
            self.assertTrue(updated_user.is_email_verified)



    def test_jwt_blacklist_logout_all(self):
        with app.app_context():
            # 1. Create a user and log in
            user = User(username="blacklist_user", email="blacklist@example.com")
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()

            login_res = self.app.post("/api/login", json={"email": "blacklist@example.com", "password": "password123"})
            self.assertEqual(login_res.status_code, 200)
            token1 = login_res.get_json()["token"]

            # 2. Verify the first token is valid
            headers1 = {"Authorization": f"Bearer {token1}"}
            profile_res1 = self.app.get("/api/profile", headers=headers1)
            self.assertEqual(profile_res1.status_code, 200)

            # 3. Call logout-all to invalidate all tokens
            logout_all_res = self.app.post("/api/auth/logout-all", headers=headers1)
            self.assertEqual(logout_all_res.status_code, 200)

            # 4. Verify the first token is now invalid
            profile_res2 = self.app.get("/api/profile", headers=headers1)
            self.assertEqual(profile_res2.status_code, 401) # 401 Unauthorized

            # 5. Login again to get a new token
            login_res2 = self.app.post("/api/login", json={"email": "blacklist@example.com", "password": "password123"})
            self.assertEqual(login_res2.status_code, 200)
            token2 = login_res2.get_json()["token"]

            # 6. Verify the new token is valid
            headers2 = {"Authorization": f"Bearer {token2}"}
            profile_res3 = self.app.get("/api/profile", headers=headers2)
            self.assertEqual(profile_res3.status_code, 200)

