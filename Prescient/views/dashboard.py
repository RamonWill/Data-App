from flask import (Blueprint,
                   render_template,
                   request, redirect,url_for)
from flask_login import login_required, current_user
from werkzeug.exceptions import abort
from Prescient.database_tools.Extracts import Portfolio_Performance, Portfolio_Summaries, PositionSummary
from Prescient.forms import WatchlistGroupForm
from Prescient.models import Watchlist_Group, WatchlistItems
from sqlalchemy.sql import func
bp = Blueprint("dashboard", __name__)

## DELETE SOON
import plotly
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import json
## DELETE SOON

def worldmap(user_id, group_id):
    conn = sqlite3.connect(r"C:\Users\Owner\Documents\Data-App\Prescient\MainDB.db")
    query = """Select COUNT(DISTINCT a.ticker) as 'No. of Positions', b.country as 'Country', b.ISO_alpha3_codes as 'ISO Code'
    from watchlist_securities a, available_securities b
    where b.ticker=a.ticker and user_id=:user_id and group_id=:group_id
    GROUP BY b.ticker
    HAVING SUM(a.quantity)<>0
    """
    params = {"user_id": user_id, "group_id":group_id}

    df = pd.read_sql_query(query, conn, params=params)
    df = df.groupby(["Country", "ISO Code"]).count().reset_index()
    fig = dict(data=[go.Choropleth(locations=df["ISO Code"],
                                   z=df["No. of Positions"],
                                   text=df["Country"],
                                   colorscale="dense")],
                                   layout=dict(title="No. of Positions by Country",
                                               scene=dict(bgcolor='rgb(23,4,55)'),
                                                          paper_bgcolor='rgba(0,0,0,0)',
                                               font=dict(size = 20,
                                                         color = "#FFFFFF")))


    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

def get_group_names(user_id):
    names = Watchlist_Group.query.filter_by(user_id=user_id).all()
    if names is None:
        return []
    else:
        names_list = [i.name for i in names]
        return names_list


def get_tickers(user_id, group_id):
    params = {"user_id": user_id, "group_id": group_id}
    tickers = WatchlistItems.query.\
              with_entities(WatchlistItems.ticker).\
              filter_by(**params).\
              order_by(WatchlistItems.created_timestamp).\
              distinct(WatchlistItems.ticker).all()
    print(user_id, group_id)
    print([item.ticker for item in tickers])
    return [item.ticker for item in tickers]


def get_position_summary(user_id, group_id):
    all_tickers = get_tickers(user_id, group_id)
    params = {"user_id": user_id, "group_id": group_id}
    all_trades = WatchlistItems.query.with_entities(WatchlistItems.ticker, WatchlistItems.quantity, WatchlistItems.price, func.date(WatchlistItems.created_timestamp).label("date")).filter_by(**params).order_by(WatchlistItems.created_timestamp)
    summary_table = []
    for ticker in all_tickers:
        trade_history = [trade for trade in all_trades if trade.ticker == ticker]
        summary = PositionSummary(trade_history, ticker).get_summary()
        if summary.quantity != 0:
            summary_table.append(summary)
    return summary_table

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
        first_watchlist_name=None
    else:
        first_watchlist_name = user_watchlists[0]
        watchlist_id = get_group_id(first_watchlist_name, user_id)

    if request.method == "POST":
        selection = request.form.get('watchlist_group_selection')
        selection_id = get_group_id(selection, user_id)
        summary = get_position_summary(user_id, selection_id)
        if len(summary) > 7:
            summary = summary[0:7]
        user_details = Portfolio_Performance(user_id, selection_id)
        map = worldmap(user_id, selection_id)
        line_chart = user_details.summed_table()
        pie_chart = user_details.get_pie_chart()
        bar_chart = user_details.get_bar_chart()
        return render_template("securities/dashboard.html", summary=summary, line_chart=line_chart, pie_chart=pie_chart, bar_chart=bar_chart, user_watchlists=user_watchlists, group_name=selection, map=map)

    summary = get_position_summary(user_id, watchlist_id)
    if len(summary) > 7:
        summary = summary[0:7]
    user_details = Portfolio_Performance(user_id, watchlist_id)
    line_chart = user_details.summed_table()
    pie_chart = user_details.get_pie_chart()
    bar_chart = user_details.get_bar_chart()
    map = worldmap(user_id, watchlist_id)
    return render_template("securities/dashboard.html", summary=summary, line_chart=line_chart, pie_chart=pie_chart, bar_chart=bar_chart, user_watchlists=user_watchlists, group_name=first_watchlist_name, map=map)
