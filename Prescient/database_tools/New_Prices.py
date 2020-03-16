import requests
import pandas as pd
from sqlalchemy import create_engine
# When a user adds a new item to to watchlist perform a check in the views.py
# if the item has never existed add it to the database, otherwise do nothing
# USE CRON TO UPDATE PRICES DAILY
av_key = "UHJKNP33E9D8KCRS"
url = "https://www.alphavantage.co/query?"


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
        engine = create_engine("mysql://root:E6#hK-rA5!tn@localhost/prescientpricesdb")
        # writes the dataframes to SQL
        df = self.av_table()
        df.to_sql(self.ticker, con=engine, if_exists="replace", index=False)
        print(f"The Database has been updated with the table {self.ticker}")
