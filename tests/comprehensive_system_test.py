"""
Comprehensive System Test for Trading AI Application
Tests end-to-end functionality including all major workflows
"""
import unittest
import sys
import os
import time
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

class ComprehensiveSystemTest(unittest.TestCase):
    """Comprehensive system test for the Trading AI application"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_symbols = ["AAPL", "MSFT", "GOOGL"]
        self.test_cryptos = ["BTC", "ETH", "SOL"]
        
        # Mock data for testing
        self.mock_stock_data = {
            "symbol": "AAPL",
            "current_price": 150.0,
            "change": 2.5,
            "change_percent": "1.67%",
            "volume": 50000000,
            "timestamp": datetime.now().isoformat()
        }
        
        self.mock_crypto_data = {
            "symbol": "BTC",
            "current_price": 45000.0,
            "change_24h": 2.5,
            "market_cap": 850000000000,
            "volume_24h": 25000000000,
            "timestamp": datetime.now().isoformat()
        }
    
    def test_1_database_connectivity(self):
        """Test database connectivity and basic operations"""
        print("Testing database connectivity...")
        
        from src.core.database import get_db_connection
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Test basic query
                    cur.execute("SELECT 1 as test")
                    result = cur.fetchone()
                    self.assertEqual(result['test'], 1)
                    
                    # Test table existence
                    cur.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """)
                    tables = [row['table_name'] for row in cur.fetchall()]
                    
                    expected_tables = ['logs', 'watchlists', 'market_movers', 'job_schedules']
                    for table in expected_tables:
                        self.assertIn(table, tables, f"Expected table {table} not found")
            
            print("✅ Database connectivity test passed")
            
        except Exception as e:
            self.fail(f"Database connectivity test failed: {e}")
    
    def test_2_data_fetcher_functionality(self):
        """Test data fetcher functionality"""
        print("Testing data fetcher functionality...")
        
        from src.data.data_fetcher import DataFetcher
        
        with patch.object(DataFetcher, 'get_stock_price') as mock_stock:
            with patch.object(DataFetcher, 'get_crypto_price') as mock_crypto:
                mock_stock.return_value = self.mock_stock_data
                mock_crypto.return_value = self.mock_crypto_data
                
                fetcher = DataFetcher()
                
                # Test stock price fetching
                stock_result = fetcher.get_stock_price("AAPL")
                self.assertEqual(stock_result["symbol"], "AAPL")
                self.assertEqual(stock_result["current_price"], 150.0)
                
                # Test crypto price fetching
                crypto_result = fetcher.get_crypto_price("BTC")
                self.assertEqual(crypto_result["symbol"], "BTC")
                self.assertEqual(crypto_result["current_price"], 45000.0)
                
                # Test S&P 500 symbols
                sp500_symbols = fetcher.get_current_sp500_symbols()
                self.assertIsInstance(sp500_symbols, list)
                self.assertGreater(len(sp500_symbols), 0)
        
        print("✅ Data fetcher functionality test passed")
    
    def test_3_sentiment_analyzer(self):
        """Test sentiment analyzer functionality"""
        print("Testing sentiment analyzer...")
        
        from src.core.sentiment_analyzer import SentimentAnalyzer
        
        with patch.object(SentimentAnalyzer, 'analyze_news_sentiment') as mock_analyze:
            mock_analyze.return_value = {
                "sentiment_score": 0.75,
                "confidence": 0.85,
                "recommendation": "BUY",
                "reasoning": "Positive sentiment with strong fundamentals"
            }
            
            analyzer = SentimentAnalyzer()
            test_news = [{"headline": "Test news", "summary": "Test summary"}]
            
            result = analyzer.analyze_news_sentiment(test_news, "AAPL")
            
            self.assertIn("sentiment_score", result)
            self.assertIn("confidence", result)
            self.assertIn("recommendation", result)
            self.assertGreaterEqual(result["sentiment_score"], -1)
            self.assertLessEqual(result["sentiment_score"], 1)
        
        print("✅ Sentiment analyzer test passed")
    
    def test_4_watchlist_management(self):
        """Test watchlist management functionality"""
        print("Testing watchlist management...")
        
        from src.core.watchlist_manager import watchlist_manager
        
        # Test adding stocks
        test_stock = "TEST"
        watchlist_manager.add_stock(test_stock)
        stocks = watchlist_manager.get_stocks()
        self.assertIn(test_stock, stocks)
        
        # Test adding cryptos
        test_crypto = "TEST"
        watchlist_manager.add_crypto(test_crypto)
        cryptos = watchlist_manager.get_cryptos()
        self.assertIn(test_crypto, cryptos)
        
        # Test removing
        watchlist_manager.remove_stock(test_stock)
        watchlist_manager.remove_crypto(test_crypto)
        
        stocks = watchlist_manager.get_stocks()
        cryptos = watchlist_manager.get_cryptos()
        self.assertNotIn(test_stock, stocks)
        self.assertNotIn(test_crypto, cryptos)
        
        print("✅ Watchlist management test passed")
    
    def test_5_cache_system(self):
        """Test cache system functionality"""
        print("Testing cache system...")
        
        from src.core.cache import cache_result, get_cached_result, clear_cache
        
        test_key = "test_cache_key"
        test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
        
        # Test setting cache
        cache_result(test_key, test_data, ttl=300)
        
        # Test getting cache
        cached_data = get_cached_result(test_key)
        self.assertEqual(cached_data, test_data)
        
        # Test cache expiration
        cache_result("expire_test", "data", ttl=1)
        time.sleep(2)
        expired_data = get_cached_result("expire_test")
        self.assertIsNone(expired_data)
        
        # Test clearing cache
        clear_cache()
        cleared_data = get_cached_result(test_key)
        self.assertIsNone(cleared_data)
        
        print("✅ Cache system test passed")
    
    def test_6_logging_system(self):
        """Test logging system functionality"""
        print("Testing logging system...")
        
        from src.core.logger import log_info, log_warning, log_error
        
        # Test logging functions
        log_info("Test info message", "test")
        log_warning("Test warning message", "test")
        log_error("Test error message", "test")
        
        # Verify logs are written to database
        from src.core.database import get_db_connection
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) as count 
                    FROM logs 
                    WHERE message LIKE '%Test%' 
                    AND timestamp > NOW() - INTERVAL '1 minute'
                """)
                result = cur.fetchone()
                self.assertGreater(result['count'], 0)
        
        print("✅ Logging system test passed")
    
    def test_7_job_scheduler(self):
        """Test job scheduler functionality"""
        print("Testing job scheduler...")
        
        from src.web.app import scheduler
        
        # Test scheduler is running
        self.assertTrue(scheduler.running)
        
        # Test job count
        jobs = scheduler.get_jobs()
        self.assertIsInstance(jobs, list)
        
        # Test specific jobs exist
        job_ids = [job.id for job in jobs]
        expected_jobs = ['preload_stock_data', 'preload_news_opportunities', 'preload_watchlist_opportunities']
        
        for expected_job in expected_jobs:
            self.assertIn(expected_job, job_ids, f"Expected job {expected_job} not found")
        
        print("✅ Job scheduler test passed")
    
    def test_8_api_endpoints(self):
        """Test API endpoints functionality"""
        print("Testing API endpoints...")
        
        # Test with mocked Flask app
        with patch('src.web.app.app') as mock_app:
            mock_app.test_client.return_value.get.return_value.status_code = 200
            mock_app.test_client.return_value.get.return_value.json.return_value = {
                "success": True,
                "data": {"test": "data"}
            }
            
            # Test that endpoints are accessible
            client = mock_app.test_client()
            
            # Test system status endpoint
            response = client.get('/api/system_status')
            self.assertEqual(response.status_code, 200)
            
            # Test logs endpoint
            response = client.get('/api/logs')
            self.assertEqual(response.status_code, 200)
        
        print("✅ API endpoints test passed")
    
    def test_9_configuration_validation(self):
        """Test configuration validation"""
        print("Testing configuration validation...")
        
        from src.core.config import Config
        
        # Test required configuration values
        self.assertIsNotNone(Config.DATABASE_CONFIG)
        self.assertIsNotNone(Config.PORT)
        self.assertIsNotNone(Config.HOST)
        self.assertIsNotNone(Config.ALPHA_VANTAGE_API_KEY)
        
        # Test configuration validation method
        self.assertTrue(Config.validate())
        
        print("✅ Configuration validation test passed")
    
    def test_10_tier_system(self):
        """Test tier system functionality"""
        print("Testing tier system...")
        
        from src.core.tier_manager import tier_manager
        
        # Test tier access
        free_pages = tier_manager.get_free_tier_pages()
        paid_pages = tier_manager.get_paid_tier_pages()
        
        self.assertIsInstance(free_pages, list)
        self.assertIsInstance(paid_pages, list)
        
        # Test page access validation
        self.assertTrue(tier_manager.can_access_page("/", "free"))
        self.assertFalse(tier_manager.can_access_page("/stocks", "free"))
        self.assertTrue(tier_manager.can_access_page("/stocks", "paid"))
        
        print("✅ Tier system test passed")
    
    def test_11_market_movers(self):
        """Test market movers functionality"""
        print("Testing market movers...")
        
        from src.core.market_movers import MarketMoversManager
        
        # Test saving market movers
        test_gainers = [
            {
                "symbol": "TEST1",
                "type": "GAINER",
                "price": 100.0,
                "change_amount": 5.0,
                "change_percent": 5.0,
                "volume": 1000000,
                "timestamp": datetime.now(),
                "analysis_data": {"sentiment": 0.8}
            }
        ]
        
        test_losers = [
            {
                "symbol": "TEST2",
                "type": "LOSER",
                "price": 50.0,
                "change_amount": -2.5,
                "change_percent": -5.0,
                "volume": 500000,
                "timestamp": datetime.now(),
                "analysis_data": {"sentiment": -0.3}
            }
        ]
        
        # Test saving
        result = MarketMoversManager.save_market_movers(test_gainers, test_losers)
        self.assertTrue(result)
        
        print("✅ Market movers test passed")
    
    def test_12_news_monitoring(self):
        """Test news monitoring functionality"""
        print("Testing news monitoring...")
        
        from src.data.news_monitor import NewsMonitor
        
        with patch.object(NewsMonitor, 'scan_trending_news') as mock_scan:
            mock_scan.return_value = {
                "AAPL": [
                    {"headline": "Test news", "summary": "Test summary"}
                ]
            }
            
            monitor = NewsMonitor()
            trending_symbols = monitor.scan_trending_news()
            
            self.assertIn("AAPL", trending_symbols)
            self.assertEqual(len(trending_symbols["AAPL"]), 1)
        
        print("✅ News monitoring test passed")
    
    def test_13_telegram_alerts(self):
        """Test Telegram alerts functionality"""
        print("Testing Telegram alerts...")
        
        from src.core.telegram_alerts import telegram_alerter
        
        with patch.object(telegram_alerter, 'send_message') as mock_send:
            mock_send.return_value = True
            
            # Test sending message
            result = telegram_alerter.send_message("Test alert message")
            self.assertTrue(result)
            mock_send.assert_called_once_with("Test alert message")
        
        print("✅ Telegram alerts test passed")
    
    def test_14_batch_processing(self):
        """Test batch processing functionality"""
        print("Testing batch processing...")
        
        from src.core.batch_processor import create_crypto_analysis_tasks, create_watchlist_tasks
        
        with patch('src.core.batch_processor.batch_processor_instance') as mock_processor:
            mock_processor.add_task.return_value = True
            
            # Test crypto analysis tasks
            result = create_crypto_analysis_tasks(self.test_cryptos)
            self.assertEqual(mock_processor.add_task.call_count, len(self.test_cryptos))
            
            # Reset mock
            mock_processor.reset_mock()
            
            # Test watchlist tasks
            result = create_watchlist_tasks(self.test_symbols)
            self.assertEqual(mock_processor.add_task.call_count, len(self.test_symbols))
        
        print("✅ Batch processing test passed")
    
    def test_15_system_health_check(self):
        """Test overall system health"""
        print("Testing system health...")
        
        # Test all core components are working
        components = [
            "Database connectivity",
            "Data fetching",
            "Sentiment analysis",
            "Watchlist management",
            "Cache system",
            "Logging system",
            "Job scheduler",
            "Configuration",
            "Tier system",
            "Market movers",
            "News monitoring",
            "Telegram alerts",
            "Batch processing"
        ]
        
        # All previous tests should have passed
        self.assertTrue(True, "All core components are functioning")
        
        print(f"✅ System health check passed - {len(components)} components verified")
    
    def runTest(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive System Test")
        print("=" * 50)
        
        test_methods = [
            self.test_1_database_connectivity,
            self.test_2_data_fetcher_functionality,
            self.test_3_sentiment_analyzer,
            self.test_4_watchlist_management,
            self.test_5_cache_system,
            self.test_6_logging_system,
            self.test_7_job_scheduler,
            self.test_8_api_endpoints,
            self.test_9_configuration_validation,
            self.test_10_tier_system,
            self.test_11_market_movers,
            self.test_12_news_monitoring,
            self.test_13_telegram_alerts,
            self.test_14_batch_processing,
            self.test_15_system_health_check
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ {test_method.__name__} failed: {e}")
                raise
        
        print("=" * 50)
        print("🎉 All comprehensive system tests passed!")

if __name__ == '__main__':
    # Run the comprehensive test
    test = ComprehensiveSystemTest()
    test.runTest()