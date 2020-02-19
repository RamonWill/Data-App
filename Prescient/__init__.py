from flask import Flask
from .config import Config

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager(app)
login.login_view = "auth.login"

from . import views
from . import models


app.register_blueprint(views.auth.bp)
app.register_blueprint(views.dashboard.bp)
app.add_url_rule("/", endpoint="dashboard")
app.register_blueprint(views.watchlist.bp)
app.register_blueprint(views.charts.bp)
