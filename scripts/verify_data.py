"""
verify_data.py
--------------
Verify completeness and quality of fetched stock data.

Checks:
  1. Coverage  — how many tickers have Parquet files vs symbol lists
  2. Staleness — which files haven't been updated recently
  3. Emptiness — files that exist but have 0 rows
  4. Date gaps  — stocks whose last trading date is suspiciously old
  5. Failed log — tickers in failed_tickers.txt

Usage:
    python scripts/verify_data.py              # Full report
    python scripts/verify_data.py --stale-days 3   # Flag stocks not updated in 3 days
    python scripts/verify_data.py --export missing.csv  # Export missing tickers to CSV
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    load_nse_symbols,
    load_bse_symbols,
    parquet_path,
    FAILED_LOG,
    log,
    NSE_DIR,
    BSE_DIR,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def check_file(ticker: str, exchange: str, stale_cutoff: datetime) -> dict:
    path = parquet_path(ticker, exchange)
    result = {
        "ticker":    ticker,
        "exchange":  exchange,
        "exists":    path.exists(),
        "rows":      0,
        "first_date": None,
        "last_date":  None,
        "size_kb":   0,
        "stale":     False,
        "issue":     None,
    }
    if not path.exists():
        result["issue"] = "missing"
        return result

    try:
        df = pd.read_parquet(path)
        result["size_kb"] = round(path.stat().st_size / 1024, 1)
        result["rows"]    = len(df)

        if len(df) == 0:
            result["issue"] = "empty"
            return result

        result["first_date"] = str(df.index.min().date())
        result["last_date"]  = str(df.index.max().date())

        last_dt = df.index.max().to_pydatetime().replace(tzinfo=None)
        if last_dt < stale_cutoff:
            result["stale"] = True
            result["issue"] = f"stale (last={result['last_date']})"

    except Exception as e:
        result["issue"] = f"read_error: {e}"

    return result


def load_failed_log() -> list[str]:
    if not FAILED_LOG.exists():
        return []
    lines = FAILED_LOG.read_text().strip().splitlines()
    return [l.split("\t")[0] for l in lines if l.strip()]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Verify stock data completeness")
    parser.add_argument("--stale-days", type=int, default=7,
                        help="Flag stocks not updated in N calendar days (default: 7)")
    parser.add_argument("--export", type=str, default=None,
                        help="Export missing/failed tickers to a CSV file")
    parser.add_argument("--show-stale", action="store_true",
                        help="Print list of stale tickers")
    args = parser.parse_args()

    stale_cutoff = datetime.now() - timedelta(days=args.stale_days)

    nse_tickers = load_nse_symbols()
    bse_tickers = load_bse_symbols()
    all_tickers = [(t, "NSE") for t in nse_tickers] + [(t, "BSE") for t in bse_tickers]

    print(f"\n{'='*60}")
    print(f"  STOCK DATA VERIFICATION REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # ── Scan all files ─────────────────────────────────────────────────────────
    results = []
    print("Scanning files…")
    for ticker, exchange in tqdm(all_tickers, unit="stock"):
        results.append(check_file(ticker, exchange, stale_cutoff))

    df = pd.DataFrame(results)

    # ── Coverage ───────────────────────────────────────────────────────────────
    for exch in ["NSE", "BSE"]:
        sub = df[df["exchange"] == exch]
        total    = len(sub)
        fetched  = sub["exists"].sum()
        missing  = total - fetched
        empty    = (sub["rows"] == 0).sum()
        stale    = sub["stale"].sum()
        pct      = fetched / total * 100 if total else 0

        print(f"{'─'*60}")
        print(f"  {exch}  ({fetched}/{total} fetched  |  {pct:.1f}% coverage)")
        print(f"{'─'*60}")
        print(f"  ✅ Fetched          : {fetched:>6,}")
        print(f"  ❌ Missing          : {missing:>6,}")
        print(f"  ⚠️  Empty files      : {empty:>6,}")
        print(f"  🕐 Stale (>{args.stale_days}d)    : {stale:>6,}")

        if fetched > 0:
            valid = sub[sub["rows"] > 0]
            if len(valid):
                print(f"  📅 Oldest listing   : {valid['first_date'].min()}")
                print(f"  📅 Most recent data : {valid['last_date'].max()}")
                print(f"  📊 Avg rows/stock   : {valid['rows'].mean():.0f}")
                total_size = sub["size_kb"].sum() / 1024
                print(f"  💾 Total size       : {total_size:.1f} MB")
        print()

    # ── Overall summary ────────────────────────────────────────────────────────
    total_all   = len(df)
    fetched_all = df["exists"].sum()
    missing_all = df[df["issue"] == "missing"]
    stale_all   = df[df["stale"] == True]
    error_all   = df[df["issue"].str.startswith("read_error", na=False)]
    failed_log  = load_failed_log()

    print(f"{'='*60}")
    print(f"  OVERALL SUMMARY")
    print(f"{'='*60}")
    print(f"  Total tickers        : {total_all:>6,}")
    print(f"  Fetched              : {fetched_all:>6,}  ({fetched_all/total_all*100:.1f}%)")
    print(f"  Missing              : {len(missing_all):>6,}  ({len(missing_all)/total_all*100:.1f}%)")
    print(f"  Stale (>{args.stale_days}d ago)    : {len(stale_all):>6,}")
    print(f"  Read errors          : {len(error_all):>6,}")
    print(f"  In failed_tickers.txt: {len(failed_log):>6,}")

    # ── Stale list ────────────────────────────────────────────────────────────
    if args.show_stale and len(stale_all):
        print(f"\n{'─'*60}")
        print("  STALE TICKERS (last data older than cutoff):")
        print(f"{'─'*60}")
        for _, row in stale_all.iterrows():
            print(f"  {row['ticker']:<25} last={row['last_date']}")

    # ── Failed log ────────────────────────────────────────────────────────────
    if failed_log:
        print(f"\n{'─'*60}")
        print(f"  FAILED TICKERS ({len(failed_log)} in failed_tickers.txt):")
        print(f"{'─'*60}")
        for t in failed_log[:20]:
            print(f"  {t}")
        if len(failed_log) > 20:
            print(f"  … and {len(failed_log)-20} more (see failed_tickers.txt)")

    # ── Export ────────────────────────────────────────────────────────────────
    if args.export:
        export_df = df[df["exists"] == False][["ticker", "exchange", "issue"]]
        export_df.to_csv(args.export, index=False)
        print(f"\n  📁 Missing tickers exported → {args.export}")

    print(f"\n{'='*60}\n")

    # ── Return non-zero exit if incomplete ────────────────────────────────────
    if len(missing_all) > 0 or len(error_all) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
