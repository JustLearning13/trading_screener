import requests
import pandas as pd
import time
from tqdm import tqdm  # Progress bar library

# Configuration constants
from config.config import FMP_API_KEY  # Your API key stored securely in config.py
from config.config import MIN_MARKET_CAP # Minimum acceptable market cap (usually $100M)
from config.config import MIN_PRICE   # Minimum stock price to include in the final list
from config.config import MIN_VOLUME
from config.config import EXCHANGES # Usually only US major exchanges
from config.config import BATCH_SIZE   # Max batch size for efficient API calls
from config.config import SLEEP_BETWEEN_CALLS # Pause to avoid getting rate-limited

# Local Configuration constants
API_LIST_URL = "https://financialmodelingprep.com/api/v3/stock/list"
API_PROFILE_URL = "https://financialmodelingprep.com/api/v3/profile"
OUTPUT_FILE = "data/all_tickers.csv"

# Fetch a master list of all publicly traded stocks from FMP.
def fetch_all_us_tickers():
    response = requests.get(f"{API_LIST_URL}?apikey={FMP_API_KEY}")
    if response.status_code != 200:
        print(f"❌ Failed to fetch tickers: {response.status_code}")
        return None

    data = response.json()
    df = pd.DataFrame(data)
    print("Returned from FMP:", df.columns.tolist())

    # Keep only major exchanges
    df = df[df['exchangeShortName'].isin(EXCHANGES)]
    # Exclude tickers with non-alphabetic characters (e.g., warrants, bonds)
    df = df[df['symbol'].str.match("^[A-Z]+$")]
    # Exclude inactive tickers and keep only stocks,etfs, and spac (e.g., warrants, bonds)
    df = df[df["type"].isin(["stock", "etf", "spac"])]

    # Rename and keep only useful columns
    df = df.rename(columns={
        "symbol": "Ticker",
        "name": "CompanyName",
        "exchangeShortName": "Exchange",
        "price": "Price",
        "type": "Type"
    })

    df = df[["Ticker", "CompanyName", "Exchange", "Price", "Type"]]
    return df

# For each batch of tickers call the /profile to fetch: Sector, Industry, MarketCap
def enrich_with_profile_data(ticker_list):
 
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
            df = pd.DataFrame(profiles)

            # Build up a list of dictionaries for valid profile entries
            for prof in profiles:
               enriched_data.append({
                   "Ticker": prof.get("symbol"),
                   "CompanyName": prof.get("companyName"),
                   "Sector": prof.get("sector", "Unknown"),
                   "Industry": prof.get("industry", "Unknown"),
                   "MarketCap": prof.get("mktCap", None),
                   "VolumeAvg": prof.get("volAvg", None),                      # 🟦 Avg daily volume
                   "Range52W": prof.get("range", "N/A"),                       # 🟩 52-week range (as string: e.g., '120.34-265.89')
                   "DailyChange": prof.get("changes", None),                   # 🟥 Price change from last close
                   "IsActivelyTrading": prof.get("isActivelyTrading", False)
               })

        except Exception as e:
            print(f"❌ Batch error at index {i}: {e}")

        # Polite pause to avoid hammering the API
        time.sleep(SLEEP_BETWEEN_CALLS)

    return pd.DataFrame(enriched_data)

if __name__ == "__main__":
    # Step 1: Get the basic ticker list (only NASDAQ/NYSE/AMEX)
    tickers_df = fetch_all_us_tickers()
    if tickers_df is None:
        exit()

    # Step 2: Enrich that list with sector/industry/market cap data
    ticker_list = tickers_df["Ticker"].tolist()
    enriched_df = enrich_with_profile_data(ticker_list)
    enriched_df = enriched_df[enriched_df["IsActivelyTrading"] == True]

    # Step 3: Merge raw + enriched info into one table
    full_df = pd.merge(tickers_df, enriched_df, on="Ticker", how="left")

    # Step 4: Apply filters to remove junk, penny stocks, and missing info
    clean_df = full_df[
        (full_df["Sector"] != "Unknown") &
        (full_df["Industry"] != "Unknown") &
        (full_df["MarketCap"] >= MIN_MARKET_CAP) &
        (full_df["Price"] >= MIN_PRICE) &
        (full_df["VolumeAvg"] >= MIN_VOLUME)
    ]

    # Clean Ticker column before saving
    clean_df = clean_df.dropna(subset=["Ticker"])
    clean_df["Ticker"] = clean_df["Ticker"].astype(str).str.strip()
    clean_df = clean_df[clean_df["Ticker"] != ""]

    # Step 5: Save results
    clean_df.to_csv(OUTPUT_FILE, index=False)

    print(f"🧼 Filtered down to {len(clean_df)} clean tickers out of {len(full_df)} total")
    print(f"💾 Saved to {OUTPUT_FILE}")