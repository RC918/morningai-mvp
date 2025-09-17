import unittest
from src.main import app

class HealthCheckTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_health_check(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'ok': True})

if __name__ == "__main__":
    unittest.main()


