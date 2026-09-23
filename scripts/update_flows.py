#!/usr/bin/env python3
"""
scripts/update_flows.py
Daily incremental updater for Institutional Capital Flows (FII / DII):
1. Cash Market net flows (₹ Crores) from official NSE clearing API (fallback Groww).
2. Derivatives Open Interest & Sentiment (FII Long Ratio %) from NSE NSCCL archives.
"""

import os
import io
import sys
import json
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
FLOWS_DIR = ROOT_DIR / "data" / "FLOWS"
FLOWS_DIR.mkdir(parents=True, exist_ok=True)

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
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        pass
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
    """Fallback fetch from Groww SSR data."""
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


def update_cash_flows():
    """Update daily cash market dataset."""
    parquet_path = FLOWS_DIR / "fii_dii_cash.parquet"
    csv_path = FLOWS_DIR / "fii_dii_cash.csv"

    if parquet_path.exists():
        existing_df = pd.read_parquet(parquet_path)
    else:
        existing_df = pd.DataFrame()

    new_rows = fetch_nse_live_cash()
    if not new_rows:
        new_rows = fetch_groww_cash()

    if not new_rows:
        print("[INFO] No new cash flow data received today.")
        return 0

    new_df = pd.DataFrame(new_rows)
    combined = pd.concat([existing_df, new_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=["Date"], keep="last").sort_values("Date").reset_index(drop=True)

    cols = ["Date", "FII_Buy_Cr", "FII_Sell_Cr", "FII_Net_Cr", "DII_Buy_Cr", "DII_Sell_Cr", "DII_Net_Cr", "Total_Net_Cr"]
    combined = combined[[c for c in cols if c in combined.columns]]

    combined.to_parquet(parquet_path, index=False)
    combined.to_csv(csv_path, index=False)

    latest = combined.iloc[-1]
    print(f"✅ Cash Flows updated: Latest {latest['Date']} | FII Net: ₹{latest['FII_Net_Cr']:,.2f} Cr | DII Net: ₹{latest['DII_Net_Cr']:,.2f} Cr | Total: ₹{latest['Total_Net_Cr']:,.2f} Cr")
    return len(new_rows)


def fetch_participant_oi_day(date_obj):
    """Fetch participant OI CSV for a single date from NSE archives."""
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
            with urllib.request.urlopen(req, timeout=8) as resp:
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


def update_derivatives_oi():
    """Update derivatives open interest and FII sentiment metrics."""
    parquet_path = FLOWS_DIR / "fii_derivatives.parquet"
    csv_path = FLOWS_DIR / "fii_derivatives.csv"

    if parquet_path.exists():
        existing_df = pd.read_parquet(parquet_path)
    else:
        existing_df = pd.DataFrame()

    # Check today and the past 3 days in case any were missed
    recent_dates = [datetime.now() - timedelta(days=i) for i in range(4)]
    trading_dates = [d for d in recent_dates if d.weekday() < 5]

    fetched_rows = []
    for d in trading_dates:
        row = fetch_participant_oi_day(d)
        if row:
            fetched_rows.append(row)

    if not fetched_rows:
        print("[INFO] No new derivatives OI records found for recent trading days.")
        return 0

    new_df = pd.DataFrame(fetched_rows)
    combined = pd.concat([existing_df, new_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=["Date"], keep="last").sort_values("Date").reset_index(drop=True)

    combined.to_parquet(parquet_path, index=False)
    combined.to_csv(csv_path, index=False)

    latest = combined.iloc[-1]
    print(f"✅ Derivatives OI updated: Latest {latest['Date']} | FII Index Long: {latest.get('FII_Index_Futures_Long', 0):,} | Short: {latest.get('FII_Index_Futures_Short', 0):,} | Net: {latest.get('FII_Index_Futures_Net', 0):,} | Long Ratio: {latest.get('FII_Long_Ratio_Pct', 0)}%")
    return len(fetched_rows)


def main():
    print("=" * 60)
    print("DAILY UPDATE: INSTITUTIONAL CAPITAL FLOWS (FII / DII)")
    print("=" * 60)
    update_cash_flows()
    print("-" * 60)
    update_derivatives_oi()
    print("=" * 60)
    print("Flows update complete!")


if __name__ == "__main__":
    main()
