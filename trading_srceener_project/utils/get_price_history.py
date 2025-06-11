import os
import time
import pandas as pd
import yfinance as yf

from config.config import HISTORICAL_PERIOD 
from config.config import SLEEP_BETWEEN_CALLS

from tqdm import tqdm  # For a progress bar

# ------------------------ CONFIGURATION ------------------------
INPUT_CSV = "data/all_tickers.csv"       # Your master list of tickers
OUTPUT_FILE = "data/price_history.csv"   # File to store all historical price data
SAVE_EVERY_N = 100                       # Save interim results every N tickers
# ---------------------------------------------------------------

def load_existing_tickers():
    """
    Reads the output price history CSV (if it exists) to check
    which tickers have already been fetched — avoids repeating them.
    """
    if os.path.exists(OUTPUT_FILE):
        df = pd.read_csv(OUTPUT_FILE, usecols=["Ticker"])
        return set(df["Ticker"].unique())
    return set()

def is_valid_ticker(ticker):
    """
    Apply basic checks to make sure the ticker is clean and usable.
    Prevents wasting time on junk or malformed tickers.
    """
    return (
        isinstance(ticker, str) and
        ticker.isupper() and
        ticker.isalpha() and
        not ticker.startswith("$") and
        len(ticker) <= 6
    )

def fetch_history(ticker):
    """
    Use yfinance to pull 1 year of daily OHLCV (Open, High, Low, Close, Volume)
    price history for a given ticker. Return None if the result is empty or fails.
    """
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

def save_chunk(data_chunk, append=True):
    """
    Write a batch of data to CSV. Use append mode to grow the file.
    Creates the file if it doesn’t exist.
    """
    mode = 'a' if append and os.path.exists(OUTPUT_FILE) else 'w'
    header = not os.path.exists(OUTPUT_FILE) or not append
    data_chunk.to_csv(OUTPUT_FILE, mode=mode, header=header, index=False)

def load_failed_tickers():
    """
    Optional recovery tool: if you previously saved a list of failed tickers,
    this will let you skip them on the next run.
    """
    if os.path.exists("failed_tickers.txt"):
        with open("failed_tickers.txt") as f:
            return set(line.strip() for line in f.readlines())
    return set()

def main():
    os.makedirs("data", exist_ok=True)  # Make sure the data/ folder exists

    failed_tickers = load_failed_tickers()
    tickers_df = pd.read_csv(INPUT_CSV)
    all_tickers = tickers_df["Ticker"].dropna().unique()

    already_fetched = load_existing_tickers()

    # Filter out duplicates, failed, and invalid tickers
    tickers_to_fetch = [t for t in all_tickers if t not in already_fetched 
                        and t not in failed_tickers and is_valid_ticker(t)]

    print(f"📊 {len(tickers_to_fetch)} tickers remaining (out of {len(all_tickers)} total)")

    temp_chunk = []  # This holds the temporary in-memory batch
    for i, ticker in enumerate(tqdm(tickers_to_fetch, desc="Fetching history")):
        hist = fetch_history(ticker)
        if hist is not None:
            temp_chunk.append(hist)

        time.sleep(SLEEP_BETWEEN_CALLS)

        # Save to file every N tickers to avoid memory bloat and allow recovery
        if (i + 1) % SAVE_EVERY_N == 0 and temp_chunk:
            chunk_df = pd.concat(temp_chunk)
            save_chunk(chunk_df)
            temp_chunk.clear()

    # Final save if we still have leftover data
    if temp_chunk:
        chunk_df = pd.concat(temp_chunk)
        save_chunk(chunk_df)

    print(f"\n✅ Done! Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
