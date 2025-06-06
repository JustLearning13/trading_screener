# -*- coding: utf-8 -*-
import requests
import yfinance as yf
import pandas as pd
import time

def download_ticker_file(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Failed to download from {url}")
        return []
    return response.text.splitlines()[1:]  # skip header

def parse_ticker_line(line, source):
    parts = line.split("|")
    symbol = parts[0]
    name = parts[1]
    test_issue = parts[3]
    etf_flag = parts[4] if len(parts) > 4 else "N"
    nextshares_flag = parts[5] if len(parts) > 5 else "N"

    if "File Creation Time" in symbol:
        return None
    if test_issue == "Y" or etf_flag == "Y" or nextshares_flag == "Y":
        return None

    return {"Ticker": symbol, "Exchange": source}

def enrich_with_yfinance(ticker_dict):
    symbol = ticker_dict["Ticker"]
    try:
        t = yf.Ticker(symbol)
        info = t.info
        hist = t.history(period="1d")

        if hist.empty:
            return None

        price = hist["Close"].iloc[-1]
        volume = hist["Volume"].iloc[-1]
        if price <= 1.0 or volume <= 0:
            return None

        ticker_dict["Price"] = round(price, 2)
        ticker_dict["Volume"] = round(volume, 2)
        ticker_dict["MarketCap"] = info.get("marketCap", None)
        ticker_dict["Sector"] = info.get("sector", "Unknown")
        ticker_dict["Industry"] = info.get("industry", "Unknown")
        return ticker_dict
    except Exception as e:
        print(f"❌ {symbol}: Error - {e}")
        return None

# 🔹 Step 1: Download and parse both lists
nasdaq_url = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
other_url = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"

nasdaq_lines = download_ticker_file(nasdaq_url)
other_lines = download_ticker_file(other_url)

tickers_raw = []

for line in nasdaq_lines:
    t = parse_ticker_line(line, "NASDAQ")
    if t:
        tickers_raw.append(t)

for line in other_lines:
    t = parse_ticker_line(line, "OTHER")  # Will contain NYSE/AMEX
    if t:
        tickers_raw.append(t)

print(f"📥 Loaded {len(tickers_raw)} tickers to enrich with data...")

# 🔹 Step 2: Enrich with yfinance
final_data = []
for i, ticker_dict in enumerate(tickers_raw):
    enriched = enrich_with_yfinance(ticker_dict)
    if enriched:
        final_data.append(enriched)
    time.sleep(0.2)  # gentle pause to avoid throttling

# 🔹 Step 3: Remove duplicates
df = pd.DataFrame(final_data)
df = df.drop_duplicates(subset="Ticker", keep="first")

# 🔹 Step 4: Save to CSV
df.to_csv("all_tickers.csv", index=False)
print(f"\n💾 Saved {len(df)} unique tickers to all_tickers.csv")
