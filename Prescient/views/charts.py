from Prescient import db
from flask import (Blueprint,
                   render_template,
                   redirect,
                   url_for)
from flask_login import login_required, current_user
from Prescient.database_tools.Extracts import Security_Breakdown
from Prescient.forms import ChartForm

bp = Blueprint("charts", __name__)


@bp.route("/performance_breakdown", methods=("GET", "POST"))
@login_required
def chart_breakdown():
    # A line chart with performance. A chart with average price/ performance
    # breakdown
    user_id = current_user.id
    obj = Security_Breakdown(user_id)
    user_tickers = obj.get_tickers()

    if len(user_tickers) == 0:
        form = ChartForm()
        plot_data = []

    else:
        first_ticker = user_tickers[0][0]
        form = ChartForm(ticker=first_ticker)
        plot_data = obj.performance_table(first_ticker)
    form.ticker.choices = user_tickers

    if form.validate_on_submit():
        selection = form.ticker.data
        plot_data = obj.performance_table(selection)
        line_chart = plot_data
        breakdown = plot_data
        return redirect(url_for("charts.chart_breakdown", line_chart=line_chart, breakdown=breakdown, form=form))

    line_chart = plot_data
    breakdown = plot_data

    return render_template("charts/performance_breakdown.html", line_chart=line_chart, breakdown=breakdown, form=form)
