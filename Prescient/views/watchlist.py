from flask import(Blueprint, flash, g, redirect,
                  render_template, request, session,
                  url_for)
from werkzeug.exceptions import abort
from flask_login import login_required, current_user


bp = Blueprint("watchlist", __name__)



@bp.route("/main", methods=('GET', 'POST'))
@login_required
def main():
    db = get_db()
    holder_id = g.user["id"]
    query1 = """SELECT securities.*
                FROM securities
                WHERE holder_id = ?"""
    query2 = """SELECT
                    name,
                    SUM(units) as quantity,
                    ROUND(AVG(price),2) as price,
                    holder_id
                FROM
                    (SELECT
                        a.holder_id,
                        a.name,
                        CASE WHEN a.quantity < 0 THEN SUM(a.quantity) ELSE 0 END AS 'units',
                        CASE WHEN a.quantity < 0 THEN SUM(a.quantity*a.price)/SUM(a.quantity) ELSE 0 END AS 'price'
                    FROM securities a
                    WHERE a.quantity < 0 and holder_id=:holder_id
                    GROUP BY a.name
                    HAVING 'price' > 0

                    UNION ALL
                    SELECT
                        b.holder_id,
                        b.name,
                        CASE WHEN b.quantity > 0 THEN SUM(b.quantity) ELSE 0 END AS 'units',
                        CASE WHEN b.quantity > 0 THEN SUM(b.quantity*b.price)/SUM(b.quantity) ELSE 0 END AS 'price'
                    FROM securities b
                    WHERE b.quantity > 0 and holder_id=:holder_id
                    GROUP BY b.name
                    HAVING 'price' > 0)
                    WHERE holder_id=:holder_id
                    GROUP BY name """

    watchlist = db.execute(query1, (holder_id,)).fetchall()
    table1 = db.execute(query2, {"holder_id":holder_id}).fetchall()
    add_form = forms.WatchlistForm(request.form)
    add_form.sector.choices = get_sectors()
    return render_template("watchlist/main.html", watchlist=watchlist, table1=table1, add_form=add_form)

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
            return redirect(url_for('watchlist.main'))


    return render_template("watchlist/main.html", form=form)
