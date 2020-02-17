from flask import (Blueprint,
                   render_template,
                   redirect,
                   url_for)
from flask_login import login_required, current_user


bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def index():
    line_chart = []
    table1 = []
    pie_chart = []
    bar_chart = []
    return render_template("securities/dashboard.html", table1=table1, line_chart=line_chart, pie_chart=pie_chart, bar_chart=bar_chart)
