# extract_sectors_industries.py

import pandas as pd

# Load the precomputed file
df = pd.read_csv("all_tickers.csv")

# Drop entries where sector or industry is missing
df_clean = df.dropna(subset=["Sector", "Industry"])

# Get distinct sector-industry combinations
unique_pairs = df_clean[["Sector", "Industry"]].drop_duplicates().sort_values(by=["Sector", "Industry"])

# Save to CSV
unique_pairs.to_csv("sectors_industries_unique.csv", index=False)

print(f"✅ Saved {len(unique_pairs)} unique sector/industry pairs to sectors_industries_unique.csv")
