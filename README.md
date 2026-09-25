# 📈 Indian Historical Stock Prices, Indices, Corporate Actions, Institutional Flows, Sovereign Gold Bonds, Commodities, Mutual Funds & Unlisted Shares

A free, open dataset of **complete daily historical stock price data** (NSE & BSE), **major benchmark and sectoral indices** (NIFTY 50, SENSEX, etc.), **comprehensive corporate actions master catalog** (Bonus, Splits, Dividends, Rights, Demergers 1990 → Present), **institutional capital flows & derivatives positioning** (FII/DII daily cash flows & FII Long Ratio %), **complete master catalog of Sovereign Gold Bonds (SGB 2015 → 2024)** with all 67 tranches, cash flow schedules, and secondary market prices, **50+ years of historical Gold & Silver bullion rates**, **complete daily NAV history of all Indian Mutual Funds from inception**, and **historical valuations of major Indian Unlisted / Pre-IPO shares (2019 → Present)** — updated automatically every market working day.

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

### Corporate Actions (Master Catalog)
| Category | Events Tracked | Format | Date Range | Total Catalog Records |
|----------|----------------|--------|------------|-----------------------|
| **All Listed Equities** | **Bonus Issues, Stock Splits, Dividends, Rights, Buybacks, Demergers** | `data/CORPORATE_ACTIONS/corporate_actions.parquet`<br>`data/CORPORATE_ACTIONS/corporate_actions.csv` | 1990 → Present & Upcoming Announced | **43,748 events** |

### Institutional Capital Flows (FII / DII)
| Segment | Tracked Metrics & Sentiment | Format | Date Range | Total Records |
|---------|-----------------------------|--------|------------|---------------|
| **Cash Market Flows** | Gross Buy, Sell, and Net Investment in ₹ Crores for FII & DII | `data/FLOWS/fii_dii_cash.parquet`<br>`data/FLOWS/fii_dii_cash.csv` | Daily (2026 → Present) | **159 daily records** |
| **Derivatives Positioning & Sentiment** | Participant Open Interest (Client, DII, FII, Pro) & **FII Long Ratio %** | `data/FLOWS/fii_derivatives.parquet`<br>`data/FLOWS/fii_derivatives.csv` | Daily (2024 → Present) | **673 daily records** |
| **NSDL Monthly Macro Flows** | Foreign Portfolio Investors (FPI) Net Equity vs Debt Inflows in ₹ Crores | `data/FLOWS/fpi_monthly_history.parquet`<br>`data/FLOWS/fpi_monthly_history.csv` | 2005 → Present (21+ yrs) | **255 monthly records** |

### Sovereign Gold Bonds (SGB 2015 → 2024)
| Dataset | Scope & Description | Format | Date Range | Total Records |
|---------|---------------------|--------|------------|---------------|
| **SGB Master Catalog** | **All 67 Tranches** (Series I 2015-16 → Series IV 2023-24) with Issue & Redemption prices, 146.96 tonnes subscribed (₹72,274 Cr), and realized/expected CAGR % | `data/SGB/sgb_master_catalog.parquet`<br>`data/SGB/sgb_master_catalog.csv` | 2015 → 2032 (Maturity) | **67 tranches** |
| **Cash Flows Schedule** | Complete semi-annual coupon schedule (2.75% / 2.50%) & principal redemption payouts for every bond | `data/SGB/sgb_cash_flows.parquet`<br>`data/SGB/sgb_cash_flows.csv` | 2016 → 2032 | **1,139 cash flow events** |
| **Secondary Market Quotes** | Live trading quotes on NSE & BSE, LTP, Spot Gold comparison, and Discount/Premium % | `data/SGB/sgb_market_prices.parquet`<br>`data/SGB/sgb_market_prices.csv` | Active Tranches | **45 active bonds** |

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
- **Total corporate actions catalog:** 43,748 events (Parquet + CSV)
- **Total institutional flows datasets:** 3 unified datasets (Cash, Derivatives OI, NSDL Monthly)
- **Total sovereign gold bonds datasets:** 3 unified datasets (Master Catalog, Cash Flows, Market Prices)
- **Total commodities files:** 2
- **Total mutual fund partitions:** 10 + 1 master index
- **Total unlisted shares datasets:** 1 unified master file
- **Total dataset size:** ~1.04 GB

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

### Corporate Actions Master Catalog (`data/CORPORATE_ACTIONS/`)
* **Master Datasets:** `data/CORPORATE_ACTIONS/corporate_actions.parquet` & `corporate_actions.csv`
* `Ex_Date`: Ex-benefit trading cutoff date (`YYYY-MM-DD`)
* `Record_Date`: Shareholder entitlement eligibility date (`YYYY-MM-DD`)
* `Symbol`: Stock trading symbol (e.g. `RELIANCE`, `TCS`, `INFY`)
* `Company_Name`: Full legal corporate name
* `Series`: Equity series (`EQ`, `BE`, `SM`)
* `Action_Type`: Normalized classification (`BONUS`, `SPLIT`, `DIVIDEND`, `RIGHTS`, `BUYBACK`, `DEMERGER`, `CAPITAL_REDUCTION`, `MEETING`, `INTEREST`, `OTHER`)
* `Ratio_or_Amount`: Extracted benefit ratio or cash payout (e.g. `1:1`, `10:2`, `10:1`, `37.00`)
* `Purpose`: Raw official disclosure description
* `Face_Value`: Face value per share (₹)
* `ISIN`: International Securities Identification Number
* `BC_Start_Date`, `BC_End_Date`: Book closure dates

### Institutional Capital Flows (`data/FLOWS/`)
* **Cash Market Net Flows (`data/FLOWS/fii_dii_cash.parquet` & `.csv`):**
  * `Date`: Trading date (`YYYY-MM-DD`)
  * `FII_Buy_Cr`, `FII_Sell_Cr`, `FII_Net_Cr`: FII gross buy, sell, and net investment in ₹ Crores
  * `DII_Buy_Cr`, `DII_Sell_Cr`, `DII_Net_Cr`: DII gross buy, sell, and net investment in ₹ Crores
  * `Total_Net_Cr`: Combined institutional net cash flow (`FII_Net_Cr + DII_Net_Cr`)
* **Derivatives Open Interest & Sentiment (`data/FLOWS/fii_derivatives.parquet` & `.csv`):**
  * `Date`: Trading date (`YYYY-MM-DD`)
  * `FII_Index_Futures_Long`, `FII_Index_Futures_Short`, `FII_Index_Futures_Net`: FII contracts in Index Futures
  * `FII_Long_Ratio_Pct`: **FII Long Ratio %** (`Long / (Long + Short) * 100`) — Primary quant directional sentiment indicator
  * `DII_Index_Futures_Long`, `DII_Index_Futures_Short`, `DII_Index_Futures_Net`: DII positioning
  * `Pro_Index_Futures_Net`, `Client_Index_Futures_Net`: Proprietary desk and Retail client net positions
  * `FII_Stock_Futures_Net`, `DII_Stock_Futures_Net`: Stock futures net contracts
  * `FII_Index_Call_Long`, `FII_Index_Call_Short`, `FII_Index_Put_Long`, `FII_Index_Put_Short`: FII index options positioning
  * `Total_Index_Futures_OI`: Total index futures open interest contracts
* **NSDL Macro History (`data/FLOWS/fpi_monthly_history.parquet` & `.csv`):**
  * `Year`, `Month`, `Equity_Net_Cr`, `Debt_Net_Cr`, `Total_Net_Cr`, `Source` (NSDL)

### Sovereign Gold Bonds (`data/SGB/`)
* **Master Catalog (`data/SGB/sgb_master_catalog.parquet` & `.csv`):**
  * `Sr_No`: Chronological issue index (1 to 67)
  * `Tranche`: Standardized series name (e.g. `2015-16 Series I`, `2023-24 Series IV`)
  * `Symbol`: Exchange trading symbol (e.g. `SGBNOV23`, `SGBFEB32IV`)
  * `BSE_Code`: BSE scrip code (e.g. `539428`, `544128`)
  * `ISIN`: 12-character alphanumeric identifier (`IN0020150085` to `IN0020230184`)
  * `Issue_Date`, `Maturity_Date`, `Premature_Exit_Date`: Tenor timelines (8 years tenor; 5 years lock-in)
  * `Issue_Price`, `Online_Price`: Initial allotment price & discounted digital price (₹50 discount)
  * `Coupon_Rate_Pct`: Semi-annual coupon interest rate (2.75% for first 3 tranches; 2.50% thereafter)
  * `Annual_Interest_Per_Gram`: Fixed annual interest payout per gram (₹)
  * `Units_Subscribed_Grams`: Total volume subscribed in grams (146.96 tonnes total)
  * `Total_Amount_Cr`: Total sovereign capital raised (₹72,274 Cr across all tranches)
  * `Status`: `REDEEMED` or `ACTIVE`
  * `Redemption_Price`: Official RBI final settlement price (for matured series) or spot reference
  * `Secondary_Market_LTP`: Recent traded price on stock exchanges
  * `Capital_Gains_Pct`: Percentage price appreciation
  * `Total_CAGR_Pct`: True annualized compounded return factoring both price appreciation and all 16 semi-annual coupons
* **Cash Flow Schedule (`data/SGB/sgb_cash_flows.parquet` & `.csv`):**
  * `Symbol`, `Tranche`, `ISIN`, `Payment_Date`, `Payment_Type` (`COUPON` / `REDEMPTION`), `Amount_Per_Gram` (₹)
* **Secondary Market Quotes (`data/SGB/sgb_market_prices.parquet` & `.csv`):**
  * `Symbol`, `Tranche`, `ISIN`, `Exchange` (`NSE`/`BSE`), `LTP`, `Spot_Gold_Rate`, `Premium_Discount_Pct`, `Issue_Price`, `Maturity_Date`, `Status`

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
├── CORPORATE_ACTIONS/
│   ├── corporate_actions.parquet # 43,700+ corporate actions (1990 - present & upcoming)
│   └── corporate_actions.csv     # Complete tabular catalog for spreadsheet inspection
├── FLOWS/
│   ├── fii_dii_cash.parquet      # Daily Cash Market net flows (₹ Crores) for FII & DII
│   ├── fii_dii_cash.csv          # Tabular CSV for spreadsheet analysis
│   ├── fii_derivatives.parquet   # Daily participant Open Interest (NSE NSCCL) + FII Long Ratio %
│   ├── fii_derivatives.csv       # Tabular derivatives positioning CSV
│   ├── fpi_monthly_history.parquet # 21+ Years (2005 - 2026) NSDL monthly equity/debt flows
│   └── fpi_monthly_history.csv   # Tabular monthly macro flow history
├── SGB/
│   ├── sgb_master_catalog.parquet # All 67 SGB tranches (2015-2024), Issue/Redemption Prices, CAGR %
│   ├── sgb_master_catalog.csv     # Complete tabular catalog for spreadsheet inspection
│   ├── sgb_cash_flows.parquet     # 1,139 semi-annual coupon & principal redemption events
│   ├── sgb_cash_flows.csv         # Tabular cash flows schedule
│   ├── sgb_market_prices.parquet  # Live trading quotes, LTP, Spot Gold comparison, Discount/Premium %
│   └── sgb_market_prices.csv      # Tabular secondary market quotes
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
├── fetch_all_stocks.py             # One-time full history bootstrap
├── update_stocks.py                # Daily incremental updater
├── fetch_all_indices.py            # One-time index history bootstrap
├── update_indices.py               # Daily incremental indices updater
├── fetch_all_corporate_actions.py  # One-time full corporate actions bootstrap
├── update_corporate_actions.py     # Daily incremental corporate actions updater
├── fetch_all_flows.py              # One-time full institutional flows bootstrap
├── update_flows.py                 # Daily incremental institutional flows updater
├── build_sgb.py                    # Complete builder for all 67 Sovereign Gold Bond tranches
├── update_sgb.py                   # Daily updater and market price tracker for SGBs
├── update_commodities.py           # Daily commodities updater (Gold & Silver)
├── update_mf.py                    # Daily mutual funds NAV updater
├── build_unlisted.py               # Full compiler for unlisted equity valuations (2019 - Present)
├── update_unlisted.py              # Maintenance and updater for unlisted equity valuations
├── verify_data.py                  # Data quality checker
├── download_symbol_lists.py        # Refresh stock symbol master lists
└── utils.py                        # Shared helpers
.github/workflows/
├── daily_sgb_update.yml            # 06:40 PM IST — Sovereign Gold Bonds (SGB) master & secondary quotes
├── daily_mf_update.yml                # 06:47 PM IST — Mutual Funds NAV from inception
├── daily_commodities_update.yml       # 06:53 PM IST — Gold & Silver bullion spot rates
├── daily_unlisted_update.yml          # 06:58 PM IST — Top 22 unlisted / pre-IPO equities
├── daily_indices_update.yml           # 07:04 PM IST — Benchmark & Sectoral indices
├── daily_corporate_actions_update.yml # 07:11 PM IST — Corporate Actions Master Update
├── daily_flows_update.yml             # 07:16 PM IST — Institutional Capital Flows (FII / DII)
└── daily_stocks_update.yml            # 07:25 PM IST — NSE & BSE stocks (with circuit breaker)
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

# Corporate Actions Master Catalog (Bonus, Splits, Dividends, Rights, Demergers)
ca = pd.read_parquet("data/CORPORATE_ACTIONS/corporate_actions.parquet")
# Find all bonus issues in Indian market history:
bonuses = ca[ca["Action_Type"] == "BONUS"]
print(bonuses[["Ex_Date", "Symbol", "Company_Name", "Ratio_or_Amount"]].head())

# Find all corporate actions for Reliance Industries:
reliance_ca = ca[ca["Symbol"] == "RELIANCE"]
print(reliance_ca[["Ex_Date", "Action_Type", "Ratio_or_Amount", "Purpose"]].head())

# Benchmark & Sectoral Indices
nifty = pd.read_parquet("data/INDICES/NIFTY_50.parquet")
print(nifty.tail())

vix = pd.read_parquet("data/INDICES/INDIA_VIX.parquet")
print(vix.tail())

# Institutional Capital Flows (Cash & Derivatives Sentiment)
flows_cash = pd.read_parquet("data/FLOWS/fii_dii_cash.parquet")
print(flows_cash[["Date", "FII_Net_Cr", "DII_Net_Cr", "Total_Net_Cr"]].tail())

# Track FII Index Futures Long Ratio % (Primary quant bullish/bearish bias)
derivatives = pd.read_parquet("data/FLOWS/fii_derivatives.parquet")
latest_fao = derivatives.iloc[-1]
print(f"Date: {latest_fao['Date']}")
print(f"FII Index Futures Long: {latest_fao['FII_Index_Futures_Long']:,} | Short: {latest_fao['FII_Index_Futures_Short']:,}")
print(f"FII Long Ratio: {latest_fao['FII_Long_Ratio_Pct']}%")

# Sovereign Gold Bonds (Master Catalog, Returns & Cash Flows)
sgb = pd.read_parquet("data/SGB/sgb_master_catalog.parquet")
print(sgb[["Tranche", "Symbol", "Issue_Price", "Status", "Total_CAGR_Pct"]].head())

# Find all redeemed tranches and realized annualized CAGR returns
redeemed = sgb[sgb["Status"] == "REDEEMED"]
print(redeemed[["Tranche", "Issue_Date", "Maturity_Date", "Issue_Price", "Redemption_Price", "Total_CAGR_Pct"]])

# Secondary market quotes & discount to spot gold for active bonds
sgb_mkt = pd.read_parquet("data/SGB/sgb_market_prices.parquet")
discounted = sgb_mkt[sgb_mkt["Premium_Discount_Pct"] < 0]
print(discounted[["Symbol", "Tranche", "LTP", "Spot_Gold_Rate", "Premium_Discount_Pct"]].head())

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

Data is automatically updated strictly on **Indian Market Working Days** (NSE & BSE trading days, excluding weekends and official stock exchange trading holidays) via **8 dedicated, isolated workflows**:

| Workflow | Asset Class | Execution Time | Average Duration | Isolation & Resilience |
|----------|-------------|----------------|------------------|------------------------|
| `daily_sgb_update.yml` | **Sovereign Gold Bonds (SGB)** | **6:40 PM IST** (13:10 UTC) | ~10 seconds | Catalog status & secondary quotes; 100% independent |
| `daily_mf_update.yml` | **Mutual Funds (Daily NAV)** | **6:47 PM IST** (13:17 UTC) | ~35 seconds | AMFI direct fetch; 100% independent |
| `daily_commodities_update.yml` | **Commodities (Gold & Silver)** | **6:53 PM IST** (13:23 UTC) | ~10 seconds | Bullion spot rates; 100% independent |
| `daily_unlisted_update.yml` | **Unlisted & Pre-IPO Equities** | **6:58 PM IST** (13:28 UTC) | ~5 seconds | Indicative milestones; 100% independent |
| `daily_indices_update.yml` | **Benchmark & Sectoral Indices** | **7:04 PM IST** (13:34 UTC) | ~5 seconds | Key indices & India VIX; 100% independent |
| `daily_corporate_actions_update.yml` | **Corporate Actions Master** | **7:11 PM IST** (13:41 UTC) | ~5 seconds | Bonus, Splits, Dividends; 100% independent |
| `daily_flows_update.yml` | **Institutional Capital Flows** | **7:16 PM IST** (13:46 UTC) | ~10 seconds | FII/DII cash & F&O sentiment; 100% independent |
| `daily_stocks_update.yml` | **Equities (NSE & BSE)** | **7:25 PM IST** (13:55 UTC) | ~30–50 minutes | Built-in circuit breaker & cooldown; 90m cap |

> **Zero Blast Radius:** Because each asset class runs in its own dedicated workflow, a delay or rate limit in stock fetching has zero impact on Mutual Funds, Commodities, Indices, Corporate Actions, Institutional Flows, or Sovereign Gold Bonds. Everything is committed and available immediately every evening.
>
> **Evening Readiness:** Running between 6:40 PM and 7:25 PM IST ensures that all market closes, settlements, and institutional reports are committed early in the evening, well before nightfall.
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
