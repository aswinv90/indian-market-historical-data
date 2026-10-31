"""
scripts/mf_parser.py
Core parsing and classification library for AMFI Mutual Fund data.

Strict Principles:
1. Exactly 6 semicolon-delimited fields per data row. Any other count is rejected.
2. SOURCE-SUPPORTED FACT -> NORMALIZED VALUE.
3. NO SOURCE SUPPORT     -> UNKNOWN.
4. Raw source strings are preserved verbatim. Semantic mappings require explicit option proof.
5. NEVER GUESS.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("mf_parser")

# =====================================================================
# Strict Regex Classifiers
# =====================================================================

ISIN_REGEX = re.compile(r"^IN[A-Z0-9]{10}$")

# Plan: explicit phrases only. Avoid loose abbreviations that cause false positives.
DIRECT_PLAN_REGEX = re.compile(r"\b(direct\s*plan|direct)\b", re.IGNORECASE)
REGULAR_PLAN_REGEX = re.compile(r"\b(regular\s*plan|regular)\b", re.IGNORECASE)

# Option: explicit phrases only.
# Generic IDCW/Dividend without payout/reinvest marker MUST resolve to UNKNOWN.
IDCW_PAYOUT_REGEX = re.compile(
    r"\b(idcw\s*payout|payout\s*of\s*idcw|dividend\s*payout|payout\s*option|div\s*payout|monthly\s*payout|quarterly\s*payout|annual\s*payout|half\s*yearly\s*payout)\b",
    re.IGNORECASE,
)
IDCW_REINVEST_REGEX = re.compile(
    r"\b(idcw\s*reinvest(?:ment)?|dividend\s*reinvest(?:ment)?|div\s*reinv(?:estment)?|daily\s*reinvest|weekly\s*reinvest|monthly\s*reinvest)\b",
    re.IGNORECASE,
)
GROWTH_REGEX = re.compile(r"\b(growth|growth\s*plan|growth\s*option)\b", re.IGNORECASE)
GENERIC_IDCW_REGEX = re.compile(r"\b(idcw|dividend|div)\b", re.IGNORECASE)

# AMFI Header Category Regex
HEADER_CATEGORY_REGEX = re.compile(
    r"^(Open Ended|Close Ended|Interval Fund|Interval)\s*Schemes?\s*(?:\*\*\s*)?\(\s*(.+?)\s*\)$",
    re.IGNORECASE,
)

# Safe Clean Name derivation (conservative trailing suffix removal)
CLEAN_SUFFIX_REGEX = re.compile(
    r"\s*[-–(]\s*(?:Direct|Regular)?\s*(?:Plan)?\s*[-–/]?\s*(?:Growth|IDCW|Dividend|Payout|Reinvestment)(?:\s*(?:Option|Plan))?\s*\)?\s*$",
    re.IGNORECASE,
)


# =====================================================================
# Data Structures
# =====================================================================

@dataclass
class ParsedSchemeMeta:
    amfi_code: int
    scheme_name: str
    clean_name: str
    amc_name: str
    plan: str              # 'DIRECT' | 'REGULAR' | 'UNKNOWN'
    option: str            # 'GROWTH' | 'IDCW_PAYOUT' | 'IDCW_REINVESTMENT' | 'UNKNOWN'
    asset_type: str        # 'EQUITY' | 'DEBT' | 'HYBRID' | 'SOLUTION_ORIENTED' | 'OTHER' | 'UNKNOWN'
    category: str          # SEBI category or 'UNKNOWN'
    raw_isin_1: str        # Verbatim raw Col 1 (preserved exactly as received)
    raw_isin_2: str        # Verbatim raw Col 2 (preserved exactly as received)
    isin_growth: Optional[str]
    isin_payout: Optional[str]
    isin_reinvestment: Optional[str]
    status: str            # 'ACTIVE' | 'UNKNOWN'
    latest_nav: Optional[float]
    latest_nav_date: Optional[date]


@dataclass
class ParsedNavRow:
    amfi_code: int
    nav: float
    nav_date: date


# =====================================================================
# Classifiers
# =====================================================================

def extract_plan(scheme_name: str) -> str:
    """Classifies plan strictly if explicitly established by plan markers."""
    is_direct = bool(DIRECT_PLAN_REGEX.search(scheme_name))
    is_regular = bool(REGULAR_PLAN_REGEX.search(scheme_name))
    if is_direct and not is_regular:
        return "DIRECT"
    if is_regular and not is_direct:
        return "REGULAR"
    return "UNKNOWN"


def extract_option(scheme_name: str) -> str:
    """
    Classifies option strictly:
    - Explicit Growth -> GROWTH
    - Explicit IDCW Payout -> IDCW_PAYOUT
    - Explicit IDCW Reinvestment -> IDCW_REINVESTMENT
    - Generic IDCW/Dividend without payout/reinvestment marker -> UNKNOWN
    - Ambiguous or unidentified -> UNKNOWN
    """
    has_growth = bool(GROWTH_REGEX.search(scheme_name))
    has_payout = bool(IDCW_PAYOUT_REGEX.search(scheme_name))
    has_reinvest = bool(IDCW_REINVEST_REGEX.search(scheme_name))
    has_generic_idcw = bool(GENERIC_IDCW_REGEX.search(scheme_name))

    if has_growth and not (has_payout or has_reinvest or has_generic_idcw):
        return "GROWTH"
    if has_payout and not has_reinvest:
        return "IDCW_PAYOUT"
    if has_reinvest and not has_payout:
        return "IDCW_REINVESTMENT"
    # Generic IDCW without explicit payout or reinvestment establishment -> UNKNOWN
    if has_generic_idcw:
        return "UNKNOWN"
    return "UNKNOWN"


def derive_clean_name(scheme_name: str) -> str:
    """Safely derives a clean display name. Falls back strictly to scheme_name if ambiguous."""
    cleaned = CLEAN_SUFFIX_REGEX.sub("", scheme_name).strip()
    if len(cleaned) >= 8 and cleaned != scheme_name:
        return cleaned
    return scheme_name.strip()


def parse_header_taxonomy(header_inner: str) -> Tuple[str, str]:
    """
    Extracts (asset_type, category) strictly from AMFI header text.
    Never guesses. If category cannot be extracted from header, returns UNKNOWN.
    """
    asset_type = "UNKNOWN"
    category = "UNKNOWN"

    upper_text = header_inner.upper()

    if "EQUITY" in upper_text or "GROWTH" in upper_text or "ELSS" in upper_text:
        asset_type = "EQUITY"
    elif "DEBT" in upper_text or "INCOME" in upper_text or "GILT" in upper_text or "MONEY MARKET" in upper_text or "LIQUID" in upper_text:
        asset_type = "DEBT"
    elif "HYBRID" in upper_text or "BALANCED ADVANTAGE" in upper_text:
        asset_type = "HYBRID"
    elif "SOLUTION" in upper_text or "CHILDREN" in upper_text or "RETIREMENT" in upper_text or "LIFE CYCLE" in upper_text:
        asset_type = "SOLUTION_ORIENTED"
    elif "OTHER" in upper_text or "INDEX" in upper_text or "ETF" in upper_text or "FUND OF FUNDS" in upper_text or "FOF" in upper_text:
        asset_type = "OTHER"

    if "-" in header_inner:
        parts = header_inner.split("-", 1)
        sub_cat = parts[1].strip()
        if sub_cat:
            category = sub_cat

    return asset_type, category


def validate_isin(raw_isin: Optional[str]) -> Optional[str]:
    """Validates 12-char ISIN string starting with IN. Rejects invalid codes."""
    if not raw_isin:
        return None
    cleaned = raw_isin.strip().upper()
    if ISIN_REGEX.match(cleaned):
        return cleaned
    return None


def resolve_isins(
    raw_col1: str,
    raw_col2: str,
    option: str,
) -> Tuple[str, str, Optional[str], Optional[str], Optional[str]]:
    """
    Preserves raw source strings verbatim.
    Maps to semantic slots ONLY when valid ISIN and option is explicitly established.
    Returns: (raw_isin_1, raw_isin_2, isin_growth, isin_payout, isin_reinvestment)
    """
    # Raw preservation: exact verbatim values as received from source
    raw_isin_1 = raw_col1
    raw_isin_2 = raw_col2

    isin_growth = None
    isin_payout = None
    isin_reinvestment = None

    v1 = validate_isin(raw_col1)
    v2 = validate_isin(raw_col2)

    # AMFI Definition: Col 1 is "ISIN Div Payout / ISIN Growth"; Col 2 is "ISIN Div Reinvestment"
    if option == "GROWTH":
        isin_growth = v1
    elif option == "IDCW_PAYOUT":
        isin_payout = v1
        isin_reinvestment = v2
    elif option == "IDCW_REINVESTMENT":
        isin_reinvestment = v2
        isin_payout = v1
    # When option == "UNKNOWN", all semantic slots remain None.

    return raw_isin_1, raw_isin_2, isin_growth, isin_payout, isin_reinvestment


# =====================================================================
# Strict 6-Column Streaming Parser
# =====================================================================

def parse_amfi_stream(lines: List[str]) -> Tuple[List[ParsedSchemeMeta], List[ParsedNavRow]]:
    """
    Statefully parses lines of AMFI NAVAll.txt.
    ENFORCES: Exactly 6 semicolon-delimited fields for data rows.
    Rejects any row with != 6 fields, empty name, or invalid code.
    """
    schemes: List[ParsedSchemeMeta] = []
    nav_rows: List[ParsedNavRow] = []
    seen_codes_in_feed: Set[int] = set()

    current_amc = "UNKNOWN"
    current_asset_type = "UNKNOWN"
    current_category = "UNKNOWN"

    for line_num, line in enumerate(lines, start=1):
        line_str = line.strip()
        if not line_str:
            continue

        # Header skip: "Scheme Code;ISIN Div Payout/..."
        if line_str.startswith("Scheme Code;"):
            continue

        # Check for Category header
        cat_match = HEADER_CATEGORY_REGEX.match(line_str)
        if cat_match:
            header_inner = cat_match.group(2).strip()
            current_asset_type, current_category = parse_header_taxonomy(header_inner)
            continue

        # AMC Name lines contain no semicolons
        if ";" not in line_str:
            if len(line_str) > 3 and not line_str.startswith("http"):
                current_amc = line_str
            continue

        # FIELD COUNT ENFORCEMENT: Exactly 8 fields (modern AMFI) or 6 fields (legacy AMFI)
        parts = line_str.split(";")
        if len(parts) not in (6, 8):
            logger.warning(
                "Line %d: Rejected malformed row with %d fields (expected 6 or 8): '%s'",
                line_num, len(parts), line_str
            )
            continue

        raw_code = parts[0].strip()
        raw_col1 = parts[1]  # Exact verbatim preservation
        raw_col2 = parts[2]  # Exact verbatim preservation
        raw_name = parts[3].strip()

        if len(parts) == 8:
            raw_plan_field = parts[4].strip()
            raw_option_field = parts[5].strip()
            raw_nav = parts[6].strip()
            raw_date_str = parts[7].strip()

            # Dedicated AMFI fields are authoritative.
            plan = extract_plan(raw_plan_field)
            option = extract_option(raw_option_field)

            # Only consider scheme-name fallback when the dedicated source field
            # is genuinely blank. Do NOT override an unrecognized populated
            # source value with an inferred value from the scheme name.
            if not raw_plan_field:
                plan = extract_plan(raw_name)

            if not raw_option_field:
                option = extract_option(raw_name)
        else:  # len(parts) == 6
            raw_nav = parts[4].strip()
            raw_date_str = parts[5].strip()

            # Legacy feed: Plan/Option must be inferred from scheme name.
            plan = extract_plan(raw_name)
            option = extract_option(raw_name)

        # Validate Scheme Code: positive integer
        if not raw_code.isdigit():
            logger.warning("Line %d: Rejected non-numeric scheme code: '%s'", line_num, raw_code)
            continue
        amfi_code = int(raw_code)
        if amfi_code <= 0:
            logger.warning("Line %d: Rejected invalid scheme code: %d", line_num, amfi_code)
            continue

        if not raw_name:
            logger.warning("Line %d: Rejected row with missing scheme name", line_num)
            continue

        if amfi_code in seen_codes_in_feed:
            logger.warning("Line %d: Rejected duplicate scheme code in feed: %d", line_num, amfi_code)
            continue
        seen_codes_in_feed.add(amfi_code)

        # Parse NAV value
        nav_val: Optional[float] = None
        try:
            val = float(raw_nav)
            if val > 0:
                nav_val = val
        except (ValueError, TypeError):
            nav_val = None

        # Parse Date
        nav_date: Optional[date] = None
        for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                nav_date = datetime.strptime(raw_date_str, fmt).date()
                break
            except (ValueError, TypeError):
                continue

        # Classifications (Zero Guessing)
        clean_name = derive_clean_name(raw_name)

        r1, r2, isin_g, isin_p, isin_r = resolve_isins(raw_col1, raw_col2, option)

        meta = ParsedSchemeMeta(
            amfi_code=amfi_code,
            scheme_name=raw_name,
            clean_name=clean_name,
            amc_name=current_amc,
            plan=plan,
            option=option,
            asset_type=current_asset_type,
            category=current_category,
            raw_isin_1=r1,
            raw_isin_2=r2,
            isin_growth=isin_g,
            isin_payout=isin_p,
            isin_reinvestment=isin_r,
            status="ACTIVE",
            latest_nav=nav_val,
            latest_nav_date=nav_date,
        )
        schemes.append(meta)

        if nav_val is not None and nav_date is not None:
            nav_rows.append(ParsedNavRow(amfi_code=amfi_code, nav=nav_val, nav_date=nav_date))

    return schemes, nav_rows


# =====================================================================
# Anomaly Detection & Strict Validation
# =====================================================================

DEFAULT_ANOMALY_CONFIG = {
    "max_allowed_scheme_drop_pct": 2.0,   # Crash if > 2% of previous schemes drop
    "max_total_drift_pct": 10.0,          # Crash if total schemes jump or drop by > 10%
}

def validate_metadata_against_previous(
    curr_df_records: List[Dict[str, Any]],
    prev_df_records: List[Dict[str, Any]],
    config: Optional[Dict[str, float]] = None,
) -> None:
    """Relative anomaly check comparing candidate metadata against previous snapshot."""
    cfg = config or DEFAULT_ANOMALY_CONFIG
    if not prev_df_records:
        return

    prev_codes = {r["amfi_code"] for r in prev_df_records}
    curr_codes = {r["amfi_code"] for r in curr_df_records}

    dropped_codes = prev_codes - curr_codes
    drop_pct = (len(dropped_codes) / len(prev_codes)) * 100.0

    if drop_pct > cfg["max_allowed_scheme_drop_pct"]:
        raise ValueError(
            f"ANOMALY VIOLATION: {len(dropped_codes)} schemes ({drop_pct:.2f}%) dropped from metadata. "
            f"Allowed threshold is {cfg['max_allowed_scheme_drop_pct']}%. Aborting update to protect data."
        )

    drift_pct = abs(len(curr_codes) - len(prev_codes)) / len(prev_codes) * 100.0
    if drift_pct > cfg["max_total_drift_pct"]:
        raise ValueError(
            f"ANOMALY VIOLATION: Total metadata scheme count drifted by {drift_pct:.2f}% "
            f"({len(prev_codes)} -> {len(curr_codes)}). Threshold is {cfg['max_total_drift_pct']}%."
        )


def assert_metadata_integrity(records: List[Dict[str, Any]]) -> None:
    """Loud assertions enforcing all data invariants."""
    seen_codes: Set[int] = set()

    for idx, r in enumerate(records):
        code = r["amfi_code"]
        assert isinstance(code, int) and code > 0, f"Row {idx}: invalid amfi_code {code}"
        assert code not in seen_codes, f"Row {idx}: duplicate amfi_code {code}"
        seen_codes.add(code)

        # No delimiter or newline leakage
        for field in ("scheme_name", "amc_name", "category"):
            val = r.get(field) or ""
            assert ";" not in val, f"Row {idx} ({code}): unescaped semicolon in {field}: '{val}'"
            assert "\n" not in val, f"Row {idx} ({code}): newline in {field}: '{val}'"

        # No AMC name or tenure in category
        cat = r.get("category") or ""
        assert "Mutual Fund" not in cat and "AMC" not in cat, f"Row {idx} ({code}): AMC in category: '{cat}'"
        assert not re.match(r"^\d+\s*Days?$", cat, re.IGNORECASE), f"Row {idx} ({code}): tenure in category: '{cat}'"

        # Enum validity
        assert r["plan"] in {"DIRECT", "REGULAR", "UNKNOWN"}, f"Row {idx} ({code}): invalid plan: {r['plan']}"
        assert r["option"] in {"GROWTH", "IDCW_PAYOUT", "IDCW_REINVESTMENT", "UNKNOWN"}, f"Row {idx} ({code}): invalid option: {r['option']}"
        assert r["asset_type"] in {"EQUITY", "DEBT", "HYBRID", "SOLUTION_ORIENTED", "OTHER", "UNKNOWN"}, f"Row {idx} ({code}): invalid asset_type: {r['asset_type']}"
        assert r["status"] in {"ACTIVE", "UNKNOWN"}, f"Row {idx} ({code}): invalid status: {r['status']}"

        # Validated ISIN formatting
        for isin_field in ("isin_growth", "isin_payout", "isin_reinvestment"):
            isin_val = r.get(isin_field)
            if isin_val is not None:
                assert ISIN_REGEX.match(isin_val), f"Row {idx} ({code}): invalid format for {isin_field}: '{isin_val}'"

        # Date chronology
        d1, d2 = r.get("first_nav_date"), r.get("latest_nav_date")
        if d1 and d2:
            assert d1 <= d2, f"Row {idx} ({code}): chronology violation: first_nav_date ({d1}) > latest_nav_date ({d2})"
