# Foreign Exchanges: Simplest Integration Plan (No new API keys)

This project already supports foreign tickers end‑to‑end using Yahoo Finance symbol suffixes and the existing watchlist + analysis flows. The easiest way to add foreign exchanges is to add exchange‑qualified symbols; no new provider (e.g., Marketstack) is required.

---

## 1) Add Foreign Symbols to the Watchlist (no code changes)

Use Yahoo Finance suffixes and add symbols to the database‑backed watchlist via the existing API:

Examples
- LSE (.L): `HSBA.L`, `BP.L`, `VOD.L`
- TSX (.TO): `SHOP.TO`
- Tokyo (.T): `7203.T`
- HKEX (.HK): `0005.HK`

API call (app running on port 5001):
```bash
curl -X POST http://localhost:5001/api/watchlist/config \
  -H "Content-Type: application/json" \
  -d '{"action":"add","symbol":"HSBA.L","type":"stock"}'
```

You can then refresh Opportunities (Watchlist mode) or analyze a symbol directly from the Dashboard.

---

## 2) Data Flow Compatibility (what already works)

- News: Pulled from Alpha Vantage, Reddit, Finnhub and Yahoo RSS; these are symbol‑agnostic and work with foreign suffixes.
- Historical data: Uses `yfinance` (Yahoo) and works with foreign suffixes.
- Current price: Uses Alpha Vantage "GLOBAL_QUOTE" by default. Many foreign equities work; if a specific symbol has no quote via Alpha Vantage, analysis still runs but price may be missing in some views.

Optional improvement (small future enhancement, not required to enable foreign markets): add a fallback to use `yfinance` last price when Alpha Vantage returns no data. This preserves the current structure and only changes the price fallback path.

---

## 3) UI: No Separate Pages Required

Keep using the existing pages (Dashboard, Opportunities). The S&P page stays US‑specific by design. For clarity, you can optionally:
- Show an exchange/currency badge next to symbols based on suffix (e.g., `.L → LSE • GBP`, `.TO → TSX • CAD`, `.T → TSE • JPY`, `.HK → HKEX • HKD`).
- Add a simple market filter on Opportunities (All / US / UK / JP / HK / CA) to toggle cards by suffix.
- Keep currency formatting simple for now (USD formatting is currently used). If desired, show a small currency tag to avoid confusion rather than changing numeric formatting.

Note: Market calendar/holiday widgets are US‑centric and can remain as is.

---

## 4) Start with the Easiest Exchange

Start with the London Stock Exchange (LSE, suffix `.L`). Yahoo Finance coverage is strong, and symbols are straightforward. Suggested starters: `HSBA.L`, `BP.L`, `VOD.L`.

---

## 5) Quick Validation

- Add a symbol to the watchlist (see curl above)
- Check opportunities (watchlist mode):
```bash
curl "http://localhost:5001/api/watchlist_opportunities?refresh=1" | jq .
```
- Analyze a single foreign symbol:
```bash
curl "http://localhost:5001/api/stock/HSBA.L/analysis" | jq .
```

---

## 6) Free Access

- Price/historical/news: already leveraging `yfinance`/Yahoo and other free sources in code; no new key required.
- If Alpha Vantage limits become a concern for quotes, the optional yfinance price fallback (above) avoids new credentials.

---

## 7) What We Removed

The previous plan referenced Marketstack. There is currently no Marketstack integration in the codebase, and it is not needed for foreign market coverage. The approach above requires zero new APIs and plugs into the existing flows immediately.
