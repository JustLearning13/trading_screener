import pandas as pd
from datetime import datetime,timedelta
#df = pd.read_csv("data/price_history.csv")
#print(df["Ticker"].nunique())
import yfinance as yf
data = yf.Ticker("AAPL").history(period="5d")
print(data.tail())
print(datetime.today().strftime('%Y-%m-%d'))
print(yf.Ticker("AAPL").history(start='2025-06-06', end=(datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')))