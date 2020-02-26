import sqlite3
import requests
import pandas as pd

av_key = "UHJKNP33E9D8KCRS"
url = "https://www.alphavantage.co/query?"


class Update_existing_prices(object):

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

    def store_temp_table(self):
        # stores a temporary file to to the database
        conn = sqlite3.connect(r"C:\Users\Owner\Documents\Data-App\Prescient\Security_PricesDB.db")
        # writes the dataframes to SQL
        df = self.av_table()
        df.to_sql("TempTable", conn, if_exists="replace", index=False)
        print("Stored TempTable")

    def update_new_prices(self):
        """ runs a SQL query that appends non-duplicates to the existing database"""
        conn = sqlite3.connect(r"C:\Users\Owner\Documents\Data-App\Prescient\Security_PricesDB.db")
        c = conn.cursor()
        query = f"""INSERT INTO {self.ticker}  ('index', 'price')
                   SELECT t.'index', t.'price'
                   FROM TempTable t
                   WHERE NOT EXISTS
                    (SELECT 1 FROM {self.ticker} t2
                    WHERE t2.'index'=t.'index'
                    AND t2.'price'=t.'price')"""
        c.execute(query)
        changes = c.rowcount
        conn.commit()
        print(f"Rows inserted into table {self.ticker}: {changes}")
        c.close()
        conn.close()



# ticker = "GOOG"  # I just deleted the prices. the latest is as of 14th
# the_list = [ticker]
# for i in the_list:
#     x = Update_existing_prices(i)
#     x.store_temp_table()
#     x.update_new_prices()
