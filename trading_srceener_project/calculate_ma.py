import pandas as pd
import numpy as np
from scipy.stats import linregress

# CONFIGURATION
PRICE_HISTORY_FILE = "data/price_history.csv"
TICKER_INFO_FILE = "data/all_tickers.csv"
MA_TRENDS_FILE = "data/ma_trends.csv"
SECTOR_INDUSTRY_SLOPES_FILE = "data/sector_industry_slopes.csv"
MOVING_AVERAGES = [20, 50, 200]
TREND_WINDOW = 21

# Load data
price_df = pd.read_csv(PRICE_HISTORY_FILE, parse_dates=["Date"])
ticker_info = pd.read_csv(TICKER_INFO_FILE)

# Compute all requested MAs
for ma in MOVING_AVERAGES:
    price_df[f"MA{ma}"] = price_df.groupby("Ticker")["Close"].transform(lambda x: x.rolling(ma).mean())

# Compute MA slope for each MA
trend_results = []

def calculate_slope(series):
    y = series.dropna().tail(TREND_WINDOW)
    if len(y) < TREND_WINDOW:
        return np.nan
    x = range(len(y))
    slope, _, _, _, _ = linregress(x, y)
    return slope

for ma in MOVING_AVERAGES:
    slopes = price_df.groupby("Ticker")[f"MA{ma}"].apply(calculate_slope).reset_index(name=f"MA{ma}_slope")
    trend_results.append(slopes.set_index("Ticker"))

# Combine all slope results
ma_trends = pd.concat(trend_results, axis=1).reset_index()
ma_trends.to_csv(MA_TRENDS_FILE, index=False)

# Merge sector and industry info
merged = price_df.merge(ticker_info[["Ticker", "Sector", "Industry"]], on="Ticker", how="left")

# Calculate average daily return for sector/industry
merged["DailyReturn"] = merged.groupby("Ticker")["Close"].pct_change(fill_method=None)
sector_returns = merged.groupby(["Date", "Sector"])["DailyReturn"].mean().unstack()
industry_returns = merged.groupby(["Date", "Industry"])["DailyReturn"].mean().unstack()

# Calculate trend slope for sector/industry
sector_slopes = sector_returns.tail(TREND_WINDOW).apply(lambda x: linregress(range(len(x)), x)[0])
industry_slopes = industry_returns.tail(TREND_WINDOW).apply(lambda x: linregress(range(len(x)), x)[0])

# Save to file
sector_industry_df = pd.DataFrame({
    "Sector": sector_slopes.index,
    "Sector_slope": sector_slopes.values
}).merge(
    pd.DataFrame({
        "Industry": industry_slopes.index,
        "Industry_slope": industry_slopes.values
    }), how="outer", left_index=True, right_index=True
)

sector_industry_df.to_csv(SECTOR_INDUSTRY_SLOPES_FILE, index=False)
print("✅ MA and sector/industry trend calculations completed.")
