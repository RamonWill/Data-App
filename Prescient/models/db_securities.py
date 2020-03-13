from Prescient import db


class Available_Securities(db.Model):
    __tablename__ = "available_securities"
    name = db.Column(db.String())
    ticker = db.Column(db.String(), primary_key=True)
    country = db.Column(db.String())
    benchmark_index = db.Column(db.String())
    ISO_alpha3_codes = db.Column(db.String(3))

    def __repr__(self):
        return "<Security Name: {}, Group Name: {}, Country: {}>".format(self.name, self.ticker, self.country)


class Sector_Definitions(db.Model):
    __tablename__ = "sector_definitions"
    name = db.Column(db.String(), nullable=False, primary_key=True, index=True)

    def __repr__(self):
        return "<Sector Name: {}>".format(self.name)
