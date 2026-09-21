"""
update_unlisted.py
------------------
Updater and maintenance script for the unlisted / pre-IPO Indian share dataset.
Supports checking dataset freshness, appending newly reported secondary market quotes
or funding rounds, and re-exporting the sorted Parquet dataset.

Usage:
    # Check dataset overview:
    python scripts/update_unlisted.py

    # Append a new quote or valuation milestone:
    python scripts/update_unlisted.py --add --symbol NSE --date 2026-10-01 --price 7600 --event "Quarterly Indicative Quote"
"""

import argparse
import sys
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
UNLISTED_FILE = ROOT_DIR / "data" / "UNLISTED" / "unlisted_shares.parquet"


def inspect_dataset():
    if not UNLISTED_FILE.exists():
        print(f"Error: Dataset not found at {UNLISTED_FILE}. Run scripts/build_unlisted.py first.")
        sys.exit(1)

    df = pd.read_parquet(UNLISTED_FILE)
    df["date"] = pd.to_datetime(df["date"])
    print(f"{'='*65}")
    print(f"  UNLISTED / PRE-IPO EQUITIES DATASET OVERVIEW")
    print(f"{'='*65}")
    print(f"  Total Records        : {len(df):,}")
    print(f"  Companies Covered    : {df['symbol'].nunique()}")
    print(f"  Date Range           : {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"  File Size            : {UNLISTED_FILE.stat().st_size / 1024:.2f} KB")
    print(f"{'─'*65}")
    print(f"  Latest Indicative Quotes per Company:")
    print(f"{'─'*65}")

    latest = df.sort_values(by="date").groupby("symbol").last().reset_index()
    latest.sort_values(by="symbol", inplace=True)
    for _, r in latest.iterrows():
        print(f"  {r['symbol']:<16} ₹{r['price']:>8,.1f}  ({r['date'].strftime('%Y-%m-%d')}) - {r['company']}")
    print(f"{'='*65}\n")


def add_record(symbol: str, date: str, price: float, event: str, company: str = None, sector: str = None, face_value: float = None):
    if not UNLISTED_FILE.exists():
        print(f"Error: Dataset not found at {UNLISTED_FILE}. Run scripts/build_unlisted.py first.")
        sys.exit(1)

    df = pd.read_parquet(UNLISTED_FILE)
    df["date"] = pd.to_datetime(df["date"])

    # If company / sector / face_value not provided, inherit from existing symbol record
    matching = df[df["symbol"].str.upper() == symbol.upper()]
    if not matching.empty:
        sample = matching.iloc[-1]
        company = company or sample.get("company", symbol)
        sector = sector or sample.get("sector", "Uncategorized")
        face_value = face_value if face_value is not None else sample.get("face_value", 10.0)
    else:
        company = company or symbol
        sector = sector or "General"
        face_value = face_value if face_value is not None else 10.0

    new_row = {
        "date": pd.to_datetime(date),
        "symbol": symbol.upper(),
        "company": company,
        "price": float(price),
        "event": event,
        "sector": sector,
        "face_value": float(face_value),
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.sort_values(by=["symbol", "date"], inplace=True)
    df.drop_duplicates(subset=["symbol", "date", "event"], keep="last", inplace=True)

    df.to_parquet(UNLISTED_FILE, engine="pyarrow", compression="snappy", index=False)
    print(f"✓ Successfully added {symbol.upper()} record ({date} - ₹{price}) to {UNLISTED_FILE}")


def main():
    parser = argparse.ArgumentParser(description="Update and inspect unlisted equity data.")
    parser.add_argument("--add", action="store_true", help="Add a new valuation/quote milestone")
    parser.add_argument("--symbol", type=str, help="Company symbol (e.g. NSE, TATA_CAPITAL)")
    parser.add_argument("--date", type=str, help="Date (YYYY-MM-DD)")
    parser.add_argument("--price", type=float, help="Indicative price in INR")
    parser.add_argument("--event", type=str, default="Secondary Market Quote", help="Description or event name")
    parser.add_argument("--company", type=str, default=None, help="Company legal name")
    parser.add_argument("--sector", type=str, default=None, help="Industry sector")
    parser.add_argument("--face-value", type=float, default=None, help="Face value per share")

    args = parser.parse_args()

    if args.add:
        if not args.symbol or not args.date or args.price is None:
            print("Error: --add requires --symbol, --date, and --price")
            sys.exit(1)
        add_record(
            symbol=args.symbol,
            date=args.date,
            price=args.price,
            event=args.event,
            company=args.company,
            sector=args.sector,
            face_value=args.face_value,
        )
    else:
        inspect_dataset()


if __name__ == "__main__":
    main()
