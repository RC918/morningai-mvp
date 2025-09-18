import unittest
from src.main import app
from src.models.user import User
from src.database import db

class UserRoutesTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_user(self):
        response = self.app.post(
            '/api/users',
            json={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'testpassword'
            }
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn('testuser', response.json['username'])
        self.assertIn('test@example.com', response.json['email'])

    def test_get_users(self):
        user = User(username='testuser2', email='test2@example.com')
        user.set_password('testpassword2') # Add password
        db.session.add(user)
        db.session.commit()

        response = self.app.get('/api/users')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json), 0)
        # Note: The current /api/users endpoint returns a list of user dicts, not a single user dict.
        # We need to iterate through the list to find the user.
        found_user = False
        for u_data in response.json:
            if u_data['username'] == 'testuser2' and u_data['email'] == 'test2@example.com':
                found_user = True
                break
        self.assertTrue(found_user)

if __name__ == '__main__':
    unittest.main()


