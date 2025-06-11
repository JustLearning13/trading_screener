import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import linregress

def plot_top_trending_sectors(sector_returns, sector_slopes, window=21, top_n=5):
    # Step 1: Get top trending sectors
    top_sectors = sector_slopes.dropna().head(top_n).index.tolist()

    # Step 2: Slice last `window` days of returns
    recent_returns = sector_returns[top_sectors].dropna().tail(window)

    # Step 3: Plot returns and trend lines
    plt.figure(figsize=(14, 7))
    for sector in top_sectors:
        y = recent_returns[sector].values
        x = range(len(y))
        plt.plot(recent_returns.index, y, label=f"{sector} (slope={sector_slopes[sector]:.4f})")

        # Optional: overlay trend line
        slope, intercept, _, _, _ = linregress(x, y)
        trend_line = intercept + slope * pd.Series(x)
        plt.plot(recent_returns.index, trend_line, linestyle='--', alpha=0.5)

    plt.title(f"Top {top_n} Uptrending Sectors - Last {window} Days")
    plt.xlabel("Date")
    plt.ylabel("Daily Return")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

