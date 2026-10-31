"""
scripts/update_mf.py
Daily Mutual Fund NAV and metadata update pipeline.

Key Architectural Guarantees:
1. Strict 6-column parsing.
2. 100% Idempotent record counting: total_records increments ONLY when a genuinely new
   (schemeCode, date) observation is inserted into the partition (0 increment on re-runs).
3. All-or-Nothing True Transactional Rollback:
   Creates byte-exact backups (.bak.parquet) of all destination files before replacement.
   If any replacement fails, all modified destinations are restored from backups.
   Zero partial repository modifications on failure.
"""

from __future__ import annotations

import logging
import shutil
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

# Add scripts directory to path for robust imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mf_parser import (
    assert_metadata_integrity,
    parse_amfi_stream,
    validate_metadata_against_previous,
)

logger = logging.getLogger("update_mf")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent
MF_DIR = BASE_DIR / "data" / "MF"
META_PARQUET = MF_DIR / "mf_meta.parquet"
AMFI_URL = "https://www.amfiindia.com/spages/NAVAll.txt"


def fetch_amfi_lines() -> List[str]:
    logger.info(f"Fetching {AMFI_URL}...")
    req = urllib.request.Request(AMFI_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore").splitlines()


def main() -> None:
    logger.info("=== Starting Daily Mutual Fund Update ===")

    # 1. Load existing canonical metadata
    if not META_PARQUET.exists():
        logger.error(f"{META_PARQUET} does not exist. Run scripts/normalize_mf_metadata.py first.")
        sys.exit(1)

    old_meta_df = pd.read_parquet(META_PARQUET)
    old_records = old_meta_df.to_dict(orient="records")
    meta_by_code: Dict[int, Dict[str, Any]] = {r["amfi_code"]: r.copy() for r in old_records}

    # 2. Parse AMFI feed strictly
    lines = fetch_amfi_lines()
    active_schemes, nav_rows = parse_amfi_stream(lines)
    logger.info(f"Parsed {len(active_schemes)} schemes and {len(nav_rows)} valid NAV entries.")

    if not nav_rows:
        logger.error("No valid NAV records parsed from AMFI feed. Aborting.")
        sys.exit(1)

    # 3. Group candidate NAV rows by partition
    candidate_nav_by_part: Dict[int, List[Dict[str, Any]]] = {i: [] for i in range(10)}
    for row in nav_rows:
        part_idx = row.amfi_code % 10
        candidate_nav_by_part[part_idx].append({
            "date": pd.to_datetime(row.nav_date),
            "schemeCode": row.amfi_code,
            "nav": row.nav,
        })

    # 4. Prepare candidate partition DataFrames and calculate exact new observation counts
    candidate_partition_dfs: Dict[int, pd.DataFrame] = {}
    new_records_count_by_code: Dict[int, int] = {}

    for part_idx in range(10):
        part_file = MF_DIR / f"nav_part_{part_idx}.parquet"
        if not part_file.exists():
            raise FileNotFoundError(f"Required partition missing: {part_file}. Aborting update.")

        existing_part_df = pd.read_parquet(part_file)
        new_incoming = candidate_nav_by_part[part_idx]

        if not new_incoming:
            candidate_partition_dfs[part_idx] = existing_part_df
            continue

        incoming_df = pd.DataFrame(new_incoming)

        # Existing key set for exact deduplication
        existing_keys = set(zip(existing_part_df["schemeCode"], existing_part_df["date"]))

        # Identify genuinely new rows
        genuinely_new_mask = [
            (row.schemeCode, row.date) not in existing_keys
            for row in incoming_df.itertuples(index=False)
        ]
        genuinely_new_df = incoming_df[genuinely_new_mask]

        # Count newly added observations per scheme
        if not genuinely_new_df.empty:
            counts = genuinely_new_df["schemeCode"].value_counts().to_dict()
            for code, cnt in counts.items():
                new_records_count_by_code[int(code)] = cnt

        # Combine and sort candidate partition
        combined_df = pd.concat([existing_part_df, genuinely_new_df], ignore_index=True)
        combined_df.sort_values(by=["schemeCode", "date"], inplace=True)
        candidate_partition_dfs[part_idx] = combined_df

    total_new_obs = sum(new_records_count_by_code.values())
    logger.info(f"Idempotency check: {total_new_obs} genuinely new NAV observations to insert.")

    # 5. Build candidate metadata in memory
    active_codes_today = set()
    for s in active_schemes:
        active_codes_today.add(s.amfi_code)
        new_obs = new_records_count_by_code.get(s.amfi_code, 0)

        if s.amfi_code in meta_by_code:
            rec = meta_by_code[s.amfi_code]
            rec["status"] = "ACTIVE"
            if s.latest_nav is not None:
                rec["latest_nav"] = s.latest_nav
            if s.latest_nav_date is not None:
                rec["latest_nav_date"] = s.latest_nav_date
            # IDEMPOTENT: increment ONLY by genuinely new observations
            rec["total_records"] = rec.get("total_records", 0) + new_obs
        else:
            # Brand new scheme in AMFI feed
            meta_by_code[s.amfi_code] = {
                "amfi_code": s.amfi_code,
                "scheme_name": s.scheme_name,
                "clean_name": s.clean_name,
                "amc_name": s.amc_name,
                "plan": s.plan,
                "option": s.option,
                "asset_type": s.asset_type,
                "category": s.category,
                "raw_isin_1": s.raw_isin_1,
                "raw_isin_2": s.raw_isin_2,
                "isin_growth": s.isin_growth,
                "isin_payout": s.isin_payout,
                "isin_reinvestment": s.isin_reinvestment,
                "status": "ACTIVE",
                "first_nav_date": s.latest_nav_date,
                "latest_nav_date": s.latest_nav_date,
                "latest_nav": s.latest_nav,
                "total_records": new_obs,
            }

    # Schemes absent from today's feed become UNKNOWN (never guess CLOSED)
    for code, rec in meta_by_code.items():
        if code not in active_codes_today:
            rec["status"] = "UNKNOWN"

    candidate_meta_records = sorted(meta_by_code.values(), key=lambda x: x["amfi_code"])

    # 6. VALIDATE EVERYTHING BEFORE ANY DISK WRITES
    logger.info("Validating candidate metadata against anomaly detection...")
    validate_metadata_against_previous(candidate_meta_records, old_records)

    logger.info("Asserting candidate metadata integrity...")
    assert_metadata_integrity(candidate_meta_records)

    # 7. TRUE TRANSACTIONAL PERSISTENCE WITH FULL ROLLBACK
    logger.info("Validation passed. Preparing atomic transaction...")
    files_to_replace: List[Tuple[Path, Path]] = []
    backups_created: List[Tuple[Path, Path]] = []
    replaced_successfully: List[Path] = []

    try:
        # Step A: Write all temp files
        for part_idx, part_df in candidate_partition_dfs.items():
            dest_file = MF_DIR / f"nav_part_{part_idx}.parquet"
            tmp_file = dest_file.with_suffix(".tmp.parquet")
            part_df.to_parquet(tmp_file, index=False, compression="snappy")
            files_to_replace.append((tmp_file, dest_file))

        candidate_meta_df = pd.DataFrame(candidate_meta_records)
        tmp_meta_file = META_PARQUET.with_suffix(".tmp.parquet")
        candidate_meta_df.to_parquet(tmp_meta_file, index=False, compression="snappy")
        files_to_replace.append((tmp_meta_file, META_PARQUET))

        # Step B: Create byte-exact backups of all target files before replacement
        for tmp_file, dest_file in files_to_replace:
            if dest_file.exists():
                bak_file = dest_file.with_suffix(".bak.parquet")
                shutil.copy2(dest_file, bak_file)
                backups_created.append((bak_file, dest_file))

        # Step C: Replace files atomically
        for tmp_file, dest_file in files_to_replace:
            tmp_file.replace(dest_file)
            replaced_successfully.append(dest_file)

        # Step D: Transaction committed successfully -> clean up backups
        for bak_file, _ in backups_created:
            if bak_file.exists():
                bak_file.unlink()

        logger.info("Transaction committed successfully. All files replaced atomically.")

    except Exception as exc:
        logger.critical(f"TRANSACTION FAILED: {exc}. Initiating rollback...")
        # Step E: Roll back any files that were replaced using their backups
        for bak_file, dest_file in backups_created:
            if bak_file.exists():
                try:
                    bak_file.replace(dest_file)
                    logger.info(f"  Restored {dest_file.name} from backup.")
                except Exception as rollback_err:
                    logger.error(f"  Failed restoring {dest_file.name}: {rollback_err}")

        # Clean up any leftover temporary files
        for tmp_file, _ in files_to_replace:
            if tmp_file.exists():
                tmp_file.unlink()

        logger.critical("Rollback completed. Repository state preserved.")
        sys.exit(1)


if __name__ == "__main__":
    main()
