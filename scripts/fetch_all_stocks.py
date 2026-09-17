"""
fetch_all_stocks.py
-------------------
One-time bootstrap: fetch full historical OHLCV + Adj Close + Dividends +
Stock Splits data (from day of listing) for ALL NSE and BSE stocks.

Run this ONCE to seed the repository. After that, use update_stocks.py for
daily incremental updates.

Usage:
    python scripts/fetch_all_stocks.py              # Both NSE + BSE
    python scripts/fetch_all_stocks.py --nse-only
    python scripts/fetch_all_stocks.py --bse-only
    python scripts/fetch_all_stocks.py --limit 50   # Test with first 50 tickers
"""

import argparse
import sys
import time

import yfinance as yf
from tqdm import tqdm

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from utils import (
    load_nse_symbols,
    load_bse_symbols,
    merge_and_save,
    clean_numeric_columns,
    log_failure,
    log,
    rate_limited_sleep,
    FAILED_LOG,
)

# ── Constants ─────────────────────────────────────────────────────────────────
BATCH_SIZE   = 10   # download N tickers at once (yfinance group download)
RETRY_LIMIT  = 3
SLEEP_BATCH  = 2.0  # seconds between batches


def fetch_ticker_max(ticker: str, exchange: str, retries: int = RETRY_LIMIT) -> bool:
    """
    Fetch full history (period='max') for a single ticker and save to Parquet.
    Returns True on success, False on failure.
    """
    for attempt in range(1, retries + 1):
        try:
            tkr  = yf.Ticker(ticker)
            hist = tkr.history(period="max", auto_adjust=False, actions=True)

            if hist.empty:
                log.warning(f"[SKIP] {ticker}: no data returned")
                log_failure(ticker, "empty_data")
                return False

            # Normalize index to date only (drop time/tz)
            hist.index = hist.index.normalize().tz_localize(None)
            hist.index.name = "Date"

            # Keep only desired columns (some may be absent)
            keep = ["Open", "High", "Low", "Close", "Adj Close", "Volume",
                    "Dividends", "Stock Splits", "Capital Gains"]
            hist = hist[[c for c in keep if c in hist.columns]]

            # Coerce any string-valued numeric columns (e.g. '0.23 INR')
            hist = clean_numeric_columns(hist)

            rows = merge_and_save(hist, ticker, exchange)
            log.info(f"[OK] {ticker}: {rows} rows saved")
            return True

        except Exception as e:
            log.warning(f"[RETRY {attempt}/{retries}] {ticker}: {e}")
            time.sleep(2 ** attempt)

    log_failure(ticker, "max_retries_exceeded")
    return False


def run(tickers: list[str], exchange: str) -> None:
    ok = fail = 0
    for ticker in tqdm(tickers, desc=f"{exchange}", unit="stock"):
        success = fetch_ticker_max(ticker, exchange)
        if success:
            ok += 1
        else:
            fail += 1
        rate_limited_sleep(0.4)

    log.info(f"\n{exchange} done — ✓ {ok} succeeded, ✗ {fail} failed")
    if fail:
        log.info(f"Failed tickers logged to: {FAILED_LOG}")


def main():
    parser = argparse.ArgumentParser(description="Bootstrap full stock history")
    parser.add_argument("--nse-only", action="store_true")
    parser.add_argument("--bse-only", action="store_true")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit to first N tickers (for testing)")
    args = parser.parse_args()

    if not args.bse_only:
        nse_tickers = load_nse_symbols()
        if args.limit:
            nse_tickers = nse_tickers[: args.limit]
        log.info(f"Fetching {len(nse_tickers)} NSE tickers …")
        run(nse_tickers, "NSE")

    if not args.nse_only:
        bse_tickers = load_bse_symbols()
        if args.limit:
            bse_tickers = bse_tickers[: args.limit]
        log.info(f"Fetching {len(bse_tickers)} BSE tickers …")
        run(bse_tickers, "BSE")


if __name__ == "__main__":
    main()
