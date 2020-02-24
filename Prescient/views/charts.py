from Prescient import db
from flask import (Blueprint, request,
                   render_template,
                   redirect,
                   url_for, session)
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

## THIS FUNCTION SHOULD BE SPLIT INTO TWO-THREE PARTS, intial, change watchlist, change security
# FYI in auth logout the session gets closed out and in auth login the session is created
    user_watchlists = get_group_names(user_id)
    if len(user_watchlists) == 0:
        watchlist_id = 0
        first_watchlist_name = None
        session["ATEST"] = None
    else:
        first_watchlist_name = user_watchlists[0]

        if session["ATEST"] is None:
            session["ATEST"] = first_watchlist_name

        watchlist_id = get_group_id(session.get('ATEST', None), user_id)

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

    print(session.get('ATEST', None))
    if form.validate_on_submit():
        watchlist_name = session.get('ATEST', None)
        watchlist_id = get_group_id(watchlist_name, user_id)

        obj = Security_Breakdown(user_id, watchlist_id)
        print(session.get('ATEST', None), "NOW ON SECURITY CHANGE")
        selection = form.ticker.data
        plot_data = obj.performance_table(selection)
        line_chart = plot_data
        breakdown = plot_data
        return render_template("charts/performance_breakdown.html", line_chart=line_chart, breakdown=breakdown, form=form, user_watchlists=user_watchlists, group_name=watchlist_name)

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
            session["ATEST"] = selection
            print(session.get('ATEST', None), "WATCHLIST_CHANGE")
            line_chart = plot_data
            breakdown = plot_data
            return render_template("charts/performance_breakdown.html", line_chart=line_chart, breakdown=breakdown, form=form, user_watchlists=user_watchlists, group_name=selection)

    line_chart = plot_data
    breakdown = plot_data

    print(session.get('ATEST', None), "Initial Launch")
    return render_template("charts/performance_breakdown.html", line_chart=line_chart, breakdown=breakdown, form=form, user_watchlists=user_watchlists, group_name=first_watchlist_name)
