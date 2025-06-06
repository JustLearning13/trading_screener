import os
import time
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from tqdm import tqdm

# ---------------------- CONFIG ----------------------
INPUT_CSV = "fmp_all_tickers_enriched.csv"  # To get full list of tickers
HISTORY_FILE = "data/price_history.csv"     # Main price data file
SLEEP_BETWEEN_CALLS = 0.4
# ----------------------------------------------------

def load_existing_history():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE, parse_dates=["Date"])
    return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume", "Ticker"])

def get_last_date_for_ticker(history_df, ticker):
    ticker_data = history_df[history_df["Ticker"] == ticker]
    return ticker_data["Date"].max() if not ticker_data.empty else None

def fetch_new_data(ticker, start_date):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(start=start_date, interval="1d")
        if hist.empty:
            return None

        hist = hist[["Open", "High", "Low", "Close", "Volume"]].copy()
        hist["Ticker"] = ticker
        hist = hist.reset_index()  # Date as column
        return hist

    except Exception as e:
        print(f"❌ {ticker} failed: {e}")
        return None

def main():
    os.makedirs("data", exist_ok=True)

    # Load previous full price history
    full_history_df = load_existing_history()

    # Load ticker list
    tickers_df = pd.read_csv(INPUT_CSV)
    tickers = tickers_df["Ticker"].dropna().unique()

    updated_data = []

    for ticker in tqdm(tickers, desc="Updating tickers"):
        last_date = get_last_date_for_ticker(full_history_df, ticker)

        if pd.isna(last_date):
            continue  # Ticker wasn't fetched originally, skip for now

        fetch_from = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')

        # If it's already up to date, skip
        if fetch_from >= datetime.today().strftime('%Y-%m-%d'):
            continue

        new_data = fetch_new_data(ticker, fetch_from)
        if new_data is not None:
            updated_data.append(new_data)

        time.sleep(SLEEP_BETWEEN_CALLS)

    if updated_data:
        updated_df = pd.concat(updated_data)
        combined_df = pd.concat([full_history_df, updated_df])
        combined_df.drop_duplicates(subset=["Ticker", "Date"], inplace=True)
        combined_df.sort_values(by=["Ticker", "Date"], inplace=True)
        combined_df.to_csv(HISTORY_FILE, index=False)
        print(f"\n✅ Appended {len(updated_df)} new rows to {HISTORY_FILE}")
    else:
        print("\n✅ All tickers already up to date!")

if __name__ == "__main__":
    main()

