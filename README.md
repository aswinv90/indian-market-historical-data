# 📈 Historical Indian Stock Prices

A repository of **complete historical daily OHLCV price data** for all NSE and BSE listed Indian stocks, automatically updated every trading day via GitHub Actions.

## 📦 Data Coverage

| Exchange | Stocks | Tickers |
|----------|--------|---------|
| NSE      | ~2,000 | `SYMBOL.NS` (e.g. `RELIANCE.NS`) |
| BSE      | ~5,000 | `SCRIP_CODE.BO` (e.g. `500325.BO`) |

## 🗂️ Data Fields (per stock, per day)

| Field | Description |
|-------|-------------|
| `Date` | Trading date (index) |
| `Open` | Opening price |
| `High` | Day's high price |
| `Low` | Day's low price |
| `Close` | Closing price |
| `Adj Close` | Adjusted closing price (splits/dividends adjusted) |
| `Volume` | Number of shares traded |
| `Dividends` | Dividend paid on that date (if any) |
| `Stock Splits` | Split ratio on that date (if any) |

## 📁 Repository Structure

```
data/
├── NSE/
│   ├── RELIANCE_NS.parquet
│   ├── TCS_NS.parquet
│   └── ...
└── BSE/
    ├── 500325_BO.parquet
    └── ...
scripts/
├── download_symbol_lists.py   # Download/refresh NSE + BSE symbol lists
├── fetch_all_stocks.py        # One-time bootstrap (full history from listing date)
├── update_stocks.py           # Daily incremental updater
└── utils.py                   # Shared helpers
.github/workflows/
└── update_stocks.yml          # GitHub Actions: runs every weekday at 7:30 AM IST
```

## 🚀 Getting Started

### Prerequisites

```bash
pip install -r requirements.txt
```

### Step 1: Download symbol lists

```bash
python scripts/download_symbol_lists.py
```

### Step 2: Bootstrap full history (run once)

This fetches complete historical data from the day of listing for all stocks.
Expect this to take **several hours** for ~7,000 stocks.

```bash
# Test with a small batch first
python scripts/fetch_all_stocks.py --limit 20

# Full bootstrap
python scripts/fetch_all_stocks.py
```

### Step 3: Daily updates (automated via GitHub Actions)

GitHub Actions will automatically run `update_stocks.py` every **weekday at 07:30 AM IST** and commit the updated Parquet files.

You can also trigger it manually from the **Actions** tab → **Daily Stock Price Update** → **Run workflow**.

## 📊 Reading the Data

```python
import pandas as pd

# Load a single stock
df = pd.read_parquet("data/NSE/RELIANCE_NS.parquet")
print(df.tail())

# Load multiple stocks
import glob
dfs = {f.split("/")[-1].replace(".parquet",""):
       pd.read_parquet(f) for f in glob.glob("data/NSE/*.parquet")}
```

## 🔄 Update Schedule

| Event | Time |
|-------|------|
| NSE/BSE market close | 15:30 IST |
| GitHub Actions runs | 07:30 AM IST next day (02:00 UTC) |

> **Note**: The update runs early morning IST the next calendar day. This ensures the previous day's data is fully settled and available on Yahoo Finance.

## ⚠️ Disclaimer

Data is sourced from Yahoo Finance via the `yfinance` library for educational and research purposes only. This is not financial advice. Always verify data before use in production systems.

## 📜 License

MIT
