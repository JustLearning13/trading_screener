import requests
import pandas as pd
import time
from config import FMP_API_KEY
from tqdm import tqdm  # progress bar

# ------------------------- CONFIG -------------------------
API_LIST_URL = "https://financialmodelingprep.com/api/v3/stock/list"
API_PROFILE_URL = "https://financialmodelingprep.com/api/v3/profile"
OUTPUT_FILE = "all_tickers.csv"
MIN_MARKET_CAP = 100_000_000
MIN_PRICE = 1
EXCHANGES = ['NASDAQ', 'NYSE', 'AMEX']
BATCH_SIZE = 1000
SLEEP_BETWEEN_CALLS = 0.25
# ----------------------------------------------------------

def fetch_all_us_tickers():
    """Fetch tickers from FMP stock list and filter out early junk."""
    url = f"{API_LIST_URL}?apikey={FMP_API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ Failed to fetch ticker list: {response.status_code}")
        return None

    data = response.json()
    df = pd.DataFrame(data)

    # Filter for major US exchanges
    df = df[df['exchangeShortName'].isin(EXCHANGES)]

    # Only keep clean, alphabetic uppercase tickers
    df = df[df['symbol'].str.match("^[A-Z]+$")]

    df = df.rename(columns={
        "symbol": "Ticker",
        "name": "CompanyName",
        "exchangeShortName": "Exchange",
        "price": "Price"
    })

    df = df[["Ticker", "CompanyName", "Exchange", "Price"]]
    return df


def is_valid_ticker_row(row):
    """Apply all logical and financial filters to keep good tickers only."""
def is_valid_ticker_row(row):
    try:
        return (
            isinstance(row["Ticker"], str)
            and row["Ticker"].isalpha()
            and row["Ticker"].isupper()
            and not row["Ticker"].startswith("$")
            and isinstance(row["Sector"], str)
            and row["Sector"].strip() != ""
            and row["Sector"] != "Unknown"
            and isinstance(row["Industry"], str)
            and row["Industry"].strip() != ""
            and row["Industry"] != "Unknown"
            and float(row["MarketCap"] or 0) >= MIN_MARKET_CAP
            and float(row["Price"] or 0) >= MIN_PRICE
        )
    except Exception:
        return False


def enrich_with_profile_data(ticker_list):
    """Get profile info in batches for all tickers."""
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
            for prof in profiles:
                enriched_data.append({
                    "Ticker": prof.get("symbol"),
                    "Sector": prof.get("sector", "Unknown"),
                    "Industry": prof.get("industry", "Unknown"),
                    "MarketCap": prof.get("mktCap", None)
                })

        except Exception as e:
            print(f"❌ Batch error at index {i}: {e}")

        time.sleep(SLEEP_BETWEEN_CALLS)

    return pd.DataFrame(enriched_data)


if __name__ == "__main__":
    tickers_df = fetch_all_us_tickers()
    if tickers_df is None:
        exit()

    ticker_list = tickers_df["Ticker"].tolist()
    enriched_df = enrich_with_profile_data(ticker_list)

    full_df = pd.merge(tickers_df, enriched_df, on="Ticker", how="left")

    # Apply filter
    clean_df = full_df[full_df.apply(is_valid_ticker_row, axis=1)]

    # Save only filtered, clean tickers
    clean_df.to_csv(OUTPUT_FILE, index=False)

    print(f"\n🧼 Filtered down to {len(clean_df)} clean tickers out of {len(full_df)} total")
    print(f"💾 Saved to {OUTPUT_FILE}")
