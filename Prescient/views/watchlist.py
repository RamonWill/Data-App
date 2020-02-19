from Prescient import db
from flask import (Blueprint, flash, redirect,
                   render_template, url_for)
from werkzeug.exceptions import abort
from flask_login import login_required, current_user
from Prescient.forms import WatchlistForm
from Prescient.models import Watchlist, Sector_Definitions

bp = Blueprint("watchlist", __name__)


def get_sectors():
    sectors = Sector_Definitions.query.all()
    sectors_list = [(s.name, s.name) for s in sectors]
    return sectors_list


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
    info = Watchlist.query.filter_by(id=id).first()
    if info is None:
        abort(404, f"Order ID {id} doesn't exist.")
    if info.user_id != current_user.id:
        abort(403)
    return True


@bp.route("/main", methods=('GET', 'POST'))
@login_required
def main():
    user_id = current_user.id

    form = WatchlistForm()
    form.sector.choices = get_sectors()
    watchlist = Watchlist.query.filter_by(user_id=user_id)  # this is good because it defaults to an empty list
    summary = get_summary_table()
    #i will also need one function to get the sectors

    return render_template("watchlist/main.html", watchlist=watchlist, summary=summary, form=form)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    form = WatchlistForm()
    form.sector.choices = get_sectors()

    if form.validate_on_submit():
        name = form.ticker.data
        quantity = form.quantity.data
        price = form.price.data
        sector = form.sector.data
        comments = form.comments.data
        user_id = current_user.id
        new_item = Watchlist(ticker=name, quantity=quantity,
                             price=price, sector=sector,
                             comments=comments, user_id=user_id)
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
    form = WatchlistForm()
    form.sector.choices = get_sectors()
    user_id = current_user.id
    if form.validate_on_submit() and check:
        new_quantity = form.quantity.data
        new_price = form.price.data
        new_sector = form.sector.data
        new_comment = form.comments.data
        item = Watchlist.query.filter_by(id=id, user_id=user_id).first()
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
        item = Watchlist.query.filter_by(id=id, user_id=user_id).first()
        db.session.delete(item)
        db.session.commit()
        return redirect(url_for('watchlist.main'))
    return redirect(url_for('watchlist.main'))

## To get data from the DB its
# x = pd. read_sql(sql=query, con=db.engine)
# to get mainDB db.engine
# to get pricesDB db.get_engine(app, "Security_PricesDB")
#ive tested this in terminal and it works
