import pandas as pd

# Step 1: Load data
tickers_df = pd.read_csv("data/all_tickers.csv")
price_df = pd.read_csv("data/price_history_recent.csv")

# Step 2: Prep price history
price_df["Date"] = pd.to_datetime(price_df["Date"])
price_df = price_df.sort_values(by=["Ticker", "Date"])

# Step 3: Merge with sector/industry data
merged_df = pd.merge(price_df, tickers_df, on="Ticker", how="left")

# Step 4: Compute return per ticker over last N days
DAYS_BACK = 20
returns = []

for ticker, group in merged_df.groupby("Ticker"):
    group = group.sort_values("Date")
    if len(group) >= DAYS_BACK:
        start_price = group["Close"].iloc[-DAYS_BACK]
        end_price = group["Close"].iloc[-1]
        ret = (end_price - start_price) / start_price
        returns.append({
            "Ticker": ticker,
            "Sector": group["Sector"].iloc[0],
            "Industry": group["Industry"].iloc[0],
            "Return": ret
        })

returns_df = pd.DataFrame(returns)

# Step 5: Compute average returns by sector
sector_trend_df = (
    returns_df.groupby("Sector")["Return"]
    .mean()
    .reset_index()
    .rename(columns={"Return": "SectorReturn"})
)

# Step 6: Compute average returns by industry
industry_trend_df = (
    returns_df.groupby(["Sector", "Industry"])["Return"]
    .mean() 
    .reset_index()
    .rename(columns={"Return": "IndustryReturn"})
)
# Step 7: Merge sector trend into industry trend
final_df = pd.merge(industry_trend_df, sector_trend_df, on="Sector", how="left")

# Step 8: Reorganize columns for readability
final_df = final_df[["Sector", "SectorReturn", "Industry", "IndustryReturn"]]

# Step 9: Sort by sector trend first, then industry trend
final_df = final_df.sort_values(by=["SectorReturn", "IndustryReturn"], ascending=[False, False])

# Step 10: Save to CSV
final_df.to_csv("data/sector_industry_trend_scores.csv", index=False)

# Optional preview
print("📊 Sector + Industry Trends:")
print(final_df.head(15))
