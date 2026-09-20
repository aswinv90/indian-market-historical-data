# 📈 Indian Historical Stock Prices, Commodities & Mutual Funds

A free, open dataset of **complete daily historical stock price data** (NSE & BSE), **50+ years of historical Gold & Silver bullion rates**, and **complete daily NAV history of all Indian Mutual Funds from inception** — updated automatically every market working day.

---

## 📦 Coverage

### Equities
| Exchange | Stocks | Ticker Format | Date Range |
|----------|--------|---------------|------------|
| NSE | ~2,577 | `SYMBOL_NS.parquet` (e.g. `RELIANCE_NS.parquet`) | 1991 → Present |
| BSE | ~4,399 | `SYMBOL_BO.parquet` (e.g. `TATAMOTORS_BO.parquet`) | 1991 → Present |

### Commodities (Bullion)
| Commodity | Coverage & Purities | Format | Date Range |
|-----------|---------------------|--------|------------|
| **Gold** | 24K (99.9%), 22K (91.6%), 18K (75.0%) in ₹/10g & ₹/1g | `GOLD_INR.parquet` | 1970 → Present (56+ yrs) |
| **Silver** | 999 Fine Silver & 925 Sterling Silver in ₹/kg, ₹/10g & ₹/1g | `SILVER_INR.parquet` | 1970 → Present (56+ yrs) |

### Mutual Funds (NAV from Inception)
| Category | Schemes Tracked | Format | Date Range | Total Daily Records |
|----------|-----------------|--------|------------|---------------------|
| **All Indian Mutual Funds** | **37,896 schemes** | `data/MF/nav_part_0..9.parquet` | Inception → Present | **35,358,852 records** |

- **Total stock files:** ~6,976
- **Total commodities files:** 2
- **Total mutual fund partitions:** 10 + 1 master index
- **Total dataset size:** ~1.02 GB

---

## 🗂️ Data Fields

### Stock Prices (Equities)
Each stock Parquet file contains daily records with the following columns:

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

### Commodities (Gold & Silver)
* **Gold (`data/COMMODITIES/GOLD_INR.parquet`):**
  * `Gold_24K_10g`, `Gold_24K_1g` (Pure 24 Karat 99.9%)
  * `Gold_22K_10g`, `Gold_22K_1g` (Standard 22 Karat 91.6%)
  * `Gold_18K_10g`, `Gold_18K_1g` (Jewellery 18 Karat 75.0%)
* **Silver (`data/COMMODITIES/SILVER_INR.parquet`):**
  * `Silver_999_1kg`, `Silver_999_10g`, `Silver_999_1g` (Pure 999 Fine Silver)
  * `Silver_925_1kg`, `Silver_925_10g`, `Silver_925_1g` (925 Sterling Silver)

### Mutual Funds (NAV from Inception)
* **Master Scheme Directory (`data/MF/mf_meta.parquet`):**
  * Index of all 37,896 funds: `schemeCode`, `schemeName`, `fundHouse`, `category`, `schemeType`, `isinGrowth`, `isinDiv`, `records`, `oldestDate`, `latestDate`.
* **Daily NAV Partitions (`data/MF/nav_part_0.parquet` ... `nav_part_9.parquet`):**
  * `date`: Trading date
  * `schemeCode`: Unique numerical scheme code
  * `nav`: Daily Net Asset Value (₹)

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
├── COMMODITIES/
│   ├── GOLD_INR.parquet      # 50+ yrs (1970 - present) 24K, 22K, 18K in ₹/10g & ₹/1g
│   └── SILVER_INR.parquet    # 50+ yrs (1970 - present) 999 & 925 in ₹/kg, 10g & 1g
└── MF/
    ├── mf_meta.parquet       # Master scheme catalog of all 37,896 mutual fund schemes
    ├── nav_part_0.parquet    # Historical NAV from inception partitioned by schemeCode % 10
    └── ... (nav_part_0 .. nav_part_9.parquet)
scripts/
├── fetch_all_stocks.py       # One-time full history bootstrap
├── update_stocks.py          # Daily incremental updater
├── update_commodities.py     # Daily commodities updater (Gold & Silver)
├── update_mf.py              # Daily mutual funds NAV updater
├── verify_data.py            # Data quality checker
├── download_symbol_lists.py  # Refresh stock symbol master lists
└── utils.py                  # Shared helpers
.github/workflows/
└── daily_market_update.yml   # Auto-runs on Indian Market Working Days (Stocks, Commodities, MFs)
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

# Mutual Funds (Load any scheme's full inception history)
# 1. Look up scheme code from master directory:
meta = pd.read_parquet("data/MF/mf_meta.parquet")
scheme = meta[meta["schemeName"].str.contains("SBI Small Cap", case=False, na=False)]
scheme_code = scheme.index[0] # e.g. 125494

# 2. Read corresponding partition (schemeCode % 10):
part_file = f"data/MF/nav_part_{scheme_code % 10}.parquet"
df_nav = pd.read_parquet(part_file)
fund_history = df_nav[df_nav["schemeCode"] == scheme_code].set_index("date")
print(fund_history.tail())
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

url = "https://raw.githubusercontent.com/aswinv90/indian-historical-stock-gold-silver-price/main/data/NSE/RELIANCE_NS.parquet"
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

Data is automatically updated strictly on **Indian Market Working Days** (NSE & BSE trading days, excluding weekends and official stock exchange trading holidays):

| Asset Class | Market Benchmark Close | Repository Auto-Update Execution | Frequency |
|-------------|------------------------|----------------------------------|-----------|
| **Equities (NSE & BSE)** | 3:30 PM IST | **7:30 AM IST** (next morning) | Every Market Working Day |
| **Commodities (Gold & Silver)** | Spot / Evening Settlement | **7:30 AM – 8:00 AM IST** (next morning) | Every Market Working Day |
| **Mutual Funds (Daily NAV)** | Evening AMFI Settlement (9:00 PM – 11:00 PM IST) | **7:30 AM – 8:00 AM IST** (next morning) | Every Market Working Day |

> **Trading Holiday Gate:** The automated pipeline evaluates exchange holiday calendars. If a weekday is a declared market holiday (e.g. Republic Day, Holi, Diwali, etc.), the run safely exits without producing empty or redundant commits.
>
> You can also trigger an immediate update manually anytime from the **Actions** tab on GitHub.

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
