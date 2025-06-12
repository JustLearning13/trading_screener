import os
import time
import pandas as pd
import yfinance as yf
from tqdm import tqdm
from datetime import datetime, timedelta
from tqdm import tqdm

# CONFIGURATION
INPUT_CSV = "data/all_tickers.csv"
OUTPUT_FILE = "data/price_history.csv"
EXCEPTIONS_FILE = "data/price_history_exceptions.csv"
from config.config import HISTORICAL_PERIOD_DAYS
from config.config import SLEEP_BETWEEN_CALLS
from config.config import BATCH_SAVE_SIZE 

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Load existing data if present
def load_existing_history(filepath):
    if os.path.exists(filepath):
        df = pd.read_csv(filepath, parse_dates=["Date"])
        return df
    return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume", "Ticker"])

# Fetch historical data incrementally
def fetch_ticker_history(ticker, start_date):
    try:
        data = yf.Ticker(ticker).history(start=start_date, end=datetime.today().strftime('%Y-%m-%d'))
        if data.empty:
            return None
        data.reset_index(inplace=True)
        data["Ticker"] = ticker
        data = data[["Date", "Open", "High", "Low", "Close", "Volume", "Ticker"]]
        return data
    except Exception as e:
        print(f"⚠️ Error fetching {ticker}: {e}")
        return None

# MAIN PROCESS
if __name__ == "__main__":
    tickers = pd.read_csv(INPUT_CSV)["Ticker"].unique()
    existing_data = load_existing_history(OUTPUT_FILE)
    exceptions = []

    # Determine last date per ticker
    last_dates = existing_data.groupby("Ticker")["Date"].max().to_dict()
    updated_data = []

    for i, ticker in enumerate(tqdm(tickers, desc="Fetching Price History")):
        if ticker in last_dates:
            start_date = last_dates[ticker] + timedelta(days=1)
        else:
            start_date = datetime.today() - timedelta(days=HISTORICAL_PERIOD_DAYS)

        fetched_data = fetch_ticker_history(ticker, start_date.strftime('%Y-%m-%d'))

        if fetched_data is not None and not fetched_data.empty:
            updated_data.append(fetched_data)
        else:
            exceptions.append(ticker)

        # Periodically save progress
        if (i + 1) % BATCH_SAVE_SIZE == 0:
            if updated_data:
                pd.concat([existing_data] + updated_data).drop_duplicates(subset=["Ticker", "Date"]).to_csv(OUTPUT_FILE, index=False)
                updated_data = []
            time.sleep(SLEEP_BETWEEN_CALLS)

    # Final save
    if updated_data:
        pd.concat([existing_data] + updated_data).drop_duplicates(subset=["Ticker", "Date"]).to_csv(OUTPUT_FILE, index=False)

    # Handle exceptions
    if exceptions:
        # Remove exceptions from main history
        final_data = pd.read_csv(OUTPUT_FILE)
        exceptions_data = final_data[final_data["Ticker"].isin(exceptions)]
        final_data = final_data[~final_data["Ticker"].isin(exceptions)]

        final_data.to_csv(OUTPUT_FILE, index=False)
        exceptions_data.to_csv(EXCEPTIONS_FILE, index=False)

    print(f"✅ Completed fetching. Exceptions moved to '{EXCEPTIONS_FILE}'.")
