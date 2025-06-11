
import os
import time
import pandas as pd
import yfinance as yf
from tqdm import tqdm
from datetime import datetime, timedelta
from pandas.tseries.offsets import DateOffset

from config.config import HISTORICAL_PERIOD
from config.config import SLEEP_BETWEEN_CALLS

# ------------------------ CONFIGURATION ------------------------
INPUT_CSV = "data/all_tickers.csv"
OUTPUT_FILE = "data/price_history.csv"
SAVE_EVERY_N = 100
INACTIVITY_THRESHOLD_DAYS = 10
# ---------------------------------------------------------------

def load_price_history():
    if os.path.exists(OUTPUT_FILE):
        df = pd.read_csv(OUTPUT_FILE, parse_dates=["Date"])
        return df
    return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume", "Ticker"])

def fetch_missing_history(ticker, start_date):
    try:
        t = yf.Ticker(ticker)
        end_date = datetime.today().strftime("%Y-%m-%d")
        hist = t.history(start=start_date.strftime("%Y-%m-%d"), end=end_date, interval="1d")
        if hist.empty:
            return None
        hist = hist[["Open", "High", "Low", "Close", "Volume"]].copy()
        hist["Ticker"] = ticker
        return hist.reset_index()
    except Exception as e:
        print(f"⚠️ {ticker} failed: {e}")
        return None

def save_chunk(data_chunk, append=True):
    mode = 'a' if append and os.path.exists(OUTPUT_FILE) else 'w'
    header = not os.path.exists(OUTPUT_FILE) or not append
    data_chunk.to_csv(OUTPUT_FILE, mode=mode, header=header, index=False)

def main():
    os.makedirs("data", exist_ok=True)

    all_tickers = pd.read_csv(INPUT_CSV)["Ticker"].dropna().unique()
    existing_data = load_price_history()

    if not existing_data.empty:
        last_dates = existing_data.groupby("Ticker")["Date"].max().to_dict()
    else:
        last_dates = {}

    tickers_to_update = []
    today = datetime.today()

    for ticker in all_tickers:
        last_seen = last_dates.get(ticker)
        if last_seen is None:
            tickers_to_update.append(ticker)
        elif (today - last_seen).days <= INACTIVITY_THRESHOLD_DAYS:
            tickers_to_update.append(ticker)

    print(f"📊 Total tickers to process: {len(tickers_to_update)} (skipped inactive)")

    temp_chunk = []

    for i, ticker in enumerate(tqdm(tickers_to_update, desc="Updating history")):
        if ticker in last_dates:
            last_date = last_dates[ticker] + timedelta(days=1)
        else:
            # Determine starting point based on HISTORICAL_PERIOD format
            if HISTORICAL_PERIOD.endswith("y"):
                years = int(HISTORICAL_PERIOD[:-1])
                last_date = today - DateOffset(years=years)
            elif HISTORICAL_PERIOD.endswith("d"):
                days = int(HISTORICAL_PERIOD[:-1])
                last_date = today - timedelta(days=days)
            else:
                raise ValueError("Unsupported HISTORICAL_PERIOD. Use '1y' or '90d' format.")

        new_data = fetch_missing_history(ticker, last_date)

        if new_data is not None and not new_data.empty:
            temp_chunk.append(new_data)

        time.sleep(SLEEP_BETWEEN_CALLS)

        if (i + 1) % SAVE_EVERY_N == 0 and temp_chunk:
            combined = pd.concat(temp_chunk)
            save_chunk(combined)
            temp_chunk.clear()

    if temp_chunk:
        combined = pd.concat(temp_chunk)
        save_chunk(combined)

    print(f"✅ Done at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}! Updated {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
