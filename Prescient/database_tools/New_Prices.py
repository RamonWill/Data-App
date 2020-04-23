import requests
import pandas as pd
from sqlalchemy import create_engine

av_key = "UHJKNP33E9D8KCRS"
url = "https://www.alphavantage.co/query?"


class Price_Update(object):
    """
    When a user adds a new security to their watchlist a check will be
    initiated to see if the security already has prices in the database.
    If prices don't exist then prices for the previous 100 days will be
    addded to the database.
    """

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
