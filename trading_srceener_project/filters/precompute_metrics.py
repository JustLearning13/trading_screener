# precompute_filtered_metrics.py

import pandas as pd
import yfinance as yf
from tqdm import tqdm

# === CONFIGURATION ===
min_price = 5.00
min_volume = 100_000
min_market_cap = 100_000_000
ma_periods = [50, 200]  # moving averages of interest

# === Load trend slope files for filtering ===
sector_slopes = pd.read_csv("data/sector_slopes.csv")
industry_slopes = pd.read_csv("data/industry_slopes.csv")

# Filter only sectors and industries with positive MA50 slope
uptrending_sectors = set(sector_slopes[sector_slopes["Slope"] > 0]["Sector"])
uptrending_industries = set(industry_slopes[industry_slopes["Slope"] > 0]["Industry"])

# === Load ticker base list ===
all_tickers = pd.read_csv("data/all_tickers.csv")

# === Filter only those in uptrending sectors & industries ===
filtered = all_tickers[
    (all_tickers["Sector"].isin(uptrending_sectors)) &
    (all_tickers["Industry"].isin(uptrending_industries))
].dropna(subset=["Ticker"]).copy()

print(f"🎯 {len(filtered)} tickers belong to uptrending sectors and industries.")

# === Result storage ===
results = []

# === Iterate over filtered tickers ===
for _, row in tqdm(filtered.iterrows(), total=len(filtered), desc="Precomputing metrics"):
    symbol = row["Ticker"]
    try:
        try:
            t = yf.Ticker(symbol)
            info = t.info

            # 🧱 Skip if we got no info (bad or delisted ticker)
            if not info or "regularMarketPrice" not in info:
                continue

        except Exception as e:
            print(f"⚠️ {symbol}: Error retrieving info - {e}")
            continue
        price = info.get("previousClose", 0)
        volume = info.get("averageVolume", 0)
        market_cap = info.get("marketCap", 0)

        if price < min_price or volume < min_volume or market_cap < min_market_cap:
            continue

        hist = t.history(period="1y")
        if hist.empty:
            continue

        ma_data = {}
        for p in ma_periods:
            if len(hist) >= p:
                ma = hist["Close"].tail(p).mean()
                ma_data[f"MA{p}"] = round(ma, 2)
            else:
                ma_data[f"MA{p}"] = None

        if price > ma_data["MA50"] and price > ma_data["MA200"]:
            results.append({
                "Ticker": symbol,
                "Sector": row["Sector"],
                "Industry": row["Industry"],
                "MarketCap": market_cap,
                "Close": round(price, 2),
                **ma_data
            })

    except Exception:
        continue

# === Save result ===
df_out = pd.DataFrame(results)
df_out.to_csv("data/precomputed_metrics.csv", index=False)
print(f"✅ Saved {len(df_out)} filtered tickers to precomputed_metrics.csv")
