A quick script that loads csv data to the Main DataBase

import pandas as pd
import sqlite3

sectors = pd.read_csv(r"other\FTSE Sectors.csv")
ticker_list = pd.read_csv(r"other\stock_tickers_av.csv")

conn = sqlite3.connect(r"instance\MainDB.sqlite")
c = conn.cursor()
# writes the dataframes to SQL
sectors.to_sql("sector_definitions", conn, if_exists="replace", index=False)
ticker_list.to_sql("available_securities", conn, if_exists="replace", index=False)

conn.commit()
c.close()
conn.close()

# The below was done to check choices
# conn = sqlite3.connect(r"instance\MainDB.sqlite")
# c = conn.cursor()
# query = """SELECT name FROM sector_definitions"""
# c.execute(query)
# x = c.fetchall()
# p = [(c,i[0]) for c, i in enumerate(x)]
# print(p)
# conn.commit()
# c.close()
# conn.close()
