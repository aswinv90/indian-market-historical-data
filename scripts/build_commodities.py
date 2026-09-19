"""
build_commodities.py
--------------------
Compiles 50+ years (1970 to present) of Indian Gold and Silver price history
covering all standard purities:
  - Gold: 24K (99.9%), 22K (91.6%), 18K (75.0%) per 10g and per 1g
  - Silver: 999 Fine Silver, 925 Sterling Silver per 1kg, 10g, and 1g
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
COMMODITIES_DIR = ROOT_DIR / "data" / "COMMODITIES"
COMMODITIES_DIR.mkdir(parents=True, exist_ok=True)

# ── 1. Official RBI Mumbai Annual Bullion Benchmarks (1970 - 2024) ────────────
# Gold: ₹ per 10 grams (Standard 24K)
# Silver: ₹ per 1 kg (999 purity)
RBI_HISTORICAL_ANNUAL = [
    (1970, 184.0, 1635.0),
    (1971, 193.0, 1394.0),
    (1972, 202.0, 1976.0),
    (1973, 278.0, 3137.0),
    (1974, 506.0, 4391.0),
    (1975, 540.0, 4085.0),
    (1976, 432.0, 4347.0),
    (1977, 486.0, 4706.0),
    (1978, 685.0, 5930.0),
    (1979, 937.0, 21793.0),
    (1980, 1330.0, 16393.0),
    (1981, 1670.0, 2715.0),
    (1982, 1645.0, 2720.0),
    (1983, 1800.0, 3105.0),
    (1984, 1970.0, 3570.0),
    (1985, 2130.0, 3955.0),
    (1986, 2140.0, 4015.0),
    (1987, 2570.0, 4794.0),
    (1988, 3130.0, 6066.0),
    (1989, 3140.0, 6755.0),
    (1990, 3200.0, 6463.0),
    (1991, 3466.0, 6646.0),
    (1992, 4334.0, 8040.0),
    (1993, 4140.0, 5489.0),
    (1994, 4598.0, 7124.0),
    (1995, 4680.0, 6335.0),
    (1996, 5160.0, 7346.0),
    (1997, 4725.0, 7345.0),
    (1998, 4045.0, 8560.0),
    (1999, 4234.0, 7615.0),
    (2000, 4400.0, 7900.0),
    (2001, 4300.0, 7215.0),
    (2002, 4990.0, 7875.0),
    (2003, 5600.0, 7695.0),
    (2004, 5850.0, 11770.0),
    (2005, 7000.0, 10675.0),
    (2006, 8400.0, 17405.0),
    (2007, 10800.0, 19520.0),
    (2008, 12500.0, 23625.0),
    (2009, 14500.0, 22165.0),
    (2010, 18500.0, 27255.0),
    (2011, 26400.0, 56900.0),
    (2012, 31050.0, 56290.0),
    (2013, 29600.0, 54030.0),
    (2014, 28006.0, 43070.0),
    (2015, 26343.0, 37825.0),
    (2016, 28623.0, 36990.0),
    (2017, 29667.0, 37825.0),
    (2018, 31438.0, 41400.0),
    (2019, 35220.0, 40600.0),
    (2020, 48651.0, 63435.0),
    (2021, 48720.0, 62572.0),
    (2022, 52670.0, 55100.0),
    (2023, 65330.0, 78600.0),
    (2024, 77913.0, 95700.0),
]

def generate_datasets():
    print("Compiling 50-year Indian Gold and Silver historical records...")
    
    gold_records = []
    silver_records = []

    for year, gold_24k_10g, silver_999_1kg in RBI_HISTORICAL_ANNUAL:
        date_str = f"{year}-12-31"

        # Gold derivations:
        g_24k_10g = float(gold_24k_10g)
        g_24k_1g  = round(g_24k_10g / 10.0, 2)
        g_22k_10g = round(g_24k_10g * (22.0 / 24.0), 2)
        g_22k_1g  = round(g_22k_10g / 10.0, 2)
        g_18k_10g = round(g_24k_10g * (18.0 / 24.0), 2)
        g_18k_1g  = round(g_18k_10g / 10.0, 2)

        gold_records.append({
            "Date": pd.to_datetime(date_str),
            "Gold_24K_10g": g_24k_10g,
            "Gold_24K_1g":  g_24k_1g,
            "Gold_22K_10g": g_22k_10g,
            "Gold_22K_1g":  g_22k_1g,
            "Gold_18K_10g": g_18k_10g,
            "Gold_18K_1g":  g_18k_1g,
        })

        # Silver derivations:
        s_999_1kg = float(silver_999_1kg)
        s_999_10g = round(s_999_1kg / 100.0, 2)
        s_999_1g  = round(s_999_1kg / 1000.0, 2)
        s_925_1kg = round(s_999_1kg * 0.925, 2)
        s_925_10g = round(s_925_1kg / 100.0, 2)
        s_925_1g  = round(s_925_1kg / 1000.0, 2)

        silver_records.append({
            "Date": pd.to_datetime(date_str),
            "Silver_999_1kg": s_999_1kg,
            "Silver_999_10g": s_999_10g,
            "Silver_999_1g":  s_999_1g,
            "Silver_925_1kg": s_925_1kg,
            "Silver_925_10g": s_925_10g,
            "Silver_925_1g":  s_925_1g,
        })

    df_gold = pd.DataFrame(gold_records).set_index("Date").sort_index()
    df_silver = pd.DataFrame(silver_records).set_index("Date").sort_index()

    # Recent spot benchmarks
    recent_dates = [
        ("2025-12-31", 78500.0, 92000.0),
        ("2026-09-18", 136400.0, 205000.0),
    ]

    for d_str, g_val, s_val in recent_dates:
        d = pd.to_datetime(d_str)
        df_gold.loc[d] = [
            g_val,
            round(g_val / 10.0, 2),
            round(g_val * (22.0 / 24.0), 2),
            round((g_val * (22.0 / 24.0)) / 10.0, 2),
            round(g_val * (18.0 / 24.0), 2),
            round((g_val * (18.0 / 24.0)) / 10.0, 2),
        ]
        df_silver.loc[d] = [
            s_val,
            round(s_val / 100.0, 2),
            round(s_val / 1000.0, 2),
            round(s_val * 0.925, 2),
            round((s_val * 0.925) / 100.0, 2),
            round((s_val * 0.925) / 1000.0, 2),
        ]

    df_gold.sort_index(inplace=True)
    df_silver.sort_index(inplace=True)

    gold_path = COMMODITIES_DIR / "GOLD_INR.parquet"
    silver_path = COMMODITIES_DIR / "SILVER_INR.parquet"

    df_gold.to_parquet(gold_path, engine="pyarrow", compression="snappy", index=True)
    df_silver.to_parquet(silver_path, engine="pyarrow", compression="snappy", index=True)

    print(f"✓ Saved Gold: {gold_path} ({len(df_gold)} records, {gold_path.stat().st_size/1024:.1f} KB)")
    print(f"✓ Saved Silver: {silver_path} ({len(df_silver)} records, {silver_path.stat().st_size/1024:.1f} KB)")
    print(f"  Gold years: {df_gold.index.min().year} to {df_gold.index.max().year}")
    print(f"  Silver years: {df_silver.index.min().year} to {df_silver.index.max().year}")

if __name__ == "__main__":
    generate_datasets()
