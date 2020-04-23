import requests
import pandas as pd
from sqlalchemy import create_engine
import mysql.connector
import time

av_key = "UHJKNP33E9D8KCRS"
url = "https://www.alphavantage.co/query?"


class Update_existing_prices(object):

    def __init__(self, ticker):
        self.ticker = ticker
        self.market_prices = None
        self._daily_market_prices()

    def _daily_market_prices(self):
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
        self.market_prices = df

    def _store_temp_table(self):
        # stores a temporary file to to the database
        engine = create_engine("mysql://root:E6#hK-rA5!tn@localhost/prescientpricesdb")
        # writes the dataframes to SQL
        # df = self.daily_market_prices()
        self.market_prices.to_sql("temptable",
                                  con=engine,
                                  if_exists="replace",
                                  index=False)
        print(f"Stored temptable for {self.ticker}")

    def update_new_prices(self):
        """ runs a SQL query that appends new prices to the database"""
        self._store_temp_table()
        mydb = mysql.connector.connect(host="localhost",
                                       user="root",
                                       passwd="E6#hK-rA5!tn",
                                       database="prescientpricesdb")
        c = mydb.cursor()
        query = f"""INSERT INTO `{self.ticker}` (`index`, `price`)
                    SELECT t.`index`, t.`price`
                    FROM temptable t
                    WHERE NOT EXISTS
                     (SELECT 1 FROM `{self.ticker}` t2
                      WHERE t2.`index`=t.`index`
                      AND t2.`price`=t.`price`)"""
        c.execute(query)
        mydb.commit()
        c.close()
        mydb.close()
        self._drop_table()

    def _drop_table(self):
        mydb = mysql.connector.connect(host="localhost",
                                       user="root",
                                       passwd="E6#hK-rA5!tn",
                                       database="prescientpricesdb")
        c = mydb.cursor()
        query = """DROP TABLE temptable"""
        c.execute(query)
        c.close()
        mydb.close()


mydb = mysql.connector.connect(host="localhost",
                               user="root",
                               passwd="E6#hK-rA5!tn",
                               database="prescientmaindb")
cur = mydb.cursor(buffered=True)
query = """SELECT DISTINCT ticker FROM watchlist_securities"""
cur.execute(query)

counter = 0
for item in cur.fetchall():
    ticker = item[0].lower()
    Prices = Update_existing_prices(ticker)
    Prices.update_new_prices()

    # 5 API requests per minute; 500 API requests per day
    # After 5 requests delay for 60 seconds
    if counter % 5 == 0:
        time.sleep(60)
    counter += 1
cur.close()
mydb.close()
