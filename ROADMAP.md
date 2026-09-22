# 🗺️ Project Roadmap & Target Datasets

This document outlines the architectural roadmap for **`indian-market-historical-data`**, tracking completed asset classes and target datasets currently planned for integration.

---

## ✅ Completed Milestones

- [x] **NSE Equities (1991 → Present):** ~2,577 stocks in compact `.parquet` format.
- [x] **BSE Equities (1991 → Present):** ~4,401 stocks in compact `.parquet` format (cleaned of debt debentures).
- [x] **Commodities Bullion (1970 → Present):** 56+ years of 24K/22K/18K Gold and 999/925 Silver rates.
- [x] **Mutual Funds (Inception → Present):** Complete daily NAV history across all 37,896 AMFI schemes (~35.3M rows) sharded into 10 partitions + master metadata index.
- [x] **Unlisted & Pre-IPO Shares (2019 → Present):** Valuation milestones and dealer quotes for top 22 companies in both `.parquet` and `.csv`.
- [x] **Benchmark & Sectoral Indices (1997 → Present):** 10 major benchmark, sectoral, and volatility indices (NIFTY 50, S&P BSE SENSEX, NIFTY BANK, INDIA VIX, NIFTY IT, NIFTY PHARMA, NIFTY 100, NIFTY 200, NIFTY 500, NIFTY MIDCAP 50) in `data/INDICES/` with master catalog.
- [x] **Corporate Actions Master Catalog (1990 → Present):** 43,700+ corporate actions covering Bonus issues, Stock Splits, Dividends, Rights, Buybacks, and Demergers in `data/CORPORATE_ACTIONS/` (both `.parquet` and `.csv`).
- [x] **Decoupled Automation Architecture:** 6 isolated, staggered GitHub Actions workflows (MF → Commodities → Unlisted → Indices → Corporate Actions → Stocks) with built-in Yahoo Finance circuit breaker.

---

## 🎯 Target Datasets & Upcoming Phases

### Phase 1: Benchmark & Sectoral Indices 📊 *(Completed ✅)*
- [x] **Core Benchmarks:** `NIFTY_50` (^NSEI), `SENSEX` (^BSESN), `NIFTY_100` (^CNX100), `NIFTY_200` (^CNX200), `NIFTY_500` (^CRSLDX), `NIFTY_MIDCAP_50` (^NSEMDCP50)
- [x] **Key Sectorals:** `NIFTY_BANK` (^NSEBANK), `NIFTY_IT` (^CNXIT), `NIFTY_PHARMA` (^CNXPHARMA)
- [x] **Market Volatility:** `INDIA_VIX` (^INDIAVIX)
- [x] **Dedicated Daily Workflow:** Staggered at 09:15 PM IST prior to stocks update.

---

### Phase 2: Corporate Actions Master Catalog 📜 *(Completed ✅)*
- [x] **Unified Corporate Actions Table:** 43,748 events from 1990 to present + forward announcements (`data/CORPORATE_ACTIONS/`).
- [x] **Action Types Tracked:** Bonus (with ratios), Splits (with split ratios), Dividends (with payout per share), Rights issues, Buybacks, Demergers, and AGM/EGM dates.
- [x] **Dual Distribution:** Both snappy-compressed `.parquet` and plain `.csv` formats.
- [x] **Dedicated Daily Workflow:** Staggered at 09:20 PM IST prior to stocks update.

---

### Phase 3: Institutional Capital Flows (FII / DII) 💼
- **Daily Net Inflows & Outflows:** Cash market buying and selling numbers for Foreign Institutional Investors (FII) and Domestic Institutional Investors (DII) in ₹ Crores.
- **Derivatives Open Interest:** FII/DII long/short positioning ratios in index futures.

---

### Phase 4: Macroeconomic & Fixed Income Indicators 🏛️
- **10-Year Indian Government Bond Yield (G-Sec 10Y):** Benchmark risk-free rate for financial valuation and CAPM models.
- **RBI Policy Rates History:** Historical repo rate, reverse repo rate, CRR, and SLR changes.
- **Foreign Exchange Rates:** Daily historical `USD/INR`, `EUR/INR`, `GBP/INR`, and `JPY/INR`.
- **Consumer Price Index (CPI):** Monthly headline and core retail inflation rates.

---

### Phase 5: Sovereign Gold Bonds (SGB) Master History 🪙
- **Complete SGB Series Catalog (2015 → 2024):**
  - Tranche code, issue price per gram (₹), subscription period, maturity date, and redemption price history.

---

### Phase 6: Developer Ecosystem & Python SDK 🚀
- **PyPI Package (`pip install indian-market-data`):**
  - Lightweight Python wrapper with local cache handling so quants and data scientists can fetch clean DataFrames with 1 line of code:
    ```python
    import indianmarket as im

    df = im.get_stock("RELIANCE")
    gold = im.get_gold()
    nifty = im.get_index("NIFTY_50")
    ```
