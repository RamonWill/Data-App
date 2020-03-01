# from Prescient import db
import pandas as pd
import os
import sqlite3
from collections import deque, namedtuple
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
        query = f"""SELECT * FROM '{ticker}'"""

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
    # THIS IS WRONG FOR SHORT POSITIONS
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
        df["quantity"] = df["quantity"].cumsum()  # cumulative quantity
        final_df = df[["date", "quantity", "weighted_average"]]
        return final_df.to_numpy().tolist()

    def performance_table(self, ticker):

        watchlist = self.get_holding_summary(ticker)
        conn = sqlite3.connect(PRICE_DATABASE)
        query = f"""SELECT * FROM '{ticker}'"""
        df = pd.read_sql_query(query, conn, index_col="index")
        df["quantity"] = float("nan")
        df["avg_cost"] = float("nan")
        start_date = watchlist[0][0]
        df2 = df.loc[start_date:]
        df2 = df2.copy()  # copied to prevent chained assignment
        for i in watchlist:
            df2.at[i[0], "quantity"] = i[1]
            df2.at[i[0], "avg_cost"] = i[2]
        df2["quantity"] = df2["quantity"].fillna(method="ffill")
        df2["price"] = df2["price"].fillna(method="ffill")
        df2["avg_cost"] = df2["avg_cost"].fillna(method="ffill")
        df2["price"] = pd.to_numeric(df2["price"])
        df2.loc[df2['quantity'] <= 0, 'Long/Short'] = -1
        df2.loc[df2['quantity'] > 0, 'Long/Short'] = 1

        df2["pct_change"] = (((df2["price"] - df2["avg_cost"])/df2["avg_cost"])*df2["Long/Short"])*100
        df2["pct_change"] = round(df2["pct_change"], 3)
        df2 = df2.reset_index()
        df2 = df2[["index", "quantity", "avg_cost", "price", "pct_change"]]
        df2 = list(df2.itertuples(index=False))
        return df2


class PositionSummary(object):
    """docstring for PositionSummary."""

    def __init__(self, db_trades, ticker):

        self.db_trades = db_trades

        self.average_cost = None
        self.open_lots = None
        self.ticker = ticker

        self.buy_quantities = deque([])
        self.buy_prices = deque([])
        self.buy_dates = deque([])

        self.sell_quantities = deque([])
        self.sell_prices = deque([])
        self.sell_dates = deque([])
        self.open_direction = None

        self.breakdown = []
        self.net_position = 0
        # remember to use decimal module
        # remember __repl__
        self.apply_fifo()

    def total_open_lots(self):
        if self.open_direction == "long":
            return sum(self.buy_quantities)
        elif self.open_direction == "short":
            return sum(self.sell_quantities)
        else:
            return None

    def total_mv(self):
        # mv on open lots
        if self.buy_quantities and self.open_direction == "long":
            return sum(quantity*price for quantity, price in zip(self.buy_quantities, self.buy_prices))
        elif self.sell_quantities and self.open_direction == "short":
            return sum(quantity*price for quantity, price in zip(self.sell_quantities, self.sell_prices))
        else:
            return None

    def avg_cost(self):
        open_lots = self.total_open_lots()
        if open_lots == 0 or not open_lots:
            return 0

        return abs(self.total_mv()/self.total_open_lots())

    def remove_trade(self, direction):
        "direction can equal either buy or sell"
        if direction == "buy":
            popped_quantity = self.buy_quantities.popleft()
            self.buy_prices.popleft()
            self.buy_dates.popleft()
        elif direction == "sell":
            popped_quantity = self.sell_quantities.popleft()
            self.sell_prices.popleft()
            self.sell_dates.popleft()
        else:
            raise NameError("why did this happen")
        return popped_quantity

    def collapse_trade(self):
        if self.sell_quantities:
            if self.sell_quantities[0] >= 0:
                self.remove_trade("sell")

        if self.buy_quantities:
            if self.buy_quantities[0] <= 0:
                self.remove_trade("buy")



    def get_summary(self):
        Summary = namedtuple("Summary", ["ticker", "quantity", "average_price"])
        ticker = self.ticker
        quantity = self.net_position
        average_price = round(self.average_cost, 4)
        return Summary(ticker, quantity, average_price)

    def add(self, side, units, price, date):
        if side == "buy":
            self.buy_quantities.append(units)
            self.buy_prices.append(price)
            self.buy_dates.append(date)
        elif side == "sell":
            self.sell_quantities.append(units)
            self.sell_prices.append(price)
            self.sell_dates.append(date)

    def set_direction(self):
        if self.open_direction == "short" and self.net_position > 0:
            self.open_direction = "long"
        elif self.open_direction == "long" and self.net_position < 0:
            self.open_direction = "short"


    def set_initial_trade(self):
        units = self.db_trades[0].quantity
        price = self.db_trades[0].price
        date = self.db_trades[0].date
        if units >= 0:
            self.open_direction = "long"
            self.add("buy", units, price, date)

        else:
            self.open_direction = "short"
            self.add("sell", units, price, date)
        self.average_cost = self.avg_cost()
        self.net_position = self.total_open_lots()
        self.breakdown.append([date, self.net_position, self.average_cost])

    def apply_fifo(self):
        # try a while loop with a counter. the counter so i can move across the trades and the while loop to collapse them as i go.
        # I add to attributes and perform calculations on that
        if self.db_trades:
            self.set_initial_trade()
        else:
            return []

        trades = len(self.db_trades)
        c1 = 1  # counter

        while c1 < trades:
            units = self.db_trades[c1].quantity
            price = self.db_trades[c1].price
            date = self.db_trades[c1].date

            if units*self.net_position > 0:  # if true both trades have the same sign
                if self.open_direction == "long":
                    self.add("buy", units, price, date)
                else:
                    self.add("sell", units, price, date)
            elif units*self.net_position == 0:
                if units >= 0:
                    self.open_direction = "long"
                    self.add("buy", units, price, date)

                else:
                    self.open_direction = "short"
                    self.add("sell", units, price, date)

            else:  # different signs
            # elif units*self.net_position < 0:
                if self.open_direction == "long":
                    self.add("sell", units, price, date)
                    while self.sell_quantities and self.buy_quantities: # while they are not empty

                        if abs(self.sell_quantities[0]) >= self.buy_quantities[0]:
                            self.sell_quantities[0] += self.buy_quantities[0]
                            self.remove_trade("buy")

                        else:
                            temp = self.remove_trade("sell")
                            self.buy_quantities[0] += temp
                    self.net_position += units  # subtract units from net position

                else:  #self.open_direction == "short"
                    self.add("buy", units, price, date)
                    while self.sell_quantities and self.buy_quantities: # while they are not empty
                        if self.buy_quantities[0] >= abs(self.sell_quantities[0]):
                            self.buy_quantities[0] += self.sell_quantities[0]
                            self.remove_trade("sell")
                        else:
                            temp = self.remove_trade("buy")
                            self.sell_quantities[0] += temp
                    self.net_position += units

            self.collapse_trade()
            self.set_direction()
            self.average_cost = round(self.avg_cost(), 4)
            self.net_position = self.total_open_lots()
            self.breakdown.append([date, self.net_position, self.average_cost])
            c1 += 1
