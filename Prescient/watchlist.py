from flask import(Blueprint, flash, g, redirect,
                  render_template, request, session,
                  url_for)
from werkzeug.exceptions import abort
from Prescient.auth import login_required
from Prescient.db import get_db
from . import forms

bp = Blueprint("watchlist", __name__)

@bp.route("/main")
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

    return render_template("watchlist/main.html", watchlist=watchlist, table1=table1)
