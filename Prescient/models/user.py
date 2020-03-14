from Prescient import db
from Prescient import login
from flask_login import UserMixin


class User (UserMixin, db.Model):
    __tablename__ = "login_details"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(25), index=True, unique=True, nullable=False)
    password = db.Column(db.String(257), nullable=False)
    child1 = db.relationship('Watchlist_Group', backref='login_details', passive_deletes=True)
    child2 = db.relationship('WatchlistItems', backref='login_details', passive_deletes=True)

    def __repr__(self):
        return "<Username {}>".format(self.username)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
