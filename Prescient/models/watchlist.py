from Prescient import db
from datetime import datetime


class Watchlist(db.Model):
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
