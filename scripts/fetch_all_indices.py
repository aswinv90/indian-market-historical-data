"""
fetch_all_indices.py
--------------------
One-time bootstrap: fetch full historical OHLCV data for major Indian benchmark,
sectoral, and thematic indices and store as snappy-compressed Parquets.

Indices tracked:
- NIFTY 50 (^NSEI)
- S&P BSE SENSEX (^BSESN)
- NIFTY BANK (^NSEBANK)
- INDIA VIX (^INDIAVIX)
- NIFTY IT (^CNXIT)
- NIFTY PHARMA (^CNXPHARMA)
- NIFTY 100 (^CNX100)
- NIFTY 200 (^CNX200)
- NIFTY 500 (^CRSLDX)
- NIFTY MIDCAP 50 (^NSEMDCP50)
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from utils import get_engine, clean_numeric_columns, log

yf = get_engine()

ROOT_DIR = Path(__file__).resolve().parent.parent
INDICES_DIR = ROOT_DIR / "data" / "INDICES"
MASTER_FILE = INDICES_DIR / "index_list.csv"

INDICES_CONFIG = [
    {
        "symbol": "NIFTY_50",
        "ticker": "^NSEI",
        "name": "NIFTY 50",
        "exchange": "NSE",
        "category": "Benchmark",
        "description": "Benchmark 50 large-cap Indian stocks",
    },
    {
        "symbol": "SENSEX",
        "ticker": "^BSESN",
        "name": "S&P BSE SENSEX",
        "exchange": "BSE",
        "category": "Benchmark",
        "description": "Benchmark 30 large-cap Indian stocks",
    },
    {
        "symbol": "NIFTY_BANK",
        "ticker": "^NSEBANK",
        "name": "NIFTY BANK",
        "exchange": "NSE",
        "category": "Sectoral",
        "description": "Top liquid and large Indian banking stocks",
    },
    {
        "symbol": "INDIA_VIX",
        "ticker": "^INDIAVIX",
        "name": "INDIA VIX",
        "exchange": "NSE",
        "category": "Volatility",
        "description": "India Volatility Index (Market Fear Gauge)",
    },
    {
        "symbol": "NIFTY_IT",
        "ticker": "^CNXIT",
        "name": "NIFTY IT",
        "exchange": "NSE",
        "category": "Sectoral",
        "description": "Leading Indian information technology companies",
    },
    {
        "symbol": "NIFTY_PHARMA",
        "ticker": "^CNXPHARMA",
        "name": "NIFTY PHARMA",
        "exchange": "NSE",
        "category": "Sectoral",
        "description": "Leading Indian pharmaceutical and healthcare companies",
    },
    {
        "symbol": "NIFTY_100",
        "ticker": "^CNX100",
        "name": "NIFTY 100",
        "exchange": "NSE",
        "category": "Broad Market",
        "description": "Top 100 large-cap companies listed on NSE",
    },
    {
        "symbol": "NIFTY_200",
        "ticker": "^CNX200",
        "name": "NIFTY 200",
        "exchange": "NSE",
        "category": "Broad Market",
        "description": "Top 200 large and mid-cap companies listed on NSE",
    },
    {
        "symbol": "NIFTY_500",
        "ticker": "^CRSLDX",
        "name": "NIFTY 500",
        "exchange": "NSE",
        "category": "Broad Market",
        "description": "Top 500 companies representing ~90% market cap",
    },
    {
        "symbol": "NIFTY_MIDCAP_50",
        "ticker": "^NSEMDCP50",
        "name": "NIFTY MIDCAP 50",
        "exchange": "NSE",
        "category": "Broad Market",
        "description": "Top 50 liquid mid-cap Indian companies",
    },
]


def fetch_all_indices():
    INDICES_DIR.mkdir(parents=True, exist_ok=True)
    summary_rows = []

    log.info(f"Starting bootstrap fetch for {len(INDICES_CONFIG)} Indian indices...")

    for item in INDICES_CONFIG:
        symbol = item["symbol"]
        ticker = item["ticker"]
        log.info(f"Fetching full history for {item['name']} ({ticker})...")

        try:
            tkr = yf.Ticker(ticker)
            df = tkr.history(period="max", auto_adjust=False, actions=True)

            if df.empty:
                log.warning(f"No data returned for {ticker}")
                continue

            # Normalize date index
            df.index = df.index.normalize().tz_localize(None)
            df.index.name = "Date"

            # Filter standard columns
            keep_cols = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
            cols = [c for c in keep_cols if c in df.columns]
            df = df[cols]
            df = clean_numeric_columns(df)
            df.sort_index(inplace=True)
            df = df[~df.index.duplicated(keep="last")]

            parquet_file = f"{symbol}.parquet"
            out_path = INDICES_DIR / parquet_file
            df.to_parquet(out_path, engine="pyarrow", compression="snappy", index=True)

            start_date = df.index[0].strftime("%Y-%m-%d")
            end_date = df.index[-1].strftime("%Y-%m-%d")
            rows_count = len(df)
            log.info(f"Saved {symbol}: {rows_count:,} rows ({start_date} -> {end_date}) to {out_path.name}")

            summary_rows.append({
                "Symbol": symbol,
                "Ticker": ticker,
                "Name": item["name"],
                "Exchange": item["exchange"],
                "Category": item["category"],
                "Description": item["description"],
                "Start_Date": start_date,
                "End_Date": end_date,
                "Total_Records": rows_count,
                "Parquet_File": f"data/INDICES/{parquet_file}",
            })

        except Exception as e:
            log.error(f"Failed to fetch {ticker}: {e}")

    # Generate index_list.csv master catalog
    if summary_rows:
        master_df = pd.DataFrame(summary_rows)
        master_df.to_csv(MASTER_FILE, index=False)
        log.info(f"Master index catalog saved to {MASTER_FILE}")


if __name__ == "__main__":
    fetch_all_indices()
