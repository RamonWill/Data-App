from flask import (Blueprint,
                   render_template,
                   request, redirect,url_for)
from flask_login import login_required, current_user
from werkzeug.exceptions import abort
from Prescient.database_tools.Extracts import Portfolio_Performance, Portfolio_Summaries
from Prescient.forms import WatchlistGroupForm
from Prescient.models import Watchlist_Group

bp = Blueprint("dashboard", __name__)


def get_group_names(user_id):
    names = Watchlist_Group.query.filter_by(user_id=user_id).all()
    if names is None:
        return []
    else:
        names_list = [i.name for i in names]
        return names_list


def get_group_id(watchlist, user_id):
    group_id = Watchlist_Group.query.filter_by(name=watchlist, user_id=user_id).first()
    if group_id is None:
        abort(404, f"the ID for {watchlist} doesn't exist.")
    else:
        group_id = int(group_id.id)
        return group_id


@bp.route("/", methods=('GET', 'POST'))
@login_required
def index():
    user_id = current_user.id

    user_watchlists = get_group_names(user_id)
    if len(user_watchlists) == 0:
        watchlist_id = 0

    else:
        first_watchlist_name = user_watchlists[0]
        watchlist_id = get_group_id(first_watchlist_name, user_id)

    if request.method == "POST":
        selection = request.form.get('watchlist_group_selection')
        selection_id = get_group_id(selection, user_id)
        summary = Portfolio_Summaries(user_id, selection_id).summary_table()
        user_details = Portfolio_Performance(user_id, selection_id)
        line_chart = user_details.summed_table()
        pie_chart = user_details.get_pie_chart()
        bar_chart = user_details.get_bar_chart()
        return render_template("securities/dashboard.html", summary=summary, line_chart=line_chart, pie_chart=pie_chart, bar_chart=bar_chart, user_watchlists=user_watchlists, group_name=selection)

    summary = Portfolio_Summaries(user_id, watchlist_id).summary_table()
    user_details = Portfolio_Performance(user_id, watchlist_id)
    line_chart = user_details.summed_table()
    pie_chart = user_details.get_pie_chart()
    bar_chart = user_details.get_bar_chart()
    return render_template("securities/dashboard.html", summary=summary, line_chart=line_chart, pie_chart=pie_chart, bar_chart=bar_chart, user_watchlists=user_watchlists, group_name=first_watchlist_name)
