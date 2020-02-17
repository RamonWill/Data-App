from Prescient import db
from Prescient import login
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
