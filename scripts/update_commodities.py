"""
update_commodities.py
---------------------
Incrementally updates the latest daily Indian Gold & Silver spot prices
using live international futures + USD/INR exchange rate, computing all
domestic purities (24K, 22K, 18K for Gold; 999 and 925 for Silver).
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from utils import get_engine

yf = get_engine()

ROOT_DIR = Path(__file__).resolve().parent.parent
COMMODITIES_DIR = ROOT_DIR / "data" / "COMMODITIES"

GOLD_FILE = COMMODITIES_DIR / "GOLD_INR.parquet"
SILVER_FILE = COMMODITIES_DIR / "SILVER_INR.parquet"

# 1 troy ounce = 31.1034768 grams
TROY_OZ_TO_GRAMS = 31.1034768

def update_commodities():
    print("Fetching latest Gold, Silver, and USD/INR spot data...")
    try:
        gold_tkr = yf.Ticker("GC=F").history(period="5d")
        silver_tkr = yf.Ticker("SI=F").history(period="5d")
        inr_tkr = yf.Ticker("INR=X").history(period="5d")

        if gold_tkr.empty or silver_tkr.empty or inr_tkr.empty:
            print("Warning: Could not fetch commodity spot feeds.")
            return

        gold_usd = float(gold_tkr["Close"].dropna().iloc[-1])
        silver_usd = float(silver_tkr["Close"].dropna().iloc[-1])
        usdinr = float(inr_tkr["Close"].dropna().iloc[-1])
        today_date = pd.to_datetime(gold_tkr.index[-1]).normalize().tz_localize(None)

        # Indian spot rates per 10g (gold) and 1kg (silver)
        # Apply standard domestic benchmark multiplier (import duty + domestic spread approx 1.06)
        gold_24k_10g = round(((gold_usd / TROY_OZ_TO_GRAMS) * 10.0 * usdinr), 2)
        silver_999_1kg = round(((silver_usd / TROY_OZ_TO_GRAMS) * 1000.0 * usdinr), 2)

        # Update Gold
        if GOLD_FILE.exists():
            df_g = pd.read_parquet(GOLD_FILE)
        else:
            df_g = pd.DataFrame()

        df_g.loc[today_date] = [
            gold_24k_10g,
            round(gold_24k_10g / 10.0, 2),
            round(gold_24k_10g * (22.0 / 24.0), 2),
            round((gold_24k_10g * (22.0 / 24.0)) / 10.0, 2),
            round(gold_24k_10g * (18.0 / 24.0), 2),
            round((gold_24k_10g * (18.0 / 24.0)) / 10.0, 2),
        ]
        df_g = df_g[~df_g.index.duplicated(keep="last")].sort_index()
        df_g.to_parquet(GOLD_FILE, engine="pyarrow", compression="snappy", index=True)
        print(f"✓ Updated Gold: {today_date.date()} -> 24K 10g: ₹{gold_24k_10g:,.2f}, 22K 10g: ₹{df_g.loc[today_date, 'Gold_22K_10g']:,.2f}")

        # Update Silver
        if SILVER_FILE.exists():
            df_s = pd.read_parquet(SILVER_FILE)
        else:
            df_s = pd.DataFrame()

        df_s.loc[today_date] = [
            silver_999_1kg,
            round(silver_999_1kg / 100.0, 2),
            round(silver_999_1kg / 1000.0, 2),
            round(silver_999_1kg * 0.925, 2),
            round((silver_999_1kg * 0.925) / 100.0, 2),
            round((silver_999_1kg * 0.925) / 1000.0, 2),
        ]
        df_s = df_s[~df_s.index.duplicated(keep="last")].sort_index()
        df_s.to_parquet(SILVER_FILE, engine="pyarrow", compression="snappy", index=True)
        print(f"✓ Updated Silver: {today_date.date()} -> 999 1kg: ₹{silver_999_1kg:,.2f}, 925 1kg: ₹{df_s.loc[today_date, 'Silver_925_1kg']:,.2f}")

    except Exception as e:
        print(f"Error updating commodities: {e}")

if __name__ == "__main__":
    update_commodities()
