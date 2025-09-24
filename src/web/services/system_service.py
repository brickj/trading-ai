"""
System service for handling system operations and core module access
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

from ...core.logger import trading_logger, log_exception
from ...core.cache import get_cached_result, cache_result, get_cache_stats
from ...core.database import get_db_connection
from ...core.config import Config
from ...core.telegram_alerts import telegram_alerter
from ...core.sentiment_analyzer import SentimentAnalyzer
from ...core.batch_processor import (
    BatchProcessor, 
    create_watchlist_tasks, 
    create_crypto_analysis_tasks,
    batch_processor_instance
)
from ...data.historical_data_updater import HistoricalDataUpdater
from ...data.data_fetcher import DataFetcher
from ...data.news_monitor import NewsMonitor
from ...data.preload_stock_data import preload_stock_data
from ...trading.trading_strategy import TradingStrategy
from ...trading.enhanced_trading_strategy import EnhancedTradingStrategy
from ..helpers import execute_db_query


class SystemService:
    """Service for handling system operations with proper abstraction"""
    
    def __init__(self):
        self._cache_timeout = 300  # 5 minutes
        self.data_fetcher = DataFetcher()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.trading_strategy = TradingStrategy()
        self.enhanced_strategy = EnhancedTradingStrategy()
        self.historical_updater = HistoricalDataUpdater()
        self.news_monitor = NewsMonitor()
    
    def get_config_data(self) -> Dict:
        """Get configuration data"""
        try:
            return {
                "historical_lookback_days": Config.HISTORICAL_LOOKBACK_DAYS,
                "max_concurrent_requests": Config.MAX_CONCURRENT_REQUESTS,
                "cache_ttl": Config.CACHE_TTL,
                "telegram_enabled": Config.TELEGRAM_ALERTS_ENABLED,
                "debug_mode": Config.DEBUG_MODE,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            log_exception("Error getting config data", e)
            return {"error": str(e)}
    
    def get_database_connection(self):
        """Get database connection"""
        try:
            return get_db_connection()
        except Exception as e:
            log_exception("Error getting database connection", e)
            raise e
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            stats = get_cache_stats()
            return {
                "cache_stats": stats,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            log_exception("Error getting cache stats", e)
            return {"error": str(e)}
    
    def get_telegram_alerter(self):
        """Get telegram alerter instance"""
        try:
            return telegram_alerter
        except Exception as e:
            log_exception("Error getting telegram alerter", e)
            raise e
    
    def get_sentiment_analyzer(self) -> SentimentAnalyzer:
        """Get sentiment analyzer instance"""
        try:
            return self.sentiment_analyzer
        except Exception as e:
            log_exception("Error getting sentiment analyzer", e)
            raise e
    
    def get_trading_strategy(self) -> TradingStrategy:
        """Get trading strategy instance"""
        try:
            return self.trading_strategy
        except Exception as e:
            log_exception("Error getting trading strategy", e)
            raise e
    
    def get_enhanced_trading_strategy(self) -> EnhancedTradingStrategy:
        """Get enhanced trading strategy instance"""
        try:
            return self.enhanced_strategy
        except Exception as e:
            log_exception("Error getting enhanced trading strategy", e)
            raise e
    
    def get_historical_data_updater(self) -> HistoricalDataUpdater:
        """Get historical data updater instance"""
        try:
            return self.historical_updater
        except Exception as e:
            log_exception("Error getting historical data updater", e)
            raise e
    
    def get_data_fetcher(self) -> DataFetcher:
        """Get data fetcher instance"""
        try:
            return self.data_fetcher
        except Exception as e:
            log_exception("Error getting data fetcher", e)
            raise e
    
    def get_news_monitor(self) -> NewsMonitor:
        """Get news monitor instance"""
        try:
            return self.news_monitor
        except Exception as e:
            log_exception("Error getting news monitor", e)
            raise e
    
    def preload_stock_data(self) -> Dict:
        """Preload stock data"""
        try:
            result = preload_stock_data()
            return {
                "status": "success",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            log_exception("Error preloading stock data", e)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_batch_processor(self) -> BatchProcessor:
        """Get batch processor instance"""
        try:
            return batch_processor_instance
        except Exception as e:
            log_exception("Error getting batch processor", e)
            raise e
    
    def create_watchlist_analysis_tasks(self, symbols: List[str]) -> List[Dict]:
        """Create watchlist analysis tasks"""
        try:
            return create_watchlist_tasks(symbols)
        except Exception as e:
            log_exception("Error creating watchlist analysis tasks", e)
            raise e
    
    def create_crypto_analysis_tasks(self, symbols: List[str]) -> List[Dict]:
        """Create crypto analysis tasks"""
        try:
            return create_crypto_analysis_tasks(symbols)
        except Exception as e:
            log_exception("Error creating crypto analysis tasks", e)
            raise e
    
    def process_batch_sync(self, tasks: List[Dict]) -> Dict:
        """Process batch synchronously"""
        try:
            return batch_processor_instance.process_batch_sync(tasks)
        except Exception as e:
            log_exception("Error processing batch", e)
            raise e
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        try:
            start_time = time.time()
            
            # Get various system components status
            status_data = {
                "database": self._check_database_status(),
                "cache": self._check_cache_status(),
                "services": self._check_services_status(),
                "config": self.get_config_data(),
                "timestamp": datetime.now().isoformat(),
                "response_time": round(time.time() - start_time, 3)
            }
            
            return status_data
            
        except Exception as e:
            log_exception("Error getting system status", e)
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _check_database_status(self) -> Dict:
        """Check database connectivity and status"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            
            return {
                "status": "connected",
                "message": "Database connection successful"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Database connection failed: {str(e)}"
            }
    
    def _check_cache_status(self) -> Dict:
        """Check cache system status"""
        try:
            stats = get_cache_stats()
            return {
                "status": "active",
                "stats": stats
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Cache system error: {str(e)}"
            }
    
    def _check_services_status(self) -> Dict:
        """Check status of various services"""
        try:
            services_status = {}
            
            # Check if services can be instantiated
            try:
                self.data_fetcher
                services_status["data_fetcher"] = "active"
            except Exception as e:
                services_status["data_fetcher"] = f"error: {str(e)}"
            
            try:
                self.sentiment_analyzer
                services_status["sentiment_analyzer"] = "active"
            except Exception as e:
                services_status["sentiment_analyzer"] = f"error: {str(e)}"
            
            try:
                self.trading_strategy
                services_status["trading_strategy"] = "active"
            except Exception as e:
                services_status["trading_strategy"] = f"error: {str(e)}"
            
            return services_status
            
        except Exception as e:
            return {
                "error": f"Service check failed: {str(e)}"
            }
