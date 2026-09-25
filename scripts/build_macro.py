#!/usr/bin/env python3
"""
scripts/build_macro.py
----------------------
Build and compile complete historical macroeconomic and fixed income indicators:
1. data/MACRO/in10y_bond_yield.parquet & .csv: Daily 10-Year Indian Government Benchmark Bond Yield (2000 - Present).
2. data/MACRO/forex_rates.parquet & .csv: Daily multi-decade foreign exchange rates (USD/INR, EUR/INR, GBP/INR, JPY/INR 2003 - Present).
3. data/MACRO/rbi_policy_rates.parquet & .csv: Chronological history of RBI policy rates (Repo, Reverse Repo, MSF, Bank Rate, CRR, SLR 2000 - Present).
4. data/MACRO/cpi_inflation.parquet & .csv: Monthly Consumer Price Index and YoY Inflation % (1957 - Present).
"""

import os
import io
import re
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from curl_cffi import requests
import yfinance as yf

ROOT_DIR = Path(__file__).resolve().parent.parent
MACRO_DIR = ROOT_DIR / "data" / "MACRO"
MACRO_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


# ── 1. India 10-Year Government Bond Yield (IN10Y) ──────────────────────────

def build_in10y_yield():
    """Build daily historical 10-Year Indian Government Benchmark Bond Yield from 2000 to present."""
    print("Fetching India 10-Year Benchmark Government Bond Yield (IN10Y)...")
    page_url = "https://www.investing.com/rates-bonds/india-10-year-bond-yield-historical-data"
    r = requests.get(page_url, impersonate="chrome")
    m = re.search(r'<script id="__NEXT_DATA__".*?>({.*?})</script>', r.text)
    
    token = ""
    if m:
        try:
            token = json.loads(m.group(1)).get("props", {}).get("pageProps", {}).get("accessToken", "")
        except Exception:
            pass

    req_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Domain-Id": "www",
        "Referer": page_url,
    }
    if token:
        req_headers["Authorization"] = f"Bearer {token}"

    all_rows = []
    # Pull in 2 historical chunks (2000-2018 and 2018-present) to cover all 26+ years without 5k truncation
    today_str = datetime.now().strftime("%Y-%m-%d")
    chunks = [("2000-01-01", "2018-12-31"), ("2018-01-01", today_str)]
    
    for start, end in chunks:
        api_url = f"https://api.investing.com/api/financialdata/historical/24014?start-date={start}&end-date={end}&time-frame=Daily"
        try:
            resp = requests.get(api_url, headers=req_headers, cookies=r.cookies, impersonate="chrome")
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                all_rows.extend(data)
                print(f"  Downloaded chunk {start} -> {end}: {len(data):,} rows")
            else:
                print(f"  Warning: chunk {start} -> {end} returned status {resp.status_code}")
        except Exception as e:
            print(f"  Error fetching chunk {start} -> {end}: {e}")

    if not all_rows:
        print("  Falling back to FRED Long-Term Government Bond Yields...")
        fred_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=INDIRLTLT01STM"
        rf = requests.get(fred_url, impersonate="chrome")
        df_fred = pd.read_csv(io.StringIO(rf.text))
        df_fred.columns = ["Date", "Close"]
        df_fred["Open"] = df_fred["Close"]
        df_fred["High"] = df_fred["Close"]
        df_fred["Low"] = df_fred["Close"]
        df_fred["Change_Pct"] = df_fred["Close"].pct_change() * 100.0
        df_clean = df_fred[["Date", "Open", "High", "Low", "Close", "Change_Pct"]]
    else:
        df_raw = pd.DataFrame(all_rows)
        df_raw["Date"] = pd.to_datetime(df_raw["rowDateTimestamp"]).dt.strftime("%Y-%m-%d")
        df_raw = df_raw.drop_duplicates(subset=["Date"]).sort_values("Date").reset_index(drop=True)
        df_clean = pd.DataFrame({
            "Date": df_raw["Date"],
            "Open": pd.to_numeric(df_raw["last_openRaw"], errors="coerce").round(4),
            "High": pd.to_numeric(df_raw["last_maxRaw"], errors="coerce").round(4),
            "Low": pd.to_numeric(df_raw["last_minRaw"], errors="coerce").round(4),
            "Close": pd.to_numeric(df_raw["last_closeRaw"], errors="coerce").round(4),
            "Change_Pct": pd.to_numeric(df_raw["change_precentRaw"], errors="coerce").round(2),
        })

    parquet_path = MACRO_DIR / "in10y_bond_yield.parquet"
    csv_path = MACRO_DIR / "in10y_bond_yield.csv"
    df_clean.to_parquet(parquet_path, index=False)
    df_clean.to_csv(csv_path, index=False)

    print(f"✅ Saved India 10Y Benchmark Bond Yield: {len(df_clean):,} daily records ({df_clean['Date'].min()} -> {df_clean['Date'].max()})")
    print(f"   -> {parquet_path}")
    print(f"   -> {csv_path}")
    return df_clean


# ── 2. Foreign Exchange Rates (Forex) ───────────────────────────────────────

def build_forex_rates():
    """Build multi-decade daily exchange rates for key currency pairs against INR."""
    print("Fetching Foreign Exchange Rates (USD/INR, EUR/INR, GBP/INR, JPY/INR)...")
    pairs = {
        "USD_INR": "USDINR=X",
        "EUR_INR": "EURINR=X",
        "GBP_INR": "GBPINR=X",
        "JPY_INR": "JPYINR=X",
    }

    merged = None
    for name, ticker in pairs.items():
        print(f"  Downloading {name} ({ticker})...")
        d = yf.download(ticker, start="2000-01-01", progress=False)
        if isinstance(d.columns, pd.MultiIndex):
            close_s = d["Close"][ticker]
        else:
            close_s = d["Close"]
        
        df_pair = pd.DataFrame({
            "Date": close_s.index.strftime("%Y-%m-%d"),
            name: close_s.values.flatten()
        }).dropna().drop_duplicates(subset=["Date"])
        df_pair[name] = pd.to_numeric(df_pair[name], errors="coerce").round(4)

        if merged is None:
            merged = df_pair
        else:
            merged = pd.merge(merged, df_pair, on="Date", how="outer")

    merged = merged.sort_values("Date").reset_index(drop=True)
    # Forward fill brief weekend/holiday mismatch gaps
    merged = merged.ffill().dropna().reset_index(drop=True)

    parquet_path = MACRO_DIR / "forex_rates.parquet"
    csv_path = MACRO_DIR / "forex_rates.csv"
    merged.to_parquet(parquet_path, index=False)
    merged.to_csv(csv_path, index=False)

    print(f"✅ Saved Foreign Exchange Rates: {len(merged):,} daily records ({merged['Date'].min()} -> {merged['Date'].max()})")
    print(f"   -> {parquet_path}")
    print(f"   -> {csv_path}")
    return merged


# ── 3. RBI Policy Rates & Key Reserve Ratios ─────────────────────────────────

def build_rbi_policy_rates():
    """Build complete chronological history of RBI monetary policy decisions and key rates."""
    print("Compiling RBI Policy Rates & Reserve Ratios (2000 - Present)...")
    
    # Official chronicle of RBI Monetary Policy revisions
    policy_events = [
        {"Date": "2000-06-05", "Repo": 8.00, "Reverse_Repo": 5.00, "SDF": None, "MSF": None, "Bank_Rate": 8.00, "CRR": 8.00, "SLR": 25.00, "Event": "Introduction of Liquidity Adjustment Facility (LAF)"},
        {"Date": "2000-07-21", "Repo": 8.00, "Reverse_Repo": 5.00, "SDF": None, "MSF": None, "Bank_Rate": 8.00, "CRR": 8.50, "SLR": 25.00, "Event": "CRR increase by 50 bps"},
        {"Date": "2001-02-16", "Repo": 7.75, "Reverse_Repo": 5.00, "SDF": None, "MSF": None, "Bank_Rate": 7.50, "CRR": 8.25, "SLR": 25.00, "Event": "Monetary easing cycle"},
        {"Date": "2001-03-01", "Repo": 7.50, "Reverse_Repo": 5.00, "SDF": None, "MSF": None, "Bank_Rate": 7.00, "CRR": 8.00, "SLR": 25.00, "Event": "Bank Rate reduced to 7.00%"},
        {"Date": "2001-04-27", "Repo": 6.75, "Reverse_Repo": 5.00, "SDF": None, "MSF": None, "Bank_Rate": 7.00, "CRR": 7.50, "SLR": 25.00, "Event": "Annual Monetary Policy Statement"},
        {"Date": "2001-10-22", "Repo": 6.50, "Reverse_Repo": 5.00, "SDF": None, "MSF": None, "Bank_Rate": 6.50, "CRR": 5.75, "SLR": 25.00, "Event": "CRR reduction to 5.75%"},
        {"Date": "2002-06-27", "Repo": 5.75, "Reverse_Repo": 5.00, "SDF": None, "MSF": None, "Bank_Rate": 6.50, "CRR": 5.00, "SLR": 25.00, "Event": "Liquidity enhancement"},
        {"Date": "2002-10-29", "Repo": 5.50, "Reverse_Repo": 5.00, "SDF": None, "MSF": None, "Bank_Rate": 6.25, "CRR": 4.75, "SLR": 25.00, "Event": "Mid-term review rate cuts"},
        {"Date": "2003-03-03", "Repo": 5.00, "Reverse_Repo": 5.00, "SDF": None, "MSF": None, "Bank_Rate": 6.25, "CRR": 4.75, "SLR": 25.00, "Event": "Repo cut to 5.00%"},
        {"Date": "2003-04-29", "Repo": 5.00, "Reverse_Repo": 5.00, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 4.50, "SLR": 25.00, "Event": "Bank rate cut to 6.00%"},
        {"Date": "2003-08-23", "Repo": 4.50, "Reverse_Repo": 4.50, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 4.50, "SLR": 25.00, "Event": "Repo rate reduced to 4.50%"},
        {"Date": "2004-10-26", "Repo": 4.75, "Reverse_Repo": 4.75, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 5.00, "SLR": 25.00, "Event": "Gradual tightening begins"},
        {"Date": "2005-04-28", "Repo": 5.00, "Reverse_Repo": 5.00, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 5.00, "SLR": 25.00, "Event": "Reverse repo hike"},
        {"Date": "2005-10-25", "Repo": 5.25, "Reverse_Repo": 5.25, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 5.00, "SLR": 25.00, "Event": "Repo hike to 5.25%"},
        {"Date": "2006-01-24", "Repo": 5.50, "Reverse_Repo": 5.50, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 5.00, "SLR": 25.00, "Event": "Quarterly policy hike"},
        {"Date": "2006-06-08", "Repo": 5.75, "Reverse_Repo": 5.75, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 5.00, "SLR": 25.00, "Event": "Pre-emptive rate hike"},
        {"Date": "2006-07-25", "Repo": 6.00, "Reverse_Repo": 6.00, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 5.00, "SLR": 25.00, "Event": "Repo reaches 6.00%"},
        {"Date": "2007-01-31", "Repo": 7.50, "Reverse_Repo": 6.00, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 5.50, "SLR": 25.00, "Event": "Inflation control tightening"},
        {"Date": "2007-03-30", "Repo": 7.75, "Reverse_Repo": 6.00, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 6.50, "SLR": 25.00, "Event": "CRR increased to 6.50%"},
        {"Date": "2007-08-04", "Repo": 7.75, "Reverse_Repo": 6.00, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 7.00, "SLR": 25.00, "Event": "CRR increased to 7.00%"},
        {"Date": "2007-11-10", "Repo": 7.75, "Reverse_Repo": 6.00, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 7.50, "SLR": 25.00, "Event": "CRR increased to 7.50%"},
        {"Date": "2008-05-24", "Repo": 7.75, "Reverse_Repo": 6.00, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 8.25, "SLR": 25.00, "Event": "Commodity inflation response"},
        {"Date": "2008-06-11", "Repo": 8.00, "Reverse_Repo": 6.00, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 8.25, "SLR": 25.00, "Event": "Repo raised to 8.00%"},
        {"Date": "2008-06-24", "Repo": 8.50, "Reverse_Repo": 6.00, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 8.75, "SLR": 25.00, "Event": "Repo raised to 8.50%"},
        {"Date": "2008-07-29", "Repo": 9.00, "Reverse_Repo": 6.00, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 9.00, "SLR": 25.00, "Event": "Peak tightening pre-GFC"},
        {"Date": "2008-10-20", "Repo": 8.00, "Reverse_Repo": 6.00, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 6.50, "SLR": 25.00, "Event": "Global Financial Crisis emergency easing"},
        {"Date": "2008-11-03", "Repo": 7.50, "Reverse_Repo": 6.00, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 5.50, "SLR": 25.00, "Event": "Further liquidity release"},
        {"Date": "2008-12-08", "Repo": 6.50, "Reverse_Repo": 5.00, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 5.00, "SLR": 24.00, "Event": "100 bps rate cut"},
        {"Date": "2009-01-05", "Repo": 5.50, "Reverse_Repo": 4.00, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 5.00, "SLR": 24.00, "Event": "GFC stimulus continuation"},
        {"Date": "2009-03-04", "Repo": 5.00, "Reverse_Repo": 3.50, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 5.00, "SLR": 24.00, "Event": "Repo cut to 5.00%"},
        {"Date": "2009-04-21", "Repo": 4.75, "Reverse_Repo": 3.25, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 5.00, "SLR": 24.00, "Event": "Trough of post-crisis easing"},
        {"Date": "2010-03-19", "Repo": 5.00, "Reverse_Repo": 3.50, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 5.75, "SLR": 25.00, "Event": "Post-crisis normalization starts"},
        {"Date": "2010-04-20", "Repo": 5.25, "Reverse_Repo": 3.75, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 6.00, "SLR": 25.00, "Event": "Annual Policy tightening"},
        {"Date": "2010-07-02", "Repo": 5.50, "Reverse_Repo": 4.00, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 6.00, "SLR": 25.00, "Event": "Rate hike"},
        {"Date": "2010-07-27", "Repo": 5.75, "Reverse_Repo": 4.50, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 6.00, "SLR": 25.00, "Event": "First quarter review"},
        {"Date": "2010-09-16", "Repo": 6.00, "Reverse_Repo": 5.00, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 6.00, "SLR": 25.00, "Event": "Mid-quarter review hike"},
        {"Date": "2010-11-02", "Repo": 6.25, "Reverse_Repo": 5.25, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 6.00, "SLR": 24.00, "Event": "Rate hike"},
        {"Date": "2011-01-25", "Repo": 6.50, "Reverse_Repo": 5.50, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 6.00, "SLR": 24.00, "Event": "Tightening cycle accelerates"},
        {"Date": "2011-03-17", "Repo": 6.75, "Reverse_Repo": 5.75, "SDF": None, "MSF": None, "Bank_Rate": 6.00, "CRR": 6.00, "SLR": 24.00, "Event": "Rate hike"},
        {"Date": "2011-05-03", "Repo": 7.25, "Reverse_Repo": 6.25, "SDF": None, "MSF": 8.25, "Bank_Rate": 6.00, "CRR": 6.00, "SLR": 24.00, "Event": "Introduction of MSF at 8.25%"},
        {"Date": "2011-06-16", "Repo": 7.50, "Reverse_Repo": 6.50, "SDF": None, "MSF": 8.50, "Bank_Rate": 6.00, "CRR": 6.00, "SLR": 24.00, "Event": "Mid-quarter review"},
        {"Date": "2011-07-26", "Repo": 8.00, "Reverse_Repo": 7.00, "SDF": None, "MSF": 9.00, "Bank_Rate": 6.00, "CRR": 6.00, "SLR": 24.00, "Event": "50 bps surprise hike"},
        {"Date": "2011-09-16", "Repo": 8.25, "Reverse_Repo": 7.25, "SDF": None, "MSF": 9.25, "Bank_Rate": 6.00, "CRR": 6.00, "SLR": 24.00, "Event": "Inflation fighting"},
        {"Date": "2011-10-25", "Repo": 8.50, "Reverse_Repo": 7.50, "SDF": None, "MSF": 9.50, "Bank_Rate": 6.00, "CRR": 6.00, "SLR": 24.00, "Event": "Peak of 2011 cycle"},
        {"Date": "2012-01-28", "Repo": 8.50, "Reverse_Repo": 7.50, "SDF": None, "MSF": 9.50, "Bank_Rate": 6.00, "CRR": 5.50, "SLR": 24.00, "Event": "CRR cut to 5.50%"},
        {"Date": "2012-03-09", "Repo": 8.50, "Reverse_Repo": 7.50, "SDF": None, "MSF": 9.50, "Bank_Rate": 6.00, "CRR": 4.75, "SLR": 24.00, "Event": "CRR cut to 4.75%"},
        {"Date": "2012-04-17", "Repo": 8.00, "Reverse_Repo": 7.00, "SDF": None, "MSF": 9.00, "Bank_Rate": 9.00, "CRR": 4.75, "SLR": 24.00, "Event": "Bank rate aligned with MSF"},
        {"Date": "2012-08-11", "Repo": 8.00, "Reverse_Repo": 7.00, "SDF": None, "MSF": 9.00, "Bank_Rate": 9.00, "CRR": 4.75, "SLR": 23.00, "Event": "SLR reduced to 23.00%"},
        {"Date": "2012-09-17", "Repo": 8.00, "Reverse_Repo": 7.00, "SDF": None, "MSF": 9.00, "Bank_Rate": 9.00, "CRR": 4.50, "SLR": 23.00, "Event": "CRR cut to 4.50%"},
        {"Date": "2012-11-03", "Repo": 8.00, "Reverse_Repo": 7.00, "SDF": None, "MSF": 9.00, "Bank_Rate": 9.00, "CRR": 4.25, "SLR": 23.00, "Event": "CRR cut to 4.25%"},
        {"Date": "2013-01-29", "Repo": 7.75, "Reverse_Repo": 6.75, "SDF": None, "MSF": 8.75, "Bank_Rate": 8.75, "CRR": 4.00, "SLR": 23.00, "Event": "Repo cut to 7.75%"},
        {"Date": "2013-03-19", "Repo": 7.50, "Reverse_Repo": 6.50, "SDF": None, "MSF": 8.50, "Bank_Rate": 8.50, "CRR": 4.00, "SLR": 23.00, "Event": "Mid-quarter cut"},
        {"Date": "2013-05-03", "Repo": 7.25, "Reverse_Repo": 6.25, "SDF": None, "MSF": 8.25, "Bank_Rate": 8.25, "CRR": 4.00, "SLR": 23.00, "Event": "Annual policy cut"},
        {"Date": "2013-07-15", "Repo": 7.25, "Reverse_Repo": 6.25, "SDF": None, "MSF": 10.25, "Bank_Rate": 10.25, "CRR": 4.00, "SLR": 23.00, "Event": "Taper Tantrum Rupee defense"},
        {"Date": "2013-09-20", "Repo": 7.50, "Reverse_Repo": 6.50, "SDF": None, "MSF": 9.50, "Bank_Rate": 9.50, "CRR": 4.00, "SLR": 23.00, "Event": "Rajan policy transition"},
        {"Date": "2013-10-29", "Repo": 7.75, "Reverse_Repo": 6.75, "SDF": None, "MSF": 8.75, "Bank_Rate": 8.75, "CRR": 4.00, "SLR": 23.00, "Event": "MSF normalization"},
        {"Date": "2014-01-28", "Repo": 8.00, "Reverse_Repo": 7.00, "SDF": None, "MSF": 9.00, "Bank_Rate": 9.00, "CRR": 4.00, "SLR": 23.00, "Event": "CPI inflation targeting framework"},
        {"Date": "2014-06-14", "Repo": 8.00, "Reverse_Repo": 7.00, "SDF": None, "MSF": 9.00, "Bank_Rate": 9.00, "CRR": 4.00, "SLR": 22.50, "Event": "SLR reduced to 22.50%"},
        {"Date": "2014-08-09", "Repo": 8.00, "Reverse_Repo": 7.00, "SDF": None, "MSF": 9.00, "Bank_Rate": 9.00, "CRR": 4.00, "SLR": 22.00, "Event": "SLR reduced to 22.00%"},
        {"Date": "2015-01-15", "Repo": 7.75, "Reverse_Repo": 6.75, "SDF": None, "MSF": 8.75, "Bank_Rate": 8.75, "CRR": 4.00, "SLR": 22.00, "Event": "Off-cycle 25 bps rate cut"},
        {"Date": "2015-02-07", "Repo": 7.75, "Reverse_Repo": 6.75, "SDF": None, "MSF": 8.75, "Bank_Rate": 8.75, "CRR": 4.00, "SLR": 21.50, "Event": "SLR reduced to 21.50%"},
        {"Date": "2015-03-04", "Repo": 7.50, "Reverse_Repo": 6.50, "SDF": None, "MSF": 8.50, "Bank_Rate": 8.50, "CRR": 4.00, "SLR": 21.50, "Event": "Post-budget off-cycle cut"},
        {"Date": "2015-06-02", "Repo": 7.25, "Reverse_Repo": 6.25, "SDF": None, "MSF": 8.25, "Bank_Rate": 8.25, "CRR": 4.00, "SLR": 21.50, "Event": "Bi-monthly cut to 7.25%"},
        {"Date": "2015-09-29", "Repo": 6.75, "Reverse_Repo": 5.75, "SDF": None, "MSF": 7.75, "Bank_Rate": 7.75, "CRR": 4.00, "SLR": 21.50, "Event": "50 bps surprise easing"},
        {"Date": "2016-04-05", "Repo": 6.50, "Reverse_Repo": 6.00, "SDF": None, "MSF": 7.00, "Bank_Rate": 7.00, "CRR": 4.00, "SLR": 21.25, "Event": "Narrowing policy corridor"},
        {"Date": "2016-10-04", "Repo": 6.25, "Reverse_Repo": 5.75, "SDF": None, "MSF": 6.75, "Bank_Rate": 6.75, "CRR": 4.00, "SLR": 20.75, "Event": "First MPC committee meeting"},
        {"Date": "2017-08-02", "Repo": 6.00, "Reverse_Repo": 5.75, "SDF": None, "MSF": 6.25, "Bank_Rate": 6.25, "CRR": 4.00, "SLR": 20.00, "Event": "Repo cut to 6.00%"},
        {"Date": "2018-06-06", "Repo": 6.25, "Reverse_Repo": 6.00, "SDF": None, "MSF": 6.50, "Bank_Rate": 6.50, "CRR": 4.00, "SLR": 19.50, "Event": "Rate hike to 6.25%"},
        {"Date": "2018-08-01", "Repo": 6.50, "Reverse_Repo": 6.25, "SDF": None, "MSF": 6.75, "Bank_Rate": 6.75, "CRR": 4.00, "SLR": 19.50, "Event": "Rate hike to 6.50%"},
        {"Date": "2019-02-07", "Repo": 6.25, "Reverse_Repo": 6.00, "SDF": None, "MSF": 6.50, "Bank_Rate": 6.50, "CRR": 4.00, "SLR": 19.25, "Event": "Das MPC easing starts"},
        {"Date": "2019-04-04", "Repo": 6.00, "Reverse_Repo": 5.75, "SDF": None, "MSF": 6.25, "Bank_Rate": 6.25, "CRR": 4.00, "SLR": 19.25, "Event": "Repo cut to 6.00%"},
        {"Date": "2019-06-06", "Repo": 5.75, "Reverse_Repo": 5.50, "SDF": None, "MSF": 6.00, "Bank_Rate": 6.00, "CRR": 4.00, "SLR": 19.00, "Event": "Stance changed to accommodative"},
        {"Date": "2019-08-07", "Repo": 5.40, "Reverse_Repo": 5.15, "SDF": None, "MSF": 5.65, "Bank_Rate": 5.65, "CRR": 4.00, "SLR": 18.75, "Event": "Unconventional 35 bps cut"},
        {"Date": "2019-10-04", "Repo": 5.15, "Reverse_Repo": 4.90, "SDF": None, "MSF": 5.40, "Bank_Rate": 5.40, "CRR": 4.00, "SLR": 18.50, "Event": "Repo cut to 5.15%"},
        {"Date": "2020-03-27", "Repo": 4.40, "Reverse_Repo": 4.00, "SDF": None, "MSF": 4.65, "Bank_Rate": 4.65, "CRR": 3.00, "SLR": 18.00, "Event": "COVID-19 Emergency Package (75 bps cut)"},
        {"Date": "2020-04-17", "Repo": 4.40, "Reverse_Repo": 3.75, "SDF": None, "MSF": 4.65, "Bank_Rate": 4.65, "CRR": 3.00, "SLR": 18.00, "Event": "Reverse repo cut to 3.75%"},
        {"Date": "2020-05-22", "Repo": 4.00, "Reverse_Repo": 3.35, "SDF": None, "MSF": 4.25, "Bank_Rate": 4.25, "CRR": 3.00, "SLR": 18.00, "Event": "Historic low repo rate 4.00%"},
        {"Date": "2021-03-27", "Repo": 4.00, "Reverse_Repo": 3.35, "SDF": None, "MSF": 4.25, "Bank_Rate": 4.25, "CRR": 3.50, "SLR": 18.00, "Event": "Stage 1 CRR restoration"},
        {"Date": "2021-05-22", "Repo": 4.00, "Reverse_Repo": 3.35, "SDF": None, "MSF": 4.25, "Bank_Rate": 4.25, "CRR": 4.00, "SLR": 18.00, "Event": "CRR normalized to 4.00%"},
        {"Date": "2022-04-08", "Repo": 4.00, "Reverse_Repo": 3.35, "SDF": 3.75, "MSF": 4.25, "Bank_Rate": 4.25, "CRR": 4.00, "SLR": 18.00, "Event": "Standing Deposit Facility (SDF) introduced"},
        {"Date": "2022-05-04", "Repo": 4.40, "Reverse_Repo": 3.35, "SDF": 4.15, "MSF": 4.65, "Bank_Rate": 4.65, "CRR": 4.50, "SLR": 18.00, "Event": "Off-cycle post-Ukraine war rate hike"},
        {"Date": "2022-06-08", "Repo": 4.90, "Reverse_Repo": 3.35, "SDF": 4.65, "MSF": 5.15, "Bank_Rate": 5.15, "CRR": 4.50, "SLR": 18.00, "Event": "50 bps hike"},
        {"Date": "2022-08-05", "Repo": 5.40, "Reverse_Repo": 3.35, "SDF": 5.15, "MSF": 5.65, "Bank_Rate": 5.65, "CRR": 4.50, "SLR": 18.00, "Event": "50 bps hike"},
        {"Date": "2022-09-30", "Repo": 5.90, "Reverse_Repo": 3.35, "SDF": 5.65, "MSF": 6.15, "Bank_Rate": 6.15, "CRR": 4.50, "SLR": 18.00, "Event": "50 bps hike"},
        {"Date": "2022-12-07", "Repo": 6.25, "Reverse_Repo": 3.35, "SDF": 6.00, "MSF": 6.50, "Bank_Rate": 6.50, "CRR": 4.50, "SLR": 18.00, "Event": "35 bps hike"},
        {"Date": "2023-02-08", "Repo": 6.50, "Reverse_Repo": 3.35, "SDF": 6.25, "MSF": 6.75, "Bank_Rate": 6.75, "CRR": 4.50, "SLR": 18.00, "Event": "Terminal rate 6.50% reached"},
        {"Date": "2025-02-07", "Repo": 6.25, "Reverse_Repo": 3.35, "SDF": 6.00, "MSF": 6.50, "Bank_Rate": 6.50, "CRR": 4.00, "SLR": 18.00, "Event": "Disinflationary cycle cut to 6.25%"},
        {"Date": "2025-04-09", "Repo": 6.00, "Reverse_Repo": 3.35, "SDF": 5.75, "MSF": 6.25, "Bank_Rate": 6.25, "CRR": 3.50, "SLR": 18.00, "Event": "Rate cut to 6.00%"},
        {"Date": "2025-06-06", "Repo": 5.50, "Reverse_Repo": 3.35, "SDF": 5.25, "MSF": 5.75, "Bank_Rate": 5.75, "CRR": 3.00, "SLR": 18.00, "Event": "50 bps growth support cut"},
        {"Date": "2025-12-05", "Repo": 5.25, "Reverse_Repo": 3.35, "SDF": 5.00, "MSF": 5.50, "Bank_Rate": 5.50, "CRR": 3.00, "SLR": 18.00, "Event": "Repo lowered to 5.25%"},
        {"Date": "2026-08-05", "Repo": 5.25, "Reverse_Repo": 3.35, "SDF": 5.00, "MSF": 5.50, "Bank_Rate": 5.50, "CRR": 3.00, "SLR": 18.00, "Event": "MPC pause maintained at 5.25%"},
    ]

    df = pd.DataFrame(policy_events).sort_values("Date").reset_index(drop=True)
    parquet_path = MACRO_DIR / "rbi_policy_rates.parquet"
    csv_path = MACRO_DIR / "rbi_policy_rates.csv"
    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)

    print(f"✅ Saved RBI Policy Rates History: {len(df)} monetary policy decision events (2000 - Present)")
    print(f"   -> {parquet_path}")
    print(f"   -> {csv_path}")
    return df


# ── 4. Consumer Price Index (CPI Inflation) ──────────────────────────────────

def build_cpi_inflation():
    """Build multi-decade monthly Consumer Price Index (CPI) and YoY inflation rates."""
    print("Fetching Consumer Price Index (CPI) history...")
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=INDCPIALLMINMEI"
    r = requests.get(url, impersonate="chrome")
    
    if r.status_code != 200:
        print(f"  Warning: FRED CPI download failed with status {r.status_code}")
        return pd.DataFrame()

    df = pd.read_csv(io.StringIO(r.text))
    df.columns = ["Date", "CPI_Index"]
    df["CPI_Index"] = pd.to_numeric(df["CPI_Index"], errors="coerce")
    df = df.dropna().sort_values("Date").reset_index(drop=True)
    
    # Calculate Year-over-Year (YoY) Inflation Rate %
    df["Inflation_YoY_Pct"] = (df["CPI_Index"].pct_change(12) * 100.0).round(2)
    df["CPI_Index"] = df["CPI_Index"].round(4)

    parquet_path = MACRO_DIR / "cpi_inflation.parquet"
    csv_path = MACRO_DIR / "cpi_inflation.csv"
    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)

    print(f"✅ Saved CPI Inflation History: {len(df):,} monthly records ({df['Date'].min()} -> {df['Date'].max()})")
    print(f"   -> {parquet_path}")
    print(f"   -> {csv_path}")
    return df


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("MACROECONOMIC & FIXED INCOME INDICATORS BOOTSTRAP")
    print("=" * 60)
    build_in10y_yield()
    print("-" * 60)
    build_forex_rates()
    print("-" * 60)
    build_rbi_policy_rates()
    print("-" * 60)
    build_cpi_inflation()
    print("=" * 60)
    print("Macroeconomic indicators bootstrap complete!")


if __name__ == "__main__":
    main()
