import os
import unittest
import sys

topdir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(topdir)

from Prescient import app, db
from Prescient.config import basedir


# Integeration Tests
class WatchlistTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + \
                                                os.path.join(basedir,
                                                             'test.db')
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    # Helper methods to create dummy post requests and store to test database
    def register_user(self, username, password, confirm):
        credentials = dict(username=username,
                           password=password,
                           confirm=confirm)
        return self.app.post("auth/register",
                             data=credentials,
                             follow_redirects=True)

    def login_user(self, username, password):
        credentials = dict(username=username,
                           password=password)
        return self.app.post("auth/login",
                             data=credentials,
                             follow_redirects=True)

    def add_group(self, group_name):
        new_group = dict(name=group_name, user_id=999)
        return self.app.post("/create-group", data=new_group,
                             follow_redirects=True)

    def test_watchlist_urls(self):
        response_main_page = self.app.get("/main", follow_redirects=True)
        response_create_security = self.app.get("/create", follow_redirects=True)
        response_create_group = self.app.get("/create-group", follow_redirects=True)
        response_update = self.app.get("1/DIS/update", follow_redirects=True)

        self.assertEqual(response_main_page.status_code, 200)
        self.assertEqual(response_create_security.status_code, 200)
        self.assertEqual(response_create_group.status_code, 200)
        self.assertEqual(response_update.status_code, 200)

    def test_valid_group_creation(self):
        self.register_user("test_user1", "admin123", "admin123")
        self.login_user("test_user1", "admin123")
        response = self.add_group("RANDOM PORTFOLIO")
        self.assertIn(b"RANDOM PORTFOLIO", response.data)

    def test_invalid_group_creation(self):
        self.register_user("test_user1", "admin123", "admin123")
        self.login_user("test_user1", "admin123")
        response = self.add_group("")
        self.assertIn(b"Name: This field is required.", response.data)


if __name__ == "__main__":
    unittest.main()
