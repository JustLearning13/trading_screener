
import pandas as pd
import yfinance as yf
from collections import defaultdict
from tqdm import tqdm

# ------------------- SETTINGS -------------------
CSV_FILE = "fmp_all_tickers_enriched.csv"    # Your enriched ticker file
DAYS_BACK = 20                               # How many days to measure uptrend
GROUP_BY = "Industry"                        # Or "Sector"
MIN_STOCKS_IN_GROUP = 5                      # Ignore micro-groups
PRICE_THRESHOLD = 1                          # Skip penny stocks
# ------------------------------------------------

# Load enriched tickers
df = pd.read_csv(CSV_FILE)

# Drop empty or unknown industry
df = df[df[GROUP_BY].notnull()]
df = df[df["Price"] > PRICE_THRESHOLD]

# Map: industry/sector ? list of tickers
groups = df.groupby(GROUP_BY)["Ticker"].apply(list).to_dict()

# Result container
group_returns = []

print(f"?? Analyzing {DAYS_BACK}-day returns by {GROUP_BY}...")

for group_name, tickers in tqdm(groups.items()):
    if len(tickers) < MIN_STOCKS_IN_GROUP:
        continue

    returns = []

    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(period=f"{DAYS_BACK + 5}d")
            if len(hist) < DAYS_BACK:
                continue
            start = hist["Close"].iloc[-DAYS_BACK]
            end = hist["Close"].iloc[-1]
            ret = (end - start) / start
            returns.append(ret)
        except Exception:
            continue

    if returns:
        avg_return = sum(returns) / len(returns)
        group_returns.append({
            GROUP_BY: group_name,
            "AverageReturn": round(avg_return * 100, 2),
            "NumStocks": len(returns)
        })

# Create dataframe and sort by performance
result_df = pd.DataFrame(group_returns)
result_df = result_df.sort_values("AverageReturn", ascending=False)

# Save result
output_file = f"top_{GROUP_BY.lower()}_trends.csv"
result_df.to_csv(output_file, index=False)

print(f"\n? Done! Saved industry trend report to {output_file}")
print(result_df.head(10))
