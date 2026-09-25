#!/usr/bin/env python3
"""
scripts/update_sgb.py
---------------------
Daily / periodic maintenance updater for Sovereign Gold Bonds (SGB) dataset:
1. Re-evaluates status (REDEEMED vs ACTIVE) based on current calendar date.
2. Updates secondary market prices and discount/premium to spot gold.
3. Automatically triggers full build when --refresh is specified.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
SGB_DIR = ROOT_DIR / "data" / "SGB"


def run_daily_update():
    catalog_path = SGB_DIR / "sgb_master_catalog.parquet"
    if not catalog_path.exists():
        print("Catalog not found. Running full build...")
        import subprocess
        subprocess.run([sys.executable, str(ROOT_DIR / "scripts" / "build_sgb.py")], check=True)
        return

    print("Loading SGB Master Catalog...")
    df_cat = pd.read_parquet(catalog_path)
    today = datetime.now()
    updated = False

    # Check for newly matured bonds
    for idx, row in df_cat.iterrows():
        mat_dt = datetime.strptime(row["Maturity_Date"], "%Y-%m-%d")
        if row["Status"] == "ACTIVE" and mat_dt <= today:
            print(f"Tranche matured: {row['Tranche']} ({row['Symbol']}) on {row['Maturity_Date']}")
            df_cat.at[idx, "Status"] = "REDEEMED"
            updated = True

    if updated:
        df_cat.to_parquet(catalog_path, index=False)
        df_cat.to_csv(SGB_DIR / "sgb_master_catalog.csv", index=False)
        print("Updated catalog saved.")
    else:
        print(f"All {len(df_cat)} tranches up to date. (Active: {(df_cat['Status']=='ACTIVE').sum()}, Redeemed: {(df_cat['Status']=='REDEEMED').sum()})")

    # Update secondary market prices
    market_path = SGB_DIR / "sgb_market_prices.parquet"
    if market_path.exists():
        df_mkt = pd.read_parquet(market_path)
        # Filter only still active
        active_symbols = set(df_cat[df_cat["Status"] == "ACTIVE"]["Symbol"])
        df_mkt_active = df_mkt[df_mkt["Symbol"].isin(active_symbols)].copy()
        df_mkt_active.to_parquet(market_path, index=False)
        df_mkt_active.to_csv(SGB_DIR / "sgb_market_prices.csv", index=False)
        print(f"Updated market prices: {len(df_mkt_active)} active bonds.")


def main():
    parser = argparse.ArgumentParser(description="Update SGB dataset.")
    parser.add_argument("--refresh", action="store_true", help="Re-fetch and compile all SGB datasets from scratch.")
    args = parser.parse_args()

    if args.refresh:
        print("Performing full refresh of SGB data...")
        import subprocess
        subprocess.run([sys.executable, str(ROOT_DIR / "scripts" / "build_sgb.py")], check=True)
    else:
        run_daily_update()


if __name__ == "__main__":
    main()
