from Prescient import db
from flask import(Blueprint, flash, g, redirect,
                  render_template, request, session,
                  url_for)
from werkzeug.exceptions import abort
from flask_login import login_required, current_user
from Prescient.forms import WatchlistForm
from Prescient.models import Watchlist, Sector_Definitions

bp = Blueprint("watchlist", __name__)

def get_sectors():
    sectors = Sector_Definitions.query.all()
    sectors_list = [(s.name, s.name) for s in sectors]
    return sectors_list


def check_watchlist_id(id, check_holder=True):

    info = Watchlist.query.filter_by(id=id).first()
    if info is None:
        abort(404, f"Order ID {id} doesn't exist.")
    if info.holder_id != current_user.id:
        abort(403)
    return True


@bp.route("/main", methods=('GET', 'POST'))
@login_required
def main():
    form = WatchlistForm()
    form.sector.choices = get_sectors()
    watchlist = []
    table1 = []
    #i will also need one function to get the sectors

    return render_template("watchlist/main.html", watchlist=watchlist, table1=table1, form=form)

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
#ive tested this in terminal and it works
