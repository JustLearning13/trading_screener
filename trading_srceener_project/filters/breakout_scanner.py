# scanner.py

import yfinance as yf
import pandas as pd
from datetime import datetime, time

# === CONFIGURATION ===
min_price = 5.00
min_volume = 100_000
min_ma50_slope = 0  # 🟢 Keep only stocks where MA50 is trending up
volume_avg_window = 5
spike_multiplier = 2.0

# === MARKET CLOCK ===
def get_percent_of_day_complete():
    now = datetime.now().time()
    market_open = time(9, 30)
    market_close = time(16, 0)
    total_minutes = (market_close.hour - market_open.hour) * 60 + (market_close.minute - market_open.minute)
    minutes_elapsed = (now.hour - market_open.hour) * 60 + (now.minute - market_open.minute)
    if now < market_open:
        return 0.01
    elif now > market_close:
        return 1.0
    else:
        return max(0.01, min(1.0, minutes_elapsed / total_minutes))

# === VOLUME SPIKE CHECK ===
def detect_volume_spikes(tickers, percent_of_day):
    results = []
    for ticker in tickers:
        try:
            data = yf.Ticker(ticker).history(period=f"{volume_avg_window + 3}d")
            if data.empty or len(data) < volume_avg_window + 1:
                continue

            data["avg_volume"] = data["Volume"].rolling(window=volume_avg_window).mean()
            latest = data.iloc[-1]
            volume_so_far = latest["Volume"]
            avg_volume = latest["avg_volume"]
            projected_volume = volume_so_far / percent_of_day

            if projected_volume > spike_multiplier * avg_volume:
                results.append({
                    "Ticker": ticker,
                    "Projected Volume": int(projected_volume),
                    "Avg Volume": int(avg_volume),
                    "Volume So Far": int(volume_so_far)
                })

        except Exception as e:
            print(f"⚠️ {ticker}: {e}")
            continue

    return results

# === MAIN ===
if __name__ == "__main__":
    print("📄 Loading precomputed metrics...")
    df = pd.read_csv("precomputed_metrics.csv")

    print(f"🔍 Filtering stocks: price ≥ ${min_price}, volume ≥ {min_volume}, MA50_slope > {min_ma50_slope}")
    tickers = df["Ticker"].dropna().tolist()

    percent_of_day = get_percent_of_day_complete()
    print(f"⏱ Market Day Progress: {percent_of_day:.2%}\n")

    spike_results = detect_volume_spikes(tickers, percent_of_day)

    if spike_results:
        pd.DataFrame(spike_results).to_csv("spike_candidates.csv", index=False)
        print(f"💾 Saved {len(spike_results)} spike(s) to spike_candidates.csv")
    else:
        print("😴 No volume spikes to save.")

    print("\n✅ Scan complete.")
