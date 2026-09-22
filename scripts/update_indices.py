"""
update_indices.py
-----------------
Daily incremental updater for Indian benchmark, sectoral, and broad market indices.
Fetches the latest trading sessions and merges them into the existing Parquet files.
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

# Index symbol to Yahoo ticker mapping
INDEX_TICKERS = {
    "NIFTY_50": "^NSEI",
    "SENSEX": "^BSESN",
    "NIFTY_BANK": "^NSEBANK",
    "INDIA_VIX": "^INDIAVIX",
    "NIFTY_IT": "^CNXIT",
    "NIFTY_PHARMA": "^CNXPHARMA",
    "NIFTY_100": "^CNX100",
    "NIFTY_200": "^CNX200",
    "NIFTY_500": "^CRSLDX",
    "NIFTY_MIDCAP_50": "^NSEMDCP50",
}


def update_indices():
    INDICES_DIR.mkdir(parents=True, exist_ok=True)
    total_added = 0

    log.info(f"Checking for latest daily updates across {len(INDEX_TICKERS)} indices...")

    for symbol, ticker in INDEX_TICKERS.items():
        parquet_file = INDICES_DIR / f"{symbol}.parquet"

        try:
            tkr = yf.Ticker(ticker)
            df = tkr.history(period="5d", auto_adjust=False, actions=True)

            if df.empty:
                log.warning(f"No recent data returned for {ticker}")
                continue

            # Normalize date index
            df.index = df.index.normalize().tz_localize(None)
            df.index.name = "Date"

            keep_cols = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
            cols = [c for c in keep_cols if c in df.columns]
            df = df[cols]
            df = clean_numeric_columns(df)

            if parquet_file.exists():
                existing_df = pd.read_parquet(parquet_file)
                combined_df = pd.concat([existing_df, df])
                combined_df = combined_df[~combined_df.index.duplicated(keep="last")]
                combined_df.sort_index(inplace=True)
                new_rows = len(combined_df) - len(existing_df)
            else:
                combined_df = df.sort_index()
                new_rows = len(combined_df)

            combined_df.to_parquet(parquet_file, engine="pyarrow", compression="snappy", index=True)
            total_added += new_rows
            log.info(f"{symbol} updated: +{new_rows} new rows (latest: {combined_df.index[-1].strftime('%Y-%m-%d')})")

        except Exception as e:
            log.error(f"Error updating {symbol} ({ticker}): {e}")

    # Refresh master list dates and counts if master exists
    if MASTER_FILE.exists():
        try:
            m_df = pd.read_csv(MASTER_FILE)
            for idx, row in m_df.iterrows():
                sym = row["Symbol"]
                p_path = INDICES_DIR / f"{sym}.parquet"
                if p_path.exists():
                    df = pd.read_parquet(p_path)
                    m_df.at[idx, "End_Date"] = df.index[-1].strftime("%Y-%m-%d")
                    m_df.at[idx, "Total_Records"] = len(df)
            m_df.to_csv(MASTER_FILE, index=False)
            log.info(f"Updated metadata in {MASTER_FILE}")
        except Exception as e:
            log.warning(f"Could not refresh {MASTER_FILE}: {e}")

    log.info(f"Indices update completed. Total new rows appended: {total_added}")


if __name__ == "__main__":
    update_indices()
