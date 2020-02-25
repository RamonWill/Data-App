# from Prescient import db
import pandas as pd
import os
import sqlite3
MAIN_DATABASE = os.path.abspath(os.path.join(__file__, "../..", "MainDB.db"))
PRICE_DATABASE = os.path.abspath(os.path.join(__file__, "../..", "Security_PricesDB.db"))

# To get data from the DB its
# x = pd. read_sql(sql=query, con=db.engine)
# to get mainDB db.engine
# to get pricesDB db.get_engine(app, "Security_PricesDB")
# ive tested this in terminal and it works


class Portfolio_Performance(object):
    """docstring for Portfolio_Performance."""

    def __init__(self, user_id, group_id):
        self.user_id = user_id
        self.group_id = group_id

    def __repr__(self):
        return "User ID: {}\nGroup ID: {}".format(self.user_id, self.group_id)

    def get_quantity_cumsum(self, ticker):
        # Gets the cumulative summed quantity per date for each security
        conn = sqlite3.connect(MAIN_DATABASE)
        query = """Select DATE(created_timestamp), quantity
        From watchlist_securities
        where user_id =:user_id and ticker=:ticker and group_id=:group_id
        ORDER BY created_timestamp """
        params = {"user_id": self.user_id,
                  "ticker": ticker,
                  "group_id": self.group_id}

        df = pd.read_sql_query(query, conn, params=params)
        df["quantity"] = df["quantity"].cumsum()
        return df.to_numpy().tolist()

    def get_daily_mv(self, ticker):

        watchlist = self.get_quantity_cumsum(ticker)
        conn = sqlite3.connect(PRICE_DATABASE)
        query = f"""SELECT * FROM {ticker}"""

        df = pd.read_sql_query(query, conn, index_col="index")

        df["quantity"] = float("nan")
        df["market_val"] = float("nan")

        # the prices starting from the first date the security was held
        start_date = watchlist[0][0]
        df2 = df.loc[start_date:]
        df2 = df2.copy()  # copied to prevent chained assignment
        # update the quantity at each date
        for i in watchlist:
            df2.at[i[0], "quantity"] = i[1]

        df2["price"] = df2["price"].fillna(method="ffill")
        df2["quantity"] = df2["quantity"].fillna(method="ffill")

        df2["price"] = pd.to_numeric(df2["price"])
        df2["market_val"] = round((df2["price"] * df2["quantity"]), 3)

        df2 = df2[["market_val"]]
        new_name = f"market_val_{ticker}"
        new_header = {"market_val": new_name}
        df2 = df2.rename(columns=new_header)
        return df2

    def full_table(self):
        conn = sqlite3.connect(MAIN_DATABASE)
        distinct_query = """SELECT DISTINCT ticker
                            FROM watchlist_securities
                            WHERE user_id=:user_id and group_id=:group_id
                            ORDER BY created_timestamp"""
        params = {"user_id": self.user_id, "group_id": self.group_id}
        c = conn.cursor()
        result = c.execute(distinct_query, params).fetchall()
        c.close()
        conn.close()

        unique_tickers = [ticker[0] for ticker in result]

        df = pd.DataFrame()
        for ticker in unique_tickers:
            if df.empty:
                df = self.get_daily_mv(ticker)

            else:
                df_new = self.get_daily_mv(ticker)
                df = df.join(df_new)

        df = df.fillna(method="ffill")
        return df

    def summed_table(self):
        table = self.full_table()
        table["portfolio_val"] = table.sum(axis=1)
        # creates a table total daily portfolio valuations
        table = table[["portfolio_val"]]

        conn = sqlite3.connect(MAIN_DATABASE)
        query = """SELECT
                    DATE(created_timestamp) as 'index',
                    SUM(quantity * price) as flow
                  FROM watchlist_securities
                  WHERE user_id =:user_id and group_id=:group_id
                  GROUP BY DATE(created_timestamp)
                  ORDER BY DATE(created_timestamp)"""
        params = {"user_id": self.user_id, "group_id": self.group_id}
        # inflows/outflows
        df_flows = pd.read_sql_query(query, conn, index_col="index", params=params)
        table = table.join(df_flows)
        table = table.reset_index()
        # shifts the flows back by previous day
        # to get the previous day valuation including flows
        table["flow"] = table["flow"].shift(-1)
        table["flow"] = table["flow"].fillna(value=0)
        table["total_portfolio_val"] = table.sum(axis=1)
        table["pct_change"] = (((table["portfolio_val"].shift(-1)/(table["total_portfolio_val"]))-1)*100)
        table["pct_change"] = round(table["pct_change"].shift(1), 2)

        table = list(table.itertuples(index=False))
        return table

    def get_pie_chart(self):

        df = self.full_table().tail(1)
        df = df.T.reset_index()  # transpose table to make the tickers the rows
        if df.empty:
            return df

        new_headers = {df.columns[0]: "ticker", df.columns[1]: "Market_val"}
        df = df.rename(columns=new_headers)
        df["Market_val"] = abs(df["Market_val"])
        total_portfolio_val = sum(df["Market_val"])

        df["ticker"] = df["ticker"].replace("market_val_", "", regex=True)
        df["market_val_perc"] = round(df["Market_val"]/total_portfolio_val, 2)
        df = df[df["Market_val"] != 0]  # filter rows where valuation isnt zero
        df = df.sort_values(by=['market_val_perc'], ascending=False)

        if len(df) >= 7:
            # split the dataframe into two parts
            df_bottom = df.tail(len(df)-6)
            df = df.head(6)

            # sum the bottom dataframe to create an "Other" field
            df_bottom.loc['Other'] = df_bottom.sum(numeric_only=True, axis=0)
            df_bottom.at["Other", "ticker"] = "Other"
            df_bottom = df_bottom.tail(1)

            df_final = pd.concat([df, df_bottom])
            df_final = list(df_final.itertuples(index=False))
            return df_final
        else:
            df_final = list(df.itertuples(index=False))
            return df_final

    def get_bar_chart(self):
        df = self.full_table().tail(1)
        df = df.T.reset_index()
        if df.empty:
            return df

        new_headers = {df.columns[0]: "ticker", df.columns[1]: "market_val"}
        df = df.rename(columns=new_headers)

        df["ticker"] = df["ticker"].replace("market_val_", "", regex=True)
        # sort the dataframe by largest exposures (descending order)
        df = df.iloc[df['market_val'].abs().argsort()]
        df = df[df["market_val"] != 0]  # filter rows where valuation isnt zero
        df = df.tail(5)  # the 5 largest positions by absolute mv
        df_final = list(df.itertuples(index=False))
        return df_final


class Portfolio_Summaries(object):
    def __init__(self, user_id, group_id):
        self.user_id = user_id
        self.group_id = group_id

    def summary_table(self):
        query = """SELECT
                ticker,
                SUM(units) as quantity,
                ROUND(AVG(price),2) as price
            FROM
                (SELECT
                    a.user_id,
                    a.ticker,
                    CASE WHEN a.quantity < 0 THEN SUM(a.quantity) ELSE 0 END AS 'units',
                    CASE WHEN a.quantity < 0 THEN SUM(a.quantity*a.price)/SUM(a.quantity) ELSE 0 END AS 'price',
                    a.group_id
                FROM watchlist_securities a
                WHERE a.quantity < 0 and user_id=:user_id and group_id=:group_id
                GROUP BY a.ticker
                HAVING 'price' > 0

                UNION ALL
                SELECT
                    b.user_id,
                    b.ticker,
                    CASE WHEN b.quantity > 0 THEN SUM(b.quantity) ELSE 0 END AS 'units',
                    CASE WHEN b.quantity > 0 THEN SUM(b.quantity*b.price)/SUM(b.quantity) ELSE 0 END AS 'price',
                    b.group_id
                FROM watchlist_securities b
                WHERE b.quantity > 0 and user_id=:user_id and group_id=:group_id
                GROUP BY b.ticker
                HAVING 'price' > 0)
                WHERE user_id=:user_id and group_id=:group_id
                GROUP BY ticker
                """
        conn = sqlite3.connect(MAIN_DATABASE)
        conn.row_factory = sqlite3.Row
        params = {"user_id": self.user_id, "group_id": self.group_id}
        c = conn.cursor()
        result = c.execute(query, params).fetchall()
        c.close()
        conn.close()

        return result


class Security_Breakdown(object):
    """docstring for Security_Breakdown."""

    def __init__(self, user_id, group_id):
        self.user_id = user_id
        self.group_id = group_id

    def get_tickers(self):
        conn = sqlite3.connect(MAIN_DATABASE)
        conn.row_factory = sqlite3.Row
        params = {"user_id": self.user_id, "group_id": self.group_id}
        distinct_query = """SELECT DISTINCT ticker
                            FROM watchlist_securities
                            WHERE user_id=:user_id and group_id=:group_id"""
        c = conn.cursor()
        all_tickers = c.execute(distinct_query, params).fetchall()
        c.close()
        conn.close()
        if all_tickers is None:
            return []
        tickers_list = [(i["ticker"], i["ticker"]) for i in all_tickers]
        return tickers_list

    def get_holding_summary(self, ticker):

        conn = sqlite3.connect(MAIN_DATABASE)
        query = """SELECT
        DATE(created_timestamp) as 'date',
        ticker,
        SUM(units) as 'quantity',
        ROUND(AVG(price),2) as 'price'
        FROM
        (SELECT
            a.created_timestamp,
            a.user_id,
            a.group_id,
            a.ticker,
            CASE WHEN a.quantity < 0 THEN SUM(a.quantity) ELSE 0 END AS 'units',
            CASE WHEN a.quantity < 0 THEN SUM(a.quantity*a.price)/SUM(a.quantity) ELSE 0 END AS 'price'
        FROM watchlist_securities a
        WHERE a.quantity < 0 and user_id=:user_id and ticker=:ticker and group_id=:group_id
        GROUP BY DATE(a.created_timestamp)
        HAVING 'price' > 0
        UNION ALL
        SELECT
            b.created_timestamp,
            b.user_id,
            b.group_id,
            b.ticker,
            CASE WHEN b.quantity > 0 THEN SUM(b.quantity) ELSE 0 END AS 'units',
            CASE WHEN b.quantity > 0 THEN SUM(b.quantity*b.price)/SUM(b.quantity) ELSE 0 END AS 'price'
        FROM watchlist_securities b
        WHERE b.quantity > 0 and user_id=:user_id and ticker=:ticker and group_id=:group_id
        GROUP BY DATE(b.created_timestamp)
        HAVING 'price' > 0)
        WHERE user_id=:user_id and group_id=:group_id
        GROUP BY DATE(created_timestamp)"""
        # need to filter this excution by the user_id and ticker
        params = {"user_id": self.user_id,
                  "ticker": ticker,
                  "group_id": self.group_id}
        df = pd.read_sql_query(query, conn, params=params)

        averages = []
        for i in range(0, len(df)):
            if i > 0:
                sum_of_weighted_terms = sum(df["quantity"].iloc[0:i+1] * df["price"].iloc[0:i+1])
                sum_of_terms = sum(df["quantity"].iloc[0:i+1])
                if sum_of_weighted_terms == 0:
                    averages.append(float("nan"))
                else:
                    weighted_avg = sum_of_weighted_terms/sum_of_terms
                    averages.append(weighted_avg)
            else:
                averages.append(df["price"].iloc[0])
        df["weighted_average"] = averages
        df["weighted_average"] = round(df["weighted_average"], 4)
        final_df = df[["date", "weighted_average"]]
        return final_df.to_numpy().tolist()

    def performance_table(self, ticker):

        watchlist = self.get_holding_summary(ticker)
        conn = sqlite3.connect(PRICE_DATABASE)
        query = f"""SELECT * FROM {ticker}"""
        df = pd.read_sql_query(query, conn, index_col="index")
        df["avg_cost"], df["pct_change"] = float("nan"), float("nan")
        start_date = watchlist[0][0]
        df2 = df.loc[start_date:]
        df2 = df2.copy()  # copied to prevent chained assignment
        for i in watchlist:
            df2.at[i[0], "avg_cost"] = i[1]
        df2["price"] = df2["price"].fillna(method="ffill")
        df2["avg_cost"] = df2["avg_cost"].fillna(method="ffill")
        df2["price"] = pd.to_numeric(df2["price"])
        df2["pct_change"] = round(((df2["price"] - df2["avg_cost"])/df2["avg_cost"])*100, 3)

        df2 = df2.reset_index()
        df2 = list(df2.itertuples(index=False))
        return df2
