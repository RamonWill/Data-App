from flask import(Blueprint, flash, g, redirect,
                  render_template, request, session,
                  url_for)
from werkzeug.exceptions import abort
from Prescient.auth import login_required
from Prescient.db import get_db
import pandas as pd
import sqlite3  # set this up as class at some point
from . import forms

bp = Blueprint("Dashboard", __name__)


def get_holding_summary(symbol):
    holder_id = g.user["id"]

    conn = sqlite3.connect(r"instance\MainDB.sqlite")
    query = f"""SELECT
    DATE(created) as 'date',
    name as 'symbol',
    SUM(units) as 'quantity',
    ROUND(AVG(price),2) as 'price',
    holder_id
    FROM
    (SELECT
    	a.created,
    	a.holder_id,
    	a.name,
    	CASE WHEN a.quantity < 0 THEN SUM(a.quantity) ELSE 0 END AS 'units',
    	CASE WHEN a.quantity < 0 THEN SUM(a.quantity*a.price)/SUM(a.quantity) ELSE 0 END AS 'price'
    FROM securities a
    WHERE a.quantity < 0 and holder_id={holder_id} and name='{symbol}'
    GROUP BY DATE(a.created)
    HAVING 'price' > 0

    UNION ALL
    SELECT
    	b.created,
    	b.holder_id,
    	b.name,
    	CASE WHEN b.quantity > 0 THEN SUM(b.quantity) ELSE 0 END AS 'units',
    	CASE WHEN b.quantity > 0 THEN SUM(b.quantity*b.price)/SUM(b.quantity) ELSE 0 END AS 'price'
    FROM securities b
    WHERE b.quantity > 0 and holder_id={holder_id} and name='{symbol}'
    GROUP BY DATE(b.created)
    HAVING 'price' > 0)
    WHERE holder_id={holder_id}
    GROUP BY DATE(created)"""
    # need to filter this excution by the holder_id and name
    df = pd.read_sql_query(query, conn)

    averages = []
    for i in range(0, len(df)):

        if i > 0:
            sum_of_weighted_terms = sum(df["quantity"].iloc[0:i+1] * df["price"].iloc[0:i+1])
            sum_of_terms = sum(df["quantity"].iloc[0:i+1])
            weighted_avg = sum_of_weighted_terms/sum_of_terms
            averages.append(weighted_avg)
        else:
            averages.append(df["price"].iloc[0])
    df["weighted-average"] = averages
    final_df = df[["date", "weighted-average"]]
    return final_df.to_numpy().tolist()


def get_line_chart_info(symbol):
    # using amazon
    watchlist = get_holding_summary(symbol)
    conn = sqlite3.connect(r"instance\price_data.sqlite")
    query = f"""SELECT * FROM {symbol}"""
    df = pd.read_sql_query(query, conn, index_col="index")
    df["avg_cost"], df["pct_change"] = float("nan"), float("nan")
    start_date = watchlist[0][0]
    df2 = df.loc[start_date:]
    df2 = df2.copy()  # prevents chain assignment
    for i in watchlist:
        df2.at[i[0], "avg_cost"] = i[1]  # at the date, insert price
    df2["price"] = df2["price"].fillna(method="ffill")
    df2["avg_cost"] = df2["avg_cost"].fillna(method="ffill")
    df2["price"] = pd.to_numeric(df2["price"])
    df2["pct_change"] = round(((df2["price"] - df2["avg_cost"])/df2["avg_cost"])*100,3)
    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    #     print(df2)
    df2 = df2.reset_index()
    df2 = list(df2.itertuples(index=False))
    return df2
def get_quantity_cumsum(symbol):
    conn = sqlite3.connect(r"C:\Users\Owner\Documents\Data-App\instance\MainDB.sqlite")
    query = f"""Select DATE(created), quantity
    From securities
    where holder_id =1 and name='{symbol}'
    ORDER BY created """
    df = pd.read_sql_query(query, conn)
    df["quantity"] = df["quantity"].cumsum()
    return df.to_numpy().tolist()

def get_daily_mv(symbol):
    # using amazon
    watchlist = get_quantity_cumsum(symbol)
    conn = sqlite3.connect(r"C:\Users\Owner\Documents\Data-App\instance\price_data.sqlite")
    query = f"""SELECT * FROM {symbol}"""
    df = pd.read_sql_query(query, conn, index_col="index")

    df["quantity"], df["market_val"] = float("nan"), float("nan")
    start_date = watchlist[0][0]
    df2 = df.loc[start_date:]
    df2 = df2.copy()  # prevents chain assignment
    for i in watchlist:
        df2.at[i[0], "quantity"] = i[1]  # at the date, insert price
    df2["price"] = df2["price"].fillna(method="ffill")
    df2["quantity"] = df2["quantity"].fillna(method="ffill")

    df2["price"] = pd.to_numeric(df2["price"])
    df2["market_val"] = round((df2["price"] * df2["quantity"]),3)

    #df2 = df2.reset_index()
    df2 = df2[["market_val"]]
    new_name = {"market_val": f"market_val_{symbol}"}
    df2 = df2.rename(columns=new_name)
    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    #     print(df2)
    return df2
    # df2 = list(df2.itertuples(index=False)) # changes df to  named tuples so it can be rendered


def full_table():
    x = ["AMZN","MSFT","IBM","DIS","CAT","AAPL"]
    p = pd.DataFrame()
    for i in x:
        if p.empty:
            p = get_daily_mv(i)

        else:
            n = get_daily_mv(i)
            p = p.join(n)

    p = p.fillna(method="ffill")
    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    #     print(p)
    return p

#full_table()
def summed_table():
    table = full_table()
    table["portfolio_val"] = table.sum(axis=1)
    table = table[["portfolio_val"]]
    #table.to_csv(r"C:\Users\Owner\Documents\MyScripts\Random Scripts\Scrap\test.csv")
    conn = sqlite3.connect(r"C:\Users\Owner\Documents\Data-App\instance\MainDB.sqlite")
    query= """Select DATE(created) as 'index', SUM(quantity * price) as flow
From securities
where holder_id =1
GROUP BY DATE(created)
ORDER BY DATE(created)"""

    df = pd.read_sql_query(query, conn, index_col="index")
    #print(df)
    table = table.join(df)
    table = table.reset_index()


    table["flow"] = table["flow"].shift(-1)
    table["flow"] = table["flow"].fillna(value=0)
    table["total_portfolio_val"] = table.sum(axis=1)
    table["pct_change"] = (((table["portfolio_val"].shift(-1)/(table["total_portfolio_val"]))-1)*100)
    table["pct_change"] = table["pct_change"].shift(1)
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        print(table)
    table = list(table.itertuples(index=False))
    return table

def get_sectors():
    db = get_db()
    query = """SELECT name
               FROM sector_definitions"""

    data = db.execute(query).fetchall()
    sectors = [(name[0], name[0]) for name in data]

    return sectors


def get_watchlist_id(id, check_holder=True):
    db = get_db()
    query = """SELECT securities.id,
                      securities.name,
                      securities.quantity,
                      securities.price,
                      securities.sector,
                      securities.comments,
                      securities.holder_id
                FROM securities
                JOIN login_details ON securities.holder_id = login_details.id
                WHERE securities.id = ?"""
    info = db.execute(query, (id,)).fetchone()
    if info is None:
        abort(404, f"Order ID {id} doesn't exist.")
    if check_holder and info["holder_id"] != g.user["id"]:
        abort(403)
    return info


@bp.route("/")
@login_required
def index():
    db = get_db()
    holder_id = g.user["id"]
    #line_chart = get_line_chart_info("MSFT")  # make this an empty list [] so that the line chart has no info then populate it on user request
    line_chart = summed_table()
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
    query3 = """SELECT name, ROUND(ABS(SUM(quantity*price)/t.s)*100,2) as "Market_val_perc"
from securities
CROSS JOIN (SELECT SUM(quantity*price) AS s FROM securities WHERE holder_id=:holder_id) t
WHERE holder_id=:holder_id
GROUP BY name"""
    query4 = """SELECT name, ROUND(ABS(SUM(quantity*price)),2) as "Market_val"
    from securities
    WHERE holder_id=:holder_id
    GROUP BY name
    LIMIT 5"""
    table1 = db.execute(query2, {"holder_id":holder_id}).fetchall()
    pie_chart = db.execute(query3, {"holder_id":holder_id}).fetchall()
    bar_chart = db.execute(query4, {"holder_id":holder_id}).fetchall()
    return render_template("securities/dashboard.html", table1=table1, line_chart=line_chart, pie_chart=pie_chart, bar_chart=bar_chart)
