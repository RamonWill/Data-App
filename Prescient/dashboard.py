from flask import(Blueprint, flash, g, redirect,
                  render_template, request, session,
                  url_for)

from Prescient.auth import login_required
from Prescient.db import get_db
from . import forms

bp = Blueprint("Dashboard", __name__)


@bp.route("/")
def index():
    return render_template("securities/dashboard.html")


def get_sectors():
    db = get_db()
    query = """SELECT name
               FROM sector_definitions"""

    data = db.execute(query).fetchall()
    sectors = [(name[0], name[0]) for name in data]

    return sectors


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    form = forms.WatchlistForm(request.form)  # request.form fills in the form with data from the request
    form.sector.choices = get_sectors()
    if request.method == 'POST':
        name = form.ticker.data
        quantity = form.quantity.data
        price = form.price.data

        sector = form.sector.data
        comments = form.comments.data
        holder_id = g.user["id"]
        error = None

        db = get_db()
        check = db.execute("SELECT ticker FROM available_securities WHERE ticker = ?", (name,)).fetchone()
        if check is None:
            error = f"The ticker {name} is not available."
            flash(error)

        elif form.validate():
            db = get_db()
            db.execute(
                """INSERT INTO securities (name, quantity, price, sector, holder_id, comments)
                   VALUES (?, ?, ?, ?, ?, ?)""", (name, int(quantity), float(price), sector, holder_id, comments,))
            db.commit()
            return redirect(url_for('dashboard'))


    return render_template('securities/create.html', form=form)
