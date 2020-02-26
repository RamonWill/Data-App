import sqlite3
import requests
import pandas as pd

# When a user adds a new item to to watchlist perform a check in the views.py
# if the item has never existed add it to the database, otherwise do nothing


class Price_Update(object):

    def __init__(self, ticker):
        self.ticker = ticker

    def av_table(self):
        parameters = {"apikey": "av_key",
                      "function": "TIME_SERIES_DAILY",
                      "symbol": self.ticker}
        response = requests.get(url, params=parameters)
        response_json = response.json()
        data = response_json['Time Series (Daily)']

        df = pd.DataFrame.from_dict(data,
                                    orient="index",
                                    columns=["4. close"])
        df = df.rename(columns={"4. close": "price"})
        df = df.reset_index()
        return df

    def import_prices(self):
        conn = sqlite3.connect(r"C:\Users\Owner\Documents\Data-App\Prescient\Security_PricesDB.db")
        # writes the dataframes to SQL
        df = self.av_table()
        df.to_sql(self.ticker, conn, if_exists="replace", index=False)
        print(f"The Database has been updated with the table {self.ticker}")

#
#
# conn = sqlite3.connect(r"C:\Users\Owner\Documents\Data-App\Prescient\Security_PricesDB.db")
# c = conn.cursor()
#
# query = """SELECT name FROM sqlite_master
# WHERE type='table'and name=:ticker
# ORDER BY name;
# """
# ticker = "GOOG"
# param = {"ticker": ticker}
# tables = c.execute(query, param).fetchone()
# c.close()
# conn.close()
# # If its none then load the price from alpha vantage for the last 100 days
# # else do nothing
# av_key = "UHJKNP33E9D8KCRS"
# url = "https://www.alphavantage.co/query?"
# if tables is None:
#     x = Price_Update(ticker)
#     x.import_prices()
# else:
#     print(f"{ticker} already exists")
