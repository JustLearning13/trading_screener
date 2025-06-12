# 🧠 Stock Market Screener — Price History Pipeline

This script maintains a complete and **up-to-date historical price record** for all valid tickers in your project, using `yfinance` and `FMP` data sources.

---

## 📂 Script: `get_price_history.py`

### ✅ Features:
- Automatically pulls **1 year** of daily OHLCV data for any **new tickers**
- Detects the **most recent date per ticker** in your historical file
- Adds **only missing data** per ticker (incremental updates)
- Uses **batch writing** for stability and resilience
- Creates the `price_history.csv` file automatically on first run
- Respects polite delays to avoid throttling

---

## 📁 Files Used

| File | Description |
|------|-------------|
| `data/all_tickers.csv` | Your master list of clean, active tickers |
| `data/price_history.csv` | Automatically maintained full price history |

---

## 🏃 How to Run

```bash
python get_price_history.py
```

💡 Run this script **daily after market close** to keep your dataset fresh and accurate.

---

## ⚙️ Configurable Options

Stored in `config/config.py`:

```python
HISTORICAL_PERIOD = "1y"
SLEEP_BETWEEN_CALLS = 0.4
```

You can adjust these without modifying the main script.

