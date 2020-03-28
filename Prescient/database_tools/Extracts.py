import pandas as pd
from collections import deque, namedtuple


class PositionSummary(object):
    """
    Takes the trade history for a user's watchlist from the database and it's
    ticker. Then applies the FIFO accounting methodology to calculate the
    overall positions status i.e. final open lots, average cost and a breakdown
    of the open lots.

    This is a queue data structure.
    """

    def __init__(self, trade_history):

        self.trade_history = trade_history
        self.average_cost = None
        self.open_lots = None
        self.ticker = self.set_ticker()

        self.buy_quantities = deque([])
        self.buy_prices = deque([])
        self.buy_dates = deque([])
        self.sell_quantities = deque([])
        self.sell_prices = deque([])
        self.sell_dates = deque([])
        self.open_direction = None

        self.breakdown = []
        self.net_position = 0

        self.__apply_fifo()

    def __repr__(self):
        return "<Ticker: {}, Quantity: {}>".format(self.ticker,
                                                   self.net_position)

    def set_ticker(self):
        tickers = set([i[0] for i in self.trade_history])
        if len(tickers) == 1:
            return self.trade_history[0][0]
        else:
            raise ValueError("The Trade History for this security contains multiple tickers")

    def total_open_lots(self):
        """ returns the sum of the positions open lots"""
        if self.open_direction == "long":
            return sum(self.buy_quantities)
        elif self.open_direction == "short":
            return sum(self.sell_quantities)
        else:
            return None

    def total_mv(self):
        """Returns the position's market value"""
        if self.buy_quantities and self.open_direction == "long":
            return sum(quantity*price for quantity, price in zip(self.buy_quantities, self.buy_prices))
        elif self.sell_quantities and self.open_direction == "short":
            return sum(quantity*price for quantity, price in zip(self.sell_quantities, self.sell_prices))
        else:
            return None

    def avg_cost(self):
        """Returns the weighted average cost of the positions open lots."""
        open_lots = self.total_open_lots()
        if open_lots == 0 or not open_lots:
            return 0

        return abs(self.total_mv()/self.total_open_lots())

    def remove_trade(self, direction):
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

    def __collapse_trade(self):
        if self.sell_quantities:
            if self.sell_quantities[0] >= 0:
                self.remove_trade("sell")

        if self.buy_quantities:
            if self.buy_quantities[0] <= 0:
                self.remove_trade("buy")

    def get_summary(self):
        """
        Returns a named tuple of the ticker, net position and the average
        price of the opens lots
        """
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

    def __set_direction(self):
        """
        Checks if there has been a reversal in the users overall
        trade direction and sets that direction accordingly.
        """
        if self.open_direction == "short" and self.net_position > 0:
            self.open_direction = "long"
        elif self.open_direction == "long" and self.net_position < 0:
            self.open_direction = "short"

    def set_initial_trade(self):

        units = self.trade_history[0].quantity
        price = self.trade_history[0].price
        date = self.trade_history[0].date
        if units >= 0:
            self.open_direction = "long"
            self.add("buy", units, price, date)

        else:
            self.open_direction = "short"
            self.add("sell", units, price, date)
        self.average_cost = self.avg_cost()
        self.net_position = self.total_open_lots()
        self.breakdown.append([date, self.net_position, self.average_cost])

    def __apply_fifo(self):
        """
        This algorithm iterate over the trade history. It sets the
        initial trade direction to get the initial open lots and then increases
        or closes lots based on each trade.

        In the event that a position was initally long then becomes short or
        vice versa the open lots will be increased or closed accordingly.
        """
        if self.trade_history:
            self.set_initial_trade()
        else:
            return []

        trades = len(self.trade_history)
        c1 = 1  # counter

        while c1 < trades:
            units = self.trade_history[c1].quantity
            price = self.trade_history[c1].price
            date = self.trade_history[c1].date

            if units*self.net_position > 0:  # if true both trades have the same sign
                if self.open_direction == "long":
                    self.add("buy", units, price, date)
                else:
                    self.add("sell", units, price, date)
            elif units*self.net_position == 0:  # position is flat
                if units >= 0:
                    self.open_direction = "long"
                    self.add("buy", units, price, date)

                else:
                    self.open_direction = "short"
                    self.add("sell", units, price, date)

            else:  # both trades are in different directions
                if self.open_direction == "long":
                    self.add("sell", units, price, date)
                    # while the lots are not empty
                    while self.sell_quantities and self.buy_quantities:

                        if abs(self.sell_quantities[0]) >= self.buy_quantities[0]:
                            self.sell_quantities[0] += self.buy_quantities[0]
                            self.remove_trade("buy")

                        else:
                            temp = self.remove_trade("sell")
                            self.buy_quantities[0] += temp
                    self.net_position += units  # subtract units from net position

                else:  # self.open_direction == "short"
                    self.add("buy", units, price, date)
                    while self.sell_quantities and self.buy_quantities:
                        if self.buy_quantities[0] >= abs(self.sell_quantities[0]):
                            self.buy_quantities[0] += self.sell_quantities[0]
                            self.remove_trade("sell")
                        else:
                            temp = self.remove_trade("buy")
                            self.sell_quantities[0] += temp
                    self.net_position += units

            self.__collapse_trade()
            self.__set_direction()
            self.average_cost = round(self.avg_cost(), 4)
            self.net_position = self.total_open_lots()
            self.breakdown.append([date, self.net_position, self.average_cost])
            c1 += 1


class PositionAccounting(PositionSummary):
    """
    Inherits from the Position Summary and applies accounting methods
    to a Position
    """

    def __init__(self, close_prices, trade_history):
        PositionSummary.__init__(self, trade_history)
        self.close_prices = close_prices  # Daily market prices

    def performance_table(self):
        """
        Combines the position breakdown with the daily prices to calculate
        daily unrealised P&L. The Daily unrealised P&L is the difference
        between the postion's weighted average cost and the market
        price.
        """
        df = pd.DataFrame(self.close_prices, columns=["date", "price"])
        df = df.set_index("date")
        df["quantity"] = float("nan")
        df["avg_cost"] = float("nan")
        start_date = str(self.breakdown[0][0])
        df2 = df.loc[start_date:]
        df2 = df2.copy()  # copied to prevent chained assignment
        for row in self.breakdown:
            df2.at[str(row[0]), "quantity"] = row[1]
            df2.at[str(row[0]), "avg_cost"] = row[2]
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
        """
        Combines the position breakdown with the daily prices to calculate
        daily market value. The Daily market value is the positions quantity
        multiplied by the market price.
        """
        df = pd.DataFrame(self.close_prices, columns=["date", "price"])
        df = df.set_index("date")
        df["quantity"] = float("nan")
        df["market_val"] = float("nan")
        # the prices starting from the first date the security was held
        start_date = str(self.breakdown[0][0])

        df2 = df.loc[start_date:]
        df2 = df2.copy()  # copied to prevent chained assignment
        # update the quantity at each date
        for row in self.breakdown:
            df2.at[str(row[0]), "quantity"] = row[1]
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
    """
    This is a collection of the Positions for the user accounts, priced as of
    the latest market prices
    """
    # this is the same as full_table
    def __init__(self):
        self.portfolio_breakdown = pd.DataFrame()

    def add_position(self, close_prices, trade_history):
        """
        Adds each positions daily market value to the portfolio breakdown.
        """
        Position = PositionAccounting(close_prices, trade_history)
        Position_valuation = Position.daily_valuations()
        if self.portfolio_breakdown.empty:
            self.portfolio_breakdown = Position_valuation

        else:
            self.portfolio_breakdown = self.portfolio_breakdown.join(Position_valuation)
        self.portfolio_breakdown = self.portfolio_breakdown.fillna(method="ffill")

    def net_valuations(self):
        """
        returns the portfolios daily market value
        """
        valuation = self.portfolio_breakdown.copy()
        valuation["portfolio_val"] = valuation.sum(axis=1)
        valuation = valuation[["portfolio_val"]]
        return valuation

    def convert_flows(self, flows):
        """
        Using the Holding Period Return (HPR) methodology. Purchases of
        securities are accounted as fund inflows and the sale of securities are
        accounted as increases in cash.

        By creating the cumulative sum of these values we can maintain an
        accurate calculation of the HPR which can be distorted as purchases and
        sells are added to the trades.
        """
        df_flows = pd.DataFrame(flows, columns=["date", "flows"])
        df_flows["cash"] = float("nan")
        df_flows["inflows"] = float("nan")
        df_flows["date"] = df_flows["date"].astype(str)
        df_flows["cash"] = df_flows.loc[df_flows['flows'] > 0, "flows"]
        df_flows["inflows"] = df_flows.loc[df_flows['flows'] <= 0, "flows"]
        df_flows["cash"] = df_flows["cash"].cumsum()
        df_flows["inflows"] = df_flows["inflows"].abs()
        df_flows = df_flows.set_index("date")  # need to sum groupby date
        df_flows = df_flows.groupby([df_flows.index]).sum()
        df_flows = df_flows.drop(columns=['flows'])
        df_flows = df_flows.replace({'cash': 0, 'inflows': 0}, float("nan"))
        return df_flows

    def generate_hpr(self, flows):
        """
        Where PortVal = Portfolio Value. The Formula for the Daily
        Holding Period Return (HPR) is calculated as follows:
        (Ending PortVal) / (Previous PortVal After Cash Flow) – 1.

        1. Add the cash from the sale of securities to the portfolio value.
        2. shift the total portfolio value column to allow us to easily
           caclulate the Percentage change before and after each cash flow.
        Returns a named tuple of daily HPR % changes.
        """
        df_flows = self.convert_flows(flows)
        valuation = self.net_valuations()
        valuation = valuation.join(df_flows)
        valuation["cash"] = valuation["cash"].fillna(method="ffill")
        valuation = valuation.fillna(value=0)
        valuation["total_portfolio_val"] = valuation["portfolio_val"] + valuation["cash"]
        valuation["portfolio_val"] = valuation["total_portfolio_val"].shift(1)
        valuation["pct_change"] = ((valuation["total_portfolio_val"])/(valuation["portfolio_val"]+valuation["inflows"])-1)*100
        valuation["pct_change"] = round(valuation["pct_change"], 3)
        valuation = valuation.reset_index()
        valuation = list(valuation.itertuples(index=False))
        return valuation


class DashboardCharts(object):
    """
    Various methods that take portfolio data from the database and cleans the
    data so that it can be plotted into graphs on the front end
    """

    def worldmap(map_data):
        """
        Groups the users positions by the country and ISO Count
        the aggregagte function used here is COUNT
        """
        df = pd.DataFrame(map_data)
        if not df.empty:
            df = df.groupby(["Country", "ISO Code"]).count().reset_index()
            return df
        else:
            return pd.DataFrame(columns=["No. of Positions",
                                         "Country",
                                         "ISO Code"])

    def get_pie_chart(self, portfolio_valuation):
        """
        Returns a named tuple of the largest positions by absolute exposure
        in descending order. For the portfolios that contain more than 6
        positions the next n positons are aggregated to and classified
        'as other'
        """
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
        """
        Returns a named tuple of the 5 largest positions by absolute exposure
        in descending order
        """
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
