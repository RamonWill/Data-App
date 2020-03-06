import pandas as pd
from collections import deque, namedtuple

# remember to use private methods i.e. _apply_fifo
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
        # remember __repr__
        # DO NOT FORGET TO ADD THE __repr__
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


class PositionAccounting(PositionSummary):
    """docstring for PositionAccounting."""

    def __init__(self, close_prices, db_trades, ticker):
        PositionSummary.__init__(self, db_trades, ticker)
        self.close_prices = close_prices

    def performance_table(self):
        df = pd.DataFrame(self.close_prices, columns=["date", "price"])
        df = df.set_index("date")
        df["quantity"] = float("nan")
        df["avg_cost"] = float("nan")
        start_date = self.breakdown[0][0]
        df2 = df.loc[start_date:]
        df2 = df2.copy()  # copied to prevent chained assignment
        for row in self.breakdown:
            df2.at[row[0], "quantity"] = row[1]
            df2.at[row[0], "avg_cost"] = row[2]
        df2["quantity"] = df2["quantity"].fillna(method="ffill")
        df2["price"] = df2["price"].fillna(method="ffill")
        df2["avg_cost"] = df2["avg_cost"].fillna(method="ffill")
        df2["price"] = pd.to_numeric(df2["price"])
        df2.loc[df2['quantity'] <= 0, 'Long/Short'] = -1
        df2.loc[df2['quantity'] > 0, 'Long/Short'] = 1

        df2["pct_change"] = (((df2["price"] - df2["avg_cost"])/df2["avg_cost"])*df2["Long/Short"])*100
        df2["pct_change"] = round(df2["pct_change"], 3)
        df2 = df2.reset_index()
        df2 = df2[["date", "quantity", "avg_cost", "price", "pct_change"]]
        df2 = list(df2.itertuples(index=False))
        return df2

    def daily_valuations(self):
        df = pd.DataFrame(self.close_prices, columns=["date", "price"])
        df = df.set_index("date")
        df["quantity"] = float("nan")
        df["market_val"] = float("nan")
        # the prices starting from the first date the security was held
        start_date = self.breakdown[0][0]
        df2 = df.loc[start_date:]
        df2 = df2.copy()  # copied to prevent chained assignment
        # update the quantity at each date
        for row in self.breakdown:
            df2.at[row[0], "quantity"] = row[1]

        df2["price"] = df2["price"].fillna(method="ffill")
        df2["quantity"] = df2["quantity"].fillna(method="ffill")

        df2["price"] = pd.to_numeric(df2["price"])
        df2["market_val"] = round((df2["price"] * df2["quantity"]), 3)

        df2 = df2[["market_val"]]
        new_name = f"market_val_{self.ticker}"
        new_header = {"market_val": new_name}
        df2 = df2.rename(columns=new_header)
        return df2


class Portfolio_Summary(object):
    """docstring for PortfolioSummary."""
    # this is the same as full_table
    def __init__(self):
        self.portfolio_breakdown = pd.DataFrame()

    def add_position(self, close_prices, db_trades, ticker):
        Position = PositionAccounting(close_prices, db_trades, ticker)
        Position_valuation = Position.daily_valuations()
        if self.portfolio_breakdown.empty:
            self.portfolio_breakdown = Position_valuation

        else:
            self.portfolio_breakdown = self.portfolio_breakdown.join(Position_valuation)
        self.portfolio_breakdown = self.portfolio_breakdown.fillna(method="ffill")

    def net_valuations(self):
        valuation = self.portfolio_breakdown.copy()
        valuation["portfolio_val"] = valuation.sum(axis=1)
        valuation = valuation[["portfolio_val"]]
        return valuation

    def generate_hpr(self, flows):
        valuation = self.net_valuations()
        df_flows = pd.DataFrame(flows, columns=["index", "flow"])
        df_flows = df_flows.set_index("index")
        valuation = valuation.join(df_flows)
        valuation = valuation.reset_index()
        # shifts the flows back by previous day
        # to get the previous day valuation including flows
        valuation["flow"] = valuation["flow"].shift(-1)
        valuation["flow"] = valuation["flow"].fillna(value=0)
        valuation["total_portfolio_val"] = valuation.sum(axis=1)
        valuation["pct_change"] = (((valuation["portfolio_val"].shift(-1)/(valuation["total_portfolio_val"]))-1)*100)
        valuation["pct_change"] = round(valuation["pct_change"].shift(1), 2)

        valuation = list(valuation.itertuples(index=False))
        return valuation

class DashboardCharts(object):
    """docstring for DashboardCharts."""

    def worldmap(map_data):
        df = pd.DataFrame(map_data)
        if not df.empty:
            df = df.groupby(["Country", "ISO Code"]).count().reset_index()
            return df
        else:
            return pd.DataFrame(columns=["No. of Positions",
                                         "Country",
                                         "ISO Code"])

    def get_pie_chart(self, portfolio_valuation):

        df = portfolio_valuation.tail(1)
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

    def get_bar_chart(self, portfolio_valuation):
        df = portfolio_valuation.tail(1)
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
