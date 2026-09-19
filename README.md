# 📈 Indian Historical Stock Prices

A free, open dataset of **complete daily historical stock price data** for all NSE and BSE listed Indian stocks — updated automatically every trading day.

---

## 📦 Coverage

| Exchange | Stocks | Ticker Format |
|----------|--------|--------------|
| NSE | ~2,577 | `SYMBOL_NS.parquet` (e.g. `RELIANCE_NS.parquet`) |
| BSE | ~4,399 | `SYMBOL_BO.parquet` (e.g. `TATAMOTORS_BO.parquet`) |

- **Date range:** January 1991 → Present
- **Total stocks:** ~6,976
- **Total size:** ~801 MB

---

## 🗂️ Data Fields

Each Parquet file contains daily records with the following columns:

| Column | Description |
|--------|-------------|
| `Date` | Trading date (index) |
| `Open` | Opening price (₹) |
| `High` | Day's highest price (₹) |
| `Low` | Day's lowest price (₹) |
| `Close` | Closing price (₹) |
| `Adj Close` | Adjusted closing price (accounts for splits & dividends) |
| `Volume` | Number of shares traded |
| `Dividends` | Dividend amount on that date (if any) |
| `Stock Splits` | Split ratio on that date (if any) |

---

## 📁 Repository Structure

```
data/
├── NSE/
│   ├── RELIANCE_NS.parquet
│   ├── TCS_NS.parquet
│   ├── INFY_NS.parquet
│   └── ... (~2,577 files)
├── BSE/
│   ├── TATAMOTORS_BO.parquet
│   ├── HDFCBANK_BO.parquet
│   └── ... (~4,399 files)
└── COMMODITIES/
    ├── GOLD_INR.parquet      # 50+ yrs (1970 - present) 24K, 22K, 18K in ₹/10g & ₹/1g
    └── SILVER_INR.parquet    # 50+ yrs (1970 - present) 999 & 925 in ₹/kg, 10g & 1g
scripts/
├── fetch_all_stocks.py       # One-time full history bootstrap
├── update_stocks.py          # Daily incremental updater
├── update_commodities.py     # Daily commodities updater (Gold & Silver)
├── verify_data.py            # Data quality checker
├── download_symbol_lists.py  # Refresh stock symbol master lists
└── utils.py                  # Shared helpers
.github/workflows/
└── update_stocks.yml         # Auto-runs every weekday at 7:30 AM IST
```

---

## 🚀 How to Use

### Install dependencies
```bash
pip install pandas pyarrow
```

### Load a single stock
```python
import pandas as pd

# NSE stock
df = pd.read_parquet("data/NSE/INFY_NS.parquet")
print(df.tail())

# BSE stock
df = pd.read_parquet("data/BSE/HDFCBANK_BO.parquet")
print(df.tail())

# Commodities (Gold & Silver - 50+ Years)
gold = pd.read_parquet("data/COMMODITIES/GOLD_INR.parquet")
print(gold[["Gold_24K_10g", "Gold_22K_10g", "Gold_18K_10g"]].tail())

silver = pd.read_parquet("data/COMMODITIES/SILVER_INR.parquet")
print(silver[["Silver_999_1kg", "Silver_925_1kg"]].tail())
```

### Query a specific date
```python
import pandas as pd

df = pd.read_parquet("data/NSE/INFY_NS.parquet")
df.index = pd.to_datetime(df.index)

# Get price on a specific date
print(df.loc["2020-03-12"])

# Get a date range
print(df.loc["2020-01-01":"2020-12-31"])
```

### Load directly from GitHub (no download needed)
```python
import pandas as pd

url = "https://raw.githubusercontent.com/aswinv90/indian-historical-stock-price/main/data/NSE/RELIANCE_NS.parquet"
df = pd.read_parquet(url)
print(df.tail())
```

### Load multiple stocks
```python
import pandas as pd
import glob

# All NSE stocks
dfs = {}
for f in glob.glob("data/NSE/*.parquet"):
    symbol = f.split("/")[-1].replace(".parquet", "")
    dfs[symbol] = pd.read_parquet(f)

print(f"Loaded {len(dfs)} stocks")
```

---

## 🔄 Update Schedule

Data is automatically updated every trading day:

| Event | Time |
|-------|------|
| NSE / BSE market close | 3:30 PM IST |
| Repository auto-update | 7:30 AM IST (next day) |

Updates are committed automatically by GitHub Actions — no manual intervention needed.

---

## ✅ Data Quality

Run the built-in verification script to check coverage and freshness:

```bash
python scripts/verify_data.py
```

---

## 🚦 Usage Limits

This is a static file repository hosted on GitHub. GitHub enforces a rate limit of approximately **60 raw file requests per hour per IP address**. Please be mindful of this when building applications on top of this dataset.

If you need bulk access, clone the repository locally instead of fetching individual files via raw URLs.

---

## ⚠️ Disclaimer

This dataset is provided for **educational and personal research purposes only**. It is not financial advice. Always verify data independently before use in any decision-making.

---

## 📜 License

**Personal Use Only.**

This dataset is free to use for **personal, non-commercial purposes** (learning, research, personal projects).

❌ Commercial use, redistribution, resale, or use in paid products/services is **not permitted** without explicit written permission from the author.

For permissions or enquiries: **mail@aswinv.com**

© 2026 aswinv90. All rights reserved.
