import pandas as pd
import os
from sqlalchemy import create_engine
# A quick script that loads csv data to the Main DataBase

FILE_PATH = os.path.abspath(os.path.dirname(__file__))
engine = create_engine("mysql://root:E6#hK-rA5!tn@localhost/prescientmaindb")

sector_file = os.path.join(FILE_PATH, "csv_files", "FTSE_Sectors.csv")
security_details = os.path.join(FILE_PATH, "csv_files", "stock_tickers_av.csv")

sectors = pd.read_csv(sector_file)
tradeable_securities = pd.read_csv(security_details)

sectors.to_sql("sector_definitions",
               con=engine,
               if_exists="append",
               index=False)

tradeable_securities.to_sql("available_securities",
                            con=engine,
                            if_exists="append",
                            index=False)
