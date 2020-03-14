import pandas as pd
import requests
import sqlite3
import os

av_key = "UHJKNP33E9D8KCRS"
url = "https://www.alphavantage.co/query?"
MAIN_DATABASE = os.path.abspath(os.path.join(__file__, "../..", "MainDB.db"))
PRICE_DATABASE = os.path.abspath(os.path.join(__file__, "../..", "Security_PricesDB.db"))

""" Changes to be made, distinguish between new tickers and old tickers.
new tickers will need to be imported, old tickers will need to be updated
new tickers should always take priority"""


class Price_Update(object):

    def __init__(self, db_tickers):
        self.db_tickers = db_tickers

    def get_list(self):
        if self.db_tickers == []:
            raise ValueError("The list is empty")
        else:
            all_tickers = [ticker[0] for ticker in self.db_tickers]
            return all_tickers

    def av_price(self, ticker):
        parameters = {"apikey": "av_key",
                      "function": "TIME_SERIES_DAILY",
                      "symbol": ticker}
        response = requests.get(url, params=parameters)
        response_json = response.json()
        data = response_json['Time Series (Daily)']

        df = pd.DataFrame.from_dict(data,
                                    orient="index",
                                    columns=["4. close"])
        df = df.rename(columns={"4. close": "price"})
        df = df.reset_index()
        return df

    def price_import(self):
        all_tickers = self.get_list()
        conn = sqlite3.connect(PRICE_DATABASE)
        # writes the dataframes to SQL
        for ticker in all_tickers:
            df = self.av_price(ticker)
            df.to_sql(ticker, conn, if_exists="replace", index=False)
            print(f"{PRICE_DATABASE} has been updated with the table {ticker}")
        print("End")


conn = sqlite3.connect(MAIN_DATABASE)
distinct_query = """SELECT DISTINCT ticker from watchlist_securities"""
c = conn.cursor()
tickers = c.execute(distinct_query).fetchall()
#tickers = [("AAL", "AAL"), ("AAP", "AAP"), ("CME", "CME"), ("KO", "KO"), ("SRE","SRE")]
prices = Price_Update(tickers)
c.close()
conn.close()
prices.price_import()
