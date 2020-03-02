from Prescient import db, app
from flask import (Blueprint, flash, redirect,
                   render_template, url_for, request)
from werkzeug.exceptions import abort
from flask_login import login_required, current_user
from Prescient.forms import WatchlistItemsForm, WatchlistGroupForm
from Prescient.models import WatchlistItems, Sector_Definitions, Watchlist_Group
from Prescient.database_tools.New_Prices import Price_Update
from Prescient.database_tools.Extracts import PositionSummary
from sqlalchemy.sql import func
import sqlite3

bp = Blueprint("watchlist", __name__)


def update_db_prices(ticker):
    # check the tables. If the ticker doesnt exist get the price from AV and create a new table
    conn = sqlite3.connect(r"C:\Users\Owner\Documents\Data-App\Prescient\Security_PricesDB.db")
    c = conn.cursor()

    query = """SELECT name FROM sqlite_master
    WHERE type='table'and name=:ticker
    ORDER BY name;
    """
    param = {"ticker": ticker}
    tables = c.execute(query, param).fetchone()
    c.close()
    conn.close()

    if tables is None:
        obj = Price_Update(ticker)
        obj.import_prices()
    else:
        print(f"{ticker} already exists")


def get_sectors():
    sectors = Sector_Definitions.query.all()
    sectors_list = [(s.name, s.name) for s in sectors]
    return sectors_list


def get_group_names1(user_id):
    # returns list of items
    names = Watchlist_Group.query.filter_by(user_id=user_id).all()
    if names is None:
        return []
    else:
        names_list = [i.name for i in names]
        return names_list

def get_group_names2(user_id):
    # returns list of tuples
    names = Watchlist_Group.query.filter_by(user_id=user_id).all()
    if names is None:
        return []
    else:
        names_list = [(i.name, i.name) for i in names]
        return names_list

def get_group_id(watchlist, user_id):
    group_id = Watchlist_Group.query.filter_by(name=watchlist, user_id=user_id).first()
    if group_id is None:
        abort(404, f"the ID for {watchlist} doesn't exist.")
    else:
        group_id = int(group_id.id)
        return group_id


def get_tickers(user_id, group_id):
    params = {"user_id": user_id, "group_id": group_id}
    tickers = WatchlistItems.query.\
              with_entities(WatchlistItems.ticker).\
              filter_by(**params).\
              order_by(WatchlistItems.created_timestamp).\
              distinct(WatchlistItems.ticker).all()

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



def check_watchlist_id(id, check_holder=True):
    info = WatchlistItems.query.filter_by(id=id).first()
    if info is None:
        abort(404, f"Order ID {id} doesn't exist.")
    if info.user_id != current_user.id:
        abort(403)
    return True


@bp.route("/main", methods=('GET', 'POST'))
@login_required
def main():
    user_id = current_user.id

    user_watchlists = get_group_names1(user_id)
    if len(user_watchlists) == 0:
        watchlist_id = 0
        first_watchlist_name=None
    else:
        first_watchlist_name = user_watchlists[0]
        watchlist_id = get_group_id(first_watchlist_name, user_id)
    form = WatchlistItemsForm()
    form.sector.choices = get_sectors()
    form.watchlist.choices = get_group_names2(user_id)
    if request.method == "POST":
        selection = request.form.get('watchlist_group_selection')
        selection_id = get_group_id(selection, user_id)
        summary = get_position_summary(user_id, selection_id)
        watchlist = WatchlistItems.query.filter_by(user_id=user_id, group_id=selection_id)  # this is good because it defaults to an empty list
        group_form = WatchlistGroupForm()
        return render_template("watchlist/main.html", watchlist=watchlist, summary=summary, form=form, group_form=group_form, user_watchlists=user_watchlists, group_name=selection)
    # in the watchlist variable  filter by watchlist_id too. user can choose watchlist id. sumary table should also take this into account.
    watchlist = WatchlistItems.query.filter_by(user_id=user_id, group_id=watchlist_id)  # this is good because it defaults to an empty list

    summary = get_position_summary(user_id, watchlist_id)

    group_form = WatchlistGroupForm()

    return render_template("watchlist/main.html", watchlist=watchlist, summary=summary, form=form, group_form=group_form, user_watchlists=user_watchlists, group_name=first_watchlist_name)

@bp.route('/create-group', methods=('GET', 'POST'))
@login_required
def create_group():
    group_form = WatchlistGroupForm()
    if group_form.validate_on_submit():
        name = group_form.name.data
        user_id = current_user.id
        new_group = Watchlist_Group(name=name, user_id=user_id)
        db.session.add(new_group)
        db.session.commit()
        flash(f"The Watchlist group '{name}' has been created!")
        return redirect(url_for("watchlist.main"))

    return redirect(url_for("watchlist.main"))


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    form = WatchlistItemsForm()
    form.sector.choices = get_sectors()
    form.watchlist.choices = get_group_names2(current_user.id)

    if form.validate_on_submit():
        watchlist = form.watchlist.data
        name = form.ticker.data
        quantity = form.quantity.data
        price = form.price.data
        sector = form.sector.data
        comments = form.comments.data
        user_id = current_user.id
        group_id = get_group_id(watchlist, user_id)
        new_item = WatchlistItems(watchlist=watchlist, ticker=name, quantity=quantity,
                             price=price, sector=sector,
                             comments=comments, user_id=user_id, group_id=group_id)
        db.session.add(new_item)
        db.session.commit()
        update_db_prices(name)
        flash(f"{name} has been added to your watchlist")
        return redirect(url_for("watchlist.main"))
        # Follow the registration view
        # I will also need one function to get the sectors
    return redirect(url_for("watchlist.main"))
    #return render_template("watchlist/main.html", form=form)

@bp.route('/<int:id>/<ticker>/update', methods=('GET', 'POST'))
@login_required
def update(id, ticker):
    user_id = current_user.id
    check = check_watchlist_id(id)
    form = WatchlistItemsForm()
    group_form = WatchlistGroupForm()
    form.sector.choices = get_sectors()
    form.watchlist.choices = get_group_names2(user_id)
    if form.validate_on_submit() and check:
        new_watchlist = form.watchlist.data
        new_quantity = form.quantity.data
        new_price = form.price.data
        new_sector = form.sector.data
        new_comment = form.comments.data
        new_group_id = get_group_id(new_watchlist, user_id)
        item = WatchlistItems.query.filter_by(id=id, user_id=user_id).first()
        item.ticker = ticker
        item.watchlist = new_watchlist
        item.quantity = new_quantity
        item.price = new_price
        item.sector = new_sector
        item.comments = new_comment
        item.group_id = new_group_id
        db.session.commit()
        flash(f"Order ID {id} has now been updated")
        return redirect(url_for("watchlist.main"))

    return render_template("watchlist/main.html", form=form, group_form=group_form)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    check = check_watchlist_id(id)
    user_id = current_user.id
    if check:
        item = WatchlistItems.query.filter_by(id=id, user_id=user_id).first()
        db.session.delete(item)
        db.session.commit()
        return redirect(url_for('watchlist.main'))
    return redirect(url_for('watchlist.main'))

## To get data from the DB its
# x = pd. read_sql(sql=query, con=db.engine)
# to get mainDB db.engine
# to get pricesDB db.get_engine(app, "Security_PricesDB")
#ive tested this in terminal and it works
