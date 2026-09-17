"""
update_stocks.py
----------------
Daily incremental update: fetch the last 5 trading days for every ticker and
merge into existing Parquet files. Run by GitHub Actions every day.

Usage:
    python scripts/update_stocks.py
"""

import sys
import time

import yfinance as yf
from tqdm import tqdm

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from utils import (
    load_nse_symbols,
    load_bse_symbols,
    merge_and_save,
    load_existing,
    clean_numeric_columns,
    log_failure,
    log,
    rate_limited_sleep,
    parquet_path,
)

RETRY_LIMIT = 3


def update_ticker(ticker: str, exchange: str, retries: int = RETRY_LIMIT) -> int:
    """
    Fetch last 5 trading days for a ticker and merge into existing Parquet.
    Returns number of new rows added, or -1 on failure.
    """
    # Skip tickers that have never been bootstrapped
    if not parquet_path(ticker, exchange).exists():
        log.debug(f"[NEW] {ticker}: no existing data, doing full fetch")

    for attempt in range(1, retries + 1):
        try:
            tkr  = yf.Ticker(ticker)
            hist = tkr.history(period="5d", auto_adjust=False, actions=True)

            if hist.empty:
                return 0  # Market closed / no new data; not an error

            hist.index = hist.index.normalize().tz_localize(None)
            hist.index.name = "Date"

            keep = ["Open", "High", "Low", "Close", "Adj Close", "Volume",
                    "Dividends", "Stock Splits", "Capital Gains"]
            hist = hist[[c for c in keep if c in hist.columns]]
            hist = clean_numeric_columns(hist)

            new_rows = merge_and_save(hist, ticker, exchange)
            return new_rows

        except Exception as e:
            log.warning(f"[RETRY {attempt}/{retries}] {ticker}: {e}")
            time.sleep(2 ** attempt)

    log_failure(ticker, "update_max_retries")
    return -1


def run_exchange(tickers: list[str], exchange: str) -> tuple[int, int, int]:
    total_new = 0
    ok = fail = 0
    for ticker in tqdm(tickers, desc=f"Updating {exchange}", unit="stock"):
        result = update_ticker(ticker, exchange)
        if result >= 0:
            total_new += result
            ok += 1
        else:
            fail += 1
        rate_limited_sleep(0.3)
    return ok, fail, total_new


def main():
    log.info("=== Daily stock update started ===")

    nse_tickers = load_nse_symbols()
    bse_tickers = load_bse_symbols()

    nse_ok, nse_fail, nse_new = run_exchange(nse_tickers, "NSE")
    bse_ok, bse_fail, bse_new = run_exchange(bse_tickers, "BSE")

    log.info("=== Update complete ===")
    log.info(f"NSE: {nse_ok} OK, {nse_fail} failed, {nse_new} new rows")
    log.info(f"BSE: {bse_ok} OK, {bse_fail} failed, {bse_new} new rows")
    log.info(f"Total new rows: {nse_new + bse_new}")


if __name__ == "__main__":
    main()
