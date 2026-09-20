"""
fetch_all_mf.py
---------------
Downloads complete historical daily NAV for all Indian Mutual Fund schemes
from inception date using mfapi.in and stores them partitioned into compressed
Parquet files in data/MF/.

Partitioning:
  - data/MF/mf_meta.parquet: Master index of all 37,896 schemes (code, name, fund house, category, isin)
  - data/MF/nav_part_0.parquet ... nav_part_9.parquet: Historical daily NAVs partitioned by schemeCode % 10
"""

import sys
import time
import requests
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

ROOT_DIR = Path(__file__).resolve().parent.parent
MF_DIR = ROOT_DIR / "data" / "MF"
MF_DIR.mkdir(parents=True, exist_ok=True)

META_FILE = MF_DIR / "mf_meta.parquet"
NUM_PARTITIONS = 10
MAX_WORKERS = 15  # Optimal concurrency for mfapi.in

def fetch_scheme(scheme):
    code = scheme["schemeCode"]
    name = scheme.get("schemeName", "")
    url = f"https://api.mfapi.in/mf/{code}"
    
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=12)
            if r.status_code == 200:
                data = r.json()
                meta = data.get("meta", {})
                nav_list = data.get("data", [])
                
                rows = []
                for item in nav_list:
                    rows.append({
                        "date": item["date"],
                        "schemeCode": code,
                        "nav": float(item["nav"]) if item.get("nav") not in (None, "", "N.A.") else None
                    })
                
                meta_row = {
                    "schemeCode": code,
                    "schemeName": meta.get("scheme_name") or name,
                    "fundHouse": meta.get("fund_house", ""),
                    "category": meta.get("scheme_category", ""),
                    "schemeType": meta.get("scheme_type", ""),
                    "isinGrowth": meta.get("isin_growth") or scheme.get("isinGrowth"),
                    "isinDiv": meta.get("isin_div_reinvestment") or scheme.get("isinDivReinvestment"),
                    "records": len(rows),
                    "oldestDate": nav_list[-1]["date"] if nav_list else "",
                    "latestDate": nav_list[0]["date"] if nav_list else ""
                }
                return code, rows, meta_row
        except Exception:
            time.sleep(0.5 * (attempt + 1))
            
    return code, [], {"schemeCode": code, "schemeName": name, "records": 0}

def main():
    print("=== Indian Mutual Funds Historical Inception Bootstrap ===")
    print("1. Fetching master scheme directory from mfapi.in...")
    r = requests.get("https://api.mfapi.in/mf", timeout=20)
    schemes = r.json()
    total = len(schemes)
    print(f"Total schemes found: {total:,}")

    # Buckets for partitions: 0 to 9 based on schemeCode % 10
    buckets = {i: [] for i in range(NUM_PARTITIONS)}
    meta_list = []
    
    print(f"2. Fetching historical NAV from inception for all schemes ({MAX_WORKERS} threads)...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_scheme, s): s for s in schemes}
        
        with tqdm(total=total, desc="Downloading Mutual Funds", unit="fund") as pbar:
            for fut in as_completed(futures):
                code, rows, meta_row = fut.result()
                meta_list.append(meta_row)
                if rows:
                    part_idx = code % NUM_PARTITIONS
                    buckets[part_idx].extend(rows)
                pbar.update(1)

    print("\n3. Writing partitioned Parquet files...")
    # Save meta
    df_meta = pd.DataFrame(meta_list).set_index("schemeCode").sort_index()
    df_meta.to_parquet(META_FILE, engine="pyarrow", compression="snappy", index=True)
    print(f"✓ Saved master scheme index: {META_FILE} ({len(df_meta):,} schemes)")

    # Save NAV partitions
    total_nav_records = 0
    for part_idx in range(NUM_PARTITIONS):
        part_file = MF_DIR / f"nav_part_{part_idx}.parquet"
        rows = buckets[part_idx]
        total_nav_records += len(rows)
        if rows:
            df_part = pd.DataFrame(rows)
            df_part["date"] = pd.to_datetime(df_part["date"], format="%d-%m-%Y")
            df_part["nav"] = pd.to_numeric(df_part["nav"], errors="coerce")
            df_part.sort_values(by=["schemeCode", "date"], inplace=True)
            df_part.to_parquet(part_file, engine="pyarrow", compression="snappy", index=False)
            size_mb = part_file.stat().st_size / (1024 * 1024)
            print(f"  ✓ Partition {part_idx}: {part_file.name} ({len(df_part):,} records, {size_mb:.1f} MB)")
        else:
            print(f"  Warning: Partition {part_idx} is empty")

    print("\n=== Bootstrap Complete! ===")
    print(f"Total Mutual Fund Schemes Processed: {total:,}")
    print(f"Total Daily NAV Records from Inception: {total_nav_records:,}")
    total_mb = sum(f.stat().st_size for f in MF_DIR.glob("*.parquet")) / (1024 * 1024)
    print(f"Total Disk Usage in data/MF/: {total_mb:.1f} MB")

if __name__ == "__main__":
    main()
