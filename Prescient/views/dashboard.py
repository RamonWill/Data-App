from flask import (Blueprint,
                   render_template)
from flask_login import login_required, current_user
from Prescient.database_tools.Extracts import Portfolio_Performance, Portfolio_Summaries


bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def index():
    user_id = current_user.id
    line_chart = Portfolio_Performance(user_id).summed_table()
    chart_data = Portfolio_Summaries(user_id)
    summary = chart_data.summary_table()
    pie_chart = chart_data.get_pie_chart()
    bar_chart = chart_data.get_bar_chart()
    return render_template("securities/dashboard.html", summary=summary, line_chart=line_chart, pie_chart=pie_chart, bar_chart=bar_chart)
