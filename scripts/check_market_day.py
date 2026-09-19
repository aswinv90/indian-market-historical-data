"""
check_market_day.py
-------------------
Checks whether the date being updated was an official Indian Stock Market
(NSE & BSE) trading/working day.

If today (or the preceding settlement day) is a weekend or an official
trading holiday, this script exits with code 1 to safely halt the CI job.
"""

import sys
import json
import ssl
import datetime
import urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def is_market_working_day():
    ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    now_ist = datetime.datetime.now(ist)

    # When running at 7:30 AM IST, evaluate the preceding trading session (yesterday)
    # On Tuesday morning, evaluates Monday. On Monday morning, evaluates Friday.
    if now_ist.hour < 12:
        eval_date = now_ist.date() - datetime.timedelta(days=1)
        # If yesterday was Sunday, check Friday
    # Evaluate yesterday's trading session (for morning 7:30 AM IST run)
    yesterday = now_ist.date() - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime("%d-%b-%Y")

    # Fetch official exchange calendar
    url = "https://www.nseindia.com/api/holiday-master?type=trading"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://www.nseindia.com/"
    }

    muhurat_dates = []
    closed_holidays = []

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            data = json.loads(r.read())
            for h in data.get("CM", []):
                t_date = h.get("tradingDate")
                desc = str(h.get("description", ""))
                # Exchanges mark Muhurat Trading specifically with an asterisk '*' or mention Diwali Laxmi Pujan
                if "*" in desc or "muhurat" in desc.lower() or "laxmi" in desc.lower():
                    muhurat_dates.append(t_date)
                else:
                    closed_holidays.append(t_date)
    except Exception as e:
        print(f"Notice: Could not fetch real-time holiday master ({e}). Defaulting to standard calendar.")

    # 1. SPECIAL CHECK: Was yesterday a Muhurat Trading session?
    if yesterday_str in muhurat_dates:
        print(f"🎉 Special Session Detected: Yesterday ({yesterday_str}) was official Diwali Muhurat Trading!")
        return True

    # 2. If yesterday was a standard weekend, determine previous normal trading session
    if now_ist.hour < 12:
        eval_date = yesterday
        if eval_date.weekday() == 6: # Sunday
            eval_date = eval_date - datetime.timedelta(days=2) # Friday
        elif eval_date.weekday() == 5: # Saturday
            eval_date = eval_date - datetime.timedelta(days=1) # Friday
    else:
        eval_date = now_ist.date()

    eval_date_str = eval_date.strftime("%d-%b-%Y")
    print(f"Evaluating market trading status for session: {eval_date_str} ({eval_date.strftime('%A')})")

    # Check if eval_date was a closed holiday
    if eval_date_str in closed_holidays:
        print(f"❌ Market Closed: {eval_date_str} is an official exchange trading holiday.")
        return False

    # Weekend check for standard evaluation
    if eval_date.weekday() >= 5:
        print(f"❌ Market Closed: {eval_date.strftime('%A')} is a weekend.")
        return False

    print(f"✓ Confirmed: {eval_date_str} was an active Indian market working day.")
    return True

if __name__ == "__main__":
    is_open = is_market_working_day()
    if not is_open:
        print("Market holiday detected. Skipping automated update.")
        sys.exit(1)
    sys.exit(0)
