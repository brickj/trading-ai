"""
Options Trading Sentiment Analysis System
A comprehensive trading system that combines sentiment analysis from news sources
with options trading strategies and portfolio management.
"""

__version__ = "1.0.0"
__author__ = "Trading Team"
__email__ = "team@trading.com"
# Package-level imports for convenience
from .core.config import Config
from .core.sentiment_analyzer import SentimentAnalyzer
from .data.data_fetcher import DataFetcher
from .trading.trading_strategy import TradingStrategy

__all__ = ["Config", "SentimentAnalyzer", "DataFetcher", "TradingStrategy"]
