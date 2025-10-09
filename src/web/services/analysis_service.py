"""
Analysis service for handling stock and crypto analysis business logic
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from ...data.data_fetcher import DataFetcher
from ...core.sentiment_analyzer import SentimentAnalyzer
from ...trading.trading_strategy import TradingStrategy
from ...trading.enhanced_trading_strategy import EnhancedTradingStrategy
from ...core.logger import trading_logger, log_exception
from ...core.redis_cache import get_cached_result, cache_result
from ...core.watchlist_manager import watchlist_manager
from ..helpers import get_preloaded_opportunities


class AnalysisService:
    """Service for handling analysis operations with performance optimizations"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.trading_strategy = TradingStrategy()
        self.enhanced_strategy = EnhancedTradingStrategy()
        
        # Performance optimization: thread pool for parallel processing
        self.thread_pool = ThreadPoolExecutor(max_workers=10)

        # Cache frequently used data
        self._cache_timeout = 300  # 5 minutes
    
    def analyze_single_stock(self, symbol: str, use_cache: bool = True) -> Dict:
        """
        Analyze a single stock with caching and error handling
        
        Args:
            symbol: Stock symbol to analyze
            use_cache: Whether to use cached results
            
        Returns:
            Analysis results dictionary
        """
        try:
            # Check cache first if enabled
            if use_cache:
                cache_key = f"single_stock_analysis_{symbol}"
                cached_result = get_cached_result(cache_key)
                if cached_result:
                    trading_logger.api_logger.info(f"Cache hit for {symbol}")
                    return cached_result
            
            start_time = time.time()
            
            # Parallel data fetching for better performance
            price_future = self.thread_pool.submit(self._get_price_data, symbol)
            news_future = self.thread_pool.submit(self._get_news_data, symbol)
            
            # Get results
            price_data = price_future.result(timeout=30)
            news_data = news_future.result(timeout=30)
            
            if "error" in price_data:
                return {"error": f"Failed to fetch price data: {price_data['error']}"}
            
            # Sentiment analysis
            sentiment_result = self.sentiment_analyzer.analyze_news_sentiment(news_data, symbol=symbol)
            
            # Trading recommendation
            recommendation = self.trading_strategy.get_recommendation(
                symbol, price_data, sentiment_result, None
            )
            
            # Determine if this is a winner or loser based on price change
            change_percent = price_data.get("change_percent", "0%")
            if isinstance(change_percent, str):
                # Remove % sign and convert to float
                try:
                    change_percent_clean = change_percent.replace("%", "")
                    change_percent_float = float(change_percent_clean)
                    stock_type = "winner" if change_percent_float > 0 else "loser"
                except ValueError:
                    stock_type = "loser"  # Default to loser if we can't parse
            else:
                # If change_percent is already a number
                stock_type = "winner" if change_percent > 0 else "loser"
            
            result = {
                "symbol": symbol,
                "type": stock_type,
                "price_data": price_data,
                "sentiment_data": sentiment_result,
                "signal_data": {
                    "action": recommendation.get("action", "HOLD"),
                    "signal_strength": recommendation.get("confidence", 0),
                    "reasoning": recommendation.get("reasoning", "")
                },
                "news_data": {
                    "summary": sentiment_result.get("summary", "No news summary available"),
                    "article_count": len(news_data) if isinstance(news_data, list) else 0
                },
                "timestamp": datetime.now().isoformat(),
                "analysis_time": round(time.time() - start_time, 3)
            }
            
            # Cache result if successful
            if use_cache and "error" not in result:
                cache_result(f"single_stock_analysis_{symbol}", result, ttl=self._cache_timeout)
            
            return result
            
        except Exception as e:
            log_exception(f"Error analyzing stock {symbol}", e)
            return {
                "error": str(e),
                "symbol": symbol,
                "timestamp": datetime.now().isoformat()
            }
    
    def analyze_bulk_stocks(self, symbols: List[str], max_concurrent: int = 5) -> Dict:
        """
        Analyze multiple stocks in parallel for better performance
        
        Args:
            symbols: List of stock symbols
            max_concurrent: Maximum concurrent analyses
            
        Returns:
            Bulk analysis results
        """
        try:
            start_time = time.time()
            results = []
            errors = []
            
            # Process in batches for memory optimization
            batch_size = min(max_concurrent, len(symbols))
            
            for i in range(0, len(symbols), batch_size):
                batch_symbols = symbols[i:i + batch_size]
                
                # Submit all tasks in current batch
                futures = {
                    self.thread_pool.submit(self.analyze_single_stock, symbol): symbol 
                    for symbol in batch_symbols
                }
                
                # Collect results as they complete
                for future in as_completed(futures, timeout=60):
                    symbol = futures[future]
                    try:
                        result = future.result()
                        if "error" in result:
                            errors.append({"symbol": symbol, "error": result["error"]})
                        else:
                            results.append(result)
                    except Exception as e:
                        errors.append({"symbol": symbol, "error": str(e)})
            
            return {
                "results": results,
                "errors": errors,
                "total_requested": len(symbols),
                "successful": len(results),
                "failed": len(errors),
                "processing_time": round(time.time() - start_time, 3),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            log_exception("Error in bulk stock analysis", e)
            return {
                "results": [],
                "errors": [{"error": str(e)}],
                "total_requested": len(symbols),
                "successful": 0,
                "failed": len(symbols)
            }
    
    def get_sp500_analysis(self, limit: Optional[int] = None, refresh: bool = False) -> Dict:
        """
        Get S&P 500 analysis from pre-computed database data
        
        Args:
            limit: Limit number of stocks to analyze (for testing)
            refresh: Force refresh of cached data
            
        Returns:
            S&P 500 analysis results from database
        """
        try:
            cache_key = "sp500_analysis_service"
            
            # Check cache first
            if not refresh:
                cached_result = get_cached_result(cache_key)
                if cached_result:
                    trading_logger.api_logger.info("SP500 analysis cache hit")
                    return cached_result
            
            start_time = time.time()
            
            # Query pre-computed data from database
            from src.core.database import execute_query
            
            # Get recent recommendations (last 24 hours)
            query = """
            SELECT symbol, action, recommendation_type, final_confidence, 
                   current_stock_price, sentiment_score, reasoning, timestamp
            FROM recommendations 
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
            ORDER BY timestamp DESC
            """
            
            if limit and limit > 0:
                query += f" LIMIT {limit}"
                trading_logger.api_logger.info(f"Limited SP500 analysis to {limit} stocks")
            
            results = execute_query(query)
            
            if not results:
                trading_logger.api_logger.warning("No recent recommendations found in database")
                return {
                    "comprehensive_analysis": [],
                    "errors": [],
                    "total_analyzed": 0,
                    "opportunities_found": 0,
                    "errors_count": 0,
                    "performance": {
                        "execution_time": round(time.time() - start_time, 2),
                        "success_rate": "0%",
                        "avg_analysis_time": 0
                    },
                    "timestamp": datetime.now().isoformat(),
                    "cached": True,
                    "data_source": "database"
                }
            
            # Convert database results to expected format
            comprehensive_analysis = []
            for row in results:
                if isinstance(row, dict):
                    analysis_item = {
                        "symbol": row["symbol"],
                        "action": row["action"],
                        "recommendation_type": row["recommendation_type"],
                        "confidence": float(row["final_confidence"]) if row["final_confidence"] else 0.0,
                        "current_price": float(row["current_stock_price"]) if row["current_stock_price"] else 0.0,
                        "sentiment_score": float(row["sentiment_score"]) if row["sentiment_score"] else 0.0,
                        "reasoning": row["reasoning"] or "",
                        "timestamp": row["timestamp"].isoformat() if row["timestamp"] else "",
                        "analysis_time": 0.0  # Pre-computed data
                    }
                else:
                    # Handle tuple format
                    analysis_item = {
                        "symbol": row[0],
                        "action": row[1],
                        "recommendation_type": row[2],
                        "confidence": float(row[3]) if row[3] else 0.0,
                        "current_price": float(row[4]) if row[4] else 0.0,
                        "sentiment_score": float(row[5]) if row[5] else 0.0,
                        "reasoning": row[6] or "",
                        "timestamp": row[7].isoformat() if row[7] else "",
                        "analysis_time": 0.0
                    }
                comprehensive_analysis.append(analysis_item)
            
            response_data = {
                "comprehensive_analysis": comprehensive_analysis,
                "errors": [],
                "total_analyzed": len(comprehensive_analysis),
                "opportunities_found": len(comprehensive_analysis),
                "errors_count": 0,
                "performance": {
                    "execution_time": round(time.time() - start_time, 2),
                    "success_rate": "100%",  # Database data is always successful
                    "avg_analysis_time": 0.0  # Pre-computed
                },
                "timestamp": datetime.now().isoformat(),
                "cached": True,
                "data_source": "database"
            }
            
            # Cache successful results
            if comprehensive_analysis:
                cache_result(cache_key, response_data, ttl=self._cache_timeout * 2)  # Cache for 10 minutes
            
            return response_data
            
        except Exception as e:
            log_exception("Error in SP500 analysis", e)
            return {
                "comprehensive_analysis": [],
                "errors": [{"error": str(e)}],
                "total_analyzed": 0,
                "opportunities_found": 0,
                "errors_count": 1
            }
    
    def get_crypto_analysis(self, refresh: bool = False) -> Dict:
        """
        Get cryptocurrency analysis with preloaded data optimization
        
        Args:
            refresh: Force refresh of analysis
            
        Returns:
            Crypto analysis results
        """
        try:
            # Get crypto symbols
            crypto_symbols = watchlist_manager.get_cryptos()
            
            if not crypto_symbols:
                return {
                    "opportunities": [],
                    "errors": [],
                    "timestamp": datetime.now().isoformat(),
                    "total_analyzed": 0,
                    "opportunities_found": 0,
                    "errors_count": 0,
                    "cached": False,
                    "message": "No cryptocurrencies in watchlist."
                }
            
            # Try preloaded data first (fastest option)
            if not refresh:
                try:
                    crypto_opps, timestamp = get_preloaded_opportunities('crypto')
                    if crypto_opps:
                        return {
                            "opportunities": crypto_opps,
                            "errors": [],
                            "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
                            "total_analyzed": len(crypto_symbols),
                            "opportunities_found": len(crypto_opps),
                            "errors_count": 0,
                            "cached": True,
                            "mode": "preload",
                            "message": "Crypto opportunities loaded from preloaded table."
                        }
                except Exception as e:
                    trading_logger.error_logger.error(f"Error loading preloaded crypto data: {e}")
            
            # Fallback to fresh analysis if no preloaded data
            return self._perform_fresh_crypto_analysis(crypto_symbols)
            
        except Exception as e:
            log_exception("Error in crypto analysis", e)
            return {
                "opportunities": [],
                "errors": [{"error": str(e)}],
                "timestamp": datetime.now().isoformat(),
                "total_analyzed": 0,
                "opportunities_found": 0,
                "errors_count": 1
            }
    
    def _get_price_data(self, symbol: str) -> Dict:
        """Get price data for a symbol"""
        try:
            return self.data_fetcher.get_stock_price(symbol)
        except Exception as e:
            return {"error": str(e)}
    
    def _get_news_data(self, symbol: str) -> List:
        """Get news data for a symbol"""
        try:
            return self.data_fetcher.get_company_news(symbol)
        except Exception as e:
            trading_logger.error_logger.error(f"Error fetching news for {symbol}: {e}")
            return []
    
    def _perform_fresh_crypto_analysis(self, crypto_symbols: List[str]) -> Dict:
        """Perform fresh crypto analysis when preloaded data isn't available"""
        try:
            start_time = time.time()
            
            # Use the proper batch processor for crypto analysis
            from src.core.batch_processor import create_crypto_analysis_tasks, batch_processor_instance
            
            # Create crypto analysis tasks
            tasks = create_crypto_analysis_tasks(crypto_symbols[:5])  # Limit to prevent timeout
            
            # Process the batch
            batch_result = batch_processor_instance.process_batch_sync(tasks)
            
            # Extract results and errors
            results = []
            errors = []
            
            for symbol, result in batch_result["results"].items():
                if result and "error" not in result:
                    results.append(result)
                elif result and "error" in result:
                    errors.append({"symbol": symbol, "error": result.get("error", "unknown error")})
                else:
                    # No strong signal found
                    pass
            
            return {
                "opportunities": results,
                "errors": errors,
                "timestamp": datetime.now().isoformat(),
                "total_analyzed": len(crypto_symbols),
                "opportunities_found": len(results),
                "errors_count": len(errors),
                "cached": False,
                "mode": "fresh",
                "processing_time": round(time.time() - start_time, 3),
                "message": "Fresh crypto analysis completed."
            }
            
        except Exception as e:
            log_exception("Error in fresh crypto analysis", e)
            return {
                "opportunities": [],
                "errors": [{"error": str(e)}],
                "timestamp": datetime.now().isoformat(),
                "total_analyzed": len(crypto_symbols),
                "opportunities_found": 0,
                "errors_count": 1
            }

