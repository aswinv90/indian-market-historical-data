"""
check_market_day.py
-------------------
Checks whether the date being updated was an official Indian Stock Market
(NSE & BSE) trading/working day.

If today (or the preceding settlement day) is a weekend or an official
trading holiday, this script exits with code 1 to safely halt the CI job.
"""

import os
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

    # When running at 9:00 PM IST (21:00 IST), we evaluate today's trading session.
    # Today's date in IST:
    eval_date = now_ist.date()
    eval_date_str = eval_date.strftime("%d-%b-%Y")

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

    # 1. SPECIAL CHECK: Was today a Muhurat Trading session (even on weekend)?
    if eval_date_str in muhurat_dates:
        print(f"🎉 Special Session Detected: Today ({eval_date_str}) was official Diwali Muhurat Trading!")
        return True

    # 2. Check if today was a declared exchange holiday
    if eval_date_str in closed_holidays:
        print(f"❌ Market Closed: Today ({eval_date_str}) is an official exchange trading holiday.")
        return False

    # 3. Check if today is a weekend
    if eval_date.weekday() >= 5:
        print(f"❌ Market Closed: Today ({eval_date.strftime('%A')}) is a weekend.")
        return False

    print(f"✓ Confirmed: Today ({eval_date_str}, {eval_date.strftime('%A')}) was an active Indian market working day.")
    return True

if __name__ == "__main__":
    is_open = is_market_working_day()
    
    # Export to GitHub Actions environment output if running in CI
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a") as f:
            f.write(f"is_open={'true' if is_open else 'false'}\n")
            
    if not is_open:
        print("Market closed / holiday detected. Remaining steps will be skipped cleanly.")
    sys.exit(0)
