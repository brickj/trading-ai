#!/usr/bin/env python3
"""
Batch Processor for Trading AI Platform.
Handles concurrent processing of multiple symbols for analysis.
"""

import concurrent.futures
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..core.config import Config
from ..core.recommendation_manager import get_recommendation_manager
from ..data.data_fetcher import DataFetcher
from ..core.logger import log_error
from ..core.sentiment_analyzer import SentimentAnalyzer


class BatchProcessor:
    """Handles batch processing of multiple symbols concurrently"""

    def __init__(self):
        """Initialize the batch processor"""
        self.data_fetcher = DataFetcher()
        self.recommendation_manager = get_recommendation_manager()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.max_workers = Config.MAX_CONCURRENT_REQUESTS

    def process_crypto_concurrently(
        self, crypto_symbols: List[str], days_back: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple cryptocurrencies concurrently
        Args:
            crypto_symbols: List of crypto symbols to analyze
            days_back: Number of days of news to fetch
        Returns:
            List of crypto analysis results
        """
        days_back = days_back if days_back is not None else Config.BULK_ANALYSIS_NEWS_DAYS
        shared_crypto_news = self.data_fetcher.get_crypto_news(days_back=days_back)
        results = [
            self._process_single_crypto(symbol, shared_crypto_news, days_back)
            for symbol in crypto_symbols
        ]
        return [r for r in results if r is not None]

    def _process_single_crypto(
        self, symbol: str, shared_news: List[Dict], days_back: int
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single cryptocurrency
        Args:
            symbol: Crypto symbol to analyze
            shared_news: Shared crypto news data
            days_back: Number of days of news to fetch
        Returns:
            Crypto analysis result or None if failed
        """
        try:
            # Get crypto price
            price_data = self.data_fetcher.get_crypto_price(symbol)

            # --- Improved news matching ---
            symbol_map = {
                "BTCUSD": ["BTC", "Bitcoin"], "ETHUSD": ["ETH", "Ethereum"],
                "ADAUSD": ["ADA", "Cardano"], "DOTUSD": ["DOT", "Polkadot"],
                "LINKUSD": ["LINK", "Chainlink"], "SOLUSD": ["SOL", "Solana"],
            }
            names = symbol_map.get(symbol.upper(), [symbol.replace("USD", ""), symbol])
            
            crypto_news = [
                news for news in shared_news
                if any(name.lower() in news.get("headline", "").lower() or \
                       name.lower() in news.get("summary", "").lower() for name in names)
            ]

            if not crypto_news:
                crypto_news = shared_news

            # Analyze sentiment
            try:
                if crypto_news and len(crypto_news) > 0:
                    sentiment_data = self.sentiment_analyzer.analyze_news_sentiment(crypto_news)
                else:
                    sentiment_data = self.sentiment_analyzer.analyze_price_based_sentiment(price_data, symbol)
            except Exception as e:
                if "No news articles" in str(e):
                    sentiment_data = self.sentiment_analyzer.analyze_price_based_sentiment(price_data, symbol)
                else:
                    raise e

            from src.core.recommendation_manager import get_recommendation_manager
            crypto_recommendation = get_recommendation_manager().get_crypto_specific_recommendations(
                symbol, sentiment_data, price_data
            )
            
            signal_data = {
                "action": crypto_recommendation.get("action", "HOLD"),
                "signal_strength": abs(crypto_recommendation.get("sentiment_score", 0)) * crypto_recommendation.get("confidence", 0),
                "confidence": crypto_recommendation.get("confidence", 0),
                "reasoning": crypto_recommendation.get("reasoning", "No reasoning provided")
            }

            return {
                "symbol": symbol, "price_data": price_data, "news_data": crypto_news,
                "sentiment_data": sentiment_data, "signal_data": signal_data,
                "type": "crypto", "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None

    def get_opportunities_only(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter results to only include strong trading opportunities
        """
        opportunities = []
        for result in results:
            sentiment_score = result.get("sentiment_data", {}).get("sentiment_score", 0)
            confidence = result.get("sentiment_data", {}).get("confidence", 0)
            if abs(sentiment_score) > 0.3 and confidence > 0.5:
                opportunities.append(result)
        return opportunities

    def process_batch_sync(self, tasks, progress_callback=None):
        """
        Process a batch of tasks synchronously with optional progress callback
        """
        start_time = datetime.now()
        results = {}
        successful_tasks = 0
        failed_tasks = 0

        for i, task in enumerate(tasks):
            task_id = task.get("task_id", f"task_{i}")
            func = task.get("function")
            args = task.get("args", [])
            
            try:
                result = func(*args)
                results[task_id] = result
                if result and "error" not in result:
                    successful_tasks += 1
                else:
                    failed_tasks += 1
            except Exception as e:
                log_error(f"Batch task {task_id} failed catastrophically", str(e))
                results[task_id] = {"error": str(e)}
                failed_tasks += 1

            if progress_callback:
                progress_callback(task_id, i + 1, len(tasks), results.get(task_id))

        end_time = datetime.now()
        time_taken = (end_time - start_time).total_seconds()
        
        return {
            "results": results,
            "stats": {
                "total_tasks": len(tasks),
                "successful": successful_tasks,
                "failed": failed_tasks,
                "time_taken": time_taken,
                "avg_time_per_task": time_taken / len(tasks) if tasks else 0,
            },
        }

    def analyze_stock(self, symbol: str, days_back: Optional[int] = None):
        """
        New robust stock analysis function for batch processing.
        Returns a nested opportunity dict matching the news-driven structure.
        """
        try:
            days_back = days_back if days_back is not None else Config.BULK_ANALYSIS_NEWS_DAYS

            price_data = self.data_fetcher.get_stock_price(symbol)
            if not price_data or price_data.get("current_price") is None or price_data.get("current_price") == 0:
                log_error(f"Analysis skipped for {symbol}", "Missing critical price data")
                return {"symbol": symbol, "error": "Missing critical price data"}

            news = self.data_fetcher.get_company_news(symbol, days_back)
            articles = news[:3] if news else []
            news_count = len(news) if news else 0

            sentiment_data = None
            try:
                if news and len(news) > 0:
                    sentiment_data = self.sentiment_analyzer.analyze_news_sentiment(news, symbol=symbol)
                else:
                    sentiment_data = self.sentiment_analyzer.analyze_price_based_sentiment(price_data, symbol)
            except Exception as e:
                log_error(f"News sentiment analysis for {symbol} failed", str(e))
                try:
                    sentiment_data = self.sentiment_analyzer.analyze_price_based_sentiment(price_data, symbol)
                except Exception as price_e:
                    log_error(f"Price-based sentiment for {symbol} also failed", str(price_e))
                    return {"symbol": symbol, "error": f"Full analysis failed. See logs for details."}

            if sentiment_data is None:
                return {"symbol": symbol, "error": "Sentiment analysis returned no data"}

            signal_data = self.sentiment_analyzer.get_trading_signal(sentiment_data)
            from ..trading.trading_strategy import TradingStrategy
            trading_strategy = TradingStrategy()
            trade_signal = trading_strategy.generate_trade_signal(
                symbol, price_data["current_price"], sentiment_data, signal_data
            ) if signal_data and signal_data.get("action") != "HOLD" else {}

            if signal_data and signal_data.get("action") != "HOLD":
                return {
                    "symbol": symbol,
                    "type": "stock",
                    "trigger": "watchlist_scan",
                    "news_count": news_count,
                    "price_data": price_data,
                    "sentiment_data": sentiment_data,
                    "signal_data": signal_data,
                    "trade_signal": trade_signal,
                    "articles": articles,
                    "timestamp": datetime.now().isoformat(),
                }

            return None
        except Exception as e:
            log_error(f"Unexpected error in analyze_stock for {symbol}", str(e))
            return {"symbol": symbol, "error": f"Unexpected error: {e}"}

    def analyze_crypto(self, symbol: str, days_back: Optional[int] = None):
        """New simplified crypto analysis function for batch processing"""
        try:
            days_back_int = days_back if days_back is not None else Config.BULK_ANALYSIS_NEWS_DAYS
            shared_news = self.data_fetcher.get_crypto_news(days_back=days_back_int)
            return self._process_single_crypto(symbol, shared_news, days_back_int)
        except Exception as e:
            log_error(f"Unexpected error in analyze_crypto for {symbol}", str(e))
            return {"symbol": symbol, "error": f"Unexpected crypto error: {e}"}


# Singleton instance of the BatchProcessor
batch_processor_instance = BatchProcessor()


def create_crypto_analysis_tasks(crypto_symbols: List[str], days_back: Optional[int] = None) -> List[Dict[str, Any]]:
    """Create a list of tasks for crypto analysis"""
    days_back = days_back if days_back is not None else Config.BULK_ANALYSIS_NEWS_DAYS
    
    return [
        {
            "task_id": symbol,
            "function": batch_processor_instance.analyze_crypto,
            "args": [symbol, days_back],
        }
        for symbol in crypto_symbols
    ]


def create_watchlist_tasks(symbols: List[str], days_back: Optional[int] = None) -> List[Dict[str, Any]]:
    """Create a list of tasks for watchlist analysis"""
    days_back = days_back if days_back is not None else Config.BULK_ANALYSIS_NEWS_DAYS
    
    return [
        {
            "task_id": symbol,
            "function": batch_processor_instance.analyze_stock,
            "args": [symbol, days_back],
        }
        for symbol in symbols
    ] 