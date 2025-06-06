import os
import time
import pandas as pd
import yfinance as yf
from tqdm import tqdm

# ------------------------ CONFIG ------------------------
INPUT_CSV = "all_tickers.csv"
OUTPUT_FILE = "data/price_history.csv"
YEARS_BACK = 1
SAVE_EVERY_N = 100       # Save after every N tickers
SLEEP_BETWEEN_CALLS = 0.4
# --------------------------------------------------------

def load_existing_tickers():
    if os.path.exists(OUTPUT_FILE):
        df = pd.read_csv(OUTPUT_FILE, usecols=["Ticker"])
        return set(df["Ticker"].unique())
    return set()

def is_valid_ticker(ticker):
    return (
        isinstance(ticker, str) and
        ticker.isupper() and
        ticker.isalpha() and
        not ticker.startswith("$") and
        len(ticker) <= 6
    )

def fetch_history(ticker):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=f"{YEARS_BACK}y", interval="1d")
        if hist.empty:
            return None

        hist = hist[["Open", "High", "Low", "Close", "Volume"]].copy()
        hist["Ticker"] = ticker
        hist = hist.reset_index()  # Convert index (Date) into a column
        return hist

    except Exception as e:
        print(f"❌ {ticker} failed: {e}")
        return None

def save_chunk(data_chunk, append=True):
    mode = 'a' if append and os.path.exists(OUTPUT_FILE) else 'w'
    header = not os.path.exists(OUTPUT_FILE) or not append
    data_chunk.to_csv(OUTPUT_FILE, mode=mode, header=header, index=False)

def load_failed_tickers():
    if os.path.exists("failed_tickers.txt"):
        with open("failed_tickers.txt") as f:
            return set(line.strip() for line in f.readlines())
    return set()

def main():
    os.makedirs("data", exist_ok=True)
    failed_tickers = load_failed_tickers()
    tickers_df = pd.read_csv(INPUT_CSV)
    all_tickers = tickers_df["Ticker"].dropna().unique()

    already_fetched = load_existing_tickers()

    tickers_to_fetch = [t for t in all_tickers if t not in already_fetched 
                        and t not in failed_tickers and is_valid_ticker(t)]

    print(f"📊 {len(tickers_to_fetch)} tickers remaining (out of {len(all_tickers)} total)")

    temp_chunk = []
    for i, ticker in enumerate(tqdm(tickers_to_fetch, desc="Fetching history")):
        hist = fetch_history(ticker)
        if hist is not None:
            temp_chunk.append(hist)

        time.sleep(SLEEP_BETWEEN_CALLS)

        # Save every N tickers
        if (i + 1) % SAVE_EVERY_N == 0 and temp_chunk:
            chunk_df = pd.concat(temp_chunk)
            save_chunk(chunk_df)
            temp_chunk.clear()

    # Final save if any data left
    if temp_chunk:
        chunk_df = pd.concat(temp_chunk)
        save_chunk(chunk_df)

    print(f"\n✅ Done! Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
