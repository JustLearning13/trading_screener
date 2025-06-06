
import pandas as pd

# Load the large file in chunks
filename = "data/price_history.csv"
output = "data/price_history_recent.csv"

# Set how many days of history you want to keep
DAYS_TO_KEEP = 30

# Load full data
df = pd.read_csv(filename, parse_dates=["Date"])

# Find the latest date
latest_date = df["Date"].max()

# Filter only the last N days
cutoff = latest_date - pd.Timedelta(days=DAYS_TO_KEEP)
recent_df = df[df["Date"] >= cutoff]

# Optional: sort again
recent_df = recent_df.sort_values(by=["Ticker", "Date"])

# Save to new trimmed file
recent_df.to_csv(output, index=False)

print(f"? Trimmed down to {len(recent_df)} rows across {recent_df['Ticker'].nunique()} tickers.")
print(f"?? Saved as {output}")

