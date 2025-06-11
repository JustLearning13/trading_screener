import pandas as pd
from tqdm import tqdm

# === CONFIGURATION ===
volume_avg_window = 5
volume_multiplier_threshold = 2.0

# === Load precomputed and historical data ===
metrics_df = pd.read_csv("data/precomputed_metrics.csv")
price_df = pd.read_csv("data/price_history.csv")

# === Get the latest date in the file ===
latest_date = price_df["Date"].max()

# === Result storage ===
breakout_candidates = []




# === Scan for volume spikes ===
for _, row in tqdm(metrics_df.iterrows(), total=len(metrics_df), desc="Scanning for volume breakouts"):
    ticker = row["Ticker"]

    price_hist = price_df[price_df["Ticker"] == ticker].sort_values("Date")
    if len(price_hist) < volume_avg_window + 1:
        continue

    # Get today's volume
    today_volume_row = price_hist[price_hist["Date"] == latest_date]
    if today_volume_row.empty:
        continue

    today_volume = today_volume_row["Volume"].values[0]

    # Compute average volume from N days before today
    recent_volume = price_hist[price_hist["Date"] < latest_date]["Volume"].tail(volume_avg_window)
    if len(recent_volume) < volume_avg_window:
        continue

    avg_volume = recent_volume.mean()

    if today_volume > volume_multiplier_threshold * avg_volume:
        breakout_candidates.append({
            "Ticker": ticker,
            "Sector": row["Sector"],
            "Industry": row["Industry"],
            "Close": row["Close"],
            "MA50": row["MA50"],
            "MA200": row["MA200"],
            "Today Volume": int(today_volume),
            f"Avg Volume ({volume_avg_window}d)": int(avg_volume),
            "Multiplier": round(today_volume / avg_volume, 2)
        })
        # === Output results ===
df_breakouts = pd.DataFrame(breakout_candidates)
df_breakouts.to_csv("data/breakout_candidates.csv", index=False)
