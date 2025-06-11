
import pandas as pd
from datetime import datetime, timedelta
from scipy.stats import linregress

# ─────────────────────────────────────────────
# 🔧 CONFIGURATION
# ─────────────────────────────────────────────
INPUT_ALL_TICKERS = "data/all_tickers.csv"
INPUT_PRICE_HISTORY = "data/price_history.csv"
OUTPUT_SECTOR_RETURNS = "data/sector_history.csv"
OUTPUT_INDUSTRY_RETURNS = "data/industry_history.csv"
OUTPUT_SECTOR_SLOPES = "data/sector_slopes.csv"
OUTPUT_INDUSTRY_SLOPES = "data/industry_slopes.csv"

PERIOD_BACK = None      # e.g., 90 for last 90 days, or None for full history
WINDOW_DAYS = 21        # Number of days to calculate slope (monthly trend)
# ─────────────────────────────────────────────


def load_and_prepare_data(price_path, info_path, period_back_days=None):
    price_df = pd.read_csv(price_path)
    price_df['Date'] = pd.to_datetime(price_df['Date'], utc=True).dt.tz_convert(None)

    if period_back_days:
        cutoff = datetime.now() - timedelta(days=period_back_days)
        price_df = price_df[price_df['Date'] >= cutoff]

    meta_df = pd.read_csv(info_path)
    merged_df = price_df.merge(
        meta_df[['Ticker', 'Sector', 'Industry']], on='Ticker', how='left'
    )
    merged_df = merged_df.sort_values(by=['Ticker', 'Date'])
    merged_df['DailyReturn'] = merged_df.groupby('Ticker')['Close'].pct_change(fill_method=None)

    return merged_df


def calculate_average_returns(merged_df):
    sector_returns = merged_df.groupby(['Date', 'Sector'])['DailyReturn'].mean().unstack().sort_index()
    industry_returns = merged_df.groupby(['Date', 'Industry'])['DailyReturn'].mean().unstack().sort_index()
    return sector_returns, industry_returns


def calculate_trend_slopes(return_df, window):
    slopes = {}
    recent_data = return_df.dropna().tail(window)
    x = range(window)

    for col in recent_data.columns:
        y = recent_data[col].values
        if len(y) == window:
            slope, _, _, _, _ = linregress(x, y)
            slopes[col] = slope
        else:
            slopes[col] = None

    return pd.Series(slopes).dropna().sort_values(ascending=False)


if __name__ == "__main__":
    print("📥 Loading and preparing data...")
    merged_df = load_and_prepare_data(INPUT_PRICE_HISTORY, INPUT_ALL_TICKERS, period_back_days=PERIOD_BACK)

    print("📊 Calculating sector and industry average returns...")
    sector_returns, industry_returns = calculate_average_returns(merged_df)

    print("💾 Saving sector and industry return history to CSV...")
    sector_returns.to_csv(OUTPUT_SECTOR_RETURNS)
    industry_returns.to_csv(OUTPUT_INDUSTRY_RETURNS)

    print(f"📈 Calculating {WINDOW_DAYS}-day trend slopes...")
    sector_slopes = calculate_trend_slopes(sector_returns, window=WINDOW_DAYS)
    industry_slopes = calculate_trend_slopes(industry_returns, window=WINDOW_DAYS)

    print("💾 Saving slope trend results to CSV...")
    # For sector slopes
    sector_df = sector_slopes.to_frame().reset_index()
    sector_df.columns = ["Sector", "Slope"]
    sector_df.to_csv(OUTPUT_SECTOR_SLOPES, index=False)

    # For industry slopes
    industry_df = industry_slopes.to_frame().reset_index()
    industry_df.columns = ["Industry", "Slope"]
    industry_df.to_csv(OUTPUT_INDUSTRY_SLOPES, index=False)
    print("\n✅ All calculations completed and saved.")
