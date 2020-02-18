import pandas as pd
import os
import sqlite3

# A quick script that loads csv data to the Main DataBase using raw sql

FILE_PATH = os.path.abspath(os.path.dirname(__file__))
DATABASE_FILE = os.path.abspath(os.path.join(__file__, "../..", "MainDB.db"))

sector_file = os.path.join(FILE_PATH, "csv_files", "FTSE_Sectors.csv")
tickers_file = os.path.join(FILE_PATH, "csv_files", "stock_tickers_av.csv")

sectors = pd.read_csv(sector_file)
ticker_list = pd.read_csv(tickers_file)

conn = sqlite3.connect(DATABASE_FILE)

sectors.to_sql("sector_definitions",
               conn,
               if_exists="append",
               index=False)

ticker_list.to_sql("available_securities",
                   conn,
                   if_exists="append",
                   index=False)
