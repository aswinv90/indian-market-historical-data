# 🗺️ Project Roadmap & Target Datasets

This document outlines the architectural roadmap for **`indian-market-historical-data`**, tracking completed asset classes and target datasets currently planned for integration.

---

## ✅ Completed Milestones

- [x] **NSE Equities (1991 → Present):** ~2,577 stocks in compact `.parquet` format.
- [x] **BSE Equities (1991 → Present):** ~4,401 stocks in compact `.parquet` format (cleaned of debt debentures).
- [x] **Commodities Bullion (1970 → Present):** 56+ years of 24K/22K/18K Gold and 999/925 Silver rates.
- [x] **Mutual Funds (Inception → Present):** Complete daily NAV history across all 37,896 AMFI schemes (~35.3M rows) sharded into 10 partitions + master metadata index.
- [x] **Unlisted & Pre-IPO Shares (2019 → Present):** Valuation milestones and dealer quotes for top 22 companies in both `.parquet` and `.csv`.
- [x] **Decoupled Automation Architecture:** 4 isolated, staggered GitHub Actions workflows (MF → Commodities → Unlisted → Stocks) with built-in Yahoo Finance circuit breaker.

---

## 🎯 Target Datasets & Upcoming Phases

### Phase 1: Benchmark & Sectoral Indices 📊 *(Immediate Target)*
- **Broad Market Benchmarks:**
  - `NIFTY_50`, `NIFTY_NEXT_50`, `NIFTY_100`, `NIFTY_200`, `NIFTY_500`
  - `NIFTY_MIDCAP_150`, `NIFTY_SMALLCAP_250`, `NIFTY_MICROCAP_250`
  - `BSE_SENSEX`, `BSE_100`, `BSE_500`, `BSE_MIDCAP`, `BSE_SMALLCAP`
- **Key Sectoral Indices:**
  - `NIFTY_BANK`, `NIFTY_IT`, `NIFTY_PHARMA`, `NIFTY_AUTO`, `NIFTY_FMCG`, `NIFTY_METAL`, `NIFTY_REALTY`, `NIFTY_ENERGY`, `NIFTY_PSU_BANK`
- **Volatility Benchmark:**
  - `INDIA_VIX` (Daily implied volatility index)

---

### Phase 2: Macroeconomic & Fixed Income Indicators 🏛️
- **10-Year Indian Government Bond Yield (G-Sec 10Y):** Benchmark risk-free rate for financial valuation and CAPM models.
- **RBI Policy Rates History:** Historical repo rate, reverse repo rate, CRR, and SLR changes.
- **Foreign Exchange Rates:** Daily historical `USD/INR`, `EUR/INR`, `GBP/INR`, and `JPY/INR`.
- **Consumer Price Index (CPI):** Monthly headline and core retail inflation rates.

---

### Phase 3: Institutional Capital Flows (FII / DII) 💼
- **Daily Net Inflows & Outflows:** Cash market buying and selling numbers for Foreign Institutional Investors (FII) and Domestic Institutional Investors (DII) in ₹ Crores.
- **Derivatives Open Interest:** FII/DII long/short positioning ratios in index futures.

---

### Phase 4: Corporate Actions Master Catalog 📜
- **Unified Corporate Actions Table:**
  - Ex-date, record date, company symbol, action type (Stock Split, Bonus Issue, Demerger, Rights Issue, Dividend amount).
  - Consolidated cross-exchange historical reference file.

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
