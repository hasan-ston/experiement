import os
import sys
import unittest
from unittest.mock import patch


class FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, value):
        self.store[key] = value

    def delete(self, key):
        self.store.pop(key, None)


class AppTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Make sure the app uses in-memory DB and dummy secrets for tests.
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        os.environ["SECRET_KEY"] = "test-secret"
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"
        os.environ["RATELIMIT_STORAGE_URI"] = "memory://"

        cls.fake_redis = FakeRedis()
        class _FakeOpenAIClient:
            def __init__(self, api_key=None):
                self.chat = type(
                    "Chat", (), {"completions": type("Comp", (), {"create": lambda *a, **k: type(
                        "Resp", (), {"choices": [type("Choice", (), {"message": type("Msg", (), {"content": "fake"})()})()]}
                    )()})()}
                )
        sys.modules.setdefault("openai", type("OpenAIModule", (), {"OpenAI": _FakeOpenAIClient})())
        # Provide a fake redis module so imports don't fail if redis isn't installed.
        sys.modules.setdefault(
            "redis",
            type(
                "RedisModule",
                (),
                {"from_url": staticmethod(lambda url, decode_responses=True: cls.fake_redis)},
            )(),
        )
        with patch("redis.from_url", return_value=cls.fake_redis):
            from backend import app as app_module

        cls.app_module = app_module
        cls.app = app_module.app
        cls.db = app_module.db
        cls.User = app_module.User
        cls.client = cls.app.test_client()

    def setUp(self):
        # Fresh DB and cache for every test.
        with self.app.app_context():
            self.db.drop_all()
            self.db.create_all()
        self.fake_redis.store.clear()

    def _register_and_login(self, email="alice@example.com", password="pass123"):
        register_resp = self.client.post(
            "/api/auth/register", json={"email": email, "password": password}
        )
        self.assertEqual(register_resp.status_code, 201)
        register_data = register_resp.get_json()
        token = register_data["access_token"]
        user_id = register_data["user"]["id"]
        return token, user_id

    def test_register_and_login_flow(self):
        token, user_id = self._register_and_login()
        self.assertTrue(token)
        self.assertIsInstance(user_id, int)

        # Password should be stored hashed, not plain.
        with self.app.app_context():
            user = self.User.query.filter_by(email="alice@example.com").first()
            self.assertIsNotNone(user)
            self.assertNotEqual(user.password_hash, "pass123")

        # Login should succeed with same credentials.
        login_resp = self.client.post(
            "/api/auth/login", json={"email": "alice@example.com", "password": "pass123"}
        )
        self.assertEqual(login_resp.status_code, 200)
        self.assertIn("access_token", login_resp.get_json())

    def test_expense_summary_uses_cache_and_invalidates_on_write(self):
        token, user_id = self._register_and_login()
        headers = {"Authorization": f"Bearer {token}"}

        # Create one expense.
        create_resp = self.client.post(
            "/api/expenses",
            json={"category": "rent", "description": "Jan", "amount": 500},
            headers=headers,
        )
        self.assertEqual(create_resp.status_code, 201)

        # First summary call should compute and cache.
        summary_resp = self.client.get("/api/expenses/summary", headers=headers)
        self.assertEqual(summary_resp.status_code, 200)
        summary = summary_resp.get_json()["summary"]
        self.assertEqual(summary, [{"category": "rent", "total": 500.0}])

        cache_key = f"summary:{user_id}"
        self.assertIsNotNone(self.fake_redis.store.get(cache_key))

        # Add another expense; cache should be invalidated.
        create_resp = self.client.post(
            "/api/expenses",
            json={"category": "rent", "description": "Feb", "amount": 300},
            headers=headers,
        )
        self.assertEqual(create_resp.status_code, 201)
        self.assertIsNone(self.fake_redis.store.get(cache_key))

        # Next summary call should recompute and recache.
        summary_resp = self.client.get("/api/expenses/summary", headers=headers)
        self.assertEqual(summary_resp.status_code, 200)
        summary = summary_resp.get_json()["summary"]
        self.assertEqual(summary, [{"category": "rent", "total": 800.0}])
        self.assertIsNotNone(self.fake_redis.store.get(cache_key))


if __name__ == "__main__":
    unittest.main()
