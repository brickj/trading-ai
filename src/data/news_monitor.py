import finnhub
from datetime import datetime, timedelta
from typing import List, Dict, Set
from collections import defaultdict
from ..core.config import Config
from .data_fetcher import DataFetcher
from ..core.sentiment_analyzer import SentimentAnalyzer
from ..trading.trading_strategy import TradingStrategy
from ..core.go_service_client import GoServiceClient
from src.core.recommendation_manager import recommendation_manager


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
        Scan for trending news and identify stocks/cryptos mentioned
        """
        # Try Go service first
        if self.go_client.is_service_available("news"):
            go_result = self.go_client.process_trending_news(hours_back)
            if go_result:
                return go_result.get("trending_symbols", {})
        # Fallback to Python implementation
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        trending_symbols = defaultdict(list)
        try:
            # Get general market news
            for category in Config.NEWS_CATEGORIES:
                news = self.finnhub_client.general_news(category, min_id=0)
                for article in news[:20]:  # Check recent 20 articles
                    article_time = datetime.fromtimestamp(article.get("datetime", 0))
                    # Only process recent news
                    if article_time < start_time:
                        continue
                    # Skip if already processed
                    article_id = article.get("id", "")
                    if article_id in self.processed_news:
                        continue
                    self.processed_news.add(article_id)
                    # Extract mentioned symbols from headline and summary
                    mentioned_symbols = self._extract_symbols_from_text(
                        article.get("headline", "") + " " + article.get("summary", "")
                    )
                    for symbol in mentioned_symbols:
                        trending_symbols[symbol].append(article)
            return dict(trending_symbols)
        except Exception as e:
            print(f"Error scanning trending news: {e}")
            return {}

    def _extract_symbols_from_text(self, text: str) -> Set[str]:
        """
        Extract stock and crypto symbols mentioned in news text
        """
        text_upper = text.upper()
        mentioned_symbols = set()
        # Check for watchlist stocks
        for symbol in Config.WATCHLIST_STOCKS:
            if symbol in text_upper or self._check_company_name(symbol, text_upper):
                mentioned_symbols.add(symbol)
        # Check for watchlist cryptos
        for symbol in Config.WATCHLIST_CRYPTO:
            crypto_name = symbol.replace("USD", "")
            if crypto_name in text_upper or self._check_crypto_name(crypto_name, text_upper):
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

    def analyze_news_driven_opportunities(self) -> List[Dict]:
        """
        Main function to analyze news-driven trading opportunities
        """
        trending_symbols = self.scan_trending_news()
        opportunities = []
        for symbol, articles in trending_symbols.items():
            if len(articles) < Config.MIN_NEWS_ARTICLES:
                continue
            try:
                # Determine if it's a stock or crypto
                is_crypto = symbol in Config.WATCHLIST_CRYPTO
                # Get price data
                if is_crypto:
                    price_data = self.data_fetcher.get_crypto_price(symbol)
                else:
                    price_data = self.data_fetcher.get_stock_price(symbol)
                if "error" in price_data:
                    continue
                # Analyze sentiment
                try:
                    if articles and len(articles) > 0:
                        sentiment_data = self.sentiment_analyzer.analyze_news_sentiment(articles)
                    else:
                        # Fallback to price-based sentiment analysis
                        print(f"📊 No news articles for {symbol}, using price-based sentiment analysis...")
                        sentiment_data = self.sentiment_analyzer.analyze_price_based_sentiment(price_data, symbol)
                except Exception as e:
                    # If news sentiment fails, try price-based analysis
                    if "No news articles provided for analysis" in str(e) or "No valid news content found" in str(e):
                        print(f"📊 News analysis failed for {symbol}, falling back to price-based analysis...")
                        sentiment_data = self.sentiment_analyzer.analyze_price_based_sentiment(price_data, symbol)
                    else:
                        # Re-raise other types of errors
                        raise e
                # Apply news-specific thresholds
                if (
                    sentiment_data["confidence"] < Config.NEWS_CONFIDENCE_THRESHOLD
                    or abs(sentiment_data["sentiment_score"]) < Config.NEWS_SENTIMENT_THRESHOLD
                ):
                    continue
                # Generate trading signals
                # Use crypto-specific recommendations for crypto symbols
                if is_crypto:
                    crypto_recommendation = recommendation_manager.get_crypto_specific_recommendations(
                        symbol, sentiment_data, price_data
                    )
                    signal_data = {
                        "action": crypto_recommendation.get("action", "HOLD"),
                        "signal_strength": abs(crypto_recommendation.get("sentiment_score", 0)) * crypto_recommendation.get("confidence", 0),
                        "confidence": crypto_recommendation.get("confidence", 0),
                        "reasoning": crypto_recommendation.get("reasoning", "No reasoning provided")
                    }
                else:
                    signal_data = self.sentiment_analyzer.get_trading_signal(sentiment_data)
                # Generate trade recommendations
                if signal_data["action"] != "HOLD":
                    trade_signal = self.trading_strategy.generate_trade_signal(
                        symbol, price_data["current_price"], sentiment_data, signal_data
                    )
                    opportunity = {
                        "symbol": symbol,
                        "type": "crypto" if is_crypto else "stock",
                        "trigger": "news_driven",
                        "news_count": len(articles),
                        "price_data": price_data,
                        "sentiment_data": sentiment_data,
                        "signal_data": signal_data,
                        "trade_signal": trade_signal,
                        "articles": articles[:3],  # Include top 3 articles
                        "timestamp": datetime.now().isoformat(),
                    }
                    opportunities.append(opportunity)
            except Exception as e:
                print(f"Error analyzing {symbol}: {e}")
                continue
        return opportunities

    def analyze_watchlist_opportunities(self) -> List[Dict]:
        """
        Analyze opportunities for all symbols in watchlists regardless of news
        """
        opportunities = []
        # Analyze watchlist stocks
        for symbol in Config.WATCHLIST_STOCKS:
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
                        print(f"📊 No news articles for {symbol}, using price-based sentiment analysis...")
                        sentiment_data = self.sentiment_analyzer.analyze_price_based_sentiment(price_data, symbol)
                except Exception as e:
                    # If news sentiment fails, try price-based analysis
                    if "No news articles provided for analysis" in str(e) or "No valid news content found" in str(e):
                        print(f"📊 News analysis failed for {symbol}, falling back to price-based analysis...")
                        sentiment_data = self.sentiment_analyzer.analyze_price_based_sentiment(price_data, symbol)
                    else:
                        # Re-raise other types of errors
                        raise e
                # Use crypto-specific recommendations for crypto symbols
                crypto_recommendation = recommendation_manager.get_crypto_specific_recommendations(
                    symbol, sentiment_data, price_data
                )
                signal_data = {
                    "action": crypto_recommendation.get("action", "HOLD"),
                    "signal_strength": abs(crypto_recommendation.get("sentiment_score", 0)) * crypto_recommendation.get("confidence", 0),
                    "confidence": crypto_recommendation.get("confidence", 0),
                    "reasoning": crypto_recommendation.get("reasoning", "No reasoning provided")
                }
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
                print(f"Error analyzing stock {symbol}: {e}")
                continue
        # Analyze watchlist cryptos
        crypto_news = self.data_fetcher.get_crypto_news(days_back=2)
        if len(crypto_news) >= 2:
            for symbol in Config.WATCHLIST_CRYPTO:
                try:
                    price_data = self.data_fetcher.get_crypto_price(symbol)
                    if "error" in price_data:
                        continue
                    # Analyze sentiment with fallback
                    try:
                        if crypto_news and len(crypto_news) >= 2:
                            sentiment_data = self.sentiment_analyzer.analyze_news_sentiment(crypto_news)
                        else:
                            # Fallback to price-based sentiment analysis
                            print(f"📊 No news articles for {symbol}, using price-based sentiment analysis...")
                            sentiment_data = self.sentiment_analyzer.analyze_price_based_sentiment(price_data, symbol)
                    except Exception as e:
                        # If news sentiment fails, try price-based analysis
                        if "No news articles provided for analysis" in str(e) or "No valid news content found" in str(e):
                            print(f"📊 News analysis failed for {symbol}, falling back to price-based analysis...")
                            sentiment_data = self.sentiment_analyzer.analyze_price_based_sentiment(price_data, symbol)
                        else:
                            # Re-raise other types of errors
                            raise e
                    # Use crypto-specific recommendations for crypto symbols
                    crypto_recommendation = recommendation_manager.get_crypto_specific_recommendations(
                        symbol, sentiment_data, price_data
                    )
                    signal_data = {
                        "action": crypto_recommendation.get("action", "HOLD"),
                        "signal_strength": abs(crypto_recommendation.get("sentiment_score", 0)) * crypto_recommendation.get("confidence", 0),
                        "confidence": crypto_recommendation.get("confidence", 0),
                        "reasoning": crypto_recommendation.get("reasoning", "No reasoning provided")
                    }
                    if signal_data["action"] != "HOLD":
                        trade_signal = self.trading_strategy.generate_trade_signal(
                            symbol,
                            price_data["current_price"],
                            sentiment_data,
                            signal_data,
                        )
                        opportunity = {
                            "symbol": symbol,
                            "type": "crypto",
                            "trigger": "watchlist_scan",
                            "news_count": len(crypto_news),
                            "price_data": price_data,
                            "sentiment_data": sentiment_data,
                            "signal_data": signal_data,
                            "trade_signal": trade_signal,
                            "timestamp": datetime.now().isoformat(),
                        }
                        opportunities.append(opportunity)
                except Exception as e:
                    print(f"Error analyzing crypto {symbol}: {e}")
                    continue
        return opportunities

    def get_all_opportunities(self) -> Dict:
        """
        Get both news-driven and watchlist opportunities
        """
        news_driven = self.analyze_news_driven_opportunities()
        watchlist = self.analyze_watchlist_opportunities()
        return {
            "news_driven": news_driven,
            "watchlist": watchlist,
            "total_opportunities": len(news_driven) + len(watchlist),
            "timestamp": datetime.now().isoformat(),
        }
