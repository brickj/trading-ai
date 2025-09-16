"""Shared dependency instances for the Trading AI web application."""
from src.data.data_fetcher import DataFetcher
from src.trading.trading_strategy import TradingStrategy
from src.core.recommendation_manager import RecommendationManager
from src.core.market_manager import MarketManager
from src.core.watchlist_manager import watchlist_manager
from src.core.sentiment_analyzer import SentimentAnalyzer
from src.trading.enhanced_trading_strategy import EnhancedTradingStrategy
from .utils.db_manager import DBManager

# Lazily instantiated singletons reused across blueprints
# NOTE: These instances were previously created in app.py
#       They are centralized here so routes can import them

data_fetcher = DataFetcher()
trading_strategy = TradingStrategy()
recommendation_manager = RecommendationManager()
market_manager = MarketManager()
sentiment_analyzer = SentimentAnalyzer()
enhanced_trading_strategy = EnhancedTradingStrategy()
db_manager = DBManager()

__all__ = [
    "data_fetcher",
    "trading_strategy",
    "recommendation_manager",
    "market_manager",
    "sentiment_analyzer",
    "enhanced_trading_strategy",
    "watchlist_manager",
    "db_manager",
]
