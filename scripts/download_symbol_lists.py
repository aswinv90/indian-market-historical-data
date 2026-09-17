"""
download_symbol_lists.py
------------------------
Download the latest NSE and BSE stock symbol lists.

NSE: EQUITY_L.csv from NSE's official FTP/CDN
BSE: Equity list CSV from BSE's official URL

Run this once (or periodically) to refresh the symbol master files.

Usage:
    python scripts/download_symbol_lists.py
"""

import io
import sys
import requests
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import NSE_SYMBOL_FILE, BSE_SYMBOL_FILE, log

# ── NSE ───────────────────────────────────────────────────────────────────────
NSE_URL = (
    "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
)

# ── BSE ───────────────────────────────────────────────────────────────────────
# Zerodha's public instruments API is the most reliable source for BSE scrip codes.
# exchange_token = BSE scrip code (used as <code>.BO in Yahoo Finance)
BSE_URL = "https://api.kite.trade/instruments/BSE"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def download_nse():
    log.info("Downloading NSE symbol list …")
    try:
        r = requests.get(NSE_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
        NSE_SYMBOL_FILE.write_bytes(r.content)
        df = pd.read_csv(NSE_SYMBOL_FILE)
        log.info(f"NSE: {len(df)} symbols saved → {NSE_SYMBOL_FILE}")
    except Exception as e:
        log.error(f"Failed to download NSE list: {e}")
        # Fallback: create a minimal hardcoded list of major NSE stocks
        fallback_nifty50 = [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
            "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
            "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "TITAN",
            "SUNPHARMA", "BAJFINANCE", "ULTRACEMCO", "WIPRO", "ONGC",
            "NTPC", "POWERGRID", "TATAMOTORS", "HCLTECH", "NESTLEIND",
            "TECHM", "DRREDDY", "DIVISLAB", "CIPLA", "GRASIM",
            "ADANIPORTS", "JSWSTEEL", "TATASTEEL", "COALINDIA", "HINDALCO",
            "BPCL", "BRITANNIA", "EICHERMOT", "HEROMOTOCO", "BAJAJ-AUTO",
            "M&M", "APOLLOHOSP", "TATACONSUM", "LTIM", "INDUSINDBK",
            "UPL", "SBILIFE", "HDFCLIFE", "BAJAJFINSV", "ADANIENT",
        ]
        df = pd.DataFrame({"SYMBOL": fallback_nifty50})
        df.to_csv(NSE_SYMBOL_FILE, index=False)
        log.warning(f"Used Nifty-50 fallback list ({len(df)} symbols)")


def download_bse():
    log.info("Downloading BSE symbol list (via Zerodha instruments) …")
    try:
        r = requests.get(BSE_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        # Keep only EQ segment (already all EQ, but filter to be safe)
        df = df[df["instrument_type"] == "EQ"].copy()
        # Rename to our standard column
        df = df.rename(columns={
            "exchange_token": "Security Code",
            "tradingsymbol":  "Tradingsymbol",
            "name":           "Issuer Name",
        })
        df[["Security Code", "Tradingsymbol", "Issuer Name"]].to_csv(
            BSE_SYMBOL_FILE, index=False
        )
        log.info(f"BSE: {len(df)} symbols saved → {BSE_SYMBOL_FILE}")
    except Exception as e:
        log.error(f"Failed to download BSE list: {e}")
        log.warning("BSE list unavailable; BSE fetch will be skipped")


if __name__ == "__main__":
    download_nse()
    download_bse()
    log.info("Symbol lists ready.")
