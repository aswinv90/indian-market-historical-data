#!/usr/bin/env python3
"""
scripts/fetch_all_flows.py
Bootstrap script to fetch, build, and save full institutional capital flows (FII / DII):
1. fii_dii_cash.parquet & .csv: Daily Cash Market net flows (₹ Crores) for FII & DII.
2. fii_derivatives.parquet & .csv: Daily participant Open Interest (NSE NSCCL) + FII Long Ratio.
3. fpi_monthly_history.parquet & .csv: 21+ Years (2005-2026) NSDL monthly equity/debt flows.
"""

import os
import io
import json
import time
import urllib.request
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "FLOWS")
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
ARCHIVE_HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def parse_raw_date(date_str):
    """Normalize various date formats into YYYY-MM-DD."""
    if not date_str:
        return None
    date_str = str(date_str).strip()
    # Try YYYY-MM-DD
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        pass
    # Try DD-Mon-YYYY (e.g. 23-Sep-2026 or 23-Sept-2026)
    date_clean = date_str.replace("Sept", "Sep")
    for fmt in ["%d-%b-%Y", "%d-%B-%Y", "%d/%m/%Y", "%Y/%m/%d"]:
        try:
            return datetime.strptime(date_clean, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def fetch_nse_live_cash():
    """Fetch latest official FII/DII cash trade data from NSE API."""
    url = "https://www.nseindia.com/api/fiidiiTradeReact"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if not isinstance(data, list) or len(data) < 2:
                return []
            records = {}
            for item in data:
                cat = item.get("category", "")
                dt_str = parse_raw_date(item.get("date", ""))
                if not dt_str:
                    continue
                if dt_str not in records:
                    records[dt_str] = {"Date": dt_str}
                if "DII" in cat:
                    records[dt_str]["DII_Buy_Cr"] = float(item.get("buyValue", 0))
                    records[dt_str]["DII_Sell_Cr"] = float(item.get("sellValue", 0))
                    records[dt_str]["DII_Net_Cr"] = float(item.get("netValue", 0))
                elif "FII" in cat or "FPI" in cat:
                    records[dt_str]["FII_Buy_Cr"] = float(item.get("buyValue", 0))
                    records[dt_str]["FII_Sell_Cr"] = float(item.get("sellValue", 0))
                    records[dt_str]["FII_Net_Cr"] = float(item.get("netValue", 0))

            res = []
            for dt, row in records.items():
                if "FII_Net_Cr" in row and "DII_Net_Cr" in row:
                    row["Total_Net_Cr"] = round(row["FII_Net_Cr"] + row["DII_Net_Cr"], 2)
                    res.append(row)
            return res
    except Exception as e:
        print(f"[WARN] Failed fetching live NSE fiidiiTradeReact: {e}")
        return []


def fetch_groww_cash():
    """Fetch recent cash data from Groww SSR __NEXT_DATA__."""
    url = "https://groww.in/fii-dii-data"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            start = html.find('<script id="__NEXT_DATA__"')
            if start == -1:
                return []
            end = html.find("</script>", start)
            data = json.loads(html[html.find(">", start) + 1 : end])
            items = data.get("props", {}).get("pageProps", {}).get("initialData", [])
            records = []
            for it in items:
                dt_str = parse_raw_date(it.get("date"))
                fii = it.get("fii", {})
                dii = it.get("dii", {})
                if not dt_str or not fii or not dii:
                    continue
                fii_buy = float(fii.get("grossBuy", 0))
                fii_sell = float(fii.get("grossSell", 0))
                fii_net = float(fii.get("netBuySell", 0))
                dii_buy = float(dii.get("grossBuy", 0))
                dii_sell = float(dii.get("grossSell", 0))
                dii_net = float(dii.get("netBuySell", 0))
                records.append({
                    "Date": dt_str,
                    "FII_Buy_Cr": fii_buy,
                    "FII_Sell_Cr": fii_sell,
                    "FII_Net_Cr": fii_net,
                    "DII_Buy_Cr": dii_buy,
                    "DII_Sell_Cr": dii_sell,
                    "DII_Net_Cr": dii_net,
                    "Total_Net_Cr": round(fii_net + dii_net, 2)
                })
            return records
    except Exception as e:
        print(f"[WARN] Failed fetching Groww cash: {e}")
        return []


def fetch_mrchartist_cash():
    """Fetch verified cash data archive from MrChartist repository."""
    url = "https://raw.githubusercontent.com/MrChartist/fii-dii-data/main/data/history.json"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            items = json.loads(resp.read().decode("utf-8"))
            records = []
            for it in items:
                dt_str = parse_raw_date(it.get("date"))
                fii_buy = float(it.get("fii_buy", 0))
                fii_sell = float(it.get("fii_sell", 0))
                fii_net = float(it.get("fii_net", 0))
                dii_buy = float(it.get("dii_buy", 0))
                dii_sell = float(it.get("dii_sell", 0))
                dii_net = float(it.get("dii_net", 0))
                if not dt_str or (fii_buy == 0 and fii_sell == 0 and dii_buy == 0):
                    continue
                records.append({
                    "Date": dt_str,
                    "FII_Buy_Cr": fii_buy,
                    "FII_Sell_Cr": fii_sell,
                    "FII_Net_Cr": fii_net,
                    "DII_Buy_Cr": dii_buy,
                    "DII_Sell_Cr": dii_sell,
                    "DII_Net_Cr": dii_net,
                    "Total_Net_Cr": round(fii_net + dii_net, 2)
                })
            return records
    except Exception as e:
        print(f"[WARN] Failed fetching MrChartist cash: {e}")
        return []


def build_cash_dataset():
    """Merge and build daily cash flows dataset."""
    print("Building FII/DII Cash Market dataset...")
    all_records = {}

    # 1. MrChartist baseline
    for r in fetch_mrchartist_cash():
        all_records[r["Date"]] = r

    # 2. Groww
    for r in fetch_groww_cash():
        all_records[r["Date"]] = r

    # 3. NSE live (authoritative)
    for r in fetch_nse_live_cash():
        all_records[r["Date"]] = r

    df = pd.DataFrame(list(all_records.values()))
    if df.empty:
        print("[ERROR] No cash records found!")
        return

    df = df.sort_values("Date").reset_index(drop=True)
    cols = ["Date", "FII_Buy_Cr", "FII_Sell_Cr", "FII_Net_Cr", "DII_Buy_Cr", "DII_Sell_Cr", "DII_Net_Cr", "Total_Net_Cr"]
    df = df[cols]

    parquet_path = os.path.join(DATA_DIR, "fii_dii_cash.parquet")
    csv_path = os.path.join(DATA_DIR, "fii_dii_cash.csv")

    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)
    print(f"✅ Saved Cash flows: {len(df)} days ({df['Date'].iloc[0]} -> {df['Date'].iloc[-1]})")
    print(f"   -> {parquet_path}")
    print(f"   -> {csv_path}")


def fetch_participant_oi_day(date_obj):
    """Fetch participant OI CSV for a single date from NSE archive."""
    d_str = date_obj.strftime("%d%m%Y")
    iso_date = date_obj.strftime("%Y-%m-%d")
    urls = [
        f"https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_{d_str}.csv",
        f"https://archives.nseindia.com/content/nsccl/fao_participant_oi_{d_str}.csv",
        f"https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_{d_str}_b.csv",
    ]
    for url in urls:
        try:
            req = urllib.request.Request(url, headers=ARCHIVE_HEADERS)
            with urllib.request.urlopen(req, timeout=6) as resp:
                lines = resp.read().decode("utf-8", errors="ignore").splitlines()
                hdr_idx = None
                for idx, line in enumerate(lines):
                    if "Client Type" in line:
                        hdr_idx = idx
                        break
                if hdr_idx is None:
                    continue
                csv_data = "\n".join(lines[hdr_idx:])
                df = pd.read_csv(io.StringIO(csv_data))
                df.columns = [c.strip() for c in df.columns]

                row = {"Date": iso_date}
                for ctype in ["Client", "DII", "FII", "Pro"]:
                    sub = df[df["Client Type"].astype(str).str.strip() == ctype]
                    if not sub.empty:
                        f_idx_long = int(sub["Future Index Long"].values[0])
                        f_idx_short = int(sub["Future Index Short"].values[0])
                        f_stk_long = int(sub["Future Stock Long"].values[0])
                        f_stk_short = int(sub["Future Stock Short"].values[0])
                        row[f"{ctype}_Index_Futures_Long"] = f_idx_long
                        row[f"{ctype}_Index_Futures_Short"] = f_idx_short
                        row[f"{ctype}_Index_Futures_Net"] = f_idx_long - f_idx_short
                        row[f"{ctype}_Stock_Futures_Long"] = f_stk_long
                        row[f"{ctype}_Stock_Futures_Short"] = f_stk_short
                        row[f"{ctype}_Stock_Futures_Net"] = f_stk_long - f_stk_short

                        if "Option Index Call Long" in sub.columns:
                            row[f"{ctype}_Index_Call_Long"] = int(sub["Option Index Call Long"].values[0])
                            row[f"{ctype}_Index_Call_Short"] = int(sub["Option Index Call Short"].values[0])
                            row[f"{ctype}_Index_Put_Long"] = int(sub["Option Index Put Long"].values[0])
                            row[f"{ctype}_Index_Put_Short"] = int(sub["Option Index Put Short"].values[0])

                tot = df[df["Client Type"].astype(str).str.strip() == "TOTAL"]
                if not tot.empty:
                    row["Total_Index_Futures_OI"] = int(tot["Future Index Long"].values[0])

                fii_l = row.get("FII_Index_Futures_Long", 0)
                fii_s = row.get("FII_Index_Futures_Short", 0)
                tot_fii = fii_l + fii_s
                row["FII_Long_Ratio_Pct"] = round((fii_l / tot_fii * 100), 2) if tot_fii > 0 else 0.0

                return row
        except Exception:
            continue
    return None


def build_derivatives_dataset(start_year=2024):
    """Build multi-year daily participant derivatives dataset from NSE archives."""
    print(f"Building Derivatives Open Interest & Sentiment dataset ({start_year} -> Present)...")
    start_date = datetime(start_year, 1, 1)
    end_date = datetime.now()
    delta = end_date - start_date

    dates = [start_date + timedelta(days=i) for i in range(delta.days + 1)]
    # Skip weekends
    trading_dates = [d for d in dates if d.weekday() < 5]

    print(f"Fetching {len(trading_dates)} potential trading days from NSE archives...")
    records = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_date = {executor.submit(fetch_participant_oi_day, d): d for d in trading_dates}
        for future in as_completed(future_to_date):
            res = future.result()
            if res:
                records.append(res)

    t1 = time.time()
    print(f"Fetched {len(records)} trading days in {t1-t0:.2f}s")

    if not records:
        print("[ERROR] No derivatives records fetched!")
        return

    df = pd.DataFrame(records).sort_values("Date").reset_index(drop=True)
    parquet_path = os.path.join(DATA_DIR, "fii_derivatives.parquet")
    csv_path = os.path.join(DATA_DIR, "fii_derivatives.csv")

    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)
    print(f"✅ Saved Derivatives OI: {len(df)} days ({df['Date'].iloc[0]} -> {df['Date'].iloc[-1]})")
    print(f"   -> {parquet_path}")
    print(f"   -> {csv_path}")


def build_nsdl_monthly_dataset():
    """Build 2005-2026 NSDL monthly institutional flow history."""
    print("Building 21+ Years NSDL Monthly Macro dataset (2005 -> 2026)...")
    url = "https://raw.githubusercontent.com/MrChartist/fii-dii-data/main/data/fpi_yearly_monthly.json"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        rows = []
        for year, ydata in data.get("years", {}).items():
            for m in ydata.get("months", []):
                rows.append({
                    "Year": int(year),
                    "Month": m.get("month"),
                    "Equity_Net_Cr": float(m.get("equity", 0)),
                    "Debt_Net_Cr": float(m.get("debt_general", 0) if "debt_general" in m else m.get("debt", 0)),
                    "Total_Net_Cr": float(m.get("total", 0)),
                    "Source": "NSDL"
                })

        df = pd.DataFrame(rows)
        parquet_path = os.path.join(DATA_DIR, "fpi_monthly_history.parquet")
        csv_path = os.path.join(DATA_DIR, "fpi_monthly_history.csv")

        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)
        print(f"✅ Saved NSDL Monthly: {len(df)} months ({df['Year'].min()} -> {df['Year'].max()})")
        print(f"   -> {parquet_path}")
        print(f"   -> {csv_path}")
    except Exception as e:
        print(f"[ERROR] Failed building NSDL monthly dataset: {e}")


def main():
    print("=" * 60)
    print("PHASE 3 BOOTSTRAP: INSTITUTIONAL CAPITAL FLOWS (FII / DII)")
    print("=" * 60)
    build_cash_dataset()
    print("-" * 60)
    build_derivatives_dataset(start_year=2024)
    print("-" * 60)
    build_nsdl_monthly_dataset()
    print("=" * 60)
    print("Phase 3 bootstrap complete!")


if __name__ == "__main__":
    main()
