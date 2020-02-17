from Prescient import db
from Prescient import login
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin


class User (UserMixin, db.Model):
    __tablename__ = "login_details"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(25), index=True, unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return "<User {}>".format(self.username)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Watchlist (db.Model):
    __tablename__ = "watchlist_securities"
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    sector = db.Column(db.String(), nullable=False)
    created_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.Column(db.String())
    user_id = db.Column(db.Integer, db.ForeignKey("login_details.id"), nullable=False)

    def __repr__(self):
        return "<ID {}, Ticker{}>".format(self.id, self.ticker)
