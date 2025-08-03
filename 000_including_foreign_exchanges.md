# IBKR Foreign Exchange Integration Analysis

# Analyzing existing foreign exchange documentation

To include foreign exchanges you primarily adjust the configuration and let the existing data‑fetcher handle the new symbols.

---

## 1. Enable a Global Data Source

Config already exposes a `MARKETSTACK_API_KEY` for global price data:

```python
MARKETSTACK_API_KEY = os.getenv('MARKETSTACK_API_KEY')
```

`DataFetcher` has helpers that call Marketstack as a fallback:

```python
def _get_marketstack_price(self, symbol: str) -> Dict:
    """Get stock price from Marketstack API as another fallback"""
    if not Config.MARKETSTACK_API_KEY:
        raise Exception("Marketstack API key not configured. Please set MARKETSTACK_API_KEY in config.py")
    ...
    url = "http://api.marketstack.com/v1/intraday/latest"
    params = {
        'access_key': Config.MARKETSTACK_API_KEY,
        'symbols': symbol
    }
```

With a valid API key this fallback can fetch quotes from many world exchanges.

---

## 2. Extend the Watchlists

Stocks and cryptos to analyze are defined in `Config`:

```python
# Stocks to monitor for news-driven sentiment analysis
WATCHLIST_STOCKS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM',
    'NFLX', 'AMD', 'CRM', 'UBER', 'COIN', 'PLTR', 'SNOW', 'ZM'
]

# Cryptocurrencies to monitor for news-driven sentiment analysis
WATCHLIST_CRYPTO = [
    'BTCUSD', 'ETHUSD', 'ADAUSD', 'SOLUSD'
]
```

To analyze foreign tickers simply add them to these lists (or create a new list such as `WATCHLIST_FOREIGN_STOCKS`) using the exchange‑qualified symbols supported by Yahoo Finance/Marketstack (e.g., `"7203.T"` for Toyota on the Tokyo exchange). No other code change is needed because `NewsMonitor` and `NewsScanner` iterate through these lists dynamically.

---

## 3. Update Batch Lists if Necessary

If you wish to run bulk analysis similar to the S&P 500 batch, populate another list (e.g., `FTSE100_STOCKS` or `EUROPE_STOCKS`) following the same pattern as `SP500_STOCKS`:

```python
SP500_STOCKS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', ...
]
```

`DataFetcher.get_sp500_data()` loops over this list, so a corresponding function could iterate over your foreign list without affecting the original logic.

---

## Summary

- Obtain a Marketstack key and set `MARKETSTACK_API_KEY` to enable global price data.
- Add foreign tickers to `WATCHLIST_STOCKS` or create a new list for them in Config.
- Optionally define additional bulk lists (similar to `SP500_STOCKS`) if you need large-scale analysis.

These changes plug straight into the existing `DataFetcher`, `NewsMonitor`, and web endpoints, letting you analyze foreign markets without altering core logic.
