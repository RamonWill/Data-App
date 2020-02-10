import os
from flask import Flask

# views
from . import db
from . import auth
from . import dashboard
from . import watchlist


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY="dev",
                            DATABASE=os.path.join(app.instance_path, "MainDB.sqlite"),)

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.add_url_rule("/", endpoint="dashboard")
    app.register_blueprint(watchlist.bp)


    @app.route("/test")
    def test_page():
        return "THIS IS A TEST PAGE"

    return app
