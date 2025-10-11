import finnhub
from datetime import datetime
from typing import List, Dict, Set
from ..core.config import Config
from .data_fetcher import DataFetcher
from ..core.sentiment_analyzer import SentimentAnalyzer
from ..trading.trading_strategy import TradingStrategy
from ..core.logger import trading_logger
logger = trading_logger


class NewsMonitor:
    def __init__(self):
        self.finnhub_client = finnhub.Client(api_key=Config.FINNHUB_API_KEY)
        self.data_fetcher = DataFetcher()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.trading_strategy = TradingStrategy()
        self.processed_news = set()  # Track processed news to avoid duplicates

    def scan_trending_news(self, hours_back: int = 2) -> Dict:
        """
        Scan for trending news using Marketaux API and identify stocks mentioned
        """
        # Try Go service first
        if False:  # self.go_client.is_service_available("news") removed
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
                symbols=trending_stocks, limit_per_symbol=5
            )

            # Filter out symbols with no news
            trending_symbols = {
                symbol: news for symbol, news in trending_symbols.items() if news
            }

            print(
                f"✅ Found news for {len(trending_symbols)} trending symbols: {list(trending_symbols.keys())}"
            )

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

    def analyze_news_driven_opportunities(
        self, trending_symbols: Dict[str, List[dict]]
    ) -> List[dict]:
        """
        Analyze trending news and generate news-driven opportunities
        """
        logger.info(
            f"[DEBUG] analyze_news_driven_opportunities called with symbols: {list(trending_symbols.keys())}"
        )
        opportunities = []
        for symbol, news_list in trending_symbols.items():
            logger.info(
                f"[DEBUG] Processing symbol: {symbol}, news count: {len(news_list)}"
            )
            if not news_list:
                logger.info(f"[DEBUG] Skipping {symbol}: no news articles")
                continue
            try:
                # Get price data for stocks only
                price_data = self.data_fetcher.get_stock_price(symbol)
                if "error" in price_data:
                    logger.info(f"[DEBUG] Skipping {symbol}: price data error")
                    continue
                # Analyze sentiment
                try:
                    if news_list and len(news_list) > 0:
                        sentiment_data = self.sentiment_analyzer.analyze_news_sentiment(
                            news_list
                        )
                    else:
                        # Fallback to price-based sentiment analysis
                        logger.info(
                            f"📊 No news articles for {symbol}, using price-based sentiment analysis..."
                        )
                        sentiment_data = (
                            self.sentiment_analyzer.analyze_price_based_sentiment(
                                price_data, symbol
                            )
                        )
                except Exception as e:
                    logger.error(f"SENTIMENT ANALYSIS FAILED FOR {symbol}: {str(e)}")
                    logger.error(f"PRICE DATA: {price_data}")
                    logger.error(f"NEWS ARTICLES COUNT: {len(news_list) if news_list else 0}")
                    logger.error(f"NEWS ARTICLES: {news_list}")
                    logger.error(f"EXCEPTION TYPE: {type(e).__name__}")
                    import traceback
                    logger.error(f"FULL TRACEBACK: {traceback.format_exc()}")
                    raise Exception(f"Sentiment analysis failed for {symbol}: {str(e)}")
                logger.info(f"[DEBUG] {symbol} sentiment analysis result: confidence={sentiment_data['confidence']}, sentiment={sentiment_data['sentiment_score']}")

                # Generate trading signals for stocks using news-specific thresholds
                # Returns both stock and options recommendations
                signal_data = self._get_news_trading_signal(sentiment_data)
                
                # Extract both recommendations
                stock_recommendation = signal_data.get("stock_recommendation", {})
                options_recommendation = signal_data.get("options_recommendation", {})
                
                stock_action = stock_recommendation.get("action", "HOLD")
                options_action = options_recommendation.get("action", "HOLD")
                
                logger.info(f"[DEBUG] {symbol} signal data: stock_action={stock_action}, options_action={options_action}, confidence={stock_recommendation.get('confidence', 'UNKNOWN')}")

                # Generate trade recommendations only for actionable signals
                if stock_action != "HOLD" or options_action != "HOLD":
                    # Generate detailed options trade signal if options recommendation exists
                    trade_signal = {}
                    if options_action != "HOLD":
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
                        "signal_data": signal_data,  # Include full signal_data with BOTH recommendations
                        "trade_signal": trade_signal,
                        "articles": news_list[:3],  # Include top 3 articles
                        "timestamp": datetime.now().isoformat(),
                    }
                    logger.info(f"[DEBUG] Created opportunity for {symbol}: stock={stock_action}, options={options_action}")
                    opportunities.append(opportunity)
                else:
                    logger.info(
                        f"[DEBUG] Skipping {symbol}: both stock and options actions are HOLD"
                    )
            except Exception as e:
                logger.info(f"Error analyzing {symbol}: {e}")
                continue
        logger.info(f"[DEBUG] News-driven opportunities generated: {opportunities}")
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
                        sentiment_data = self.sentiment_analyzer.analyze_news_sentiment(
                            news_data
                        )
                    else:
                        # Fallback to price-based sentiment analysis
                        logger.info(
                            f"📊 No news articles for {symbol}, using price-based sentiment analysis..."
                        )
                        sentiment_data = (
                            self.sentiment_analyzer.analyze_price_based_sentiment(
                                price_data, symbol
                            )
                        )
                except Exception as e:
                    # If news sentiment fails, try price-based analysis
                    logger.info(
                        f"📊 News sentiment analysis failed for {symbol}: {str(e)}"
                    )
                    logger.info("📊 Falling back to price-based sentiment analysis...")
                    try:
                        sentiment_data = (
                            self.sentiment_analyzer.analyze_price_based_sentiment(
                                price_data, symbol
                            )
                        )
                    except Exception as price_error:
                        logger.info(
                            f"❌ Price-based analysis also failed for {symbol}: {str(price_error)}"
                        )
                        # Skip symbols where sentiment analysis fails
                        logger.info(f"[DEBUG] Skipping {symbol}: sentiment analysis failed")
                        continue

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
                logger.info(f"Error analyzing stock {symbol}: {e}")
                continue

        return opportunities

    def _get_news_trading_signal(self, sentiment_data: Dict) -> Dict:
        """
        Generate trading signal using news-specific thresholds instead of general thresholds.
        This uses NEWS_CONFIDENCE_THRESHOLD (0.3) and NEWS_SENTIMENT_THRESHOLD (0.1) 
        instead of the general CONFIDENCE_THRESHOLD (0.15) and SENTIMENT_THRESHOLD (0.05).
        """
        from ..core.config import Config
        
        # Ensure sentiment_data is a dictionary
        if not isinstance(sentiment_data, dict):
            raise TypeError(
                f"sentiment_data must be a dict, got {type(sentiment_data)}: {sentiment_data}"
            )

        # Extract values safely
        sentiment_score = sentiment_data.get("sentiment_score", 0)
        confidence = sentiment_data.get("confidence", 0)

        # Validate values are numeric
        try:
            sentiment_score = float(sentiment_score)
            confidence = float(confidence)
        except (ValueError, TypeError):
            raise ValueError(
                f"Invalid sentiment data format - score: {sentiment_score}, confidence: {confidence}"
            )

        # Use news-specific thresholds
        news_confidence_threshold = getattr(Config, 'NEWS_CONFIDENCE_THRESHOLD', 0.3)
        news_sentiment_threshold = getattr(Config, 'NEWS_SENTIMENT_THRESHOLD', 0.1)

        # Return both stock and options recommendations using news thresholds
        if confidence < news_confidence_threshold or abs(sentiment_score) < news_sentiment_threshold:
            stock_action = "HOLD"
            options_action = "HOLD"
            reasoning = f"Low confidence ({confidence:.2f} < {news_confidence_threshold}) or weak sentiment signal ({abs(sentiment_score):.2f} < {news_sentiment_threshold})"
        elif sentiment_score > news_sentiment_threshold:
            stock_action = "BUY"
            options_action = "CALL"
            reasoning = f"Positive sentiment ({sentiment_score:.2f}) with high confidence ({confidence:.2f})"
        elif sentiment_score < -news_sentiment_threshold:
            stock_action = "SELL"
            options_action = "PUT"
            reasoning = f"Negative sentiment ({sentiment_score:.2f}) with high confidence ({confidence:.2f})"
        else:
            stock_action = "HOLD"
            options_action = "HOLD"
            reasoning = "Neutral sentiment"

        # Return same structure as sentiment_analyzer.get_trading_signal()
        return {
            "stock_recommendation": {
                "action": stock_action,
                "signal_strength": abs(sentiment_score) * confidence if stock_action in ["BUY", "SELL"] else 0,
                "confidence": confidence,
                "reasoning": reasoning,
            },
            "options_recommendation": {
                "action": options_action,
                "signal_strength": abs(sentiment_score) * confidence if options_action in ["CALL", "PUT"] else 0,
                "confidence": confidence,
                "reasoning": reasoning,
            }
        }
