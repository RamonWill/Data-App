from flask import(Blueprint, flash, g, redirect,
                  render_template, request, session,
                  url_for)

from Prescient.auth import login_required
from Prescient.db import get_db

bp = Blueprint("Dashboard", __name__)


@bp.route("/")
def index():
    return render_template("securities/dashboard.html")


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        price = request.form['price']
        sector = request.form['sector']
        holder_id = g.user["id"]
        error = None

        if not name:
            error = 'Name is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                """INSERT INTO securities (name, quantity, price, sector, holder_id)
                   VALUES (?, ?, ?, ?, ?)""",
                (name, quantity, price, sector, holder_id))
            db.commit()
            return redirect(url_for('dashboard'))

    return render_template('securities/create.html')
