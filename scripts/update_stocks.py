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
    get_engine,
)

yf = get_engine()

RETRY_LIMIT = 2
RATE_LIMIT_CONSECUTIVE_THRESHOLD = 3
COOLDOWN_SECONDS = 60
MAX_CIRCUIT_TRIPS = 3


def update_ticker(ticker: str, exchange: str, retries: int = RETRY_LIMIT) -> int:
    """
    Fetch last 5 trading days for a ticker and merge into existing Parquet.
    Returns:
        >= 0 : number of new rows added (or 0 if already up to date / skipped)
        -1   : general error
        -429 : rate limit error (HTTP 429)
    """
    # Only update stocks that already exist in our historical archive
    if not parquet_path(ticker, exchange).exists():
        log.debug(f"[SKIP] {ticker}: not in local archive, skipping in daily update")
        return 0

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
            err_msg = str(e)
            is_429 = "Too Many Requests" in err_msg or "429" in err_msg or "Rate limited" in err_msg
            if is_429:
                log.warning(f"[RATE LIMITED] {ticker}: {err_msg}")
                return -429

            log.warning(f"[RETRY {attempt}/{retries}] {ticker}: {e}")
            time.sleep(2 ** attempt)

    log_failure(ticker, "update_max_retries")
    return -1


def run_exchange(tickers: list[str], exchange: str) -> tuple[int, int, int]:
    total_new = 0
    ok = fail = 0
    consecutive_429 = 0
    circuit_trips = 0

    for ticker in tqdm(tickers, desc=f"Updating {exchange}", unit="stock"):
        result = update_ticker(ticker, exchange)
        if result >= 0:
            total_new += result
            ok += 1
            consecutive_429 = 0  # Reset on success
        elif result == -429:
            fail += 1
            consecutive_429 += 1
            if consecutive_429 >= RATE_LIMIT_CONSECUTIVE_THRESHOLD:
                circuit_trips += 1
                log.warning(
                    f"[CIRCUIT BREAKER] Hit {consecutive_429} consecutive rate limits. "
                    f"Trip #{circuit_trips}/{MAX_CIRCUIT_TRIPS}. Cooling down for {COOLDOWN_SECONDS}s..."
                )
                time.sleep(COOLDOWN_SECONDS)
                consecutive_429 = 0  # Reset counter after cooldown
                if circuit_trips >= MAX_CIRCUIT_TRIPS:
                    log.error(
                        f"[CIRCUIT BREAKER] Maximum {MAX_CIRCUIT_TRIPS} cooldown trips reached for {exchange}. "
                        "Saving progress and gracefully moving forward."
                    )
                    break
        else:
            fail += 1
            consecutive_429 = 0

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
