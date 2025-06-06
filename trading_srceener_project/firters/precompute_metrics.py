from tqdm import tqdm
import pandas as pd
import yfinance as yf
import numpy as np
import time


# Configuration
min_price = 5.0
min_volume = 100_000
min_market_cap = 100_000_000
ma_periods = [20, 50, 150, 200]
ma_slope_check = 50  # Only apply slope filter to MA50

# Load tickers
df = pd.read_csv("all_tickers.csv")
tickers = df["Ticker"].dropna().unique().tolist()

# Output
results = []

# Process each ticker with progress bar
for symbol in tqdm(tickers, desc="Processing tickers"):
    try:
        t = yf.Ticker(symbol)
        info = t.info

        # Basic filters
        price = info.get("regularMarketPrice", 0)
        volume = info.get("volume", 0)
        market_cap = info.get("marketCap", 0)

        if price < min_price or volume < min_volume or (market_cap and market_cap < min_market_cap):
            continue

        # Historical data
        hist = t.history(period="1y")
        if hist.empty or len(hist) < max(ma_periods) + 5:
            continue

        close_prices = hist["Close"]

        ma_values = {}
        ma_slopes = {}

        for period in ma_periods:
            ma = close_prices.rolling(window=period).mean()
            ma_values[f"MA{period}"] = ma.iloc[-1]

            # Compute slope for selected MA period
            if period == ma_slope_check:
                recent_ma = ma.dropna().tail(10)
                if len(recent_ma) < 2:
                    break
                x = np.arange(len(recent_ma))
                y = recent_ma.values
                slope, _ = np.polyfit(x, y, 1)
                ma_slopes[f"MA{period}_slope"] = slope

                # Filter out downward slope
                if slope < 0:
                    break

        else:
            results.append({
                "Ticker": symbol,
                "Price": price,
                "Volume": volume,
                "MarketCap": market_cap,
                **ma_values,
                **ma_slopes
            })

    except Exception as e:
        continue

# Save results
output_df = pd.DataFrame(results)
output_df.to_csv("precomputed_metrics.csv", index=False)


