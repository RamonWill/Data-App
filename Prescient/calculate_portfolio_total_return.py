import pandas as pd
import sqlite3


def get_quantity_cumsum(symbol):
    # this gets the cumulative sum for the security
    conn = sqlite3.connect(r"C:\Users\Owner\Documents\Data-App\instance\MainDB.sqlite")
    query = f"""Select DATE(created), quantity
    From securities
    where holder_id =1 and name='{symbol}'
    ORDER BY created """
    df = pd.read_sql_query(query, conn)
    df["quantity"] = df["quantity"].cumsum()
    return df.to_numpy().tolist()

def get_daily_mv(symbol):
    # this calculates the daily Market Value for all holdings of the security
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
    # builds a table from the current positions marketvalue and joins them by their date
    x = ["AMZN","MSFT","IBM","DIS","CAT","AAPL"] # this needs to be a filter of current positions from sql (ordered by DATE!!!!)
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
    # calculates the holding period return on the total portfolio value. takes flows(buys and sells into account aka new entries)
    # USE THIS FOR TESTING PURPOSES https://www.fool.com/about/how-to-calculate-investment-returns/
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
    # df["quantity"], df["market_val"] = float("nan"), float("nan")
    # start_date = watchlist[0][0]
    # df2 = df.loc[start_date:]
    # df2 = df2.copy()  # prevents chain assignment
    # for i in watchlist:
    #     df2.at[i[0], "quantity"] = i[1]  # at the date, insert price

#print(get_quantity_cumsum("AMZN"))
