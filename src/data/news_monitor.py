import finnhub
from datetime import datetime, timedelta
from typing import List, Dict, Set
from collections import defaultdict
from ..core.config import Config
from .data_fetcher import DataFetcher
from ..core.sentiment_analyzer import SentimentAnalyzer
from ..trading.trading_strategy import TradingStrategy
from ..core.go_service_client import GoServiceClient
from src.core.recommendation_manager import get_recommendation_manager
import time # Added for time.time()
import logging
import os
logging.basicConfig(level=logging.INFO)


class NewsMonitor:
    def __init__(self):
        self.finnhub_client = finnhub.Client(api_key=Config.FINNHUB_API_KEY)
        self.data_fetcher = DataFetcher()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.trading_strategy = TradingStrategy()
        self.go_client = GoServiceClient()
        self.processed_news = set()  # Track processed news to avoid duplicates

    def scan_trending_news(self, hours_back: int = 2) -> Dict:
        """
        Scan for trending news using Marketaux API and identify stocks mentioned
        """
        # Try Go service first
        if self.go_client.is_service_available("news"):
            go_result = self.go_client.process_trending_news(hours_back)
            if go_result:
                return go_result.get("trending_symbols", {})
        
        # Use Marketaux API to get trending stocks
        try:
            print("🔍 Getting trending stocks from Marketaux API...")
            trending_stocks = self.data_fetcher.get_marketaux_trending_stocks(limit=5)
            
            if not trending_stocks:
                print("❌ No trending stocks from Marketaux API")
                return {}
            
            print(f"📈 Marketaux trending stocks: {trending_stocks}")
            
            # Get comprehensive news for trending stocks from all sources
            print("📰 Fetching comprehensive news for trending stocks...")
            trending_symbols = self.data_fetcher.get_comprehensive_news_for_symbols(
                symbols=trending_stocks, 
                limit_per_symbol=5
            )
            
            # Filter out symbols with no news
            trending_symbols = {symbol: news for symbol, news in trending_symbols.items() if news}
            
            print(f"✅ Found news for {len(trending_symbols)} trending symbols: {list(trending_symbols.keys())}")
            
            # Return only the trending symbols with news
            return dict(trending_symbols)
                
        except Exception as e:
            print(f"❌ Marketaux integration failed: {e}")
            return {}

    def _extract_symbols_from_text(self, text: str) -> Set[str]:
        """
        Extract stock symbols mentioned in text
        """
        text_upper = text.upper()
        mentioned_symbols = set()
        
        # Get stocks from database watchlist
        from ..core.watchlist_manager import WatchlistManager
        watchlist_manager = WatchlistManager()
        watchlist_stocks = watchlist_manager.get_stocks()
        
        # Check for watchlist stocks
        for symbol in watchlist_stocks:
            if symbol in text_upper or self._check_company_name(symbol, text_upper):
                mentioned_symbols.add(symbol)
                
        return mentioned_symbols

    def _check_company_name(self, symbol: str, text: str) -> bool:
        """
        Check if company name is mentioned in text
        """
        company_names = {
            "AAPL": ["APPLE", "IPHONE", "IPAD", "MAC"],
            "MSFT": ["MICROSOFT", "WINDOWS", "AZURE", "OFFICE"],
            "GOOGL": ["GOOGLE", "ALPHABET", "YOUTUBE", "ANDROID"],
            "AMZN": ["AMAZON", "AWS", "ALEXA", "PRIME"],
            "TSLA": ["TESLA", "ELON MUSK", "ELECTRIC VEHICLE", "EV"],
            "META": ["META", "FACEBOOK", "INSTAGRAM", "WHATSAPP"],
            "NVDA": ["NVIDIA", "GPU", "AI CHIP", "GRAPHICS"],
            "NFLX": ["NETFLIX", "STREAMING"],
            "AMD": ["AMD", "RYZEN", "RADEON"],
            "CRM": ["SALESFORCE"],
            "UBER": ["UBER", "RIDESHARE"],
            "COIN": ["COINBASE", "CRYPTO EXCHANGE"],
            "PLTR": ["PALANTIR"],
            "SNOW": ["SNOWFLAKE"],
            "ZM": ["ZOOM", "VIDEO CONFERENCE"],
        }
        names = company_names.get(symbol, [])
        return any(name in text for name in names)

    def _check_crypto_name(self, symbol: str, text: str) -> bool:
        """
        Check if crypto name is mentioned in text
        """
        crypto_names = {
            "BTC": ["BITCOIN", "BTC"],
            "ETH": ["ETHEREUM", "ETH", "ETHER"],
            "ADA": ["CARDANO", "ADA"],
            "SOL": ["SOLANA", "SOL"],
            "DOT": ["POLKADOT", "DOT"],
            "LINK": ["CHAINLINK", "LINK"],
            "MATIC": ["POLYGON", "MATIC"],
            "AVAX": ["AVALANCHE", "AVAX"],
            "UNI": ["UNISWAP", "UNI"],
            "LTC": ["LITECOIN", "LTC"],
            "ATOM": ["COSMOS", "ATOM"],
            "ALGO": ["ALGORAND", "ALGO"],
        }
        names = crypto_names.get(symbol, [symbol])
        return any(name in text for name in names)

    def analyze_news_driven_opportunities(self, trending_symbols: Dict[str, List[dict]]) -> List[dict]:
        """
        Analyze trending news and generate news-driven opportunities
        """
        logging.info(f"[DEBUG] analyze_news_driven_opportunities called with symbols: {list(trending_symbols.keys())}")
        opportunities = []
        for symbol, news_list in trending_symbols.items():
            logging.info(f"[DEBUG] Processing symbol: {symbol}, news count: {len(news_list)}")
            if not news_list:
                logging.info(f"[DEBUG] Skipping {symbol}: no news articles")
                continue
            try:
                # Get price data for stocks only
                price_data = self.data_fetcher.get_stock_price(symbol)
                if "error" in price_data:
                    logging.info(f"[DEBUG] Skipping {symbol}: price data error")
                    continue
                # Analyze sentiment
                try:
                    if news_list and len(news_list) > 0:
                        sentiment_data = self.sentiment_analyzer.analyze_news_sentiment(news_list)
                    else:
                        # Fallback to price-based sentiment analysis
                        logging.info(f"📊 No news articles for {symbol}, using price-based sentiment analysis...")
                        sentiment_data = self.sentiment_analyzer.analyze_price_based_sentiment(price_data, symbol)
                except Exception as e:
                    # If news sentiment fails, try price-based analysis
                    logging.info(f"📊 News sentiment analysis failed for {symbol}: {str(e)}")
                    logging.info(f"📊 Falling back to price-based sentiment analysis...")
                    try:
                        sentiment_data = self.sentiment_analyzer.analyze_price_based_sentiment(price_data, symbol)
                    except Exception as price_error:
                        logging.info(f"❌ Price-based analysis also failed for {symbol}: {str(price_error)}")
                        # Create a minimal sentiment data to continue processing
                        sentiment_data = {
                            "sentiment_score": 0.0,
                            "confidence": 0.1,
                            "summary": f"Analysis failed for {symbol}",
                            "provider": "fallback"
                        }
                # Apply news-specific thresholds (lowered for testing)
                min_confidence = min(Config.NEWS_CONFIDENCE_THRESHOLD, 0.1)  # Use lower of config or 0.1
                min_sentiment = min(Config.NEWS_SENTIMENT_THRESHOLD, 0.05)  # Use lower of config or 0.05
                
                if (
                    sentiment_data["confidence"] < min_confidence
                    or abs(sentiment_data["sentiment_score"]) < min_sentiment
                ):
                    logging.info(f"[DEBUG] Skipping {symbol}: sentiment data below thresholds (confidence: {sentiment_data['confidence']}, sentiment: {sentiment_data['sentiment_score']})")
                    continue
                
                # Generate trading signals for stocks
                signal_data = self.sentiment_analyzer.get_trading_signal(sentiment_data)
                
                # Generate trade recommendations
                if signal_data["action"] != "HOLD":
                    trade_signal = self.trading_strategy.generate_trade_signal(
                        symbol, price_data["current_price"], sentiment_data, signal_data
                    )
                    opportunity = {
                        "symbol": symbol,
                        "type": "stock",
                        "trigger": "news_driven",
                        "news_count": len(news_list),
                        "price_data": price_data,
                        "sentiment_data": sentiment_data,
                        "signal_data": signal_data,
                        "trade_signal": trade_signal,
                        "articles": news_list[:3],  # Include top 3 articles
                        "timestamp": datetime.now().isoformat(),
                    }
                    opportunities.append(opportunity)
                else:
                    logging.info(f"[DEBUG] Skipping {symbol}: signal_data action is HOLD")
            except Exception as e:
                logging.info(f"Error analyzing {symbol}: {e}")
                continue
        logging.info(f"[DEBUG] News-driven opportunities generated: {opportunities}")
        return opportunities

    def analyze_watchlist_opportunities(self) -> List[Dict]:
        """
        Analyze opportunities for all symbols in watchlists regardless of news
        """
        opportunities = []
        
        # Get stocks from database watchlist
        from ..core.watchlist_manager import WatchlistManager
        watchlist_manager = WatchlistManager()
        watchlist_stocks = watchlist_manager.get_stocks()
        
        # Analyze watchlist stocks
        for symbol in watchlist_stocks:
            try:
                price_data = self.data_fetcher.get_stock_price(symbol)
                if "error" in price_data:
                    continue
                news_data = self.data_fetcher.get_company_news(symbol, days_back=3)
                # Analyze sentiment with fallback
                try:
                    if news_data and len(news_data) >= 2:
                        sentiment_data = self.sentiment_analyzer.analyze_news_sentiment(news_data)
                    else:
                        # Fallback to price-based sentiment analysis
                        logging.info(f"📊 No news articles for {symbol}, using price-based sentiment analysis...")
                        sentiment_data = self.sentiment_analyzer.analyze_price_based_sentiment(price_data, symbol)
                except Exception as e:
                    # If news sentiment fails, try price-based analysis
                    logging.info(f"📊 News sentiment analysis failed for {symbol}: {str(e)}")
                    logging.info(f"📊 Falling back to price-based sentiment analysis...")
                    try:
                        sentiment_data = self.sentiment_analyzer.analyze_price_based_sentiment(price_data, symbol)
                    except Exception as price_error:
                        logging.info(f"❌ Price-based analysis also failed for {symbol}: {str(price_error)}")
                        # Create a minimal sentiment data to continue processing
                        sentiment_data = {
                            "sentiment_score": 0.0,
                            "confidence": 0.1,
                            "summary": f"Analysis failed for {symbol}",
                            "provider": "fallback"
                        }
                
                # Use standard trading signal for stocks
                signal_data = self.sentiment_analyzer.get_trading_signal(sentiment_data)
                
                if signal_data["action"] != "HOLD":
                    trade_signal = self.trading_strategy.generate_trade_signal(
                        symbol, price_data["current_price"], sentiment_data, signal_data
                    )
                    opportunity = {
                        "symbol": symbol,
                        "type": "stock",
                        "trigger": "watchlist_scan",
                        "news_count": len(news_data),
                        "price_data": price_data,
                        "sentiment_data": sentiment_data,
                        "signal_data": signal_data,
                        "trade_signal": trade_signal,
                        "timestamp": datetime.now().isoformat(),
                    }
                    opportunities.append(opportunity)
            except Exception as e:
                logging.info(f"Error analyzing stock {symbol}: {e}")
                continue
                
        return opportunities

    def get_all_opportunities(self) -> Dict:
        logging.info("[DEBUG] get_all_opportunities called")
        trending_symbols = self.scan_trending_news()
        logging.info(f"[DEBUG] get_all_opportunities: trending_symbols = {trending_symbols}")
        news_driven = self.analyze_news_driven_opportunities(trending_symbols)
        logging.info(f"[DEBUG] get_all_opportunities: news_driven = {news_driven}")
        watchlist = self.analyze_watchlist_opportunities()
        return {
            "news_driven": news_driven,
            "watchlist": watchlist,
            "total_opportunities": len(news_driven) + len(watchlist),
            "timestamp": datetime.now().isoformat(),
        }
