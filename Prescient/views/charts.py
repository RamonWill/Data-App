from Prescient import db, app
from flask import (Blueprint, request,
                   render_template,
                   session)
from flask_login import login_required, current_user
from Prescient.database_tools.Extracts import PositionAccounting
from Prescient.forms import ChartForm
from Prescient.models import Watchlist_Group, WatchlistItems
from sqlalchemy.sql import func
import mysql.connector

bp = Blueprint("charts", __name__)


def get_group_id(watchlist, user_id):
    group_id = Watchlist_Group.query.filter_by(name=watchlist, user_id=user_id).first()
    if group_id is None:
        return None
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


def get_tickers(user_id, group_id):
    params = {"user_id": user_id, "group_id": group_id}
    tickers = WatchlistItems.query.\
              with_entities(WatchlistItems.ticker).\
              filter_by(**params).\
              order_by(WatchlistItems.ticker).\
              distinct(WatchlistItems.ticker).all()

    return [(item.ticker, item.ticker) for item in tickers]


def get_market_prices(ticker):
    mydb = mysql.connector.connect(host="localhost",
                                   user="root",
                                   passwd="E6#hK-rA5!tn",
                                   database="prescientpricesdb")
    c = mydb.cursor()
    query = f"SELECT * FROM `{ticker}`"
    c.execute(query)
    prices = c.fetchall()
    c.close()
    mydb.close()
    return prices


def get_trade_histroy(user_id, group_id, ticker):
    params = {"user_id": user_id, "group_id": group_id, "ticker": ticker}
    all_trades = WatchlistItems.query.\
                 with_entities(WatchlistItems.ticker, WatchlistItems.quantity, WatchlistItems.price, func.date(WatchlistItems.trade_date).label("date")).\
                 filter_by(**params).\
                 order_by(WatchlistItems.trade_date).all()
    return all_trades


def get_performance(user_id, group_id, ticker):
    prices = get_market_prices(ticker)
    trade_history = get_trade_histroy(user_id, group_id, ticker)
    Performance = PositionAccounting(prices, trade_history, ticker)
    performance_table = Performance.performance_table()
    return performance_table


@bp.route("/performance_breakdown", methods=("GET", "POST"))
@login_required
def chart_breakdown():
    # A line chart with performance.
    user_id = current_user.id

    # Sets the first watchlist group as the selection to display
    user_watchlists = get_group_names(user_id)
    if len(user_watchlists) == 0:
        watchlist_id = 0
        first_watchlist_name = None
        session["ATEST"] = None
    else:
        first_watchlist_name = user_watchlists[0]

    if session["ATEST"] is None or session["ATEST"] == first_watchlist_name:
        session["ATEST"] = first_watchlist_name
    else:
        first_watchlist_name = session["ATEST"]

    watchlist_id = get_group_id(session.get('ATEST', None), user_id)

    user_tickers = get_tickers(user_id, watchlist_id)

    # Sets the first ticker as the selection to display
    if len(user_tickers) == 0:
        form = ChartForm()
        plot_data = []
        first_ticker = None
    else:
        first_ticker = user_tickers[0][0]
        form = ChartForm(ticker=first_ticker)
        plot_data = get_performance(user_id, watchlist_id, first_ticker)
    form.ticker.choices = user_tickers

    # POST REQUEST for ticker data
    if form.validate_on_submit():
        watchlist_name = session.get('ATEST', None)
        watchlist_id = get_group_id(watchlist_name, user_id)

        selection = form.ticker.data
        plot_data = get_performance(user_id, watchlist_id, selection)
        line_chart = plot_data
        breakdown = plot_data
        content = {"line_chart": line_chart, "breakdown": breakdown,
                   "form": form,
                   "user_watchlists": user_watchlists,
                   "group_name": watchlist_name,
                   "selected_ticker": selection}
        return render_template("charts/performance_breakdown.html", **content)

    # POST REQUEST for watchlist group
    if "btn_btn_default" in request.form:
        if request.method == 'POST':
            selection = request.form.get('watchlist_group_selection')
            selection_id = get_group_id(selection, user_id)
            user_tickers = get_tickers(user_id, selection_id)
            if len(user_tickers) == 0:
                form = ChartForm()
                plot_data = []

            else:
                first_ticker = user_tickers[0][0]
                form = ChartForm(ticker=first_ticker)
                plot_data = get_performance(user_id, selection_id, first_ticker)
            form.ticker.choices = user_tickers
            session["ATEST"] = selection
            line_chart = plot_data
            breakdown = plot_data
            content = {"line_chart": line_chart, "breakdown": breakdown,
                       "form": form,
                       "user_watchlists": user_watchlists,
                       "group_name": selection,
                       "selected_ticker": first_ticker}
            return render_template("charts/performance_breakdown.html", **content)

    line_chart = plot_data
    breakdown = plot_data
    content = {"line_chart": line_chart, "breakdown": breakdown,
               "form": form,
               "user_watchlists": user_watchlists,
               "group_name": first_watchlist_name,
               "selected_ticker": first_ticker}
    return render_template("charts/performance_breakdown.html", **content)
