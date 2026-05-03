import os
import sys
import tempfile
import unittest

os.environ["DB_PATH"] = os.path.join(tempfile.gettempdir(), "test_bot.db")
os.environ.setdefault("TELEGRAM_TOKEN", "test")
os.environ.setdefault("ADMIN_BOT_TOKEN", "test")
os.environ.setdefault("OPENROUTER_API_KEY", "test")
os.environ.setdefault("ADMIN_TELEGRAM_IDS", "12345")
os.environ.setdefault("VOSK_MODEL_PATH", "/tmp/vosk")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import init_db
from db.queries import (
    get_or_create_user, save_message, get_history,
    get_summary, update_summary, get_all_users,
)


class TestDatabase(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_create_user(self):
        uid = get_or_create_user(999001, "Test User")
        self.assertIsInstance(uid, int)
        uid2 = get_or_create_user(999001, "Test User")
        self.assertEqual(uid, uid2)

    def test_save_and_get_messages(self):
        uid = get_or_create_user(999002, "User2")
        save_message(uid, "user", "Привет, бот!")
        save_message(uid, "assistant", "Привет! Расскажи мне о своей ситуации.")
        history = get_history(uid, limit=10)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")

    def test_summary(self):
        uid = get_or_create_user(999003, "User3")
        self.assertIsNone(get_summary(uid))
        update_summary(uid, "Пользователь обсуждал сложные отношения на работе.")
        summary = get_summary(uid)
        self.assertIsNotNone(summary)
        self.assertIn("работе", summary)

    def test_get_all_users(self):
        get_or_create_user(999004, "User4")
        users = get_all_users()
        self.assertGreater(len(users), 0)

    def tearDown(self):
        db_path = os.environ["DB_PATH"]
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    unittest.main()
