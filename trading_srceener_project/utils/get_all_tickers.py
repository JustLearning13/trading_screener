import requests
import pandas as pd
import time
from config import FMP_API_KEY  # Your API key stored securely in config.py
from tqdm import tqdm  # Progress bar library

# Configuration constants
API_LIST_URL = "https://financialmodelingprep.com/api/v3/stock/list"
API_PROFILE_URL = "https://financialmodelingprep.com/api/v3/profile"
OUTPUT_FILE = "data/all_tickers.csv"
MIN_MARKET_CAP = 100_000_000  # Minimum acceptable market cap ($100M)
MIN_PRICE = 1  # Minimum stock price to include in the final list
EXCHANGES = ['NASDAQ', 'NYSE', 'AMEX']  # Filter only US major exchanges
BATCH_SIZE = 1000  # Max batch size for efficient API calls
SLEEP_BETWEEN_CALLS = 0.25  # Pause to avoid getting rate-limited

def fetch_all_us_tickers():
    """
    Fetch a master list of all publicly traded stocks from FMP.
    This version filters to only include US exchanges (NASDAQ, NYSE, AMEX)
    and removes junk symbols (like those with weird characters or from other regions).
    """
    response = requests.get(f"{API_LIST_URL}?apikey={FMP_API_KEY}")
    if response.status_code != 200:
        print(f"❌ Failed to fetch tickers: {response.status_code}")
        return None

    data = response.json()
    df = pd.DataFrame(data)

    # Keep only major exchanges
    df = df[df['exchangeShortName'].isin(EXCHANGES)]

    # Exclude tickers with non-alphabetic characters (e.g., warrants, bonds)
    df = df[df['symbol'].str.match("^[A-Z]+$")]

    # Rename and keep only useful columns
    df = df.rename(columns={
        "symbol": "Ticker",
        "name": "CompanyName",
        "exchangeShortName": "Exchange",
        "price": "Price"
    })

    df = df[["Ticker", "CompanyName", "Exchange", "Price"]]
    return df

def enrich_with_profile_data(ticker_list):
    """
    For each batch of tickers, call the /profile endpoint to fetch:
    - Sector
    - Industry
    - MarketCap
    Returns a DataFrame with enriched data.
    """
    print(f"🔍 Enriching {len(ticker_list)} tickers with sector, industry, market cap...")

    enriched_data = []
    for i in tqdm(range(0, len(ticker_list), BATCH_SIZE), desc="Enriching"):
        batch = ticker_list[i:i + BATCH_SIZE]
        symbols = ",".join(batch)
        url = f"{API_PROFILE_URL}/{symbols}?apikey={FMP_API_KEY}"

        try:
            response = requests.get(url)
            if response.status_code != 200:
                print(f"⚠️ Failed batch at index {i}: {response.status_code}")
                continue

            profiles = response.json()

            # Build up a list of dictionaries for valid profile entries
            for prof in profiles:
                enriched_data.append({
                    "Ticker": prof.get("symbol"),
                    "Sector": prof.get("sector", "Unknown"),
                    "Industry": prof.get("industry", "Unknown"),
                    "MarketCap": prof.get("mktCap", None)
                })

        except Exception as e:
            print(f"❌ Batch error at index {i}: {e}")

        # Polite pause to avoid hammering the API
        time.sleep(SLEEP_BETWEEN_CALLS)

    return pd.DataFrame(enriched_data)

def is_valid_ticker_row(row):
    """
    Apply a set of logical and financial filters to weed out:
    - Non-standard tickers
    - Tickers with missing sector/industry
    - Tickers that are too cheap or have too small a market cap
    """
    try:
        return (
            isinstance(row["Ticker"], str)
            and row["Ticker"].isalpha()
            and row["Ticker"].isupper()
            and not row["Ticker"].startswith("$")
            and isinstance(row["Sector"], str)
            and row["Sector"] != "Unknown"
            and isinstance(row["Industry"], str)
            and row["Industry"] != "Unknown"
            and float(row["MarketCap"] or 0) >= MIN_MARKET_CAP
            and float(row["Price"] or 0) >= MIN_PRICE
        )
    except Exception:
        return False

if __name__ == "__main__":
    # Step 1: Get the basic ticker list (only NASDAQ/NYSE/AMEX)
    tickers_df = fetch_all_us_tickers()
    if tickers_df is None:
        exit()

    # Step 2: Enrich that list with sector/industry/market cap data
    ticker_list = tickers_df["Ticker"].tolist()
    enriched_df = enrich_with_profile_data(ticker_list)

    # Step 3: Merge raw + enriched info into one table
    full_df = pd.merge(tickers_df, enriched_df, on="Ticker", how="left")

    # Step 4: Apply filters to remove junk, penny stocks, and missing info
    clean_df = full_df[full_df.apply(is_valid_ticker_row, axis=1)]

    # Step 5: Save results
    clean_df.to_csv(OUTPUT_FILE, index=False)

    print(f"🧼 Filtered down to {len(clean_df)} clean tickers out of {len(full_df)} total")
    print(f"💾 Saved to {OUTPUT_FILE}")
