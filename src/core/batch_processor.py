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

    def process_symbols_concurrently(
        self, symbols: List[str], days_back: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple symbols concurrently for enhanced analysis
        Args:
            symbols: List of stock symbols to analyze
            days_back: Number of days of news to fetch
        Returns:
            List of analysis results
        """
        days_back = days_back if days_back is not None else Config.BULK_ANALYSIS_NEWS_DAYS
        results = []
        # Use enhanced analysis timeout
        timeout = Config.ENHANCED_ANALYSIS_TIMEOUT

        # Submit all tasks
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Progress callback for real-time updates
            future_to_symbol = {
                executor.submit(self._process_single_symbol, symbol, days_back): symbol
                for symbol in symbols
            }

            for future in concurrent.futures.as_completed(future_to_symbol, timeout=timeout):
                future_to_symbol[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception:
                    print("Error processing {symbol}: {e}")

        return results

    def _process_single_symbol(self, symbol: str, days_back: int) -> Optional[Dict[str, Any]]:
        """
        Process a single symbol for enhanced analysis
        Args:
            symbol: Stock symbol to analyze
            days_back: Number of days of news to fetch
        Returns:
            Analysis result or None if failed
        """
        try:
            # Get stock data
            price_data = self.data_fetcher.get_stock_price(symbol)

            # Get news data
            news_data = self.data_fetcher.get_company_news(symbol, days_back)

            # Analyze sentiment with fallback to price-based analysis
            try:
                if news_data and len(news_data) > 0:
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

            # Get trading signal
            signal_data = self.sentiment_analyzer.get_trading_signal(sentiment_data)

            # Return enhanced result
            return {
                "symbol": symbol,
                "price_data": price_data,
                "news_data": news_data,
                "sentiment_data": sentiment_data,
                "signal_data": signal_data,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None

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

            # Get crypto news (shared across all cryptos for efficiency)
            crypto_news = [
                news
                for news in shared_news
                if symbol.lower() in news.get("headline", "").lower()
                or symbol.lower() in news.get("summary", "").lower()
            ]

            # Analyze sentiment
            try:
                if crypto_news and len(crypto_news) > 0:
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

            # Use crypto-specific recommendation manager
            signal_data = self.sentiment_analyzer.get_trading_signal(sentiment_data)

            # Return enhanced result with crypto-specific data
            return {
                "symbol": symbol,
                "price_data": price_data,
                "news_data": crypto_news,
                "sentiment_data": sentiment_data,
                "signal_data": signal_data,
                "type": "crypto",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None

    def get_opportunities_only(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter results to only include strong trading opportunities
        Args:
            results: List of analysis results
        Returns:
            List of results with strong signals only
        """
        opportunities = []

        for result in results:
            sentiment_score = result.get("sentiment_data", {}).get("sentiment_score", 0)
            confidence = result.get("sentiment_data", {}).get("confidence", 0)

            # Only return if there's a strong signal (opportunity)
            if abs(sentiment_score) > 0.3 and confidence > 0.5:
                opportunities.append(result)

        return opportunities

    def process_batch_sync(self, tasks, progress_callback=None):
        """
        Process a batch of tasks synchronously with optional progress callback
        Args:
            tasks: List of task dictionaries
            progress_callback: Optional callback function for progress updates
        Returns:
            Dictionary with results and stats (expected by web app)
        """
        start_time = datetime.now()
        results = {}
        successful = 0
        total_tasks = len(tasks)
        
        for i, task in enumerate(tasks):
            try:
                symbol = task.get("symbol")
                task_type = task.get("type", "stock")
                
                if progress_callback:
                    progress_callback(symbol, i + 1, total_tasks, None)
                
                if task_type == "crypto":
                    result = self.analyze_crypto(symbol)
                else:
                    result = self.analyze_stock(symbol)
                
                if result:
                    results[symbol] = result
                    successful += 1
                else:
                    results[symbol] = {"error": "Analysis failed"}
                    
            except Exception as e:
                log_error(f"process_batch_sync error for {task}: {e}")
                results[task.get("symbol", f"task_{i}")] = {"error": str(e)}
        
        end_time = datetime.now()
        time_taken = (end_time - start_time).total_seconds()
        
        stats = {
            "total_tasks": total_tasks,
            "successful": successful,
            "failed": total_tasks - successful,
            "time_taken": time_taken,
            "avg_time_per_task": time_taken / total_tasks if total_tasks > 0 else 0,
            "success_rate": successful / total_tasks if total_tasks > 0 else 0
        }
        
        return {
            "results": results,
            "stats": stats
        }

    def analyze_stock(self, symbol: str, days_back: Optional[int] = None):
        days_back_int = days_back if days_back is not None else Config.BULK_ANALYSIS_NEWS_DAYS
        return self._process_single_symbol(symbol, days_back_int)

    def analyze_crypto(self, symbol: str, days_back: Optional[int] = None):
        days_back_int = days_back if days_back is not None else Config.BULK_ANALYSIS_NEWS_DAYS
        shared_news = self.data_fetcher.get_crypto_news(days_back=days_back_int)
        return self._process_single_crypto(symbol, shared_news, days_back_int)


# Global batch processor instance
batch_processor = BatchProcessor()


# Convenience functions for backward compatibility
def create_crypto_analysis_tasks(crypto_symbols: List[str], days_back: Optional[int] = None) -> List[Dict[str, Any]]:
    """Create crypto analysis tasks for batch processing"""
    tasks = []
    for symbol in crypto_symbols:
        tasks.append({
            "symbol": symbol,
            "type": "crypto",
            "days_back": days_back
        })
    return tasks


def create_watchlist_tasks(symbols: List[str], days_back: Optional[int] = None) -> List[Dict[str, Any]]:
    """Create watchlist analysis tasks for batch processing"""
    tasks = []
    for symbol in symbols:
        tasks.append({
            "symbol": symbol,
            "type": "stock",
            "days_back": days_back
        })
    return tasks
