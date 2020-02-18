# from Prescient import db
import pandas as pd
import os
import sqlite3
MAIN_DATABASE = os.path.abspath(os.path.join(__file__, "../..", "MainDB.db"))
PRICE_DATABASE = os.path.abspath(os.path.join(__file__, "../..", "Security_PricesDB.db"))

## To get data from the DB its
# x = pd. read_sql(sql=query, con=db.engine)
# to get mainDB db.engine
# to get pricesDB db.get_engine(app, "Security_PricesDB")
#ive tested this in terminal and it works

def get_quantity_cumsum(symbol):
    # Gets the cumulative summed quantity per date for each security
    conn = sqlite3.connect(MAIN_DATABASE)
    query = f"""Select DATE(created_timestamp), quantity
    From watchlist_securities
    where user_id =1 and ticker='{symbol}'
    ORDER BY created_timestamp """
    df = pd.read_sql_query(query, conn)
    df["quantity"] = df["quantity"].cumsum()
    return df.to_numpy().tolist()


def get_daily_mv(symbol):

    watchlist = get_quantity_cumsum(symbol)
    conn = sqlite3.connect(PRICE_DATABASE)
    query = f"""SELECT * FROM {symbol}"""
    df = pd.read_sql_query(query, conn, index_col="index")

    df["quantity"] = float("nan")
    df["market_val"] = float("nan")
    start_date = watchlist[0][0]

    df2 = df.loc[start_date:] # the prices starting from the first date the security was held
    df2 = df2.copy()  # prevents chain assignment
    for i in watchlist:
        df2.at[i[0], "quantity"] = i[1]  # at the date, insert quantity

    df2["price"] = df2["price"].fillna(method="ffill")
    df2["quantity"] = df2["quantity"].fillna(method="ffill")

    df2["price"] = pd.to_numeric(df2["price"])
    df2["market_val"] = round((df2["price"] * df2["quantity"]),3)

    df2 = df2[["market_val"]]
    new_name = {"market_val": f"market_val_{symbol}"}
    df2 = df2.rename(columns=new_name)
    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    #     print(df2)
    return df2


def full_table():
    conn = sqlite3.connect(MAIN_DATABASE)
    distinct_query = """SELECT DISTINCT ticker from watchlist_securities WHERE user_id=1 ORDER BY created_timestamp"""
    c = conn.cursor()
    result = c.execute(distinct_query).fetchall()
    c.close()
    conn.close()
    unique_tickers = [ticker[0] for ticker in result]

    df = pd.DataFrame()
    for ticker in unique_tickers:
        if df.empty:
            df = get_daily_mv(ticker)

        else:
            df_new = get_daily_mv(ticker)
            df = df.join(df_new)

    df = df.fillna(method="ffill")
    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    #     print(p)
    return df


def summed_table():
    table = full_table()
    table["portfolio_val"] = table.sum(axis=1)
    table = table[["portfolio_val"]]  # The daily portfolio valuations excluding flows

    conn = sqlite3.connect(MAIN_DATABASE)
    query= """Select DATE(created_timestamp) as 'index', SUM(quantity * price) as flow
From watchlist_securities
where user_id =1
GROUP BY DATE(created_timestamp)
ORDER BY DATE(created_timestamp)"""

    df = pd.read_sql_query(query, conn, index_col="index")  # inflows/outflows
    table = table.join(df)
    table = table.reset_index()

    table["flow"] = table["flow"].shift(-1)  # shifts the flows back by previous day to allow us to get the previous day valuation including flows
    table["flow"] = table["flow"].fillna(value=0)
    table["total_portfolio_val"] = table.sum(axis=1)
    table["pct_change"] = (((table["portfolio_val"].shift(-1)/(table["total_portfolio_val"]))-1)*100)
    table["pct_change"] = table["pct_change"].shift(1)
    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    #     print(table)
    table = list(table.itertuples(index=False))
    return table # changes df to  named tuples so it can be rendered
