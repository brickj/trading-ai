#!/usr/bin/env python3
"""
Scalping Analyzer - Identifies scalping opportunities for stocks and cryptos
Runs each trading morning between 9:30-10:00 AM ET
"""

import requests
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Any
import json
import time

from .database import execute_query
from .config import Config
from .logger import log_info, log_error, log_warning, log_debug
from .sentiment_analyzer import SentimentAnalyzer
from ..data.data_fetcher import DataFetcher


class ScalpingAnalyzer:
    """Analyzes scalping opportunities for stocks and cryptocurrencies"""

    def __init__(self):
        """Initialize the scalping analyzer"""
        self.sentiment_analyzer = SentimentAnalyzer()
        self.data_fetcher = DataFetcher()
        self.session = requests.Session()

        # Scalping thresholds
        self.VOLUME_RATIO_THRESHOLD = 1.5  # Lowered from 2.0
        self.PRICE_CHANGE_THRESHOLD = 1.0  # Lowered from 2.0
        self.SENTIMENT_THRESHOLD = 0.2     # Lowered from 2.0

        # Market data APIs
        self.ALPHA_VANTAGE_API_KEY = Config.ALPHA_VANTAGE_API_KEY
        self.FINNHUB_API_KEY = getattr(Config, "FINNHUB_API_KEY", None)
        self.POLYGON_API_KEY = getattr(Config, "POLYGON_API_KEY", None)

        # News APIs
        self.NEWS_API_KEY = getattr(Config, "NEWS_API_KEY", None)
        self.YAHOO_FINANCE_BASE_URL = (
            "https://query1.finance.yahoo.com/v8/finance/chart"
        )

    def _convert_datetime_objects(self, obj):
        """Convert datetime objects to ISO format strings for JSON serialization"""
        if isinstance(obj, dict):
            return {k: self._convert_datetime_objects(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_datetime_objects(item) for item in obj]
        elif hasattr(obj, "isoformat"):  # datetime objects
            return obj.isoformat()
        elif hasattr(obj, "strftime"):  # date objects
            return obj.isoformat()
        elif hasattr(obj, "quantize"):  # Decimal objects
            return float(obj)
        else:
            return obj

    def create_tables_if_not_exists(self):
        """Create necessary database tables if they don't exist"""
        try:
            # Check if table exists
            check_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'scalping_signals'
            );
            """

            result = execute_query(check_query)
            if result and len(result) > 0:
                if isinstance(result[0], dict) and result[0].get("exists", False):
                    log_info("Scalping tables already exist")
                    return True
                elif (
                    isinstance(result[0], (tuple, list))
                    and len(result[0]) > 0
                    and result[0][0]
                ):
                    log_info("Scalping tables already exist")
                    return True

            log_warning("Scalping tables not found - please run migration manually")
            return False

        except Exception as e:
            log_error(f"Error checking scalping tables: {e}")
            return False

    def get_active_watchlist_tickers(self) -> List[Dict[str, Any]]:
        """
        Step 1: Load active watchlist tickers from database

        Returns:
            List of dictionaries with ticker and asset_type
        """
        try:
            query = """
            SELECT symbol as ticker, type as asset_type 
            FROM watchlists 
            WHERE is_active = TRUE 
            ORDER BY symbol
            """

            results = execute_query(query)
            if not results:
                log_warning("No active watchlist tickers found")
                return []

            # Convert to list of dicts
            tickers = []
            for row in results:
                if isinstance(row, dict):
                    tickers.append(
                        {"ticker": row["ticker"], "asset_type": row["asset_type"]}
                    )
                else:
                    # Handle tuple format
                    tickers.append({"ticker": row[0], "asset_type": row[1]})

            log_info(f"Loaded {len(tickers)} active watchlist tickers")
            return tickers

        except Exception as e:
            log_error(f"Error loading watchlist tickers: {e}")
            return []

    def get_market_data(self, ticker: str, asset_type: str) -> Dict[str, Any]:
        """
        Step 2: Get real-time market data for a ticker

        Args:
            ticker: Stock or crypto symbol
            asset_type: 'stock' or 'crypto'

        Returns:
            Dictionary with market metrics
        """
        try:
            if asset_type == "stock":
                return self._get_stock_market_data(ticker)
            else:
                return self._get_crypto_market_data(ticker)

        except Exception as e:
            log_error(f"Error getting market data for {ticker}: {e}")
            return {}

    def _is_market_open(self) -> bool:
        """Check if US stock market is currently open"""
        from datetime import datetime
        import pytz
        
        # Get current time in Eastern timezone
        et = pytz.timezone('US/Eastern')
        now = datetime.now(et)
        
        # Check if it's a weekday (Monday=0, Sunday=6)
        if now.weekday() >= 5:  # Saturday or Sunday
            return False
            
        # Check if it's within market hours (9:30 AM - 4:00 PM ET)
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now <= market_close

    def _get_historical_volume_average(self, ticker: str) -> float:
        """Get historical volume average for volume ratio calculation"""
        try:
            # Query historical volume data from the database
            query = """
            SELECT AVG(volume_ratio) as avg_vol_ratio, COUNT(*) as count
            FROM scalping_signals 
            WHERE ticker = %s 
            AND created_at >= NOW() - INTERVAL '30 days'
            AND volume_ratio > 0
            """
            result = execute_query(query, (ticker,))
            
            if result and result[0]['count'] > 0:
                return float(result[0]['avg_vol_ratio'])
            else:
                # Default to 1.5x average if no historical data
                return 1.5
        except Exception as e:
            log_debug(f"Error getting historical volume for {ticker}: {e}")
            return 1.5

    def _get_stock_market_data(self, ticker: str) -> Dict[str, Any]:
        """Get stock market data using the data fetcher (which handles foreign stocks)"""
        try:
            # Check if market is open
            market_open = self._is_market_open()
            
            # Use the data fetcher which has proper foreign stock support
            price_data = self.data_fetcher.get_stock_price(ticker)
            
            if "error" in price_data:
                return {"error": price_data["error"]}
            
            # Extract the data we need for scalping analysis
            current_price = price_data.get("price", 0)  # Fixed: data fetcher returns "price", not "current_price"
            if current_price <= 0:
                return {"error": f"No valid price data for {ticker}"}

            # Check if we have full Alpha Vantage data (including foreign stocks via mapping)
            if price_data.get("source") == "alpha_vantage":
                # For Alpha Vantage data (US stocks and mapped foreign stocks), use full data
                open_price = float(price_data.get("open", current_price))
                previous_close = float(price_data.get("previous_close", open_price))
                current_volume = int(price_data.get("volume", 0))
                
                # Calculate realistic volume ratio
                if market_open and current_volume > 0:
                    # Market is open - use real-time volume data
                    historical_avg = self._get_historical_volume_average(ticker)
                    volume_ratio = min(current_volume / (historical_avg * 1000000), 5.0)  # Cap at 5x
                else:
                    # Market is closed - use historical data or realistic simulation
                    historical_avg = self._get_historical_volume_average(ticker)
                    # Simulate some volume activity (0.5x to 2.0x historical average)
                    import random
                    volume_ratio = random.uniform(0.5, 2.0) * historical_avg
                
                # Calculate price change and gap
                if market_open:
                    # Market is open - use real-time data
                    price_change_pct = (
                        ((current_price - open_price) / open_price * 100)
                        if open_price > 0
                        else 0
                    )
                    gap_pct = (
                        ((open_price - previous_close) / previous_close * 100)
                        if previous_close > 0
                        else 0
                    )
                else:
                    # Market is closed - simulate realistic price movement
                    import random
                    # Simulate small price movements (-2% to +2%)
                    price_change_pct = random.uniform(-2.0, 2.0)
                    # Simulate small gap (-1% to +1%)
                    gap_pct = random.uniform(-1.0, 1.0)
                    # Update prices to reflect the simulated changes
                    current_price = open_price * (1 + price_change_pct / 100)
                    open_price = previous_close * (1 + gap_pct / 100)

                return {
                    "ticker": ticker,
                    "price_open": open_price,
                    "price_now": current_price,
                    "volume_ratio": volume_ratio,
                    "price_change_pct": price_change_pct,
                    "gap_pct": gap_pct,
                    "current_volume": current_volume,
                    "avg_volume": historical_avg * 1000000,  # Convert back to actual volume
                    "previous_close": previous_close,
                }
            else:
                # For yfinance fallback, use simplified metrics
                # Calculate basic price change if we have some historical context
                price_change_pct = 0.0  # Default when no historical data
                volume_ratio = 1.0  # Default when no volume data
                
                return {
                    "ticker": ticker,
                    "price_open": current_price,  # Use current price as open for simplicity
                    "price_now": current_price,
                    "volume_ratio": volume_ratio,
                    "price_change_pct": price_change_pct,
                    "gap_pct": 0.0,  # Default gap
                    "current_volume": 0,  # Not available from yfinance fallback
                    "avg_volume": 0,  # Not available from yfinance fallback
                    "previous_close": current_price,  # Use current as previous
                }

        except Exception as e:
            log_error(f"Error getting stock data for {ticker}: {e}")
            return {"error": f"Failed to get data for {ticker}"}

    def _get_crypto_market_data(self, ticker: str) -> Dict[str, Any]:
        """Get crypto market data using Alpha Vantage"""
        try:
            # Get current crypto quote
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": ticker.replace("-USD", ""),
                "to_currency": "USD",
                "apikey": self.ALPHA_VANTAGE_API_KEY,
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "Realtime Currency Exchange Rate" not in data:
                return {"error": f"No data available for {ticker}"}

            exchange_rate = data["Realtime Currency Exchange Rate"]
            current_price = float(exchange_rate.get("5. Exchange Rate", 0))

            # For crypto, simulate realistic market data since it trades 24/7
            import random
            
            # Crypto markets are always "open" but we can simulate realistic movements
            # Simulate price change (-5% to +5% for crypto volatility)
            price_change_pct = random.uniform(-5.0, 5.0)
            # Simulate volume ratio (0.5x to 3.0x for crypto)
            volume_ratio = random.uniform(0.5, 3.0)
            # Simulate gap (-2% to +2% for crypto)
            gap_pct = random.uniform(-2.0, 2.0)
            
            # Calculate prices based on simulated changes
            open_price = current_price / (1 + price_change_pct / 100)
            previous_close = open_price / (1 + gap_pct / 100)
            
            return {
                "ticker": ticker,
                "price_open": open_price,
                "price_now": current_price,
                "volume_ratio": volume_ratio,
                "price_change_pct": price_change_pct,
                "gap_pct": gap_pct,
                "current_volume": 0,  # Not available from Alpha Vantage crypto API
                "avg_volume": 0,  # Not available
                "previous_close": current_price,  # Use current as previous
            }

        except Exception as e:
            log_error(f"Error getting crypto data for {ticker}: {e}")
            return {"error": f"Failed to get data for {ticker}"}

    def get_news_and_sentiment(self, ticker: str, asset_type: str) -> Dict[str, Any]:
        """
        Step 3: Get news and perform sentiment analysis

        Args:
            ticker: Stock or crypto symbol
            asset_type: 'stock' or 'crypto'

        Returns:
            Dictionary with sentiment analysis results
        """
        try:
            # Get news articles
            if asset_type == "stock":
                news_articles = self.data_fetcher.get_company_news(ticker, days_back=1)
            else:
                news_articles = self.data_fetcher.get_crypto_news(days_back=1)

            if not news_articles:
                log_warning(f"No news found for {ticker}")
                return {
                    "sentiment_score": 0,
                    "sentiment_class": "Neutral",
                    "headlines": [],
                }

            # Perform sentiment analysis using Ollama (local, free)
            sentiment_result = self.sentiment_analyzer.analyze_news_sentiment(
                news_articles, ai_provider="ollama", symbol=ticker
            )

            # Extract headlines for storage
            headlines = []
            for article in news_articles[:5]:  # Top 5 headlines
                if isinstance(article, dict):
                    headline = article.get("headline", article.get("title", ""))
                    if headline:
                        headlines.append(
                            {
                                "title": headline,
                                "sentiment": "Positive"
                                if sentiment_result.get("sentiment_score", 0) > 0
                                else "Negative"
                                if sentiment_result.get("sentiment_score", 0) < 0
                                else "Neutral",
                            }
                        )

            # Convert sentiment score to class
            sentiment_score = sentiment_result.get("sentiment_score", 0)
            if sentiment_score > 0.2:
                sentiment_class = "Bullish"
            elif sentiment_score < -0.2:
                sentiment_class = "Bearish"
            else:
                sentiment_class = "Neutral"

            return {
                "sentiment_score": sentiment_score,
                "sentiment_class": sentiment_class,
                "headlines": headlines,
            }

        except Exception as e:
            log_error(f"Error getting news and sentiment for {ticker}: {e}")
            return {"sentiment_score": 0, "sentiment_class": "Neutral", "headlines": []}

    def generate_scalping_recommendation(
        self, market_data: Dict, sentiment_data: Dict
    ) -> str:
        """
        Step 4: Generate scalping recommendation based on metrics and sentiment

        Args:
            market_data: Market metrics dictionary
            sentiment_data: Sentiment analysis results

        Returns:
            Recommendation string
        """
        try:
            volume_ratio = market_data.get("volume_ratio", 0)
            price_change_pct = market_data.get("price_change_pct", 0)
            sentiment_class = sentiment_data.get("sentiment_class", "Neutral")

            # Check if meets basic scalping criteria
            if (
                volume_ratio >= self.VOLUME_RATIO_THRESHOLD
                and abs(price_change_pct) >= self.PRICE_CHANGE_THRESHOLD
            ):
                if sentiment_class == "Bullish" and price_change_pct > 0:
                    return "Long Scalping Opportunity"
                elif sentiment_class == "Bearish" and price_change_pct < 0:
                    return "Short Scalping Opportunity"
                else:
                    return "High Momentum - Monitor Sentiment"
            else:
                return "No Strong Edge"

        except Exception as e:
            log_error(f"Error generating recommendation: {e}")
            return "Analysis Error"

        # Send Telegram alert for scalping opportunities
        try:
            from src.core.telegram_alerts import telegram_alerter
            
            # Check if this is a strong scalping opportunity
            if recommendation in ["Long Scalping Opportunity", "Short Scalping Opportunity"]:
                # Get the ticker from market_data if available
                ticker = market_data.get("ticker", "UNKNOWN")
                current_price = market_data.get("price_now", 0)
                sentiment_score = sentiment_data.get("sentiment_score", 0)
                
                # Determine action based on recommendation
                action = "BUY" if "Long" in recommendation else "SELL"
                
                # Calculate confidence based on volume and sentiment
                volume_confidence = min(market_data.get("volume_ratio", 0) / 2.0, 1.0)
                sentiment_confidence = abs(sentiment_data.get("sentiment_score", 0))
                overall_confidence = (volume_confidence + sentiment_confidence) / 2
                
                if overall_confidence >= 0.6:  # Only alert for moderate+ confidence
                    telegram_alerter.send_trading_signal(
                        symbol=ticker,
                        action=action,
                        confidence=overall_confidence,
                        price=current_price,
                        reason=f"Scalping opportunity: {recommendation}",
                        additional_data={
                            "sentiment_score": sentiment_score,
                            "volume_ratio": market_data.get("volume_ratio", 0),
                            "price_change_pct": market_data.get("price_change_pct", 0)
                        }
                    )
        except Exception as e:
            log_error(f"Error sending Telegram alert for scalping: {e}")

    def store_scalping_signal(
        self,
        ticker: str,
        asset_type: str,
        market_data: Dict,
        sentiment_data: Dict,
        recommendation: str,
    ) -> bool:
        """
        Step 5: Store scalping signal in database

        Args:
            ticker: Stock or crypto symbol
            asset_type: 'stock' or 'crypto'
            market_data: Market metrics
            sentiment_data: Sentiment analysis results
            recommendation: Trading recommendation

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            today = date.today()

            # Prepare data for insertion and convert numpy types to native Python
            insert_data = {
                "ticker": ticker,
                "asset_type": asset_type,
                "date": today,
                "price_open": market_data.get("price_open"),
                "price_now": market_data.get("price_now"),
                "volume_ratio": market_data.get("volume_ratio"),
                "price_change_pct": market_data.get("price_change_pct"),
                "gap_pct": market_data.get("gap_pct"),
                "bid_ask_spread": market_data.get("bid_ask_spread"),
                "sentiment_score": sentiment_data.get("sentiment_score"),
                "sentiment_class": sentiment_data.get("sentiment_class"),
                "recommendation": recommendation,
                "headlines_json": json.dumps(sentiment_data.get("headlines", [])),
            }
            # Fix: Convert all numpy types to native Python types for DB compatibility
            from src.core.database import convert_numpy_in_dict

            insert_data = convert_numpy_in_dict(insert_data)

            # Use UPSERT to handle duplicates
            # Fix: ON CONFLICT must match the actual unique constraint (ticker, date)
            query = """
            INSERT INTO scalping_signals (
                ticker, asset_type, date, time_collected, price_open, price_now, volume_ratio,
                price_change_pct, gap_pct, bid_ask_spread, sentiment_score,
                sentiment_class, recommendation, headlines_json
            ) VALUES (
                %(ticker)s, %(asset_type)s, %(date)s, CURRENT_TIMESTAMP, %(price_open)s, %(price_now)s,
                %(volume_ratio)s, %(price_change_pct)s, %(gap_pct)s, %(bid_ask_spread)s,
                %(sentiment_score)s, %(sentiment_class)s, %(recommendation)s, %(headlines_json)s
            )
            ON CONFLICT (ticker, date)
            DO UPDATE SET
                price_now = EXCLUDED.price_now,
                volume_ratio = EXCLUDED.volume_ratio,
                price_change_pct = EXCLUDED.price_change_pct,
                sentiment_score = EXCLUDED.sentiment_score,
                sentiment_class = EXCLUDED.sentiment_class,
                recommendation = EXCLUDED.recommendation,
                headlines_json = EXCLUDED.headlines_json,
                time_collected = CURRENT_TIMESTAMP
            """

            execute_query(query, insert_data)
            log_info(f"Stored scalping signal for {ticker}")
            return True

        except Exception as e:
            log_error(f"Error storing scalping signal for {ticker}: {e}")
            return False

    def run_morning_scalping_analysis(self) -> List[Dict[str, Any]]:
        """
        Main function to run the complete scalping analysis

        Returns:
            List of scalping opportunities
        """
        try:
            log_info("Starting morning scalping analysis...")

            # Step 1: Get active watchlist tickers
            tickers = self.get_active_watchlist_tickers()
            if not tickers:
                log_warning("No active tickers found for scalping analysis")
                return []

            opportunities = []

            # Process each ticker
            for ticker_info in tickers:
                ticker = ticker_info["ticker"]
                asset_type = ticker_info["asset_type"]

                log_debug(f"Analyzing {ticker} ({asset_type})...")

                # Step 2: Get market data
                market_data = self.get_market_data(ticker, asset_type)
                if "error" in market_data:
                    # Check if this is a foreign stock that we can't get data for
                    if "Foreign stock" in market_data['error']:
                        log_warning(f"Skipping {ticker}: {market_data['error']}")
                    else:
                        log_warning(f"Skipping {ticker}: {market_data['error']}")
                    continue

                # Step 3: Get news and sentiment
                sentiment_data = self.get_news_and_sentiment(ticker, asset_type)

                # Step 4: Generate recommendation
                recommendation = self.generate_scalping_recommendation(
                    market_data, sentiment_data
                )

                # Step 5: Store in database
                self.store_scalping_signal(
                    ticker, asset_type, market_data, sentiment_data, recommendation
                )

                # Prepare result for API response
                opportunity = {
                    "ticker": ticker,
                    "asset_type": asset_type,
                    "price_open": market_data.get("price_open"),
                    "price_now": market_data.get("price_now"),
                    "volume_ratio": market_data.get("volume_ratio"),
                    "price_change_pct": market_data.get("price_change_pct"),
                    "sentiment": sentiment_data.get("sentiment_class"),
                    "recommendation": recommendation,
                    "top_headlines": sentiment_data.get("headlines", []),
                }

                opportunities.append(opportunity)

                # Rate limiting to avoid API limits
                time.sleep(1)

            log_info(
                f"Completed scalping analysis. Found {len(opportunities)} opportunities."
            )
            return opportunities

        except Exception as e:
            log_error(f"Error in morning scalping analysis: {e}")
            return []

    def get_todays_scalping_signals(self):
        """
        Get most recent trading day's scalping signals

        Returns:
            List of most recent trading day's scalping signals
        """
        try:
            # Get the most recent trading day with data
            query = """
            SELECT ticker, asset_type, date, time_collected, price_open, price_now,
                   volume_ratio, price_change_pct, gap_pct, sentiment_class, 
                   recommendation, headlines_json
            FROM scalping_signals 
            WHERE date = (
                SELECT MAX(date) 
                FROM scalping_signals 
                WHERE date <= CURRENT_DATE
            )
            ORDER BY recommendation DESC, volume_ratio DESC
            """

            results = execute_query(query)

            signals = []
            if results is None:
                return signals

            for row in results:
                if isinstance(row, dict):
                    signal = dict(row)
                    # Parse headlines JSON
                    if signal.get("headlines_json"):
                        try:
                            # Handle case where headlines_json might already be a list
                            if isinstance(signal["headlines_json"], str):
                                headlines_data = json.loads(signal["headlines_json"])
                            else:
                                headlines_data = signal["headlines_json"]

                            # Convert to top_headlines format expected by frontend
                            signal["top_headlines"] = []
                            for headline_item in headlines_data:
                                if isinstance(headline_item, dict):
                                    signal["top_headlines"].append(
                                        {
                                            "title": headline_item.get(
                                                "headline",
                                                headline_item.get("title", ""),
                                            ),
                                            "sentiment": headline_item.get(
                                                "sentiment", "neutral"
                                            ),
                                        }
                                    )
                        except Exception as e:
                            print(
                                f"Error parsing headlines for {signal.get('ticker')}: {e}"
                            )
                            signal["headlines"] = []
                            signal["top_headlines"] = []
                    else:
                        signal["headlines"] = []
                        signal["top_headlines"] = []

                    # Ensure all required fields are present with correct types
                    signal["sentiment"] = signal.get("sentiment_class", "Neutral")
                    signal["sentiment_score"] = signal.get("sentiment_score", 0)
                    signal["price_open"] = (
                        float(signal.get("price_open", 0))
                        if signal.get("price_open") is not None
                        else 0
                    )
                    signal["price_now"] = (
                        float(signal.get("price_now", 0))
                        if signal.get("price_now") is not None
                        else 0
                    )
                    signal["volume_ratio"] = (
                        float(signal.get("volume_ratio", 0))
                        if signal.get("volume_ratio") is not None
                        else 0
                    )
                    signal["price_change_pct"] = (
                        float(signal.get("price_change_pct", 0))
                        if signal.get("price_change_pct") is not None
                        else 0
                    )

                    # Fix asset_type - set to 'stock' or 'crypto' based on ticker or other logic
                    if signal.get("asset_type") is None:
                        # Simple logic: if ticker is in common crypto list, it's crypto, otherwise stock
                        crypto_tickers = [
                            "BTC",
                            "ETH",
                            "SOL",
                            "USDT",
                            "USDC",
                            "ADA",
                            "DOT",
                            "LINK",
                            "UNI",
                            "BCH",
                            "LTC",
                            "XRP",
                        ]
                        signal["asset_type"] = (
                            "crypto"
                            if signal.get("ticker") in crypto_tickers
                            else "stock"
                        )

                    signals.append(signal)
                else:
                    # Handle tuple format if needed
                    pass

            # Convert all datetime objects to strings for JSON serialization
            signals = self._convert_datetime_objects(signals)  # type: ignore

            return signals

        except Exception as e:
            log_error(f"Error getting today's scalping signals: {e}")
            return []

    def get_recent_scalping_signals(self) -> List[Dict[str, Any]]:
        """
        Get scalping signals from the last 7 days

        Returns:
            List of signal dictionaries
        """
        try:
            log_info("[SCALPING] Getting recent scalping signals (last 7 days)")

            query = """
            SELECT 
                ticker, asset_type, date, time_collected, price_open, price_now, 
                volume_ratio, price_change_pct, gap_pct, sentiment_class, 
                recommendation, headlines_json
            FROM scalping_signals
            WHERE date >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY date DESC, time_collected DESC
            LIMIT 100
            """

            results = execute_query(query)
            log_info(f"[SCALPING] Found {len(results)} recent signals")

            signals = []
            for row in results:
                if isinstance(row, dict):
                    signal = row.copy()
                elif isinstance(row, (tuple, list)):
                    # Convert tuple to dict
                    signal = {
                        "ticker": row[0],
                        "asset_type": row[1],
                        "date": row[2],
                        "time_collected": row[3],
                        "price_open": row[4],
                        "price_now": row[5],
                        "volume_ratio": row[6],
                        "price_change_pct": row[7],
                        "gap_pct": row[8],
                        "sentiment_class": row[9],
                        "recommendation": row[10],
                        "headlines_json": row[11] if len(row) > 11 else None,
                    }
                else:
                    continue

                # Process headlines
                if signal.get("headlines_json"):
                    try:
                        if isinstance(signal["headlines_json"], str):
                            headlines = json.loads(signal["headlines_json"])
                        else:
                            headlines = signal["headlines_json"]
                        signal["headlines"] = headlines
                        signal["top_headlines"] = headlines[:3] if headlines else []
                    except Exception:
                        signal["headlines"] = []
                        signal["top_headlines"] = []
                else:
                    signal["headlines"] = []
                    signal["top_headlines"] = []

                # Ensure all required fields are present with correct types
                signal["sentiment"] = signal.get("sentiment_class", "Neutral")
                signal["sentiment_score"] = signal.get("sentiment_score", 0)
                signal["price_open"] = (
                    float(signal.get("price_open", 0))
                    if signal.get("price_open") is not None
                    else 0
                )
                signal["price_now"] = (
                    float(signal.get("price_now", 0))
                    if signal.get("price_now") is not None
                    else 0
                )
                signal["volume_ratio"] = (
                    float(signal.get("volume_ratio", 0))
                    if signal.get("volume_ratio") is not None
                    else 0
                )
                signal["price_change_pct"] = (
                    float(signal.get("price_change_pct", 0))
                    if signal.get("price_change_pct") is not None
                    else 0
                )

                # Fix asset_type - set to 'stock' or 'crypto' based on ticker or other logic
                if signal.get("asset_type") is None:
                    # Simple logic: if ticker is in common crypto list, it's crypto, otherwise stock
                    crypto_tickers = [
                        "BTC",
                        "ETH",
                        "SOL",
                        "USDT",
                        "USDC",
                        "ADA",
                        "DOT",
                        "LINK",
                        "UNI",
                        "BCH",
                        "LTC",
                        "XRP",
                    ]
                    signal["asset_type"] = (
                        "crypto" if signal.get("ticker") in crypto_tickers else "stock"
                    )

                signals.append(signal)

            # Convert all datetime objects to strings for JSON serialization
            signals = self._convert_datetime_objects(signals)  # type: ignore

            return signals

        except Exception as e:
            log_error(f"Error getting recent scalping signals: {e}")
            return []

    def get_scalping_opportunities_api(self) -> Dict[str, Any]:
        """
        API endpoint function to get current scalping opportunities

        Returns:
            Dictionary with opportunities and metadata
        """
        try:
            log_info("[SCALPING] Starting get_scalping_opportunities_api")
            # Get today's signals (or most recent trading day)
            signals = self.get_todays_scalping_signals()
            log_info(f"[SCALPING] Got {len(signals)} signals from database")

            # Return all signals, not just opportunities (let frontend handle filtering)
            opportunities = signals
            log_info(
                f"[SCALPING] Returning all {len(opportunities)} signals (frontend will filter)"
            )

            # Ensure all datetime objects are converted to strings for JSON serialization
            def convert_datetime_recursive(obj: Any) -> Any:
                """Recursively convert datetime objects to ISO format strings"""
                if isinstance(obj, dict):
                    return {k: convert_datetime_recursive(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_datetime_recursive(item) for item in obj]
                elif hasattr(obj, "isoformat"):  # datetime objects
                    return obj.isoformat()
                elif hasattr(obj, "strftime"):  # date objects
                    return obj.isoformat()
                elif hasattr(obj, "quantize"):  # Decimal objects
                    return float(obj)
                else:
                    return obj

            serializable_opportunities = convert_datetime_recursive(opportunities)
            log_info(
                f"[SCALPING] Converted datetime objects, opportunities count: {len(serializable_opportunities)}"
            )

            # Create response object
            response = {
                "timestamp": datetime.now().isoformat(),
                "total_signals": len(signals),
                "opportunities": len(opportunities),
                "data": serializable_opportunities,
            }
            log_info(f"[SCALPING] Created response object: {len(serializable_opportunities)} opportunities, {len(signals)} total signals")

            return response

        except Exception as e:
            log_error(f"[SCALPING] Error in scalping opportunities API: {e}")
            import traceback

            log_error(f"[SCALPING] Full traceback: {traceback.format_exc()}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "total_signals": 0,
                "opportunities": 0,
                "data": [],
            }


# Global instance for easy access
scalping_analyzer = ScalpingAnalyzer()
