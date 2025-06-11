import os
import pandas as pd
import yfinance as yf
from datetime import timedelta
from tqdm import tqdm
import time

from config.config import SLEEP_BETWEEN_CALLS # Pause to avoid getting rate-limited
from config.config import BATCH_SAVE_SIZE # Save interim results every N tickers

PRICE_HISTORY_FILE = "data/price_history.csv"
TICKER_FILE = "data/all_tickers.csv"

# Read the existing price history and return a dict of {ticker: last_date}.
def get_last_dates():

    if not os.path.exists(PRICE_HISTORY_FILE):
        return {}

    df = pd.read_csv(PRICE_HISTORY_FILE, parse_dates=["Date"])
    last_dates = df.groupby("Ticker")["Date"].max().to_dict()
    return last_dates

# Fetch new history starting from the day after the last known date
def fetch_new_history(ticker, start_date):
 
    try:
        start_date = start_date + timedelta(days=1)
        t = yf.Ticker(ticker)
        hist = t.history(start=start_date)

        if hist.empty:
            return None

        hist = hist[["Open", "High", "Low", "Close", "Volume"]].copy()
        hist["Ticker"] = ticker
        hist = hist.reset_index()  # Make Date a column again
        return hist

    except Exception as e:
        print(f"⚠️ {ticker} fetch failed: {e}")
        return None

def main():
    os.makedirs("data", exist_ok=True)

    last_dates = get_last_dates()
    tickers_df = pd.read_csv(TICKER_FILE)
    all_tickers = tickers_df["Ticker"].dropna().unique()

    updates = []
    for i, ticker in enumerate(tqdm(all_tickers, desc="Updating tickers")):
        last_date = last_dates.get(ticker, None)
        if last_date is None:
            continue  # skip tickers not yet in price_history.csv

        new_data = fetch_new_history(ticker, pd.to_datetime(last_date))
        if new_data is not None:
            updates.append(new_data)

        if (i + 1) % BATCH_SAVE_SIZE == 0 and updates:
            combined = pd.concat(updates)
            combined.to_csv(PRICE_HISTORY_FILE, mode='a', header=False, index=False)
            updates.clear()

        time.sleep(SLEEP_BETWEEN_CALLS)

    if updates:
        combined = pd.concat(updates)
        combined.to_csv(PRICE_HISTORY_FILE, mode='a', header=False, index=False)

    print("✅ Price history updated.")

if __name__ == "__main__":
    main()
