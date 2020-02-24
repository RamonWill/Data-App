from Prescient import db
from flask import (Blueprint, request,
                   render_template,
                   redirect,
                   url_for)
from flask_login import login_required, current_user
from Prescient.database_tools.Extracts import Security_Breakdown
from Prescient.forms import ChartForm
from Prescient.models import Watchlist_Group
from werkzeug.exceptions import abort

bp = Blueprint("charts", __name__)


def get_group_id(watchlist, user_id):
    group_id = Watchlist_Group.query.filter_by(name=watchlist, user_id=user_id).first()
    if group_id is None:
        abort(404, f"the ID for {watchlist} doesn't exist.")
    else:
        group_id = int(group_id.id)
        return group_id


def get_group_names(user_id):
    names = Watchlist_Group.query.filter_by(user_id=user_id).all()
    if names is None:
        return []
    else:
        names_list = [i.name for i in names]
        return names_list

@bp.route("/performance_breakdown", methods=("GET", "POST"))
@login_required
def chart_breakdown():
    # A line chart with performance. A chart with average price/ performance
    # breakdown
    user_id = current_user.id

    user_watchlists = get_group_names(user_id)
    if len(user_watchlists) == 0:
        watchlist_id = 0
    else:
        first_watchlist_name = user_watchlists[0]
        watchlist_id = get_group_id(first_watchlist_name, user_id)

    obj = Security_Breakdown(user_id, watchlist_id)
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
        return render_template("charts/performance_breakdown.html", line_chart=line_chart, breakdown=breakdown, form=form, user_watchlists=user_watchlists)

    if "btn_btn_default" in request.form:
        if request.method == 'POST':
            selection = request.form.get('watchlist_group_selection')
            selection_id = get_group_id(selection, user_id)
            obj = Security_Breakdown(user_id, selection_id)
            user_tickers = obj.get_tickers()
            if len(user_tickers) == 0:
                form = ChartForm()
                plot_data = []

            else:
                first_ticker = user_tickers[0][0]
                form = ChartForm(ticker=first_ticker)
                plot_data = obj.performance_table(first_ticker)
            form.ticker.choices = user_tickers

            line_chart = plot_data
            breakdown = plot_data
            return render_template("charts/performance_breakdown.html", line_chart=line_chart, breakdown=breakdown, form=form, user_watchlists=user_watchlists, group_name=selection)

    line_chart = plot_data
    breakdown = plot_data

    return render_template("charts/performance_breakdown.html", line_chart=line_chart, breakdown=breakdown, form=form, user_watchlists=user_watchlists, group_name=first_watchlist_name)
