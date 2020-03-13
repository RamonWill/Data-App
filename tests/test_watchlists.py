import os
import unittest
import sys

topdir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(topdir)

from Prescient import app, db
from Prescient.config import basedir

# integeration tests
class WatchlistTests(unittest.TestCase):
    def setUp(self):  # sets up the database
        app.config["TESTING"] = True  # must be True to test for assertions or exceptions in my app code
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + os.path.join(basedir, 'test.db')
        self.app = app.test_client()  # this creates a test client for the application
        db.create_all()

    def tearDown(self):  # removes the database
        db.session.remove()
        db.drop_all()

    # helper methods
    # Dummy post requests that get stored to the test database.
    # REMEMBER TO ADD THE GROUP FIRST. DO A TEST FOR THIS.
    def add_group(self, group_name):
        new_group = dict(name=group_name, user_id=999)
        return self.app.post("watchlist/create-group", data=new_group,
                             follow_redirects=True)

    def add_security(self, watchlist, ticker, quantity, price, sector, comments):
        trade_details = dict(watchlist=watchlist, name=ticker,
                             quantity=quantity, price=price,
                             sector=sector, comments=comments,
                             user_id=999, group_id=999)

        return self.app.post("watchlist/create", data=trade_details,
                             follow_redirects=True)

    def edit_security(self, watchlist, quantity, trade_date, price, sector, comments):
        trade_details = dict(watchlist=watchlist, quantity=quantity,
                             trade_date=trade_date, price=price,
                             sector=sector, comments=comments,
                             user_id=999, group_id=999)
        # check how to do get request for this
        return self.app.post("watchlist/update", data=trade_details,
                             follow_redirects=True)
        # credentials = dict(username=username,
        #                    password=password)
        # return self.app.post("auth/login",
        #                      data=credentials,
        #                      follow_redirects=True)

    def delete_security(self):
        # check how to do get request for this too
        return self.app.post("watchlist/delete", follow_redirects=True)

        # return self.app.get("auth/logout", follow_redirects=True)

    # integration tests
    def test_auth_urls(self):
        pass
        # response_login = self.app.get("auth/login", follow_redirects=True)
        # response_register = self.app.get("auth/register", follow_redirects=True)
        # response_logout = self.app.get("auth/logout", follow_redirects=True)
        # self.assertEqual(response_login.status_code, 200)
        # self.assertEqual(response_register.status_code, 200)
        # self.assertEqual(response_logout.status_code, 200)

    def test_valid_user_registration(self):
        pass
        # response = self.register_user("RandomUser1!",
        #                               "Testing123",
        #                               "Testing123")
        # self.assertIn(b"Your account has now been created!", response.data)

    def test_invalid_user_registration_wrong_confirm(self):
        pass
        # response = self.register_user("RandomUser1!", "Testing123", "Testing321")
        # self.assertIn(b"Passwords must match", response.data)

    def test_invalid_user_registration_duplicate_username(self):
        pass
        # response = self.register_user("RandomUser2",
        #                               "python99",
        #                               "python99")
        # response = self.register_user("RandomUser2",
        #                               "python11",
        #                               "python11")
        # self.assertIn(b"That username is already registered.", response.data)

    def test_valid_login(self):
        pass
        # self.register_user("RandomUser1!", "Testing123", "Testing123")
        # response = self.login_user("RandomUser1!", "Testing123")
        # self.assertIn(b"Welcome to Prescient Finance", response.data)

    def test_invalid_login_wrong_username(self):
        pass
        # self.register_user("RandomUser1!", "Testing123", "Testing123")
        # response = self.login_user("randomuser1!", "Testing123")
        # self.assertNotIn(b"Welcome to Prescient Finance", response.data)

    def test_invalid_login_wrong_password(self):
        pass
        # self.register_user("RandomUser1!", "Testing123", "Testing123")
        # response = self.login_user("RandomUser1!", "Testing456")
        # self.assertNotIn(b"Welcome to Prescient Finance", response.data)

    def test_logout(self):
        pass
        # self.register_user("RandomUser1!", "Testing123", "Testing123")
        # self.login_user("RandomUser1!", "Testing123")
        # response = self.logout_user()
        # self.assertIn(b"Sign In", response.data)


if __name__ == "__main__":
    unittest.main()
