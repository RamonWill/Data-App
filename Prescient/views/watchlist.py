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
import mysql.connector

bp = Blueprint("watchlist", __name__)


def update_db_prices(ticker):
    # check the tables. If the ticker doesnt exist get the price from AV and create a new table
    mydb = mysql.connector.connect(host="localhost",
                                   user="root",
                                   passwd="E6#hK-rA5!tn",
                                   database="prescientpricesdb")
    c = mydb.cursor()
    query = """SELECT table_name
               FROM information_schema.tables
               WHERE table_name=%s
               ORDER BY table_name"""
    param = (ticker,)
    print(query)
    c.execute(query, param)
    tables = c.fetchone()
    c.close()
    mydb.close()

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


def get_watchlist_choices(user_id):
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
              order_by(WatchlistItems.trade_date).\
              distinct(WatchlistItems.ticker).all()

    return [item.ticker for item in tickers]


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
        first_watchlist_name = None
    else:
        first_watchlist_name = user_watchlists[0]
        watchlist_id = get_group_id(first_watchlist_name, user_id)
    form = WatchlistItemsForm()
    form.sector.choices = get_sectors()
    form.watchlist.choices = get_watchlist_choices(user_id)
    if request.method == "POST":
        selection = request.form.get('watchlist_group_selection')
        selection_id = get_group_id(selection, user_id)
        summary = get_position_summary(user_id, selection_id)
        watchlist = WatchlistItems.query.filter_by(user_id=user_id, group_id=selection_id)
        group_form = WatchlistGroupForm()
        content = {"watchlist": watchlist, "summary": summary, "form": form,
                   "group_form": group_form, "group_name": selection,
                   "user_watchlists": user_watchlists}
        return render_template("watchlist/main.html", **content)

    watchlist = WatchlistItems.query.filter_by(user_id=user_id, group_id=watchlist_id)
    summary = get_position_summary(user_id, watchlist_id)
    group_form = WatchlistGroupForm()
    content = {"watchlist": watchlist, "summary": summary, "form": form,
               "group_form": group_form, "user_watchlists": user_watchlists,
               "group_name": first_watchlist_name}
    return render_template("watchlist/main.html", **content)


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
    elif group_form.errors:
        for error_name, error_desc in group_form.errors.items():
            error_name = error_name.title()
            flash(f"{error_name}: {error_desc[0]}")
    return redirect(url_for("watchlist.main"))


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    form = WatchlistItemsForm()
    form.sector.choices = get_sectors()
    form.watchlist.choices = get_watchlist_choices(current_user.id)

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
    elif form.errors:
        for error_name, error_desc in form.errors.items():
            error_name = error_name.title()
            flash(f"{error_name}: {error_desc[0]}")

    return redirect(url_for("watchlist.main"))


@bp.route('/<int:id>/<ticker>/update', methods=('GET', 'POST'))
@login_required
def update(id, ticker):
    user_id = current_user.id
    check = check_watchlist_id(id)
    form = WatchlistItemsForm()
    form.order_id.data = id
    group_form = WatchlistGroupForm()
    form.sector.choices = get_sectors()
    form.watchlist.choices = get_watchlist_choices(user_id)
    if form.validate_on_submit() and check:
        new_watchlist = form.watchlist.data
        new_group_id = get_group_id(new_watchlist, user_id)
        item = WatchlistItems.query.filter_by(id=id, user_id=user_id).first()
        item.ticker = ticker
        item.watchlist = new_watchlist
        item.quantity = form.quantity.data
        item.price = form.price.data
        item.trade_date = form.trade_date.data
        item.sector = form.sector.data
        item.comments = form.comments.data
        item.group_id = new_group_id
        db.session.commit()
        flash(f"Order ID {id} has now been updated")
        return redirect(url_for("watchlist.main"))
    elif form.errors:
        for error_name, error_desc in form.errors.items():
            error_name = error_name.title()
            flash(f"{error_name}: {error_desc[0]}")
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


@bp.route('/delete-group', methods=('POST',))
@login_required
def delete_group():
    if request.method == "POST":
        name = request.form.get('watchlist_group_removed')
        user_id = current_user.id
        group_id = get_group_id(name, user_id)
        item = Watchlist_Group.query.filter_by(id=group_id, name=name, user_id=user_id).first()
        WatchlistItems.query.filter_by(group_id=group_id, user_id=user_id).delete(synchronize_session="fetch")  # temp solution until cascading works
        db.session.delete(item)
        db.session.commit()
        return redirect(url_for('watchlist.main'))
    return redirect(url_for('watchlist.main'))
