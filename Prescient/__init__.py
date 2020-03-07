from flask import Flask, session
from .config import Config
from datetime import timedelta

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager(app)
login.login_view = "auth.login"
login.refresh_view = "auth.login"
login.needs_refresh_message = (u"Your Session timedout, please re-login")
login.needs_refresh_message_category = "info"

from . import views
from . import models


app.register_blueprint(views.auth.bp)
app.register_blueprint(views.dashboard.bp)
app.add_url_rule("/", endpoint="dashboard")
app.register_blueprint(views.watchlist.bp)
app.register_blueprint(views.charts.bp)

# before a request is made check if session should be timedout
@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=10)
