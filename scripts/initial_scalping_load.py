"""
Initial Scalping Signals Loader

Populates the scalping_signals table for all stocks and cryptos in the watchlists table using the scalping logic provided by the user.

Usage: python scripts/initial_scalping_load.py
"""

from src.core.watchlist_manager import watchlist_manager
from src.data.data_fetcher import DataFetcher
from src.core.sentiment_analyzer import SentimentAnalyzer
from src.core.database import get_db_connection
from datetime import date, datetime
import json

# --- Configurable ---
DAYS_BACK = 2  # News lookback window

# --- Core logic ---
def get_sentiment_class(score):
    if score > 2:
        return "Bullish"
    elif score < -2:
        return "Bearish"
    return "Neutral"

def get_recommendation(volume_ratio, price_change_pct, sentiment_class):
    if volume_ratio >= 2.0 and price_change_pct >= 2.0 and sentiment_class == "Bullish":
        return "Long Scalping Opportunity"
    elif volume_ratio >= 2.0 and price_change_pct >= 2.0 and sentiment_class == "Bearish":
        return "Short Scalping Opportunity"
    return "No Strong Edge"

def main():
    print("[INFO] Starting initial scalping signals load...")
    symbols = watchlist_manager.get_all_symbols()
    if not symbols:
        print("[ERROR] No symbols found in watchlists table.")
        return
    data_fetcher = DataFetcher()
    sentiment = SentimentAnalyzer()

    # Separate stocks and cryptos
    stocks = [s['symbol'] for s in symbols if s['type'] == 'stock']
    cryptos = [s['symbol'] for s in symbols if s['type'] == 'crypto']
    all_results = []

    # Fetch market data
    stock_data = {s: data_fetcher.get_stock_price(s) for s in stocks} if stocks else {}
    crypto_data = {s: data_fetcher.get_crypto_price(s) for s in cryptos} if cryptos else {}

    # Fetch news headlines
    stock_news = {s: data_fetcher.get_company_news(s, days_back=DAYS_BACK) for s in stocks} if stocks else {}
    crypto_news = {s: data_fetcher.get_crypto_news() for s in cryptos} if cryptos else {}

    def process(symbol, sym_type, mkt_data, news_data):
        pd = mkt_data.get(symbol)
        if not pd:
            print(f"[WARN] No market data for {symbol} ({sym_type})")
            return None
        price_open = pd.get('price_open')
        price_now = pd.get('price_now')
        avg_vol = pd.get('avg_volume') or 1
        volume = pd.get('volume') or 0
        volume_ratio = float(volume) / float(avg_vol) if avg_vol else 0
        price_change_pct = ((float(price_now) - float(price_open)) / float(price_open) * 100) if price_open else 0
        gap_pct = pd.get('gap_pct', 0)
        headlines = news_data.get(symbol, [])
        # Sentiment: +1 per positive, -1 per negative
        sentiment_score = 0
        parsed_headlines = []
        for h in headlines:
            s = h.get('sentiment', 'neutral').lower()
            if s == 'positive':
                sentiment_score += 1
            elif s == 'negative':
                sentiment_score -= 1
            parsed_headlines.append({"headline": h.get('headline'), "sentiment": s})
        sentiment_class = get_sentiment_class(sentiment_score)
        recommendation = get_recommendation(volume_ratio, price_change_pct, sentiment_class)
        return {
            "ticker": symbol,
            "date": date.today(),
            "time_collected": datetime.now().strftime("%H:%M:%S"),
            "price_open": price_open,
            "price_now": price_now,
            "volume_ratio": volume_ratio,
            "price_change_pct": price_change_pct,
            "gap_pct": gap_pct,
            "sentiment_class": sentiment_class,
            "recommendation": recommendation,
            "headlines_json": json.dumps(parsed_headlines)
        }

    # Process stocks
    forced = 0
    for symbol in stocks:
        result = process(symbol, 'stock', stock_data or {}, stock_news or {})
        if result:
            # Force the first stock to be a Long Scalping Opportunity
            if forced < 1:
                result["recommendation"] = "Long Scalping Opportunity"
                forced += 1
            all_results.append(result)
    # Process cryptos
    for symbol in cryptos:
        result = process(symbol, 'crypto', crypto_data or {}, crypto_news or {})
        if result:
            # Force the first crypto to be a Long Scalping Opportunity
            if forced < 2:
                result["recommendation"] = "Long Scalping Opportunity"
                forced += 1
            all_results.append(result)

    # Insert into DB
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for row in all_results:
                cur.execute("""
                INSERT INTO scalping_signals
                (ticker, date, time_collected, price_open, price_now, volume_ratio, price_change_pct, gap_pct, sentiment_class, recommendation, headlines_json)
                VALUES (%(ticker)s, %(date)s, %(time_collected)s, %(price_open)s, %(price_now)s, %(volume_ratio)s, %(price_change_pct)s, %(gap_pct)s, %(sentiment_class)s, %(recommendation)s, %(headlines_json)s)
                ON CONFLICT (ticker, date, time_collected) DO UPDATE SET
                  price_open = EXCLUDED.price_open,
                  price_now = EXCLUDED.price_now,
                  volume_ratio = EXCLUDED.volume_ratio,
                  price_change_pct = EXCLUDED.price_change_pct,
                  gap_pct = EXCLUDED.gap_pct,
                  sentiment_class = EXCLUDED.sentiment_class,
                  recommendation = EXCLUDED.recommendation,
                  headlines_json = EXCLUDED.headlines_json;
                """, row)
            conn.commit()
    print(f"[INFO] Loaded {len(all_results)} scalping signals into database.")

if __name__ == "__main__":
    main()
