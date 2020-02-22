from Prescient import db
from datetime import datetime


class WatchlistItems(db.Model):
    __tablename__ = "watchlist_securities"
    id = db.Column(db.Integer, primary_key=True, index=True)
    watchlist = db.Column(db.String(), nullable=False)
    ticker = db.Column(db.String(), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    sector = db.Column(db.String(), nullable=False)
    created_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.Column(db.String())
    user_id = db.Column(db.Integer, db.ForeignKey("login_details.id", on_delete="CASCADE"), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("watchlist_group.id", on_delete="CASCADE"), nullable=False)

    def __repr__(self):
        return "<ID: {}, Ticker: {}>".format(self.id, self.ticker)


class Watchlist_Group(db.Model):
    __tablename__ = "watchlist_group"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("login_details.id", on_delete="CASCADE"), nullable=False)
    child = db.relationship("WatchlistItems", backref="watchlist_group", passive_deletes=True)

    def __repr__(self):
        return "<ID: {}, Watchlist Name: {}>".format(self.id, self.name)
