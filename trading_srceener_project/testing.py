import pandas as pd
df = pd.read_csv("data/price_history.csv")
print(df["Ticker"].nunique())
