"""
Shared utilities for fetching and storing Indian stock price data.
"""

import os
import sys
import time
import logging
import subprocess
import pandas as pd
from pathlib import Path
from typing import Optional

def get_engine():
    """Ensure engine is present and return module dynamically."""
    try:
        import yfinance as eng
        return eng
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance>=0.2.40", "-q"])
        import yfinance as eng
        return eng

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
NSE_DIR  = DATA_DIR / "NSE"
BSE_DIR  = DATA_DIR / "BSE"

NSE_SYMBOL_FILE = ROOT_DIR / "stock_list_nse.csv"
BSE_SYMBOL_FILE = ROOT_DIR / "stock_list_bse.csv"
FAILED_LOG      = ROOT_DIR / "failed_tickers.txt"

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Parquet helpers ───────────────────────────────────────────────────────────
def parquet_path(symbol: str, exchange: str) -> Path:
    """Return the Parquet file path for a given symbol."""
    folder = NSE_DIR if exchange == "NSE" else BSE_DIR
    safe   = symbol.replace(".", "_").replace("/", "_")
    return folder / f"{safe}.parquet"


def load_existing(symbol: str, exchange: str) -> Optional[pd.DataFrame]:
    """Load existing Parquet data for a symbol, or return None."""
    path = parquet_path(symbol, exchange)
    if path.exists():
        try:
            return pd.read_parquet(path)
        except Exception as e:
            log.warning(f"Could not read {path}: {e}")
    return None


def clean_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Coerce all columns to numeric, handling cases where upstream returns
    strings with currency suffixes for Dividends.
    """
    numeric_cols = ["Open", "High", "Low", "Close", "Adj Close",
                    "Volume", "Dividends", "Stock Splits", "Capital Gains"]
    for col in numeric_cols:
        if col in df.columns and df[col].dtype == object:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.extract(r"([\d.]+)")[0],
                errors="coerce"
            ).fillna(0.0)
    return df


def save_parquet(df: pd.DataFrame, symbol: str, exchange: str) -> None:
    """Persist a DataFrame to Parquet, replacing any existing file."""
    path = parquet_path(symbol, exchange)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, engine="pyarrow", compression="snappy", index=True)


def merge_and_save(new_df: pd.DataFrame, symbol: str, exchange: str) -> int:
    """
    Merge new_df with existing data (deduplicate by date index).
    Returns the number of new rows added.
    """
    existing = load_existing(symbol, exchange)
    if existing is not None:
        combined = pd.concat([existing, new_df])
        combined = combined[~combined.index.duplicated(keep="last")]
        combined.sort_index(inplace=True)
        new_rows = len(combined) - len(existing)
    else:
        combined = new_df.sort_index()
        new_rows = len(combined)

    save_parquet(combined, symbol, exchange)
    return new_rows


# ── Symbol list helpers ───────────────────────────────────────────────────────
def load_nse_symbols() -> list[str]:
    """Return list of Yahoo Finance tickers for all NSE stocks (symbol.NS)."""
    df = pd.read_csv(NSE_SYMBOL_FILE)
    # NSE EQUITY_L.csv has column 'SYMBOL'
    symbols = df["SYMBOL"].dropna().str.strip().unique().tolist()
    return [f"{s}.NS" for s in symbols]


def load_bse_symbols() -> list[str]:
    """Return list of Yahoo Finance tickers for all BSE stocks (symbol.BO).

    Zerodha's instrument list uses tradingsymbol which Yahoo Finance accepts
    as <tradingsymbol>.BO (e.g. ABB.BO), NOT the numeric scrip code.
    """
    df = pd.read_csv(BSE_SYMBOL_FILE)
    # Use Tradingsymbol column (e.g. 'ABB', 'AEGISLOG') — Yahoo Finance format
    col = "Tradingsymbol" if "Tradingsymbol" in df.columns else "Security Code"
    codes = df[col].dropna().astype(str).str.strip().unique().tolist()
    return [f"{c}.BO" for c in codes]


def log_failure(ticker: str, reason: str) -> None:
    """Append a failed ticker to the failure log."""
    with open(FAILED_LOG, "a") as f:
        f.write(f"{ticker}\t{reason}\n")


def rate_limited_sleep(seconds: float = 0.5) -> None:
    """Polite delay to avoid Yahoo Finance rate limits."""
    time.sleep(seconds)
