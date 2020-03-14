from Prescient import db


class Available_Securities(db.Model):
    __tablename__ = "available_securities"
    name = db.Column(db.String(70))
    ticker = db.Column(db.String(20), primary_key=True)
    country = db.Column(db.String(40))
    benchmark_index = db.Column(db.String(30))
    ISO_alpha3_codes = db.Column(db.String(3))

    def __repr__(self):
        return "<Security Name: {}, Group Name: {}, Country: {}>".format(self.name, self.ticker, self.country)


class Sector_Definitions(db.Model):
    __tablename__ = "sector_definitions"
    name = db.Column(db.String(70), nullable=False, primary_key=True, index=True)

    def __repr__(self):
        return "<Sector Name: {}>".format(self.name)
