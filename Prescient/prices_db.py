import pandas as pd
import requests
import sqlite3

av_key = "UHJKNP33E9D8KCRS"
url = "https://www.alphavantage.co/query?"


def add_new_security(symbol):
    parameters = {"apikey": "av_key",
                  "function": "TIME_SERIES_DAILY",
                  "symbol": symbol}
    response = requests.get(url, params=parameters)
    x = response.json()
    p = x['Time Series (Daily)']

    extract = pd.DataFrame.from_dict(p, orient="index", columns=["4. close"])
    extract = extract.rename(columns={"4. close": "price"})
    extract.to_csv(r"other\price_history\{}.csv".format(symbol))
    print(f"A .csv file has been created for {symbol}.")
    extract_final = extract.reset_index()
    return extract_final


def add_security_table(symbol, dataframe):
    conn = sqlite3.connect(r"instance\price_data.sqlite")
    # writes the dataframes to SQL
    dataframe.to_sql(symbol, conn, if_exists="append", index=False)
    print(f"The database has been updated for {symbol}")

# get_holding_summary()
# s = ["AMZN", "AAPL"]
# for symbol in s:
#     df = add_new_security(symbol)
#     add_security_table(symbol, df)
