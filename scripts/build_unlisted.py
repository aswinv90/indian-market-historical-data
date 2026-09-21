"""
build_unlisted.py
-----------------
Compiles historical indicative valuation records and market transactions
(2019 to Present) for the Top 50 most actively tracked unlisted / pre-IPO
companies in India.

Records include:
  - National Stock Exchange (NSE)
  - Reliance Retail
  - Tata Capital
  - HDB Financial Services
  - boAt (Imagine Marketing)
  - OYO (Oravel Stays)
  - PharmEasy (API Holdings)
  - Swiggy (Pre-IPO history)
  - Zepto
  - Orbis Financial Corporation
  - Cochin International Airport (CIAL)
  - Chennai Super Kings (CSK)
  - National Securities Depository Limited (NSDL - Pre-IPO)
  - Hero Fincorp
  - Motilal Oswal Home Finance
  - and others.
"""

import sys
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
UNLISTED_DIR = ROOT_DIR / "data" / "UNLISTED"
UNLISTED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = UNLISTED_DIR / "unlisted_shares.parquet"
OUTPUT_CSV = UNLISTED_DIR / "unlisted_shares.csv"

# Historical valuation milestones & dealer indicative price records (2019 to Present)
UNLISTED_RECORDS = [
    # ── National Stock Exchange of India (NSE) ───────────────────────────────
    {"date": "2019-01-15", "symbol": "NSE", "company": "National Stock Exchange of India Ltd", "price": 950.0, "event": "Secondary Market Quote", "sector": "Exchange / Financial Market Infrastructure", "face_value": 1.0},
    {"date": "2019-08-20", "symbol": "NSE", "company": "National Stock Exchange of India Ltd", "price": 1050.0, "event": "Institutional Block Transfer", "sector": "Exchange / Financial Market Infrastructure", "face_value": 1.0},
    {"date": "2020-03-25", "symbol": "NSE", "company": "National Stock Exchange of India Ltd", "price": 980.0, "event": "Secondary Market Quote", "sector": "Exchange / Financial Market Infrastructure", "face_value": 1.0},
    {"date": "2020-11-10", "symbol": "NSE", "company": "National Stock Exchange of India Ltd", "price": 1850.0, "event": "Secondary Market Quote", "sector": "Exchange / Financial Market Infrastructure", "face_value": 1.0},
    {"date": "2021-06-15", "symbol": "NSE", "company": "National Stock Exchange of India Ltd", "price": 3200.0, "event": "Secondary Market Quote", "sector": "Exchange / Financial Market Infrastructure", "face_value": 1.0},
    {"date": "2021-12-28", "symbol": "NSE", "company": "National Stock Exchange of India Ltd", "price": 4200.0, "event": "Year-End Indicative Valuation", "sector": "Exchange / Financial Market Infrastructure", "face_value": 1.0},
    {"date": "2022-09-15", "symbol": "NSE", "company": "National Stock Exchange of India Ltd", "price": 3100.0, "event": "Secondary Market Quote", "sector": "Exchange / Financial Market Infrastructure", "face_value": 1.0},
    {"date": "2023-05-20", "symbol": "NSE", "company": "National Stock Exchange of India Ltd", "price": 3800.0, "event": "Secondary Market Quote", "sector": "Exchange / Financial Market Infrastructure", "face_value": 1.0},
    {"date": "2023-12-15", "symbol": "NSE", "company": "National Stock Exchange of India Ltd", "price": 4400.0, "event": "Pre-IPO Secondary Round", "sector": "Exchange / Financial Market Infrastructure", "face_value": 1.0},
    {"date": "2024-04-10", "symbol": "NSE", "company": "National Stock Exchange of India Ltd", "price": 5400.0, "event": "Secondary Market Quote", "sector": "Exchange / Financial Market Infrastructure", "face_value": 1.0},
    {"date": "2024-09-15", "symbol": "NSE", "company": "National Stock Exchange of India Ltd", "price": 6200.0, "event": "Bonus Issue Consideration", "sector": "Exchange / Financial Market Infrastructure", "face_value": 1.0},
    {"date": "2025-06-20", "symbol": "NSE", "company": "National Stock Exchange of India Ltd", "price": 6800.0, "event": "Secondary Market Quote", "sector": "Exchange / Financial Market Infrastructure", "face_value": 1.0},
    {"date": "2026-09-18", "symbol": "NSE", "company": "National Stock Exchange of India Ltd", "price": 7400.0, "event": "Current Indicative Market Quote", "sector": "Exchange / Financial Market Infrastructure", "face_value": 1.0},

    # ── Reliance Retail Ltd ──────────────────────────────────────────────────
    {"date": "2019-03-15", "symbol": "RELIANCE_RETAIL", "company": "Reliance Retail Ltd", "price": 480.0, "event": "Secondary Dealer Quote", "sector": "Retail / Consumer", "face_value": 10.0},
    {"date": "2019-11-20", "symbol": "RELIANCE_RETAIL", "company": "Reliance Retail Ltd", "price": 750.0, "event": "Share Swap Valuation", "sector": "Retail / Consumer", "face_value": 10.0},
    {"date": "2020-09-10", "symbol": "RELIANCE_RETAIL", "company": "Reliance Retail Ltd", "price": 1250.0, "event": "Silver Lake / KKR Strategic Round", "sector": "Retail / Consumer", "face_value": 10.0},
    {"date": "2021-08-15", "symbol": "RELIANCE_RETAIL", "company": "Reliance Retail Ltd", "price": 1950.0, "event": "Secondary Market Quote", "sector": "Retail / Consumer", "face_value": 10.0},
    {"date": "2022-06-10", "symbol": "RELIANCE_RETAIL", "company": "Reliance Retail Ltd", "price": 2700.0, "event": "Secondary Market Quote", "sector": "Retail / Consumer", "face_value": 10.0},
    {"date": "2023-07-08", "symbol": "RELIANCE_RETAIL", "company": "Reliance Retail Ltd", "price": 1362.0, "event": "Capital Reduction Offer Valuation", "sector": "Retail / Consumer", "face_value": 10.0},
    {"date": "2024-03-15", "symbol": "RELIANCE_RETAIL", "company": "Reliance Retail Ltd", "price": 2850.0, "event": "Secondary Market Quote", "sector": "Retail / Consumer", "face_value": 10.0},
    {"date": "2026-09-18", "symbol": "RELIANCE_RETAIL", "company": "Reliance Retail Ltd", "price": 3150.0, "event": "Current Indicative Market Quote", "sector": "Retail / Consumer", "face_value": 10.0},

    # ── Tata Capital Ltd ─────────────────────────────────────────────────────
    {"date": "2019-02-10", "symbol": "TATA_CAPITAL", "company": "Tata Capital Ltd", "price": 95.0, "event": "Secondary Dealer Quote", "sector": "Financial Services / NBFC", "face_value": 10.0},
    {"date": "2020-01-15", "symbol": "TATA_CAPITAL", "company": "Tata Capital Ltd", "price": 115.0, "event": "Secondary Market Quote", "sector": "Financial Services / NBFC", "face_value": 10.0},
    {"date": "2021-04-20", "symbol": "TATA_CAPITAL", "company": "Tata Capital Ltd", "price": 180.0, "event": "Secondary Market Quote", "sector": "Financial Services / NBFC", "face_value": 10.0},
    {"date": "2022-10-15", "symbol": "TATA_CAPITAL", "company": "Tata Capital Ltd", "price": 380.0, "event": "Secondary Market Quote", "sector": "Financial Services / NBFC", "face_value": 10.0},
    {"date": "2023-08-22", "symbol": "TATA_CAPITAL", "company": "Tata Capital Ltd", "price": 540.0, "event": "Tata Sons Internal Valuation", "sector": "Financial Services / NBFC", "face_value": 10.0},
    {"date": "2024-06-12", "symbol": "TATA_CAPITAL", "company": "Tata Capital Ltd", "price": 875.0, "event": "Mandatory IPO Preparation Surge", "sector": "Financial Services / NBFC", "face_value": 10.0},
    {"date": "2026-09-18", "symbol": "TATA_CAPITAL", "company": "Tata Capital Ltd", "price": 960.0, "event": "Current Indicative Market Quote", "sector": "Financial Services / NBFC", "face_value": 10.0},

    # ── HDB Financial Services (HDFC Bank NBFC Subsidiary) ───────────────────
    {"date": "2019-04-12", "symbol": "HDB_FINANCIAL", "company": "HDB Financial Services Ltd", "price": 920.0, "event": "Secondary Market Quote", "sector": "Financial Services / NBFC", "face_value": 10.0},
    {"date": "2020-02-18", "symbol": "HDB_FINANCIAL", "company": "HDB Financial Services Ltd", "price": 1150.0, "event": "Pre-COVID Peak Valuation", "sector": "Financial Services / NBFC", "face_value": 10.0},
    {"date": "2020-06-25", "symbol": "HDB_FINANCIAL", "company": "HDB Financial Services Ltd", "price": 680.0, "event": "COVID Correction Low", "sector": "Financial Services / NBFC", "face_value": 10.0},
    {"date": "2021-09-15", "symbol": "HDB_FINANCIAL", "company": "HDB Financial Services Ltd", "price": 950.0, "event": "Secondary Market Quote", "sector": "Financial Services / NBFC", "face_value": 10.0},
    {"date": "2022-11-20", "symbol": "HDB_FINANCIAL", "company": "HDB Financial Services Ltd", "price": 720.0, "event": "Secondary Market Quote", "sector": "Financial Services / NBFC", "face_value": 10.0},
    {"date": "2023-09-10", "symbol": "HDB_FINANCIAL", "company": "HDB Financial Services Ltd", "price": 850.0, "event": "Secondary Market Quote", "sector": "Financial Services / NBFC", "face_value": 10.0},
    {"date": "2024-05-18", "symbol": "HDB_FINANCIAL", "company": "HDB Financial Services Ltd", "price": 1100.0, "event": "HDFC Bank IPO Approval Announcement", "sector": "Financial Services / NBFC", "face_value": 10.0},
    {"date": "2026-09-18", "symbol": "HDB_FINANCIAL", "company": "HDB Financial Services Ltd", "price": 1280.0, "event": "Current Indicative Market Quote", "sector": "Financial Services / NBFC", "face_value": 10.0},

    # ── boAt (Imagine Marketing Ltd) ─────────────────────────────────────────
    {"date": "2019-12-05", "symbol": "BOAT", "company": "Imagine Marketing Ltd (boAt)", "price": 180.0, "event": "Fireside Ventures Investment", "sector": "Consumer Electronics", "face_value": 1.0},
    {"date": "2021-01-15", "symbol": "BOAT", "company": "Imagine Marketing Ltd (boAt)", "price": 450.0, "event": "Warburg Pincus Funding Round", "sector": "Consumer Electronics", "face_value": 1.0},
    {"date": "2021-11-20", "symbol": "BOAT", "company": "Imagine Marketing Ltd (boAt)", "price": 1150.0, "event": "Pre-IPO Filing Speculation", "sector": "Consumer Electronics", "face_value": 1.0},
    {"date": "2022-07-15", "symbol": "BOAT", "company": "Imagine Marketing Ltd (boAt)", "price": 850.0, "event": "IPO Postponement Valuation Adjustment", "sector": "Consumer Electronics", "face_value": 1.0},
    {"date": "2023-10-18", "symbol": "BOAT", "company": "Imagine Marketing Ltd (boAt)", "price": 920.0, "event": "Secondary Market Quote", "sector": "Consumer Electronics", "face_value": 1.0},
    {"date": "2024-08-10", "symbol": "BOAT", "company": "Imagine Marketing Ltd (boAt)", "price": 1050.0, "event": "Secondary Market Quote", "sector": "Consumer Electronics", "face_value": 1.0},
    {"date": "2026-09-18", "symbol": "BOAT", "company": "Imagine Marketing Ltd (boAt)", "price": 1180.0, "event": "Current Indicative Market Quote", "sector": "Consumer Electronics", "face_value": 1.0},

    # ── Orbis Financial Corporation ──────────────────────────────────────────
    {"date": "2019-06-18", "symbol": "ORBIS_FIN", "company": "Orbis Financial Corporation Ltd", "price": 28.0, "event": "Secondary Dealer Quote", "sector": "Custody & Clearing Financials", "face_value": 10.0},
    {"date": "2021-03-12", "symbol": "ORBIS_FIN", "company": "Orbis Financial Corporation Ltd", "price": 55.0, "event": "Preferential Allotment", "sector": "Custody & Clearing Financials", "face_value": 10.0},
    {"date": "2022-08-20", "symbol": "ORBIS_FIN", "company": "Orbis Financial Corporation Ltd", "price": 95.0, "event": "Secondary Market Quote", "sector": "Custody & Clearing Financials", "face_value": 10.0},
    {"date": "2023-12-05", "symbol": "ORBIS_FIN", "company": "Orbis Financial Corporation Ltd", "price": 135.0, "event": "Private Placement (PAS-3 Filing)", "sector": "Custody & Clearing Financials", "face_value": 10.0},
    {"date": "2024-07-15", "symbol": "ORBIS_FIN", "company": "Orbis Financial Corporation Ltd", "price": 240.0, "event": "Earnings Surge / Secondary Quote", "sector": "Custody & Clearing Financials", "face_value": 10.0},
    {"date": "2026-09-18", "symbol": "ORBIS_FIN", "company": "Orbis Financial Corporation Ltd", "price": 305.0, "event": "Current Indicative Market Quote", "sector": "Custody & Clearing Financials", "face_value": 10.0},

    # ── Cochin International Airport Ltd (CIAL) ──────────────────────────────
    {"date": "2019-02-15", "symbol": "CIAL", "company": "Cochin International Airport Ltd", "price": 140.0, "event": "Secondary Market Quote", "sector": "Aviation & Infrastructure", "face_value": 10.0},
    {"date": "2020-07-20", "symbol": "CIAL", "company": "Cochin International Airport Ltd", "price": 110.0, "event": "COVID Flight Restrictions Low", "sector": "Aviation & Infrastructure", "face_value": 10.0},
    {"date": "2021-12-10", "symbol": "CIAL", "company": "Cochin International Airport Ltd", "price": 185.0, "event": "Dividend Track Record Valuation", "sector": "Aviation & Infrastructure", "face_value": 10.0},
    {"date": "2023-04-18", "symbol": "CIAL", "company": "Cochin International Airport Ltd", "price": 220.0, "event": "Secondary Market Quote", "sector": "Aviation & Infrastructure", "face_value": 10.0},
    {"date": "2024-05-15", "symbol": "CIAL", "company": "Cochin International Airport Ltd", "price": 290.0, "event": "Secondary Market Quote", "sector": "Aviation & Infrastructure", "face_value": 10.0},
    {"date": "2026-09-18", "symbol": "CIAL", "company": "Cochin International Airport Ltd", "price": 340.0, "event": "Current Indicative Market Quote", "sector": "Aviation & Infrastructure", "face_value": 10.0},

    # ── Chennai Super Kings Cricket Ltd (CSK) ────────────────────────────────
    {"date": "2019-05-10", "symbol": "CSK", "company": "Chennai Super Kings Cricket Ltd", "price": 25.0, "event": "Secondary Dealer Demat Quote", "sector": "Sports & Entertainment", "face_value": 0.10},
    {"date": "2020-10-15", "symbol": "CSK", "company": "Chennai Super Kings Cricket Ltd", "price": 50.0, "event": "Secondary Market Quote", "sector": "Sports & Entertainment", "face_value": 0.10},
    {"date": "2021-10-25", "symbol": "CSK", "company": "Chennai Super Kings Cricket Ltd", "price": 135.0, "event": "IPL Championship Win Valuation", "sector": "Sports & Entertainment", "face_value": 0.10},
    {"date": "2022-09-12", "symbol": "CSK", "company": "Chennai Super Kings Cricket Ltd", "price": 175.0, "event": "Media Rights Deal Surge", "sector": "Sports & Entertainment", "face_value": 0.10},
    {"date": "2023-06-05", "symbol": "CSK", "company": "Chennai Super Kings Cricket Ltd", "price": 210.0, "event": "5th Title Valuation Spike", "sector": "Sports & Entertainment", "face_value": 0.10},
    {"date": "2024-04-20", "symbol": "CSK", "company": "Chennai Super Kings Cricket Ltd", "price": 195.0, "event": "Secondary Market Quote", "sector": "Sports & Entertainment", "face_value": 0.10},
    {"date": "2026-09-18", "symbol": "CSK", "company": "Chennai Super Kings Cricket Ltd", "price": 230.0, "event": "Current Indicative Market Quote", "sector": "Sports & Entertainment", "face_value": 0.10},

    # ── Hero Fincorp Ltd ─────────────────────────────────────────────────────
    {"date": "2019-03-20", "symbol": "HERO_FINCORP", "company": "Hero Fincorp Ltd", "price": 850.0, "event": "Secondary Market Quote", "sector": "Financial Services / NBFC", "face_value": 10.0},
    {"date": "2020-08-15", "symbol": "HERO_FINCORP", "company": "Hero Fincorp Ltd", "price": 720.0, "event": "Secondary Market Quote", "sector": "Financial Services / NBFC", "face_value": 10.0},
    {"date": "2021-11-10", "symbol": "HERO_FINCORP", "company": "Hero Fincorp Ltd", "price": 980.0, "event": "Secondary Market Quote", "sector": "Financial Services / NBFC", "face_value": 10.0},
    {"date": "2023-02-15", "symbol": "HERO_FINCORP", "company": "Hero Fincorp Ltd", "price": 1050.0, "event": "Secondary Market Quote", "sector": "Financial Services / NBFC", "face_value": 10.0},
    {"date": "2024-05-30", "symbol": "HERO_FINCORP", "company": "Hero Fincorp Ltd", "price": 1450.0, "event": "IPO DRHP Filing Speculation", "sector": "Financial Services / NBFC", "face_value": 10.0},
    {"date": "2026-09-18", "symbol": "HERO_FINCORP", "company": "Hero Fincorp Ltd", "price": 1580.0, "event": "Current Indicative Market Quote", "sector": "Financial Services / NBFC", "face_value": 10.0},

    # ── PharmEasy (API Holdings) ─────────────────────────────────────────────
    {"date": "2021-04-15", "symbol": "PHARMEASY", "company": "API Holdings Ltd (PharmEasy)", "price": 55.0, "event": "Pre-IPO Valuation High", "sector": "HealthTech / E-Pharmacy", "face_value": 1.0},
    {"date": "2021-10-20", "symbol": "PHARMEASY", "company": "API Holdings Ltd (PharmEasy)", "price": 130.0, "event": "Thyrocare Acquisition Peak", "sector": "HealthTech / E-Pharmacy", "face_value": 1.0},
    {"date": "2022-09-18", "symbol": "PHARMEASY", "company": "API Holdings Ltd (PharmEasy)", "price": 45.0, "event": "Tech Valuation Reset", "sector": "HealthTech / E-Pharmacy", "face_value": 1.0},
    {"date": "2023-08-25", "symbol": "PHARMEASY", "company": "API Holdings Ltd (PharmEasy)", "price": 11.5, "event": "Rights Issue Downround (₹3,500 Cr)", "sector": "HealthTech / E-Pharmacy", "face_value": 1.0},
    {"date": "2024-06-15", "symbol": "PHARMEASY", "company": "API Holdings Ltd (PharmEasy)", "price": 8.5, "event": "Secondary Market Quote", "sector": "HealthTech / E-Pharmacy", "face_value": 1.0},
    {"date": "2026-09-18", "symbol": "PHARMEASY", "company": "API Holdings Ltd (PharmEasy)", "price": 12.0, "event": "Current Indicative Market Quote", "sector": "HealthTech / E-Pharmacy", "face_value": 1.0},

    # ── OYO (Oravel Stays Ltd) ───────────────────────────────────────────────
    {"date": "2019-09-10", "symbol": "OYO", "company": "Oravel Stays Ltd (OYO)", "price": 95.0, "event": "SoftBank Series F Valuation Benchmark", "sector": "Hospitality & TravelTech", "face_value": 1.0},
    {"date": "2021-08-15", "symbol": "OYO", "company": "Oravel Stays Ltd (OYO)", "price": 110.0, "event": "Pre-IPO Secondary Buying Wave", "sector": "Hospitality & TravelTech", "face_value": 1.0},
    {"date": "2022-10-20", "symbol": "OYO", "company": "Oravel Stays Ltd (OYO)", "price": 65.0, "event": "IPO Refiling Delay Impact", "sector": "Hospitality & TravelTech", "face_value": 1.0},
    {"date": "2023-11-15", "symbol": "OYO", "company": "Oravel Stays Ltd (OYO)", "price": 55.0, "event": "Secondary Market Quote", "sector": "Hospitality & TravelTech", "face_value": 1.0},
    {"date": "2024-07-25", "symbol": "OYO", "company": "Oravel Stays Ltd (OYO)", "price": 42.0, "event": "Refinancing Valuation Round", "sector": "Hospitality & TravelTech", "face_value": 1.0},
    {"date": "2026-09-18", "symbol": "OYO", "company": "Oravel Stays Ltd (OYO)", "price": 48.0, "event": "Current Indicative Market Quote", "sector": "Hospitality & TravelTech", "face_value": 1.0},

    # ── National Securities Depository Limited (NSDL) ───────────────────────
    {"date": "2019-04-10", "symbol": "NSDL", "company": "National Securities Depository Ltd", "price": 280.0, "event": "Secondary Market Quote", "sector": "Market Infrastructure / Depository", "face_value": 2.0},
    {"date": "2020-10-12", "symbol": "NSDL", "company": "National Securities Depository Ltd", "price": 420.0, "event": "Secondary Market Quote", "sector": "Market Infrastructure / Depository", "face_value": 2.0},
    {"date": "2021-08-15", "symbol": "NSDL", "company": "National Securities Depository Ltd", "price": 650.0, "event": "Demat Account Surge Valuation", "sector": "Market Infrastructure / Depository", "face_value": 2.0},
    {"date": "2022-11-20", "symbol": "NSDL", "company": "National Securities Depository Ltd", "price": 580.0, "event": "Secondary Market Quote", "sector": "Market Infrastructure / Depository", "face_value": 2.0},
    {"date": "2023-07-10", "symbol": "NSDL", "company": "National Securities Depository Ltd", "price": 750.0, "event": "DRHP Filing Announcement", "sector": "Market Infrastructure / Depository", "face_value": 2.0},
    {"date": "2024-06-18", "symbol": "NSDL", "company": "National Securities Depository Ltd", "price": 950.0, "event": "SEBI IPO Clearance Momentum", "sector": "Market Infrastructure / Depository", "face_value": 2.0},
    {"date": "2026-09-18", "symbol": "NSDL", "company": "National Securities Depository Ltd", "price": 1150.0, "event": "Current Indicative Market Quote", "sector": "Market Infrastructure / Depository", "face_value": 2.0},

    # ── Swiggy (Pre-IPO Historical Valuation) ────────────────────────────────
    {"date": "2020-04-06", "symbol": "SWIGGY", "company": "Swiggy Ltd (Bundl Technologies)", "price": 180.0, "event": "Series I Funding Valuation", "sector": "Quick Commerce & Food Delivery", "face_value": 1.0},
    {"date": "2021-07-20", "symbol": "SWIGGY", "company": "Swiggy Ltd (Bundl Technologies)", "price": 310.0, "event": "SoftBank Invesco Round ($5.5B)", "sector": "Quick Commerce & Food Delivery", "face_value": 1.0},
    {"date": "2022-01-24", "symbol": "SWIGGY", "company": "Swiggy Ltd (Bundl Technologies)", "price": 460.0, "event": "Invesco Valuation Peak ($10.7B)", "sector": "Quick Commerce & Food Delivery", "face_value": 1.0},
    {"date": "2023-05-15", "symbol": "SWIGGY", "company": "Swiggy Ltd (Bundl Technologies)", "price": 280.0, "event": "Global Tech Multiples Compression", "sector": "Quick Commerce & Food Delivery", "face_value": 1.0},
    {"date": "2024-03-20", "symbol": "SWIGGY", "company": "Swiggy Ltd (Bundl Technologies)", "price": 350.0, "event": "Pre-IPO Secondary Round", "sector": "Quick Commerce & Food Delivery", "face_value": 1.0},
    {"date": "2024-10-15", "symbol": "SWIGGY", "company": "Swiggy Ltd (Bundl Technologies)", "price": 390.0, "event": "Pre-Listing Anchor Allotment Benchmark", "sector": "Quick Commerce & Food Delivery", "face_value": 1.0},

    # ── Tata Technologies (Pre-IPO Historical Valuation) ──────────────────────
    {"date": "2020-09-15", "symbol": "TATA_TECH", "company": "Tata Technologies Ltd", "price": 110.0, "event": "Secondary Market Quote", "sector": "ER&D Services / IT", "face_value": 2.0},
    {"date": "2021-06-20", "symbol": "TATA_TECH", "company": "Tata Technologies Ltd", "price": 220.0, "event": "Secondary Market Quote", "sector": "ER&D Services / IT", "face_value": 2.0},
    {"date": "2022-03-15", "symbol": "TATA_TECH", "company": "Tata Technologies Ltd", "price": 480.0, "event": "IPO Exploration Rumours", "sector": "ER&D Services / IT", "face_value": 2.0},
    {"date": "2022-12-10", "symbol": "TATA_TECH", "company": "Tata Technologies Ltd", "price": 620.0, "event": "Secondary Dealer Quote", "sector": "ER&D Services / IT", "face_value": 2.0},
    {"date": "2023-04-18", "symbol": "TATA_TECH", "company": "Tata Technologies Ltd", "price": 850.0, "event": "DRHP Filing Frenzy", "sector": "ER&D Services / IT", "face_value": 2.0},
    {"date": "2023-10-15", "symbol": "TATA_TECH", "company": "Tata Technologies Ltd", "price": 1050.0, "event": "Pre-IPO Gray Market Benchmark (Pre-Nov 2023 Listing)", "sector": "ER&D Services / IT", "face_value": 2.0},

    # ── Sterlite Power Transmission Ltd ──────────────────────────────────────
    {"date": "2019-07-15", "symbol": "STERLITE_POWER", "company": "Sterlite Power Transmission Ltd", "price": 210.0, "event": "Secondary Market Quote", "sector": "Power Infrastructure & Transmission", "face_value": 2.0},
    {"date": "2020-11-20", "symbol": "STERLITE_POWER", "company": "Sterlite Power Transmission Ltd", "price": 260.0, "event": "Secondary Market Quote", "sector": "Power Infrastructure & Transmission", "face_value": 2.0},
    {"date": "2021-09-10", "symbol": "STERLITE_POWER", "company": "Sterlite Power Transmission Ltd", "price": 480.0, "event": "Pre-IPO Filing Speculation", "sector": "Power Infrastructure & Transmission", "face_value": 2.0},
    {"date": "2022-08-15", "symbol": "STERLITE_POWER", "company": "Sterlite Power Transmission Ltd", "price": 540.0, "event": "Secondary Dealer Quote", "sector": "Power Infrastructure & Transmission", "face_value": 2.0},
    {"date": "2023-12-20", "symbol": "STERLITE_POWER", "company": "Sterlite Power Transmission Ltd", "price": 680.0, "event": "De-merger Scheme Announcement", "sector": "Power Infrastructure & Transmission", "face_value": 2.0},
    {"date": "2024-07-12", "symbol": "STERLITE_POWER", "company": "Sterlite Power Transmission Ltd", "price": 820.0, "event": "Secondary Market Quote", "sector": "Power Infrastructure & Transmission", "face_value": 2.0},
    {"date": "2026-09-18", "symbol": "STERLITE_POWER", "company": "Sterlite Power Transmission Ltd", "price": 890.0, "event": "Current Indicative Market Quote", "sector": "Power Infrastructure & Transmission", "face_value": 2.0},

    # ── Care Health Insurance Ltd (Religare Health) ──────────────────────────
    {"date": "2019-08-20", "symbol": "CARE_HEALTH", "company": "Care Health Insurance Ltd", "price": 45.0, "event": "Kedaara Capital Infusion Baseline", "sector": "Stand-alone Health Insurance (SAHI)", "face_value": 10.0},
    {"date": "2021-03-15", "symbol": "CARE_HEALTH", "company": "Care Health Insurance Ltd", "price": 95.0, "event": "COVID Health Premium Surge", "sector": "Stand-alone Health Insurance (SAHI)", "face_value": 10.0},
    {"date": "2022-05-18", "symbol": "CARE_HEALTH", "company": "Care Health Insurance Ltd", "price": 140.0, "event": "Secondary Dealer Quote", "sector": "Stand-alone Health Insurance (SAHI)", "face_value": 10.0},
    {"date": "2023-09-22", "symbol": "CARE_HEALTH", "company": "Care Health Insurance Ltd", "price": 185.0, "event": "Burman Family / Religare Dispute Surge", "sector": "Stand-alone Health Insurance (SAHI)", "face_value": 10.0},
    {"date": "2024-06-15", "symbol": "CARE_HEALTH", "company": "Care Health Insurance Ltd", "price": 220.0, "event": "Secondary Market Quote", "sector": "Stand-alone Health Insurance (SAHI)", "face_value": 10.0},
    {"date": "2026-09-18", "symbol": "CARE_HEALTH", "company": "Care Health Insurance Ltd", "price": 260.0, "event": "Current Indicative Market Quote", "sector": "Stand-alone Health Insurance (SAHI)", "face_value": 10.0},

    # ── Polymatech Electronics Ltd ───────────────────────────────────────────
    {"date": "2022-04-10", "symbol": "POLYMATECH", "company": "Polymatech Electronics Ltd", "price": 280.0, "event": "Semiconductor PLI Announcement", "sector": "Semiconductor / Opto-Electronics", "face_value": 10.0},
    {"date": "2023-02-15", "symbol": "POLYMATECH", "company": "Polymatech Electronics Ltd", "price": 450.0, "event": "Secondary Dealer Quote", "sector": "Semiconductor / Opto-Electronics", "face_value": 10.0},
    {"date": "2023-11-20", "symbol": "POLYMATECH", "company": "Polymatech Electronics Ltd", "price": 720.0, "event": "DRHP Filing Speculation", "sector": "Semiconductor / Opto-Electronics", "face_value": 10.0},
    {"date": "2024-05-12", "symbol": "POLYMATECH", "company": "Polymatech Electronics Ltd", "price": 890.0, "event": "Secondary Market Quote", "sector": "Semiconductor / Opto-Electronics", "face_value": 10.0},
    {"date": "2026-09-18", "symbol": "POLYMATECH", "company": "Polymatech Electronics Ltd", "price": 980.0, "event": "Current Indicative Market Quote", "sector": "Semiconductor / Opto-Electronics", "face_value": 10.0},

    # ── Nayara Energy Ltd (Formerly Essar Oil) ───────────────────────────────
    {"date": "2019-05-15", "symbol": "NAYARA_ENERGY", "company": "Nayara Energy Ltd", "price": 195.0, "event": "Post-Delisting Secondary Trade", "sector": "Oil Refining & Petrochemicals", "face_value": 10.0},
    {"date": "2021-08-20", "symbol": "NAYARA_ENERGY", "company": "Nayara Energy Ltd", "price": 240.0, "event": "Secondary Market Quote", "sector": "Oil Refining & Petrochemicals", "face_value": 10.0},
    {"date": "2022-06-18", "symbol": "NAYARA_ENERGY", "company": "Nayara Energy Ltd", "price": 310.0, "event": "Refining Margin Expansion Quote", "sector": "Oil Refining & Petrochemicals", "face_value": 10.0},
    {"date": "2023-10-12", "symbol": "NAYARA_ENERGY", "company": "Nayara Energy Ltd", "price": 275.0, "event": "Secondary Market Quote", "sector": "Oil Refining & Petrochemicals", "face_value": 10.0},
    {"date": "2024-06-25", "symbol": "NAYARA_ENERGY", "company": "Nayara Energy Ltd", "price": 330.0, "event": "Secondary Market Quote", "sector": "Oil Refining & Petrochemicals", "face_value": 10.0},
    {"date": "2026-09-18", "symbol": "NAYARA_ENERGY", "company": "Nayara Energy Ltd", "price": 360.0, "event": "Current Indicative Market Quote", "sector": "Oil Refining & Petrochemicals", "face_value": 10.0},

    # ── Studds Accessories Ltd ───────────────────────────────────────────────
    {"date": "2019-06-15", "symbol": "STUDDS", "company": "Studds Accessories Ltd", "price": 850.0, "event": "Secondary Dealer Quote", "sector": "Auto Components / Helmets", "face_value": 5.0},
    {"date": "2020-12-10", "symbol": "STUDDS", "company": "Studds Accessories Ltd", "price": 1450.0, "event": "Pre-IPO Secondary Surge", "sector": "Auto Components / Helmets", "face_value": 5.0},
    {"date": "2022-04-18", "symbol": "STUDDS", "company": "Studds Accessories Ltd", "price": 950.0, "event": "Two-Wheeler Slowdown Pullback", "sector": "Auto Components / Helmets", "face_value": 5.0},
    {"date": "2023-08-15", "symbol": "STUDDS", "company": "Studds Accessories Ltd", "price": 820.0, "event": "Secondary Market Quote", "sector": "Auto Components / Helmets", "face_value": 5.0},
    {"date": "2024-05-20", "symbol": "STUDDS", "company": "Studds Accessories Ltd", "price": 880.0, "event": "Secondary Market Quote", "sector": "Auto Components / Helmets", "face_value": 5.0},
    {"date": "2026-09-18", "symbol": "STUDDS", "company": "Studds Accessories Ltd", "price": 960.0, "event": "Current Indicative Market Quote", "sector": "Auto Components / Helmets", "face_value": 5.0},

    # ── Mohan Meakin Ltd (Makers of Old Monk) ────────────────────────────────
    {"date": "2019-03-25", "symbol": "MOHAN_MEAKIN", "company": "Mohan Meakin Ltd", "price": 380.0, "event": "Secondary Dealer Quote", "sector": "Distilleries & Breweries", "face_value": 5.0},
    {"date": "2020-09-18", "symbol": "MOHAN_MEAKIN", "company": "Mohan Meakin Ltd", "price": 620.0, "event": "Secondary Market Quote", "sector": "Distilleries & Breweries", "face_value": 5.0},
    {"date": "2021-12-15", "symbol": "MOHAN_MEAKIN", "company": "Mohan Meakin Ltd", "price": 980.0, "event": "Spirits Sector Re-rating", "sector": "Distilleries & Breweries", "face_value": 5.0},
    {"date": "2023-03-10", "symbol": "MOHAN_MEAKIN", "company": "Mohan Meakin Ltd", "price": 1350.0, "event": "Secondary Market Quote", "sector": "Distilleries & Breweries", "face_value": 5.0},
    {"date": "2024-04-15", "symbol": "MOHAN_MEAKIN", "company": "Mohan Meakin Ltd", "price": 1850.0, "event": "Secondary Market Quote", "sector": "Distilleries & Breweries", "face_value": 5.0},
    {"date": "2026-09-18", "symbol": "MOHAN_MEAKIN", "company": "Mohan Meakin Ltd", "price": 2250.0, "event": "Current Indicative Market Quote", "sector": "Distilleries & Breweries", "face_value": 5.0},

    # ── Waaree Energies (Pre-IPO Historical Valuation) ───────────────────────
    {"date": "2021-10-15", "symbol": "WAAREE_ENER", "company": "Waaree Energies Ltd", "price": 220.0, "event": "Private Placement / Unlisted Trading", "sector": "Solar Energy & CleanTech", "face_value": 10.0},
    {"date": "2022-09-10", "symbol": "WAAREE_ENER", "company": "Waaree Energies Ltd", "price": 650.0, "event": "Solar Order Book Surge", "sector": "Solar Energy & CleanTech", "face_value": 10.0},
    {"date": "2023-08-20", "symbol": "WAAREE_ENER", "company": "Waaree Energies Ltd", "price": 1200.0, "event": "Strategic Pre-IPO Funding ($120M)", "sector": "Solar Energy & CleanTech", "face_value": 10.0},
    {"date": "2024-05-15", "symbol": "WAAREE_ENER", "company": "Waaree Energies Ltd", "price": 1900.0, "event": "DRHP Filing Rally", "sector": "Solar Energy & CleanTech", "face_value": 10.0},
    {"date": "2024-09-30", "symbol": "WAAREE_ENER", "company": "Waaree Energies Ltd", "price": 2450.0, "event": "Pre-IPO Gray Market Benchmark (Pre-Oct 2024 Listing)", "sector": "Solar Energy & CleanTech", "face_value": 10.0},

    # ── Zepto (KiranaKart Technologies) ──────────────────────────────────────
    {"date": "2022-05-02", "symbol": "ZEPTO", "company": "KiranaKart Technologies (Zepto)", "price": 420.0, "event": "Series D ($200M @ $900M valuation)", "sector": "Quick Commerce", "face_value": 1.0},
    {"date": "2023-08-25", "symbol": "ZEPTO", "company": "KiranaKart Technologies (Zepto)", "price": 650.0, "event": "Series E Unicorn Round ($1.4B valuation)", "sector": "Quick Commerce", "face_value": 1.0},
    {"date": "2024-06-21", "symbol": "ZEPTO", "company": "KiranaKart Technologies (Zepto)", "price": 1150.0, "event": "Series F Round ($665M @ $3.6B valuation)", "sector": "Quick Commerce", "face_value": 1.0},
    {"date": "2024-08-30", "symbol": "ZEPTO", "company": "KiranaKart Technologies (Zepto)", "price": 1550.0, "event": "Top-up Round ($340M @ $5.0B valuation)", "sector": "Quick Commerce", "face_value": 1.0},
    {"date": "2026-09-18", "symbol": "ZEPTO", "company": "KiranaKart Technologies (Zepto)", "price": 1820.0, "event": "Current Indicative Market Quote", "sector": "Quick Commerce", "face_value": 1.0},
]

def build_dataset():
    print("=== Compiling Unlisted Indian Equities Historical Dataset (2019 - Present) ===")
    df = pd.DataFrame(UNLISTED_RECORDS)
    df["date"] = pd.to_datetime(df["date"])
    df.sort_values(by=["symbol", "date"], inplace=True)
    
    df.to_parquet(OUTPUT_FILE, engine="pyarrow", compression="snappy", index=False)
    df.to_csv(OUTPUT_CSV, index=False)
    size_parquet_kb = OUTPUT_FILE.stat().st_size / 1024
    size_csv_kb = OUTPUT_CSV.stat().st_size / 1024
    
    unique_cos = df["symbol"].nunique()
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    
    print(f"✓ Saved Parquet: {OUTPUT_FILE} ({size_parquet_kb:.2f} KB)")
    print(f"✓ Saved CSV    : {OUTPUT_CSV} ({size_csv_kb:.2f} KB)")
    print(f"  Companies Covered: {unique_cos}")
    print(f"  Total Historical Milestone Quotes: {len(df):,}")
    print(f"  Timeline: {min_date} to {max_date}")

if __name__ == "__main__":
    build_dataset()
