"""
scripts/normalize_mf_metadata.py
One-time canonical metadata generator.

Key Architectural Guarantees:
1. Recomputes total_records, first_nav_date, latest_nav_date, and latest_nav
   directly from the authoritative historical NAV partitions (nav_part_0..9.parquet).
2. Requires all 10 partition files to exist; aborts immediately if any is missing.
3. Enforces full partition data integrity (modulo, duplicates, date, NAV reasonability)
   before computing statistics.
4. Legacy mf_meta.parquet is treated as secondary reference data only.
5. Never manufactures scheme names: unreferenced historical schemes are marked UNKNOWN.
6. NAV partitions are opened in READ-ONLY mode. Zero partitions are modified.
"""

from __future__ import annotations

import logging
import sys
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Add scripts directory to path for robust imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mf_parser import (
    assert_metadata_integrity,
    derive_clean_name,
    extract_option,
    extract_plan,
    parse_amfi_stream,
    resolve_isins,
    validate_metadata_against_previous,
)

logger = logging.getLogger("normalize_mf_metadata")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent
MF_DIR = BASE_DIR / "data" / "MF"
META_PARQUET = MF_DIR / "mf_meta.parquet"
AMFI_URL = "https://www.amfiindia.com/spages/NAVAll.txt"


@dataclass
class PartitionSchemeStats:
    total_records: int
    first_nav_date: date
    latest_nav_date: date
    latest_nav: float


def validate_and_compute_partition_stats() -> Dict[int, PartitionSchemeStats]:
    """
    1. Verifies that all 10 partitions exist. Aborts if any is missing.
    2. Validates schema, positive schemeCode, modulo consistency, partition disjointness,
       date validity, NAV validity, and absence of duplicate (schemeCode, date) pairs.
    3. Returns exact statistics aggregated per schemeCode.
    """
    logger.info("Validating authoritative NAV partitions (nav_part_0..9.parquet)...")

    # Guard 1: All 10 partitions MUST exist
    for part_idx in range(10):
        part_file = MF_DIR / f"nav_part_{part_idx}.parquet"
        if not part_file.exists():
            raise FileNotFoundError(
                f"CRITICAL ERROR: Required NAV partition missing: {part_file}. "
                "All 10 partitions (nav_part_0..9.parquet) are mandatory. Aborting migration."
            )

    stats: Dict[int, PartitionSchemeStats] = {}
    seen_codes_globally: Set[int] = set()

    for part_idx in range(10):
        part_file = MF_DIR / f"nav_part_{part_idx}.parquet"
        logger.info(f"  Validating and scanning partition {part_idx}/9: {part_file.name}...")
        df = pd.read_parquet(part_file)

        # Check required columns
        for req_col in ("schemeCode", "date", "nav"):
            if req_col not in df.columns:
                raise ValueError(f"Partition {part_file.name} is missing required column '{req_col}'")

        if df.empty:
            continue

        # Check positive schemeCode
        codes = df["schemeCode"]
        if (codes <= 0).any():
            raise ValueError(f"Partition {part_file.name} contains non-positive schemeCode values.")

        # Check modulo distribution: schemeCode % 10 == part_idx
        modulo_violations = codes[codes % 10 != part_idx]
        if not modulo_violations.empty:
            raise ValueError(
                f"Partition {part_file.name} contains {len(modulo_violations)} schemeCodes violating "
                f"modulo {part_idx} distribution (e.g. {modulo_violations.iloc[0]})."
            )

        # Check partition disjointness
        part_unique_codes = set(codes.unique())
        intersect = seen_codes_globally & part_unique_codes
        if intersect:
            raise ValueError(f"Partition disjointness violated: schemeCodes {intersect} exist in multiple partitions.")
        seen_codes_globally.update(part_unique_codes)

        # Check duplicate (schemeCode, date)
        dup_mask = df.duplicated(subset=["schemeCode", "date"])
        if dup_mask.any():
            raise ValueError(
                f"Partition {part_file.name} contains {dup_mask.sum()} duplicate (schemeCode, date) observations."
            )

        # Check date and NAV nullability
        if df["date"].isna().any():
            raise ValueError(f"Partition {part_file.name} contains null dates.")
        if df["nav"].isna().any():
            raise ValueError(f"Partition {part_file.name} contains null NAV values.")

        # Compute exact statistics
        grouped = df.groupby("schemeCode")
        for code, group in grouped:
            code_int = int(code)
            cnt = len(group)
            min_date = group["date"].min().date()
            max_row = group.loc[group["date"].idxmax()]
            max_date = max_row["date"].date()
            latest_nav = float(max_row["nav"])

            stats[code_int] = PartitionSchemeStats(
                total_records=cnt,
                first_nav_date=min_date,
                latest_nav_date=max_date,
                latest_nav=latest_nav,
            )

    logger.info(f"Integrity verified. Computed statistics for {len(stats)} historical schemes.")
    return stats


def fetch_amfi_lines() -> List[str]:
    logger.info(f"Downloading AMFI feed from {AMFI_URL}...")
    req = urllib.request.Request(AMFI_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode("utf-8", errors="ignore")
    return content.splitlines()


def main() -> None:
    logger.info("=== Starting Mutual Fund Metadata Normalization ===")

    # Step 1: Validate partitions and compute authoritative statistics
    partition_stats = validate_and_compute_partition_stats()

    # Step 2: Read legacy metadata as secondary reference only
    old_reference_by_code: Dict[int, Dict[str, Any]] = {}
    old_raw_records: List[Dict[str, Any]] = []
    if META_PARQUET.exists():
        logger.info(f"Reading legacy reference metadata from {META_PARQUET}...")
        old_df = pd.read_parquet(META_PARQUET)
        if old_df.index.name in ("schemeCode", "amfi_code") or "schemeCode" not in old_df.columns:
            old_df = old_df.reset_index()
        for _, row in old_df.iterrows():
            code = int(row.get("schemeCode", row.get("amfi_code", 0)))
            if code <= 0:
                continue
            rec = row.to_dict()
            rec["amfi_code"] = code
            old_reference_by_code[code] = rec
            old_raw_records.append(rec)
        logger.info(f"Found {len(old_reference_by_code)} legacy records for reference.")

    # Step 3: Fetch and parse current AMFI live stream with strict 6-column parser
    amfi_lines = fetch_amfi_lines()
    active_schemes, _ = parse_amfi_stream(amfi_lines)
    active_by_code = {s.amfi_code: s for s in active_schemes}
    logger.info(f"Parsed {len(active_by_code)} active schemes from live AMFI feed.")

    # Step 4: Union all known scheme codes
    all_codes = sorted(set(partition_stats.keys()) | set(old_reference_by_code.keys()) | set(active_by_code.keys()))
    logger.info(f"Total schemes to normalize: {len(all_codes)}")

    canonical_records: List[Dict[str, Any]] = []

    for code in all_codes:
        active_meta = active_by_code.get(code)
        legacy_ref = old_reference_by_code.get(code)
        part_stat = partition_stats.get(code)

        if active_meta:
            scheme_name = active_meta.scheme_name
            clean_name = active_meta.clean_name
            amc_name = active_meta.amc_name
            plan = active_meta.plan
            option = active_meta.option
            asset_type = active_meta.asset_type
            category = active_meta.category
            r1 = active_meta.raw_isin_1
            r2 = active_meta.raw_isin_2
            isin_g = active_meta.isin_growth
            isin_p = active_meta.isin_payout
            isin_r = active_meta.isin_reinvestment
            status = "ACTIVE"
        elif legacy_ref:
            # Historical scheme not in today's active AMFI feed
            raw_name = str(legacy_ref.get("schemeName", "")).strip()
            scheme_name = raw_name if raw_name else "UNKNOWN"
            clean_name = derive_clean_name(raw_name) if raw_name else "UNKNOWN"
            legacy_amc = str(legacy_ref.get("fundHouse", "")).strip()
            amc_name = legacy_amc if legacy_amc and ";" not in legacy_amc else "UNKNOWN"
            plan = extract_plan(raw_name) if raw_name else "UNKNOWN"
            option = extract_option(raw_name) if raw_name else "UNKNOWN"
            asset_type = "UNKNOWN"
            category = "UNKNOWN"
            raw_col1 = str(legacy_ref.get("isinGrowth", "")) if pd.notnull(legacy_ref.get("isinGrowth")) else ""
            raw_col2 = str(legacy_ref.get("isinDiv", "")) if pd.notnull(legacy_ref.get("isinDiv")) else ""
            r1, r2, isin_g, isin_p, isin_r = resolve_isins(raw_col1, raw_col2, option)
            status = "UNKNOWN"
        else:
            # ZERO GUESSING: Never manufacture a scheme name like f"Scheme {code}"
            logger.warning(
                "Scheme %d found in NAV partitions but has NO metadata in live feed or legacy file. "
                "Marking all metadata attributes as UNKNOWN.", code
            )
            scheme_name = "UNKNOWN"
            clean_name = "UNKNOWN"
            amc_name = "UNKNOWN"
            plan = "UNKNOWN"
            option = "UNKNOWN"
            asset_type = "UNKNOWN"
            category = "UNKNOWN"
            r1, r2 = "", ""
            isin_g, isin_p, isin_r = None, None, None
            status = "UNKNOWN"

        # Authoritative partition statistics take precedence
        if part_stat:
            first_nav_date = part_stat.first_nav_date
            latest_nav_date = part_stat.latest_nav_date
            latest_nav = part_stat.latest_nav
            total_records = part_stat.total_records
        elif active_meta:
            first_nav_date = active_meta.latest_nav_date
            latest_nav_date = active_meta.latest_nav_date
            latest_nav = active_meta.latest_nav
            total_records = 1
        else:
            first_nav_date = None
            latest_nav_date = None
            latest_nav = None
            total_records = 0

        canonical_records.append({
            "amfi_code": code,
            "scheme_name": scheme_name,
            "clean_name": clean_name,
            "amc_name": amc_name,
            "plan": plan,
            "option": option,
            "asset_type": asset_type,
            "category": category,
            "raw_isin_1": r1,
            "raw_isin_2": r2,
            "isin_growth": isin_g,
            "isin_payout": isin_p,
            "isin_reinvestment": isin_r,
            "status": status,
            "first_nav_date": first_nav_date,
            "latest_nav_date": latest_nav_date,
            "latest_nav": latest_nav,
            "total_records": total_records,
        })

    # Step 5: Relative anomaly validation against legacy metadata
    if old_raw_records:
        logger.info("Running relative anomaly validation against previous snapshot...")
        validate_metadata_against_previous(canonical_records, old_raw_records)

    # Step 6: Strict assertions
    logger.info("Running strict schema integrity assertions...")
    assert_metadata_integrity(canonical_records)

    # Step 7: Atomic Parquet export
    arrow_schema = pa.schema([
        ("amfi_code", pa.int64()),
        ("scheme_name", pa.string()),
        ("clean_name", pa.string()),
        ("amc_name", pa.string()),
        ("plan", pa.string()),
        ("option", pa.string()),
        ("asset_type", pa.string()),
        ("category", pa.string()),
        ("raw_isin_1", pa.string()),
        ("raw_isin_2", pa.string()),
        ("isin_growth", pa.string()),
        ("isin_payout", pa.string()),
        ("isin_reinvestment", pa.string()),
        ("status", pa.string()),
        ("first_nav_date", pa.date32()),
        ("latest_nav_date", pa.date32()),
        ("latest_nav", pa.float64()),
        ("total_records", pa.int64()),
    ])

    df = pd.DataFrame(canonical_records)
    table = pa.Table.from_pandas(df, schema=arrow_schema, preserve_index=False)

    tmp_path = META_PARQUET.with_suffix(".tmp.parquet")
    pq.write_table(table, tmp_path, compression="snappy")
    tmp_path.replace(META_PARQUET)

    logger.info(f"Successfully generated canonical {META_PARQUET} ({len(canonical_records)} schemes).")
    logger.info("NAV partitions (nav_part_0..9.parquet) remained completely untouched.")


if __name__ == "__main__":
    main()
