import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import requests

NIFTY50 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "HCLTECH.NS",
    "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "BAJFINANCE.NS", "WIPRO.NS",
    "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "NESTLEIND.NS", "TECHM.NS",
    "M&M.NS", "ADANIENT.NS", "ADANIPORTS.NS", "COALINDIA.NS", "JSWSTEEL.NS",
    "TVSMOTOR.NS", "TATASTEEL.NS", "BAJAJFINSV.NS", "BPCL.NS", "DRREDDY.NS",
    "CIPLA.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "INDUSINDBK.NS", "GRASIM.NS",
    "APOLLOHOSP.NS", "BRITANNIA.NS", "DIVISLAB.NS", "TATACONSUM.NS", "SBILIFE.NS",
    "HDFCLIFE.NS", "BAJAJ-AUTO.NS", "UPL.NS", "LTM.NS", "HINDALCO.NS",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}


def fetch_one(ticker):
    try:
        sym = "%5ENSEI" if ticker == "^NSEI" else ticker
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=5d"
        resp = requests.get(url, headers=HEADERS, timeout=8)
        data = resp.json()
        meta = data["chart"]["result"][0]["meta"]
        curr = meta.get("regularMarketPrice")
        prev = meta.get("previousClose") or meta.get("chartPreviousClose")
        if curr is not None and prev:
            pct = ((curr - prev) / prev) * 100
            return ticker, {"price": curr, "pct": pct}
        elif curr is not None:
            return ticker, {"price": curr, "pct": None}
        return ticker, {"price": None, "pct": None}
    except Exception:
        return ticker, {"price": None, "pct": None}


def main():
    all_tickers = ["^NSEI"] + NIFTY50
    quotes = {}
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_one, t): t for t in all_tickers}
        for future in as_completed(futures):
            ticker, value = future.result()
            quotes[ticker] = value

    out = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "index": quotes.get("^NSEI", {"price": None, "pct": None}),
        "stocks": {t: quotes[t] for t in NIFTY50},
    }

    out_path = os.path.join(os.path.dirname(__file__), "..", "data.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    loaded = sum(1 for v in out["stocks"].values() if v["price"] is not None)
    print(f"Wrote data.json — {loaded}/{len(NIFTY50)} stocks loaded")


if __name__ == "__main__":
    main()
