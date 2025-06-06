FMP_API_KEY = ""
EXCHANGES = ['NASDAQ', 'NYSE', 'AMEX']
BATCH_SIZE = 1000
SLEEP_BETWEEN_CALLS = 0.25
# How many times higher today's volume must be vs average to trigger an alert
VOLUME_MULTIPLIER = 2.0

# The lookback period for historical stock data (used in volume, MA, etc.)
HISTORICAL_PERIOD = "1y"  # e.g., "30d", "6mo", "1y"

# The timeframe used to calculate the slope of the moving average (for trend)
MA_SLOPE_PERIOD = "10d"  # Used to detect upward MA trends

# Minimum average daily trading volume a stock must have to be considered
MIN_VOLUME = 100_000  # Helps exclude illiquid stocks

# Minimum stock price (in dollars); skips penny stocks
MIN_PRICE = 1  # Ignores stocks trading below $1

# Minimum market cap in USD (e.g., $100 million)
MIN_MARKET_CAP = 100_000_000  # Helps filter out micro-cap companies


