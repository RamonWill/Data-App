from Prescient import db
from flask import (Blueprint, flash, redirect,
                   render_template, url_for)
from werkzeug.exceptions import abort
from flask_login import login_required, current_user
from Prescient.forms import WatchlistItemsForm, WatchlistGroupForm
from Prescient.models import WatchlistItems, Sector_Definitions, Watchlist_Group

bp = Blueprint("watchlist", __name__)


def get_sectors():
    sectors = Sector_Definitions.query.all()
    sectors_list = [(s.name, s.name) for s in sectors]
    return sectors_list


def get_group_names(user_id):
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


def get_summary_table():
    user_id = current_user.id
    query = """SELECT
        ticker,
        SUM(units) as quantity,
        ROUND(AVG(price),2) as price,
        user_id
    FROM
        (SELECT
            a.user_id,
            a.ticker,
            CASE WHEN a.quantity < 0 THEN SUM(a.quantity) ELSE 0 END AS 'units',
            CASE WHEN a.quantity < 0 THEN SUM(a.quantity*a.price)/SUM(a.quantity) ELSE 0 END AS 'price'
        FROM watchlist_securities a
        WHERE a.quantity < 0 and user_id=:user_id
        GROUP BY a.ticker
        HAVING 'price' > 0

        UNION ALL
        SELECT
            b.user_id,
            b.ticker,
            CASE WHEN b.quantity > 0 THEN SUM(b.quantity) ELSE 0 END AS 'units',
            CASE WHEN b.quantity > 0 THEN SUM(b.quantity*b.price)/SUM(b.quantity) ELSE 0 END AS 'price'
        FROM watchlist_securities b
        WHERE b.quantity > 0 and user_id=:user_id
        GROUP BY b.ticker
        HAVING 'price' > 0)
        WHERE user_id=:user_id
        GROUP BY ticker"""
    result = db.session.execute(query, {"user_id": user_id})
    return result


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

    form = WatchlistItemsForm()
    form.sector.choices = get_sectors()
    form.watchlist.choices = get_group_names(user_id)
    watchlist = WatchlistItems.query.filter_by(user_id=user_id)  # this is good because it defaults to an empty list
    summary = get_summary_table()

    group_form = WatchlistGroupForm()

    return render_template("watchlist/main.html", watchlist=watchlist, summary=summary, form=form, group_form=group_form)

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
    form.watchlist.choices = get_group_names(current_user.id)

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
        flash(f"{name} has been added to your watchlist")
        return redirect(url_for("watchlist.main"))
        # Follow the registration view
        # I will also need one function to get the sectors

    return render_template("watchlist/main.html", form=form)

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    check = check_watchlist_id(id)
    form = WatchlistItemsForm()
    form.sector.choices = get_sectors()
    user_id = current_user.id
    if form.validate_on_submit() and check:
        new_quantity = form.quantity.data
        new_price = form.price.data
        new_sector = form.sector.data
        new_comment = form.comments.data
        item = WatchlistItems.query.filter_by(id=id, user_id=user_id).first()
        item.quantity = new_quantity
        item.price = new_price
        item.sector = new_sector
        item.comments = new_comment
        db.session.commit()
        flash(f"Order ID {id} has now been updated")
        return redirect(url_for("watchlist.main"))

    return render_template("watchlist/main.html", form=form)

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
