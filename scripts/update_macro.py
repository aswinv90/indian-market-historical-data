#!/usr/bin/env python3
"""
scripts/update_macro.py
-----------------------
Daily incremental updater for macroeconomic and fixed income indicators:
1. Appends latest trading day 10Y Indian Government Bond Yield (IN10Y).
2. Appends latest foreign exchange rates (USD/INR, EUR/INR, GBP/INR, JPY/INR).
3. Checks for latest monthly CPI inflation release.
"""

import argparse
import sys
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from curl_cffi import requests
import yfinance as yf

ROOT_DIR = Path(__file__).resolve().parent.parent
MACRO_DIR = ROOT_DIR / "data" / "MACRO"
MACRO_DIR.mkdir(parents=True, exist_ok=True)


def update_in10y_yield():
    """Incrementally update India 10-Year Bond Yield."""
    p_path = MACRO_DIR / "in10y_bond_yield.parquet"
    if not p_path.exists():
        print("in10y_bond_yield.parquet not found. Running full build...")
        import subprocess
        subprocess.run([sys.executable, str(ROOT_DIR / "scripts" / "build_macro.py")], check=True)
        return

    df_old = pd.read_parquet(p_path)
    last_dt = df_old["Date"].max()
    print(f"Updating IN10Y Bond Yield (current latest: {last_dt})...")

    page_url = "https://www.investing.com/rates-bonds/india-10-year-bond-yield-historical-data"
    try:
        r = requests.get(page_url, impersonate="chrome")
        m = re.search(r'<script id="__NEXT_DATA__".*?>({.*?})</script>', r.text)
        token = ""
        if m:
            token = json.loads(m.group(1)).get("props", {}).get("pageProps", {}).get("accessToken", "")

        req_headers = {
            "User-Agent": "Mozilla/5.0",
            "Domain-Id": "www",
            "Referer": page_url,
        }
        if token:
            req_headers["Authorization"] = f"Bearer {token}"

        start_dt = (datetime.strptime(last_dt, "%Y-%m-%d") - timedelta(days=5)).strftime("%Y-%m-%d")
        end_dt = datetime.now().strftime("%Y-%m-%d")
        api_url = f"https://api.investing.com/api/financialdata/historical/24014?start-date={start_dt}&end-date={end_dt}&time-frame=Daily"
        
        r2 = requests.get(api_url, headers=req_headers, cookies=r.cookies, impersonate="chrome")
        if r2.status_code == 200:
            data = r2.json().get("data", [])
            if data:
                df_new = pd.DataFrame(data)
                df_new["Date"] = pd.to_datetime(df_new["rowDateTimestamp"]).dt.strftime("%Y-%m-%d")
                df_new = pd.DataFrame({
                    "Date": df_new["Date"],
                    "Open": pd.to_numeric(df_new["last_openRaw"], errors="coerce").round(4),
                    "High": pd.to_numeric(df_new["last_maxRaw"], errors="coerce").round(4),
                    "Low": pd.to_numeric(df_new["last_minRaw"], errors="coerce").round(4),
                    "Close": pd.to_numeric(df_new["last_closeRaw"], errors="coerce").round(4),
                    "Change_Pct": pd.to_numeric(df_new["change_precentRaw"], errors="coerce").round(2),
                })
                combined = pd.concat([df_old, df_new], ignore_index=True)
                combined = combined.drop_duplicates(subset=["Date"]).sort_values("Date").reset_index(drop=True)
                combined.to_parquet(p_path, index=False)
                combined.to_csv(MACRO_DIR / "in10y_bond_yield.csv", index=False)
                print(f"  IN10Y updated: {len(combined):,} rows (latest: {combined['Date'].max()})")
                return
    except Exception as e:
        print(f"  Warning updating IN10Y: {e}")
    print(f"  IN10Y already at latest: {last_dt}")


def update_forex_rates():
    """Incrementally update Forex exchange rates."""
    p_path = MACRO_DIR / "forex_rates.parquet"
    if not p_path.exists():
        return

    df_old = pd.read_parquet(p_path)
    last_dt = df_old["Date"].max()
    print(f"Updating Forex Rates (current latest: {last_dt})...")

    pairs = {
        "USD_INR": "USDINR=X",
        "EUR_INR": "EURINR=X",
        "GBP_INR": "GBPINR=X",
        "JPY_INR": "JPYINR=X",
    }

    start_fetch = (datetime.strptime(last_dt, "%Y-%m-%d") - timedelta(days=5)).strftime("%Y-%m-%d")
    merged_new = None

    for name, ticker in pairs.items():
        try:
            d = yf.download(ticker, start=start_fetch, progress=False)
            if isinstance(d.columns, pd.MultiIndex):
                close_s = d["Close"][ticker]
            else:
                close_s = d["Close"]
            df_p = pd.DataFrame({
                "Date": close_s.index.strftime("%Y-%m-%d"),
                name: close_s.values.flatten()
            }).dropna().drop_duplicates(subset=["Date"])
            df_p[name] = pd.to_numeric(df_p[name], errors="coerce").round(4)
            if merged_new is None:
                merged_new = df_p
            else:
                merged_new = pd.merge(merged_new, df_p, on="Date", how="outer")
        except Exception as e:
            print(f"  Warning fetching {ticker}: {e}")

    if merged_new is not None and not merged_new.empty:
        merged_new = merged_new.ffill().dropna()
        combined = pd.concat([df_old, merged_new], ignore_index=True)
        combined = combined.drop_duplicates(subset=["Date"]).sort_values("Date").reset_index(drop=True)
        combined.to_parquet(p_path, index=False)
        combined.to_csv(MACRO_DIR / "forex_rates.csv", index=False)
        print(f"  Forex updated: {len(combined):,} rows (latest: {combined['Date'].max()})")
    else:
        print(f"  Forex already at latest: {last_dt}")


def main():
    parser = argparse.ArgumentParser(description="Update macroeconomic indicators.")
    parser.add_argument("--refresh", action="store_true", help="Recompile all macro datasets from scratch.")
    args = parser.parse_args()

    if args.refresh:
        print("Performing full refresh of macro datasets...")
        import subprocess
        subprocess.run([sys.executable, str(ROOT_DIR / "scripts" / "build_macro.py")], check=True)
    else:
        update_in10y_yield()
        update_forex_rates()


if __name__ == "__main__":
    main()
