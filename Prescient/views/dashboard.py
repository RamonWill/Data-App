from Prescient import db, app
from flask import (Blueprint,
                   render_template,
                   request)
from flask_login import login_required, current_user
from werkzeug.exceptions import abort
from sqlalchemy.sql import func
from sqlalchemy.orm import aliased
import plotly
import plotly.graph_objects as go
import json
from Prescient.database_tools.Extracts import (Portfolio_Summary,
                                               PositionSummary,
                                               DashboardCharts)
from Prescient.models import (Watchlist_Group, WatchlistItems,
                              Available_Securities)
import mysql.connector

bp = Blueprint("dashboard", __name__)


def get_worldmap(user_id, group_id):
    params = {"user_id": user_id, "group_id": group_id}
    w = aliased(WatchlistItems)
    s = aliased(Available_Securities)
    map_data = db.session.query(WatchlistItems, Available_Securities).\
               with_entities(func.count(w.ticker.distinct()).label("No. of Positions"), s.country.label("Country"), s.ISO_alpha3_codes.label("ISO Code")).\
               filter(s.ticker == w.ticker).\
               filter_by(**params).\
               group_by(s.ticker).\
               having(func.sum(w.quantity) != 0)
    map_dataframe = DashboardCharts.worldmap(map_data)

    fig = dict(data=[go.Choropleth(locations=map_dataframe["ISO Code"],
                                   z=map_dataframe["No. of Positions"],
                                   text=map_dataframe["Country"],
                                   colorscale="dense")],
                                   layout=dict(title="No. of Positions by Country",
                                               scene=dict(bgcolor='rgb(23,4,55)'),
                                               paper_bgcolor='rgba(0,0,0,0)',
                                               font=dict(size=20,
                                                         color="#FFFFFF")))

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
              order_by(WatchlistItems.trade_date).\
              distinct(WatchlistItems.ticker).all()

    return [item.ticker for item in tickers]


def get_trade_histroy(user_id, group_id, ticker):
    params = {"user_id": user_id, "group_id": group_id, "ticker": ticker}
    all_trades = WatchlistItems.query.\
                 with_entities(WatchlistItems.ticker, WatchlistItems.quantity, WatchlistItems.price, func.date(WatchlistItems.trade_date).label("date")).\
                 filter_by(**params).\
                 order_by(WatchlistItems.trade_date).all()
    return all_trades


def get_flows(user_id, group_id):
    params = {"user_id": user_id, "group_id": group_id}
    w = aliased(WatchlistItems)
    flows = WatchlistItems.query.\
            with_entities(func.date(w.trade_date).label("index"), func.sum(w.quantity*w.price*-1).label("flows")).\
            filter_by(**params).\
            group_by(func.date(w.trade_date)).\
            order_by(w.trade_date).all()
    return flows


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


def get_position_summary(user_id, group_id):
    all_tickers = get_tickers(user_id, group_id)
    params = {"user_id": user_id, "group_id": group_id}
    all_trades = WatchlistItems.query.\
                 with_entities(WatchlistItems.ticker, WatchlistItems.quantity, WatchlistItems.price, func.date(WatchlistItems.trade_date).label("date")).\
                 filter_by(**params).\
                 order_by(WatchlistItems.trade_date)
    summary_table = []
    for ticker in all_tickers:
        trade_history = [trade for trade in all_trades if trade.ticker == ticker]
        summary = PositionSummary(trade_history, ticker).get_summary()
        if summary.quantity != 0:
            summary_table.append(summary)

    if len(summary_table) > 7:
        summary_table = summary_table[0:7]
    return summary_table


def get_portfolio_summary(user_id, group_id):
    Portfolio = Portfolio_Summary()
    tickers = get_tickers(user_id, group_id)
    for ticker in tickers:
        prices = get_market_prices(ticker)
        trades = get_trade_histroy(user_id, group_id, ticker)
        Portfolio.add_position(prices, trades, ticker)
    return Portfolio


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
    flows = get_flows(user_id, watchlist_id)
    if request.method == "POST":
        selection = request.form.get('watchlist_group_selection')
        selection_id = get_group_id(selection, user_id)
        flows = get_flows(user_id, selection_id)
        summary = get_position_summary(user_id, selection_id)

        Portfolio = get_portfolio_summary(user_id, selection_id)
        portfolio_breakdown = Portfolio.portfolio_breakdown
        portfolio_performance = Portfolio.generate_hpr(flows)
        Charts = DashboardCharts()
        pie_chart = Charts.get_pie_chart(portfolio_breakdown)
        bar_chart = Charts.get_bar_chart(portfolio_breakdown)
        map = get_worldmap(user_id, selection_id)
        line_chart = portfolio_performance
        content = {"summary": summary, "line_chart": line_chart,
                   "pie_chart": pie_chart, "bar_chart": bar_chart,
                   "user_watchlists": user_watchlists, "map": map,
                   "group_name": selection}

        return render_template("securities/dashboard.html", **content)

    summary = get_position_summary(user_id, watchlist_id)

    Portfolio = get_portfolio_summary(user_id, watchlist_id)
    portfolio_breakdown = Portfolio.portfolio_breakdown
    Charts = DashboardCharts()
    pie_chart = Charts.get_pie_chart(portfolio_breakdown)
    bar_chart = Charts.get_bar_chart(portfolio_breakdown)
    portfolio_performance = Portfolio.generate_hpr(flows)

    line_chart = portfolio_performance

    map = get_worldmap(user_id, watchlist_id)
    content = {"summary": summary, "line_chart": line_chart,
               "pie_chart": pie_chart, "bar_chart": bar_chart,
               "user_watchlists": user_watchlists, "map": map,
               "group_name": first_watchlist_name}
    return render_template("securities/dashboard.html", **content)
