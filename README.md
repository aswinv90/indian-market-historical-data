# 📈 Indian Historical Stock Prices, Indices, Commodities, Mutual Funds & Unlisted Shares

A free, open dataset of **complete daily historical stock price data** (NSE & BSE), **major benchmark and sectoral indices** (NIFTY 50, SENSEX, etc.), **50+ years of historical Gold & Silver bullion rates**, **complete daily NAV history of all Indian Mutual Funds from inception**, and **historical valuations of major Indian Unlisted / Pre-IPO shares (2019 → Present)** — updated automatically every market working day.

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support%20Project-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/aswinv)

---

## 📦 Coverage

### Equities (Listed)
| Exchange | Stocks | Ticker Format | Date Range |
|----------|--------|---------------|------------|
| NSE | ~2,577 | `SYMBOL_NS.parquet` (e.g. `RELIANCE_NS.parquet`) | 1991 → Present |
| BSE | ~4,399 | `SYMBOL_BO.parquet` (e.g. `TATAMOTORS_BO.parquet`) | 1991 → Present |

### Benchmark & Sectoral Indices
| Index | Symbol | Category | Format | Date Range | Total Daily Records |
|-------|--------|----------|--------|------------|---------------------|
| **NIFTY 50** | `^NSEI` | Benchmark | `NIFTY_50.parquet` | 2007 → Present | ~4,665 records |
| **S&P BSE SENSEX** | `^BSESN` | Benchmark | `SENSEX.parquet` | 1997 → Present | ~7,200 records |
| **NIFTY BANK** | `^NSEBANK` | Sectoral | `NIFTY_BANK.parquet` | 2007 → Present | ~4,680 records |
| **INDIA VIX** | `^INDIAVIX` | Volatility | `INDIA_VIX.parquet` | 2008 → Present | ~4,546 records |
| **NIFTY IT** | `^CNXIT` | Sectoral | `NIFTY_IT.parquet` | 2007 → Present | ~4,680 records |
| **NIFTY PHARMA** | `^CNXPHARMA` | Sectoral | `NIFTY_PHARMA.parquet` | 2011 → Present | ~3,852 records |
| **NIFTY 100** | `^CNX100` | Broad Market | `NIFTY_100.parquet` | 2005 → Present | ~5,119 records |
| **NIFTY 200** | `^CNX200` | Broad Market | `NIFTY_200.parquet` | 2004 → Present | ~5,602 records |
| **NIFTY 500** | `^CRSLDX` | Broad Market | `NIFTY_500.parquet` | 2005 → Present | ~5,162 records |
| **NIFTY MIDCAP 50** | `^NSEMDCP50` | Broad Market | `NIFTY_MIDCAP_50.parquet` | 2007 → Present | ~4,633 records |

### Commodities (Bullion)
| Commodity | Coverage & Purities | Format | Date Range |
|-----------|---------------------|--------|------------|
| **Gold** | 24K (99.9%), 22K (91.6%), 18K (75.0%) in ₹/10g & ₹/1g | `GOLD_INR.parquet` | 1970 → Present (56+ yrs) |
| **Silver** | 999 Fine Silver & 925 Sterling Silver in ₹/kg, ₹/10g & ₹/1g | `SILVER_INR.parquet` | 1970 → Present (56+ yrs) |

### Mutual Funds (NAV from Inception)
| Category | Schemes Tracked | Format | Date Range | Total Daily Records |
|----------|-----------------|--------|------------|---------------------|
| **All Indian Mutual Funds** | **37,896 schemes** | `data/MF/nav_part_0..9.parquet` | Inception → Present | **35,358,852 records** |

### Unlisted & Pre-IPO Equities
| Universe | Companies Tracked | Format | Date Range | Valuation Milestones & Quotes |
|----------|-------------------|--------|------------|-------------------------------|
| **Top Indian Unlisted / Pre-IPO** | **22 companies** (NSE, Reliance Retail, Tata Capital, HDB Financial, NSDL, Swiggy, boAt, CSK, Zepto, etc.) | `data/UNLISTED/unlisted_shares.parquet`<br>`data/UNLISTED/unlisted_shares.csv` | 2019 → Present | **145 milestone records** |

- **Total stock files:** ~6,976
- **Total index files:** 10 + 1 master catalog
- **Total commodities files:** 2
- **Total mutual fund partitions:** 10 + 1 master index
- **Total unlisted shares datasets:** 1 unified master file
- **Total dataset size:** ~1.03 GB

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

### Benchmark & Sectoral Indices (`data/INDICES/*.parquet`)
* **Daily OHLCV Data:**
  * `Date`: Trading date (index)
  * `Open`, `High`, `Low`, `Close`, `Adj Close`: Index values
  * `Volume`: Total index volume / turnover
* **Index Catalog (`data/INDICES/index_list.csv`):**
  * `Symbol`, `Ticker`, `Name`, `Exchange`, `Category`, `Description`, `Start_Date`, `End_Date`, `Total_Records`, `Parquet_File`

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

### Unlisted & Pre-IPO Equities (`data/UNLISTED/unlisted_shares.parquet`)
* `date`: Benchmark transaction or quote date
* `symbol`: Standardized identifier (e.g. `NSE`, `RELIANCE_RETAIL`, `TATA_CAPITAL`, `HDB_FINANCIAL`, `BOAT`, `CSK`, `ZEPTO`)
* `company`: Full legal entity name
* `price`: Indicative price or round valuation per share (₹)
* `event`: Nature of valuation milestone (e.g., *Secondary Market Quote*, *Strategic Funding Round*, *Capital Reduction Valuation*, *De-merger Scheme*)
* `sector`: Industry sector
* `face_value`: Face value per share (₹)

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
├── INDICES/
│   ├── index_list.csv        # Master directory with ticker mapping and record counts
│   ├── NIFTY_50.parquet      # Multi-decade OHLCV (2007 - present)
│   ├── SENSEX.parquet        # Multi-decade OHLCV (1997 - present)
│   ├── NIFTY_BANK.parquet    # Top liquid Indian banking stocks
│   ├── INDIA_VIX.parquet     # Implied volatility index (Fear Gauge)
│   └── ... (10 major indices)
├── COMMODITIES/
│   ├── GOLD_INR.parquet      # 50+ yrs (1970 - present) 24K, 22K, 18K in ₹/10g & ₹/1g
│   └── SILVER_INR.parquet    # 50+ yrs (1970 - present) 999 & 925 in ₹/kg, 10g & 1g
├── MF/
│   ├── mf_meta.parquet       # Master scheme catalog of all 37,896 mutual fund schemes
│   ├── nav_part_0.parquet    # Historical NAV from inception partitioned by schemeCode % 10
│   └── ... (nav_part_0 .. nav_part_9.parquet)
└── UNLISTED/
    ├── unlisted_shares.parquet # Historical valuations & quotes (2019 - Present) for top 22 unlisted firms
    └── unlisted_shares.csv     # Plain CSV version for easy spreadsheet / Excel inspection
scripts/
├── fetch_all_stocks.py       # One-time full history bootstrap
├── update_stocks.py          # Daily incremental updater
├── fetch_all_indices.py      # One-time index history bootstrap
├── update_indices.py         # Daily incremental indices updater
├── update_commodities.py     # Daily commodities updater (Gold & Silver)
├── update_mf.py              # Daily mutual funds NAV updater
├── build_unlisted.py         # Full compiler for unlisted equity valuations (2019 - Present)
├── update_unlisted.py        # Maintenance and updater for unlisted equity valuations
├── verify_data.py            # Data quality checker
├── download_symbol_lists.py  # Refresh stock symbol master lists
└── utils.py                  # Shared helpers
.github/workflows/
├── daily_mf_update.yml          # 09:00 PM IST — Mutual Funds NAV from inception
├── daily_commodities_update.yml # 09:05 PM IST — Gold & Silver bullion spot rates
├── daily_unlisted_update.yml    # 09:10 PM IST — Top 22 unlisted / pre-IPO equities
├── daily_indices_update.yml     # 09:15 PM IST — Benchmark & Sectoral indices
└── daily_stocks_update.yml      # 09:30 PM IST — NSE & BSE stocks (with circuit breaker)
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

# Benchmark & Sectoral Indices
nifty = pd.read_parquet("data/INDICES/NIFTY_50.parquet")
print(nifty.tail())

vix = pd.read_parquet("data/INDICES/INDIA_VIX.parquet")
print(vix.tail())

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

# Unlisted & Pre-IPO Equities (Valuation Milestones & Dealer Quotes)
unlisted = pd.read_parquet("data/UNLISTED/unlisted_shares.parquet")
print(unlisted[unlisted["symbol"] == "NSE"][["date", "price", "event"]])
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

url = "https://raw.githubusercontent.com/aswinv90/indian-market-historical-data/main/data/NSE/RELIANCE_NS.parquet"
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

Data is automatically updated strictly on **Indian Market Working Days** (NSE & BSE trading days, excluding weekends and official stock exchange trading holidays) via **5 dedicated, isolated workflows**:

| Workflow | Asset Class | Execution Time | Average Duration | Isolation & Resilience |
|----------|-------------|----------------|------------------|------------------------|
| `daily_mf_update.yml` | **Mutual Funds (Daily NAV)** | **9:00 PM IST** (15:30 UTC) | ~35 seconds | AMFI direct fetch; 100% independent |
| `daily_commodities_update.yml` | **Commodities (Gold & Silver)** | **9:05 PM IST** (15:35 UTC) | ~10 seconds | Bullion spot rates; 100% independent |
| `daily_unlisted_update.yml` | **Unlisted & Pre-IPO Equities** | **9:10 PM IST** (15:40 UTC) | ~5 seconds | Indicative milestones; 100% independent |
| `daily_indices_update.yml` | **Benchmark & Sectoral Indices** | **9:15 PM IST** (15:45 UTC) | ~5 seconds | Key indices & India VIX; 100% independent |
| `daily_stocks_update.yml` | **Equities (NSE & BSE)** | **9:30 PM IST** (16:00 UTC) | ~30–50 minutes | Built-in circuit breaker & cooldown; 90m cap |

> **Zero Blast Radius:** Because each asset class runs in its own dedicated workflow, a delay or rate limit in stock fetching has zero impact on Mutual Funds, Commodities, or Indices. NAVs, bullion prices, and indices are committed and available immediately every evening.
>
> **Weekend Readiness:** Running on the same evening between 9:00 PM and 9:30 PM IST ensures that all Friday closing prices and weekend Muhurat sessions are committed and available immediately for researchers, portfolio backtesters, and weekend users throughout Saturday and Sunday.
>
> **Trading Holiday Gate:** The automated pipeline evaluates exchange holiday calendars. If a day is a declared market holiday (e.g. Republic Day, Holi, etc.), the run safely exits without producing empty commits.
>
> You can also trigger an immediate update for any asset class manually anytime from the **Actions** tab on GitHub.

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

## 🗺️ Roadmap & Upcoming Targets

See [**ROADMAP.md**](ROADMAP.md) for full project milestones, including upcoming additions:
- 📜 **Corporate Actions:** Consolidated Bonus, Splits, and Dividend histories
- 💼 **Institutional Flows:** Daily FII / DII net cash & derivatives positioning
- 🏛️ **Macro & Fixed Income:** 10Y G-Sec Yield, RBI Repo Rates, Forex (USD/INR), CPI Inflation
- 🪙 **Sovereign Gold Bonds:** Complete SGB tranche issue & redemption history
- 🚀 **Python SDK:** `pip install indian-market-data` for 1-line Python access

---

## ☕ Support & Sponsorship

If this free, open dataset saves you time, powers your research, or assists your financial modeling, consider supporting its daily server bandwidth and ongoing maintenance:

<a href="https://www.buymeacoffee.com/aswinv" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="190"></a>

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
