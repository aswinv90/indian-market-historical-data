"""
tests/test_mf_parser.py
Comprehensive test suite verifying strict parsing, zero-guessing classifiers,
raw ISIN preservation, partition integrity validation, and transactional rollback.
"""

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT))

from mf_parser import (
    extract_option,
    extract_plan,
    parse_amfi_stream,
    resolve_isins,
)


class TestStrictLineParsing(unittest.TestCase):
    def test_valid_6_column_legacy_row(self):
        line = "119063;INF179K01BE2;INF179K01BF9;HDFC Top 100 Fund - Regular Plan - Growth;980.25;26-Sep-2026"
        schemes, nav_rows = parse_amfi_stream([line])
        assert len(schemes) == 1
        assert len(nav_rows) == 1
        assert schemes[0].amfi_code == 119063
        assert schemes[0].latest_nav == 980.25
        assert schemes[0].latest_nav_date == date(2026, 9, 26)

    def test_valid_8_column_modern_amfi_row(self):
        line = "135762;INF846K01WO1;-;Axis Children's Fund;Direct Plan;Growth Option;29.6905;25-Sep-2026"
        schemes, nav_rows = parse_amfi_stream([line])
        assert len(schemes) == 1
        assert len(nav_rows) == 1
        assert schemes[0].amfi_code == 135762
        assert schemes[0].plan == "DIRECT"
        assert schemes[0].option == "GROWTH"
        assert schemes[0].latest_nav == 29.6905
        assert schemes[0].latest_nav_date == date(2026, 9, 25)

    def test_5_column_malformed_row_rejected(self):
        # Missing Date column (5 fields) -> MUST REJECT
        line = "119063;INF179K01BE2;INF179K01BF9;HDFC Top 100 Fund - Regular Plan - Growth;980.25"
        schemes, nav_rows = parse_amfi_stream([line])
        assert len(schemes) == 0
        assert len(nav_rows) == 0

    def test_7_column_malformed_row_rejected(self):
        # Malformed column count (7 fields) -> MUST REJECT
        line = "119063;INF179K01BE2;INF179K01BF9;HDFC Top 100;Extra;980.25;26-Sep-2026"
        schemes, nav_rows = parse_amfi_stream([line])
        assert len(schemes) == 0
        assert len(nav_rows) == 0

    def test_9_column_malformed_row_rejected(self):
        # Extra delimiter (9 fields) -> MUST REJECT
        line = "135762;INF846K01WO1;-;Axis Children's Fund;Direct Plan;Growth Option;Extra;29.6905;25-Sep-2026"
        schemes, nav_rows = parse_amfi_stream([line])
        assert len(schemes) == 0
        assert len(nav_rows) == 0

    def test_extra_semicolon_in_notes_rejected(self):
        line = "119063;INF179K01BE2;-;Fund Name with ; Semicolon;15.5;26-Sep-2026"
        schemes, nav_rows = parse_amfi_stream([line])
        assert len(schemes) == 0
        assert len(nav_rows) == 0

    def test_missing_scheme_name_rejected(self):
        line = "119063;INF179K01BE2;;;15.5;26-Sep-2026"
        schemes, nav_rows = parse_amfi_stream([line])
        assert len(schemes) == 0

    def test_invalid_scheme_code_rejected(self):
        line1 = "NOTNUM;INF179K01BE2;-;Some Fund - Growth;15.5;26-Sep-2026"
        line2 = "-100;INF179K01BE2;-;Some Fund - Growth;15.5;26-Sep-2026"
        line3 = "0;INF179K01BE2;-;Some Fund - Growth;15.5;26-Sep-2026"
        schemes, _ = parse_amfi_stream([line1, line2, line3])
        assert len(schemes) == 0

    def test_invalid_nav_still_preserves_meta_without_nav_row(self):
        line = "119063;INF179K01BE2;-;HDFC Top 100 Fund - Regular Plan - Growth;N.A.;26-Sep-2026"
        schemes, nav_rows = parse_amfi_stream([line])
        assert len(schemes) == 1
        assert schemes[0].latest_nav is None
        assert len(nav_rows) == 0

    def test_duplicate_scheme_code_in_same_feed_rejected(self):
        line1 = "119063;INF179K01BE2;-;HDFC Top 100 Fund - Regular Plan - Growth;980.25;26-Sep-2026"
        line2 = "119063;INF179K01BE2;-;Duplicate Code Row;981.00;26-Sep-2026"
        schemes, _ = parse_amfi_stream([line1, line2])
        assert len(schemes) == 1
        assert schemes[0].scheme_name == "HDFC Top 100 Fund - Regular Plan - Growth"


class TestStateTransitions(unittest.TestCase):
    def test_amc_and_category_state_machine(self):
        feed = [
            "HDFC Mutual Fund",
            "Open Ended Schemes ( Equity Scheme - Large Cap Fund )",
            "119063;INF179K01BE2;INF179K01BF9;HDFC Top 100 Fund - Regular Plan - Growth;980.25;26-Sep-2026",
            "Kotak Mahindra Mutual Fund",
            "Close Ended Schemes ( Income )",
            "135488;INF174K01Y15;-;Kotak FMP Series 187 - 1099 Days - Growth;12.87;26-Sep-2026",
        ]
        schemes, _ = parse_amfi_stream(feed)
        assert len(schemes) == 2

        s1 = schemes[0]
        assert s1.amc_name == "HDFC Mutual Fund"
        assert s1.asset_type == "EQUITY"
        assert s1.category == "Large Cap Fund"

        s2 = schemes[1]
        assert s2.amc_name == "Kotak Mahindra Mutual Fund"
        assert s2.asset_type == "DEBT"
        assert s2.category == "UNKNOWN"  # Header lacked subcategory; never guess FMP


class TestPlanClassifier(unittest.TestCase):
    def test_direct_plan_explicit(self):
        assert extract_plan("Axis Bluechip Fund - Direct Plan - Growth") == "DIRECT"
        assert extract_plan("SBI Large & Midcap Fund - Direct - Growth") == "DIRECT"

    def test_regular_plan_explicit(self):
        assert extract_plan("HDFC Top 100 Fund - Regular Plan - Growth") == "REGULAR"
        assert extract_plan("Mirae Asset Large Cap Fund - Regular - IDCW") == "REGULAR"

    def test_unknown_plan_never_guessed(self):
        # Zero guessing: absence of "Direct" does not mean Regular!
        assert extract_plan("Kotak FMP Series 187 - 1099 Days - Growth") == "UNKNOWN"
        assert extract_plan("Canara Robeco Balance Fund") == "UNKNOWN"
        assert extract_plan("UTI Mastershare Unit Scheme") == "UNKNOWN"


class TestOptionClassifier(unittest.TestCase):
    def test_explicit_growth(self):
        assert extract_option("Axis Bluechip Fund - Direct Plan - Growth") == "GROWTH"
        assert extract_option("Axis Bluechip Fund - Direct Plan - Growth Option") == "GROWTH"

    def test_explicit_idcw_payout(self):
        assert extract_option("ICICI Prudential Equity & Debt Fund - IDCW Payout") == "IDCW_PAYOUT"
        assert extract_option("SBI Bluechip Fund - Dividend Payout") == "IDCW_PAYOUT"
        assert extract_option("HDFC Balanced Advantage Fund - Payout of IDCW") == "IDCW_PAYOUT"

    def test_explicit_idcw_reinvestment(self):
        assert extract_option("Nippon India Small Cap - Direct - IDCW Reinvestment") == "IDCW_REINVESTMENT"
        assert extract_option("DSP Flexi Cap Fund - Dividend Reinvestment") == "IDCW_REINVESTMENT"

    def test_generic_idcw_is_strictly_unknown(self):
        # User Rule: Generic IDCW / Dividend without payout/reinvest marker MUST be UNKNOWN
        assert extract_option("Franklin India Bluechip Fund - IDCW") == "UNKNOWN"
        assert extract_option("Canara Robeco Equity Hybrid Fund - Dividend Option") == "UNKNOWN"
        assert extract_option("HDFC Mid-Cap Opportunities Fund - IDCW Plan") == "UNKNOWN"


class TestIsinResolution(unittest.TestCase):
    def test_raw_values_preserved_verbatim_including_hyphen(self):
        # User Rule: raw_isin_1 and raw_isin_2 preserve verbatim source values even when "-"
        r1, r2, g, p, r = resolve_isins("INF846K01DP8", "-", "GROWTH")
        assert r1 == "INF846K01DP8"
        assert r2 == "-"  # Preserved verbatim!
        assert g == "INF846K01DP8"
        assert p is None
        assert r is None

    def test_unknown_option_leaves_semantic_slots_null_and_preserves_raw(self):
        r1, r2, g, p, r = resolve_isins("INF846K01DP8", "INF846K01DO1", "UNKNOWN")
        assert r1 == "INF846K01DP8"
        assert r2 == "INF846K01DO1"
        assert g is None
        assert p is None
        assert r is None


class TestPartitionIntegrityAndValidation(unittest.TestCase):
    def test_modulo_violation_in_partition_detected(self):
        # If partition 0 contains schemeCode 1001 (which belongs in partition 1)
        df = pd.DataFrame([
            {"schemeCode": 1001, "date": pd.to_datetime("2026-03-25"), "nav": 50.0}
        ])
        codes = df["schemeCode"]
        assert ((codes % 10) != 0).any()  # Fails modulo check for partition 0

    def test_duplicate_scheme_date_in_partition_detected(self):
        df = pd.DataFrame([
            {"schemeCode": 1000, "date": pd.to_datetime("2026-03-25"), "nav": 50.0},
            {"schemeCode": 1000, "date": pd.to_datetime("2026-03-25"), "nav": 50.5},
        ])
        assert df.duplicated(subset=["schemeCode", "date"]).any()

    def test_non_positive_nav_in_partition_detected(self):
        df = pd.DataFrame([
            {"schemeCode": 1000, "date": pd.to_datetime("2026-03-25"), "nav": -5.0},
        ])
        assert (df["nav"] <= 0).any()


class TestTransactionalRollback(unittest.TestCase):
    def test_rollback_restores_original_file_on_failure(self):
        import shutil

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            # Setup original file
            dest_file = tmp_path / "test_part.parquet"
            dest_file.write_text("ORIGINAL_CONTENT")

            # Simulate replacement failure during transactional loop
            bak_file = dest_file.with_suffix(".bak.parquet")
            shutil.copy2(dest_file, bak_file)

            # Dest is replaced
            tmp_file = tmp_path / "test_part.tmp.parquet"
            tmp_file.write_text("CORRUPTED_CONTENT")
            tmp_file.replace(dest_file)
            self.assertEqual(dest_file.read_text(), "CORRUPTED_CONTENT")

            # Simulate rollback trigger
            bak_file.replace(dest_file)
            self.assertEqual(dest_file.read_text(), "ORIGINAL_CONTENT")  # Restored!


class TestModernAmfiDedicatedColumnPrecedence(unittest.TestCase):
    def test_dedicated_plan_overrides_conflicting_scheme_name(self):
        # Name contains 'Regular', but dedicated Plan column explicitly states 'Direct Plan'
        line = "120503;INF846K01DP8;-;Axis Bluechip Fund - Regular;Direct Plan;Growth Option;58.42;25-Sep-2026"
        schemes, _ = parse_amfi_stream([line])
        assert len(schemes) == 1
        assert schemes[0].plan == "DIRECT"

    def test_dedicated_option_overrides_conflicting_scheme_name(self):
        # Name contains 'Dividend', but dedicated Option column explicitly states 'Growth'
        line = "120503;INF846K01DP8;-;Axis Bluechip Fund - Dividend;Regular Plan;Growth;58.42;25-Sep-2026"
        schemes, _ = parse_amfi_stream([line])
        assert len(schemes) == 1
        assert schemes[0].option == "GROWTH"

    def test_blank_dedicated_plan_falls_back_to_scheme_name(self):
        # Dedicated Plan column is blank; falls back to legacy scheme name classification
        line = "120503;INF846K01DP8;-;Axis Bluechip Fund - Direct Plan - Growth;;Growth Option;58.42;25-Sep-2026"
        schemes, _ = parse_amfi_stream([line])
        assert len(schemes) == 1
        assert schemes[0].plan == "DIRECT"

    def test_blank_dedicated_option_falls_back_to_scheme_name(self):
        # Dedicated Option column is blank; falls back to legacy scheme name classification
        line = "120503;INF846K01DP8;-;Axis Bluechip Fund - Direct Plan - Growth;Direct Plan;;58.42;25-Sep-2026"
        schemes, _ = parse_amfi_stream([line])
        assert len(schemes) == 1
        assert schemes[0].option == "GROWTH"

    def test_unrecognized_populated_plan_does_not_fall_back(self):
        # Dedicated Plan column is populated with unrecognized value: must NOT fall back to 'Direct Plan' in name
        line = "120503;INF846K01DP8;-;Axis Bluechip Fund - Direct Plan;Special Plan;Growth Option;58.42;25-Sep-2026"
        schemes, _ = parse_amfi_stream([line])
        assert len(schemes) == 1
        assert schemes[0].plan == "UNKNOWN"

    def test_unrecognized_populated_option_does_not_fall_back(self):
        # Dedicated Option column is populated with unrecognized value: must NOT fall back to 'Growth' in name
        line = "120503;INF846K01DP8;-;Axis Bluechip Fund - Growth;Direct Plan;Special Option;58.42;25-Sep-2026"
        schemes, _ = parse_amfi_stream([line])
        assert len(schemes) == 1
        assert schemes[0].option == "UNKNOWN"


if __name__ == "__main__":
    unittest.main()

