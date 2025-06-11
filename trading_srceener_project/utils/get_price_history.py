import os
import time
import pandas as pd
import yfinance as yf
from tqdm import tqdm  # For a progress bar
from datetime import datetime

from config.config import HISTORICAL_PERIOD 
from config.config import SLEEP_BETWEEN_CALLS
from config.config import BATCH_SAVE_SIZE

# ------------------------ CONFIGURATION ------------------------
INPUT_CSV = "data/all_tickers.csv"       # Your master list of tickers
OUTPUT_FILE = "data/price_history.csv"   # File to store all historical price data
# ---------------------------------------------------------------

# Load previously fetched tickers to avoid re-downloading them
def load_existing_tickers():
    if os.path.exists(OUTPUT_FILE):
        df = pd.read_csv(OUTPUT_FILE, usecols=["Ticker"])
        return set(df["Ticker"].unique())
    return set()

# Pull 1 year of daily OHLCV (Open, High, Low, Close, Volume)
def fetch_history(ticker):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=HISTORICAL_PERIOD, interval="1d")

        if hist.empty:
            return None

        # Keep only the essential columns and format for appending
        hist = hist[["Open", "High", "Low", "Close", "Volume"]].copy()
        hist["Ticker"] = ticker
        hist = hist.reset_index()  # Make the Date column visible

        return hist

    except Exception as e:
        print(f"❌ {ticker} failed: {e}")
        return None

# Write a batch of data to CSV. Use append mode to grow the file
def save_chunk(data_chunk, append=True):
    mode = 'a' if append and os.path.exists(OUTPUT_FILE) else 'w'
    header = not os.path.exists(OUTPUT_FILE) or not append
    data_chunk.to_csv(OUTPUT_FILE, mode=mode, header=header, index=False)

def main():
    os.makedirs("data", exist_ok=True)  # Make sure the data/ folder exists

    tickers_df = pd.read_csv(INPUT_CSV)
    all_tickers = tickers_df["Ticker"].dropna().unique()

    already_fetched = load_existing_tickers()

    # Filter out duplicates and already fetched tickers
    tickers_to_fetch = [t for t in all_tickers if t not in already_fetched]

    print(f"📊 {len(tickers_to_fetch)} tickers remaining (out of {len(all_tickers)} total)")

    temp_chunk = []  # This holds the temporary in-memory batch
    for i, ticker in enumerate(tqdm(tickers_to_fetch, desc="Fetching history")):
        hist = fetch_history(ticker)
        if hist is not None:
            temp_chunk.append(hist)

        time.sleep(SLEEP_BETWEEN_CALLS)

        # Save to file every N tickers to avoid memory bloat and allow recovery
        if (i + 1) % BATCH_SAVE_SIZE == 0 and temp_chunk:
            chunk_df = pd.concat(temp_chunk)
            save_chunk(chunk_df)
            temp_chunk.clear()

    # Final save if we still have leftover data
    if temp_chunk:
        chunk_df = pd.concat(temp_chunk)
        save_chunk(chunk_df)

    print(f"✅ Done at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}! Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()