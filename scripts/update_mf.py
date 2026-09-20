"""
update_mf.py
------------
Daily incremental updater for Indian Mutual Fund NAVs.
Fetches latest NAVs and updates the partitioned Parquet files in data/MF/.
"""

import sys
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
MF_DIR = ROOT_DIR / "data" / "MF"
META_FILE = MF_DIR / "mf_meta.parquet"
NUM_PARTITIONS = 10

def update_mutual_funds():
    print("Fetching master scheme list to check for daily NAV updates...")
    try:
        r = requests.get("https://api.mfapi.in/mf", timeout=20)
        schemes = r.json()
        print(f"Master scheme catalog: {len(schemes):,} schemes")
    except Exception as e:
        print(f"Error connecting to MF catalog: {e}")
        return

    # In daily updates, AMFI publishes NAVAll.txt which provides all latest daily NAVs in 1 request
    # This avoids hitting 37,000 endpoints individually!
    amfi_url = "https://www.amfiindia.com/spages/NAVAll.txt"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        print("Fetching daily consolidated NAV feed from AMFI...")
        resp = requests.get(amfi_url, headers=headers, timeout=25)
        lines = resp.text.strip().splitlines()
        
        daily_records = []
        # Format: Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date
        for line in lines:
            parts = line.split(";")
            if len(parts) >= 6:
                try:
                    code = int(parts[0].strip())
                    nav_str = parts[4].strip()
                    date_str = parts[5].strip()
                    nav_val = float(nav_str)
                    d = datetime.strptime(date_str, "%d-%b-%Y")
                    daily_records.append({
                        "date": d,
                        "schemeCode": code,
                        "nav": nav_val
                    })
                except (ValueError, IndexError):
                    continue

        print(f"Parsed {len(daily_records):,} daily NAV updates from AMFI feed.")
        if not daily_records:
            print("No new records found.")
            return

        df_daily = pd.DataFrame(daily_records)
        
        # Partition updates into 10 buckets
        for part_idx in range(NUM_PARTITIONS):
            part_file = MF_DIR / f"nav_part_{part_idx}.parquet"
            if part_file.exists():
                df_part = pd.read_parquet(part_file)
            else:
                df_part = pd.DataFrame()

            subset = df_daily[df_daily["schemeCode"] % NUM_PARTITIONS == part_idx]
            if not subset.empty:
                combined = pd.concat([df_part, subset], ignore_index=True)
                combined.drop_duplicates(subset=["schemeCode", "date"], keep="last", inplace=True)
                combined.sort_values(by=["schemeCode", "date"], inplace=True)
                combined.to_parquet(part_file, engine="pyarrow", compression="snappy", index=False)
                print(f"  ✓ Updated partition {part_idx} (+{len(subset):,} updates)")

        print("✓ Mutual fund daily update complete!")
    except Exception as e:
        print(f"Error during MF daily update: {e}")

if __name__ == "__main__":
    update_mutual_funds()
