"""
update_corporate_actions.py
---------------------------
Daily incremental updater for Indian Corporate Actions Master Catalog.
Pulls recent announcements (-30 days to +90 days into the future),
deduplicates, and updates the master Parquet and CSV files.
"""

import sys
import json
import time
import subprocess
import re
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from utils import log

ROOT_DIR = Path(__file__).resolve().parent.parent
CORP_DIR = ROOT_DIR / "data" / "CORPORATE_ACTIONS"
PARQUET_FILE = CORP_DIR / "corporate_actions.parquet"
CSV_FILE = CORP_DIR / "corporate_actions.csv"


def parse_date(d_str):
    if not d_str or str(d_str).strip() in ("-", "", "None"):
        return None
    d_str = str(d_str).strip()
    for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(d_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def classify_action(subject):
    s = (subject or "").upper()
    if "BONUS" in s:
        return "BONUS"
    elif "SPLIT" in s or "SUB-DIVISION" in s or "SUB DIVISION" in s:
        return "SPLIT"
    elif "DIVIDEND" in s:
        return "DIVIDEND"
    elif "RIGHTS" in s or "RIGHT ISSUE" in s or "RIGHTS ISSUE" in s:
        return "RIGHTS"
    elif "BUY BACK" in s or "BUYBACK" in s:
        return "BUYBACK"
    elif "DEMERGER" in s or "AMALGAMATION" in s or "SCHEME OF ARRANGEMENT" in s or "SPIN" in s:
        return "DEMERGER"
    elif "AGM" in s or "ANNUAL GENERAL MEETING" in s or "EGM" in s or "EXTRA ORDINARY" in s:
        return "MEETING"
    elif "INTEREST PAYMENT" in s or "INTEREST" in s:
        return "INTEREST"
    elif "REDUCTION OF CAPITAL" in s or "CAPITAL REDUCTION" in s:
        return "CAPITAL_REDUCTION"
    else:
        return "OTHER"


def extract_ratio_or_amount(action_type, subject):
    s = (subject or "").strip()
    if not s:
        return ""

    if action_type in ("BONUS", "RIGHTS"):
        m = re.search(r"(\d+\s*:\s*\d+)", s)
        if m:
            return m.group(1).replace(" ", "")

    elif action_type == "SPLIT":
        m = re.search(r"from\s+(?:rs\.?|re\.?|inr)?\s*(\d+(?:\.\d+)?)[^t]*?to\s+(?:rs\.?|re\.?|inr)?\s*(\d+(?:\.\d+)?)", s, re.I)
        if m:
            return f"{m.group(1)}:{m.group(2)}"
        m2 = re.search(r"(\d+\s*:\s*\d+)", s)
        if m2:
            return m2.group(1).replace(" ", "")

    elif action_type == "DIVIDEND":
        m = re.search(r"(?:rs\.?|re\.?|inr)\s*(\d+(?:\.\d+)?)", s, re.I)
        if m:
            try:
                return f"{float(m.group(1)):.2f}"
            except ValueError:
                pass

    return ""


def fetch_nse_chunk(from_date, to_date):
    url = f"https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date={from_date}&to_date={to_date}"
    cmd = [
        "curl", "-s", url,
        "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "-H", "Accept: application/json, text/plain, */*",
        "-H", "Referer: https://www.nseindia.com/companies-listing/corporate-filings-actions",
        "--max-time", "60",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=65)
        if res.returncode == 0 and res.stdout.strip().startswith("["):
            return json.loads(res.stdout)
    except Exception as e:
        log.warning(f"Error fetching chunk {from_date} -> {to_date}: {e}")
    return []


def update_corporate_actions():
    CORP_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.now()
    start_date = (today - timedelta(days=30)).strftime("%d-%m-%Y")
    future_date = (today + timedelta(days=90)).strftime("%d-%m-%Y")

    log.info(f"Checking for recent and upcoming corporate actions ({start_date} to {future_date})...")
    raw_records = fetch_nse_chunk(start_date, future_date)

    if not raw_records:
        log.warning("No recent corporate actions returned from exchange feed.")
        return

    log.info(f"Retrieved {len(raw_records)} events in recent window.")

    cleaned = []
    for r in raw_records:
        symbol = str(r.get("symbol") or "").strip()
        comp = str(r.get("comp") or "").strip()
        series = str(r.get("series") or "").strip()
        face_val = str(r.get("faceVal") or "").strip()
        isin = str(r.get("isin") or "").strip()
        subject = str(r.get("subject") or "").strip()

        ex_date = parse_date(r.get("exDate"))
        rec_date = parse_date(r.get("recDate"))
        bc_start = parse_date(r.get("bcStartDate"))
        bc_end = parse_date(r.get("bcEndDate"))

        action_type = classify_action(subject)
        ratio_amount = extract_ratio_or_amount(action_type, subject)

        cleaned.append({
            "Ex_Date": ex_date,
            "Record_Date": rec_date,
            "Symbol": symbol,
            "Company_Name": comp,
            "Series": series,
            "Action_Type": action_type,
            "Ratio_or_Amount": ratio_amount,
            "Purpose": subject,
            "Face_Value": face_val if face_val != "-" else None,
            "ISIN": isin if isin != "-" else None,
            "BC_Start_Date": bc_start,
            "BC_End_Date": bc_end,
        })

    new_df = pd.DataFrame(cleaned)

    if PARQUET_FILE.exists():
        existing_df = pd.read_parquet(PARQUET_FILE)
        combined = pd.concat([existing_df, new_df])
        combined.drop_duplicates(subset=["Symbol", "Ex_Date", "Action_Type", "Purpose"], keep="last", inplace=True)
        new_count = len(combined) - len(existing_df)
    else:
        combined = new_df.drop_duplicates(subset=["Symbol", "Ex_Date", "Action_Type", "Purpose"])
        new_count = len(combined)

    combined.sort_values(by=["Ex_Date", "Symbol"], ascending=[False, True], na_position="last", inplace=True)
    combined.reset_index(drop=True, inplace=True)

    combined.to_parquet(PARQUET_FILE, engine="pyarrow", compression="snappy", index=False)
    combined.to_csv(CSV_FILE, index=False)

    log.info(f"Corporate Actions updated: +{new_count} new records added (Total catalog: {len(combined):,} events)")


if __name__ == "__main__":
    update_corporate_actions()
