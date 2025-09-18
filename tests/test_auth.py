import unittest
from fastapi.testclient import TestClient
from app.main import app

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})

    def test_register_user(self):
        response = self.client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")

    def test_login_user(self):
        # 先注册一个用户
        self.client.post("/api/auth/register", json={
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "testpassword"
        })
        
        # 然后登录
        response = self.client.post("/api/auth/login", data={
            "username": "test2@example.com",
            "password": "testpassword"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")

if __name__ == "__main__":
    unittest.main()