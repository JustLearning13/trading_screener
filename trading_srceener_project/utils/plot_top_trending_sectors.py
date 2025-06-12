
import pandas as pd
import matplotlib.pyplot as plt
import os

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
DATA_DIR = "data"
SECTOR_RETURNS_CSV = os.path.join(DATA_DIR, "sector_history.csv")
SECTOR_SLOPES_CSV = os.path.join(DATA_DIR, "sector_slopes.csv")
INDUSTRY_RETURNS_CSV = os.path.join(DATA_DIR, "industry_history.csv")
INDUSTRY_SLOPES_CSV = os.path.join(DATA_DIR, "industry_slopes.csv")
OUTPUT_PLOT_SECTOR = os.path.join(DATA_DIR, "top_sector_50MA.jpeg")
OUTPUT_PLOT_INDUSTRY = os.path.join(DATA_DIR, "top_industry_50MA.jpeg")

MA_WINDOW = 50
TOP_N = 5
# ─────────────────────────────────────────────

def plot_top_trending_groups_ma(return_df, slope_series, group_type="Sector", top_n=5, window=50, output_path=None):
    top_groups = slope_series.dropna().sort_values(ascending=False).head(top_n).index.tolist()
    ma_df = return_df[top_groups].rolling(window=window).mean().dropna()

    # Limit to last `window` rows
    ma_df = ma_df.tail(window)

    plt.figure(figsize=(14, 7))
    for group in top_groups:
        plt.plot(ma_df.index, ma_df[group], label=f"{group} (50MA)")

    plt.title(f"Top {top_n} {group_type}s by 50-Day Moving Average")
    plt.xlabel("Date")
    plt.ylabel("50-Day Avg Daily Return")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, format='jpeg')
    plt.close()

if __name__ == "__main__":
    # Load sector data
    print("📥 Loading sector data...")
    sector_returns = pd.read_csv(SECTOR_RETURNS_CSV, index_col="Date", parse_dates=True)
    sector_slopes = pd.read_csv(SECTOR_SLOPES_CSV, index_col=0)
    if isinstance(sector_slopes, pd.DataFrame):
        sector_slopes = sector_slopes.iloc[:, 0]

    print("💾 Saving top sector 50MA plot...")
    plot_top_trending_groups_ma(
        return_df=sector_returns,
        slope_series=sector_slopes,
        group_type="Sector",
        top_n=TOP_N,
        window=MA_WINDOW,
        output_path=OUTPUT_PLOT_SECTOR
    )

    # Load industry data
    print("📥 Loading industry data...")
    industry_returns = pd.read_csv(INDUSTRY_RETURNS_CSV, index_col="Date", parse_dates=True)
    industry_slopes = pd.read_csv(INDUSTRY_SLOPES_CSV, index_col=0)
    if isinstance(industry_slopes, pd.DataFrame):
        industry_slopes = industry_slopes.iloc[:, 0]

    print("💾 Saving top industry 50MA plot...")
    plot_top_trending_groups_ma(
        return_df=industry_returns,
        slope_series=industry_slopes,
        group_type="Industry",
        top_n=TOP_N,
        window=MA_WINDOW,
        output_path=OUTPUT_PLOT_INDUSTRY
    )

    print("\n✅ 50-Day MA trend graphs saved as JPEGs.")