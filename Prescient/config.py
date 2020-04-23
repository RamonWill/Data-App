import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """docstring for Config."""
    # General Configurations
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev"

    # Database Configurations
    SQLALCHEMY_DATABASE_URI = "mysql://root:E6#hK-rA5!tn@localhost/prescientmaindb"
    SQLALCHEMY_BINDS = {"Security_PricesDB": ("mysql://root:E6#hK-rA5!tn@localhost/prescientpricesdb")}
    SQLALCHEMY_TRACK_MODIFICATIONS = False
