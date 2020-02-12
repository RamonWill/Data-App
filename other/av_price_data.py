import pandas as pd
import sqlite3


def get_holding_summary(symbol, holder_id):
    conn = sqlite3.connect(r"instance\MainDB.sqlite")
    query = """SELECT
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
    WHERE a.quantity < 0 and holder_id=1 and name="AMZN"
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
    WHERE b.quantity > 0 and holder_id=1 and name="AMZN"
    GROUP BY DATE(b.created)
    HAVING 'price' > 0)
    WHERE holder_id=1
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


def get_line_chart_info(symbol, holder_id):
    # using amazon
    watchlist = get_holding_summary(symbol, holder_id)
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
    df2["pct_change"] = (df2["price"] - df2["avg_cost"])/df2["avg_cost"]
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        print(df2)
        print(df2.to_json(orient="split"))
    df2 = df2[["pct_change"]]
    return df2.reset_index().to_json(orient="split")
#get_line_chart_info("AMZN", 1)

# conn  = sqlite3.connect(r"instance\maindb.sqlite")
# c = conn.cursor()
# holder_id=1
# query2 = """SELECT
#                 name,
#                 SUM(units) as quantity,
#                 ROUND(AVG(price),2) as price,
#                 holder_id
#             FROM
#                 (SELECT
#                     a.holder_id,
#                     a.name,
#                     CASE WHEN a.quantity < 0 THEN SUM(a.quantity) ELSE 0 END AS 'units',
#                     CASE WHEN a.quantity < 0 THEN SUM(a.quantity*a.price)/SUM(a.quantity) ELSE 0 END AS 'price'
#                 FROM securities a
#                 WHERE a.quantity < 0 and holder_id=:holder_id
#                 GROUP BY a.name
#                 HAVING 'price' > 0
#
#                 UNION ALL
#                 SELECT
#                     b.holder_id,
#                     b.name,
#                     CASE WHEN b.quantity > 0 THEN SUM(b.quantity) ELSE 0 END AS 'units',
#                     CASE WHEN b.quantity > 0 THEN SUM(b.quantity*b.price)/SUM(b.quantity) ELSE 0 END AS 'price'
#                 FROM securities b
#                 WHERE b.quantity > 0 and holder_id=:holder_id
#                 GROUP BY b.name
#                 HAVING 'price' > 0)
#                 WHERE holder_id=:holder_id
#                 GROUP BY name """
#
# table1 = c.execute(query2, {"holder_id":holder_id}).fetchall()
# print(table1)
# print(type(table1))
