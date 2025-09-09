#!/usr/bin/env python3
"""
Unit tests for configuration system.
Tests the Config class functionality.
"""

import unittest
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from core.config import Config


class ConfigTest(unittest.TestCase):
    """Unit tests for Config class."""

    def setUp(self):
        """Set up test environment."""
        # Tier system has been removed - no setup needed
        pass

    def tearDown(self):
        """Clean up after tests."""
        # Tier system has been removed - no cleanup needed
        pass

    def test_default_tier_configuration(self):
        """Test default tier configuration - REMOVED"""
        # Tier system has been eliminated from the application
        self.assertTrue(True, "Tier system removed")
    
    def test_tier_names_configuration(self):
        """Test tier names configuration - REMOVED"""
        # Tier system has been eliminated from the application
        self.assertTrue(True, "Tier system removed")

    def test_free_tier_pages_configuration(self):
        """Test free tier pages configuration - REMOVED"""
        # Tier system has been eliminated from the application
        self.assertTrue(True, "Tier system removed")

    def test_paid_tier_pages_configuration(self):
        """Test paid tier pages configuration - REMOVED"""
        # Tier system has been eliminated from the application
        self.assertTrue(True, "Tier system removed")

    def test_contact_info_configuration(self):
        """Test contact information configuration - REMOVED"""
        # Tier system has been eliminated from the application
        self.assertTrue(True, "Tier system removed")

    def test_ai_provider_configuration(self):
        """Test AI provider configuration."""
        self.assertEqual(Config.PREFERRED_AI_PROVIDER, "ollama")
        self.assertIn(Config.PREFERRED_AI_PROVIDER, Config.AI_PROVIDER_FALLBACKS)

        # Verify fallback order includes free options first
        fallbacks = Config.AI_PROVIDER_FALLBACKS
        self.assertIn("ollama", fallbacks)
        self.assertIn("deepseek", fallbacks)

        # OpenAI should be last (paid option)
        self.assertEqual(fallbacks[-1], "openai")

    def test_telegram_configuration(self):
        """Test Telegram configuration."""
        self.assertIsInstance(Config.TELEGRAM_CHAT_IDS, list)
        self.assertGreater(len(Config.TELEGRAM_CHAT_IDS), 0)

        # Verify alert settings
        self.assertIsInstance(Config.TELEGRAM_ALERTS_ENABLED, bool)
        self.assertIsInstance(Config.TELEGRAM_ALERT_THRESHOLD, (int, float))
        self.assertIsInstance(Config.TELEGRAM_ALERT_COOLDOWN, int)

        # Verify reasonable threshold values
        self.assertGreaterEqual(Config.TELEGRAM_ALERT_THRESHOLD, 0.0)
        self.assertLessEqual(Config.TELEGRAM_ALERT_THRESHOLD, 1.0)
        self.assertGreater(Config.TELEGRAM_ALERT_COOLDOWN, 0)

    def test_watchlist_stocks(self):
        """Test that watchlist stocks are properly configured"""
        self.assertIsInstance(Config.WATCHLIST_STOCKS, list)
        self.assertGreater(len(Config.WATCHLIST_STOCKS), 0)
        
        # Check that all symbols are valid stock symbols (no crypto)
        for symbol in Config.WATCHLIST_STOCKS:
            self.assertIsInstance(symbol, str)
            self.assertGreater(len(symbol), 0)
            # Ensure no crypto symbols (should not contain USD suffix)
            self.assertFalse(symbol.endswith('USD'))

    def test_trading_parameters(self):
        """Test trading parameters configuration."""
        # Verify sentiment threshold
        self.assertIsInstance(Config.SENTIMENT_THRESHOLD, (int, float))
        self.assertGreaterEqual(Config.SENTIMENT_THRESHOLD, 0.0)

        # Verify position size
        self.assertIsInstance(Config.MAX_POSITION_SIZE, (int, float))
        self.assertGreater(Config.MAX_POSITION_SIZE, 0)

        # Verify news parameters
        self.assertIsInstance(Config.NEWS_SENTIMENT_THRESHOLD, (int, float))
        self.assertIsInstance(Config.NEWS_CONFIDENCE_THRESHOLD, (int, float))
        self.assertGreaterEqual(Config.NEWS_CONFIDENCE_THRESHOLD, 0.0)
        self.assertLessEqual(Config.NEWS_CONFIDENCE_THRESHOLD, 1.0)

    def test_go_services_configuration(self):
        """Test Go services configuration."""
        self.assertIsInstance(Config.USE_GO_SERVICES, bool)

        # Verify service URLs
        service_urls = [
            Config.GO_NEWS_SERVICE_URL,
            Config.GO_SIGNAL_SERVICE_URL,
            Config.GO_RISK_SERVICE_URL,
            Config.GO_DATA_SERVICE_URL
        ]

        for url in service_urls:
            self.assertIsInstance(url, str)
            self.assertTrue(url.startswith("http://"))
            self.assertIn("localhost", url)

        # Verify timeout settings
        self.assertIsInstance(Config.GO_SERVICE_TIMEOUT, int)
        self.assertIsInstance(Config.GO_SERVICE_RETRY_COUNT, int)
        self.assertGreater(Config.GO_SERVICE_TIMEOUT, 0)
        self.assertGreater(Config.GO_SERVICE_RETRY_COUNT, 0)

    def test_current_tier_modification(self):
        """Test that CURRENT_TIER can be modified."""
        # Test setting to paid tier
        Config.CURRENT_TIER = "paid"
        self.assertEqual(Config.CURRENT_TIER, "paid")

        # Test setting to free tier
        Config.CURRENT_TIER = "free"
        self.assertEqual(Config.CURRENT_TIER, "free")

        # Test invalid tier (should still be settable for flexibility)
        Config.CURRENT_TIER = "invalid"
        self.assertEqual(Config.CURRENT_TIER, "invalid")

    def test_news_sources_configuration(self):
        """Test news sources configuration."""
        # Test news source enable/disable flags
        self.assertIsInstance(Config.ENABLE_YAHOO_NEWS, bool)
        self.assertIsInstance(Config.ENABLE_ALPHA_VANTAGE_NEWS, bool)
        self.assertIsInstance(Config.ENABLE_NEWSAPI_ORG, bool)

        # Test news source limits
        self.assertIsInstance(Config.YAHOO_NEWS_MAX_ARTICLES, int)
        self.assertIsInstance(Config.ALPHA_VANTAGE_NEWS_MAX_ARTICLES, int)
        self.assertGreater(Config.YAHOO_NEWS_MAX_ARTICLES, 0)
        self.assertGreater(Config.ALPHA_VANTAGE_NEWS_MAX_ARTICLES, 0)

        # Test API key configurations
        self.assertIsNotNone(Config.ALPHA_VANTAGE_API_KEY)
        self.assertIsInstance(Config.ALPHA_VANTAGE_API_KEY, str)

    def test_performance_optimization_settings(self):
        """Test performance optimization settings."""
        # Test bulk analysis cache settings
        self.assertIsInstance(Config.BULK_ANALYSIS_CACHE_DURATION, int)
        self.assertGreater(Config.BULK_ANALYSIS_CACHE_DURATION, 0)

        # Test processing limits
        self.assertIsInstance(Config.BULK_ANALYSIS_SP500_LIMIT, int)
        self.assertIsInstance(Config.BULK_ANALYSIS_CRYPTO_LIMIT, int)
        self.assertIsInstance(Config.BULK_ANALYSIS_WATCHLIST_LIMIT, int)
        self.assertIsInstance(Config.BULK_ANALYSIS_NEWS_DAYS, int)

        self.assertGreater(Config.BULK_ANALYSIS_SP500_LIMIT, 0)
        self.assertGreater(Config.BULK_ANALYSIS_CRYPTO_LIMIT, 0)
        self.assertGreater(Config.BULK_ANALYSIS_WATCHLIST_LIMIT, 0)
        self.assertGreater(Config.BULK_ANALYSIS_NEWS_DAYS, 0)

        # Test timeout settings
        self.assertIsInstance(Config.API_REQUEST_TIMEOUT, int)
        self.assertIsInstance(Config.BULK_ANALYSIS_TIMEOUT, int)
        self.assertGreater(Config.API_REQUEST_TIMEOUT, 0)
        self.assertGreater(Config.BULK_ANALYSIS_TIMEOUT, 0)

    def test_performance_limits_reasonableness(self):
        """Test that performance limits are reasonable."""
        # Ensure limits don't exceed total available items
        self.assertLessEqual(Config.BULK_ANALYSIS_SP500_LIMIT, len(Config.SP500_STOCKS))
        self.assertLessEqual(Config.BULK_ANALYSIS_CRYPTO_LIMIT, len(Config.CRYPTO_SYMBOLS))
        self.assertLessEqual(Config.BULK_ANALYSIS_WATCHLIST_LIMIT, len(Config.WATCHLIST_STOCKS))

        # Ensure news days is reasonable (not too many, not too few)
        self.assertGreaterEqual(Config.BULK_ANALYSIS_NEWS_DAYS, 1)
        self.assertLessEqual(Config.BULK_ANALYSIS_NEWS_DAYS, 14)  # Max 2 weeks

        # Ensure cache duration is reasonable (5-30 minutes)
        self.assertGreaterEqual(Config.BULK_ANALYSIS_CACHE_DURATION, 300)  # 5 minutes
        self.assertLessEqual(Config.BULK_ANALYSIS_CACHE_DURATION, 1800)   # 30 minutes


class TierLogicTest(unittest.TestCase):
    """Unit tests for tier-related logic - REMOVED."""

    def test_page_categorization(self):
        """Test that pages are properly categorized - REMOVED."""
        # Tier system has been eliminated from the application
        self.assertTrue(True, "Tier system removed")

    def test_tier_access_logic(self):
        """Test tier access logic - REMOVED."""
        # Tier system has been eliminated from the application
        self.assertTrue(True, "Tier system removed")

    def test_contact_info_completeness(self):
        """Test that contact info is complete and valid - REMOVED."""
        # Tier system has been eliminated from the application
        self.assertTrue(True, "Tier system removed")


class NewsSourceConfigurationTest(unittest.TestCase):
    """Unit tests for news source configuration."""

    def test_finnhub_configuration(self):
        """Test Finnhub API configuration."""
        self.assertIsNotNone(Config.FINNHUB_API_KEY)
        self.assertIsInstance(Config.FINNHUB_API_KEY, str)
        self.assertGreater(len(Config.FINNHUB_API_KEY), 10)

    def test_reddit_configuration(self):
        """Test Reddit API configuration."""
        self.assertIsNotNone(Config.REDDIT_CLIENT_ID)
        self.assertIsNotNone(Config.REDDIT_SECRET_KEY)
        self.assertIsInstance(Config.REDDIT_CLIENT_ID, str)
        self.assertIsInstance(Config.REDDIT_SECRET_KEY, str)
        self.assertGreater(len(Config.REDDIT_CLIENT_ID), 5)
        self.assertGreater(len(Config.REDDIT_SECRET_KEY), 10)

    def test_alpha_vantage_configuration(self):
        """Test Alpha Vantage API configuration."""
        if Config.ENABLE_ALPHA_VANTAGE_NEWS:
            self.assertIsNotNone(Config.ALPHA_VANTAGE_API_KEY)
            self.assertIsInstance(Config.ALPHA_VANTAGE_API_KEY, str)
            self.assertGreater(len(Config.ALPHA_VANTAGE_API_KEY), 5)

    def test_news_source_consistency(self):
        """Test consistency between news source settings."""
        # If Alpha Vantage is enabled, API key should be present
        if Config.ENABLE_ALPHA_VANTAGE_NEWS:
            self.assertIsNotNone(Config.ALPHA_VANTAGE_API_KEY)
            self.assertNotEqual(Config.ALPHA_VANTAGE_API_KEY.strip(), "")


class PerformanceConfigurationTest(unittest.TestCase):
    """Unit tests for performance-related configuration."""

    def test_cache_configuration(self):
        """Test cache configuration settings."""
        # Cache duration should be reasonable (5-30 minutes)
        self.assertGreaterEqual(Config.BULK_ANALYSIS_CACHE_DURATION, 300)
        self.assertLessEqual(Config.BULK_ANALYSIS_CACHE_DURATION, 1800)

    def test_processing_limits_optimization(self):
        """Test that processing limits are optimized for performance."""
        # SP500 limit should be reasonable (20-50% of total)
        sp500_percentage = Config.BULK_ANALYSIS_SP500_LIMIT / len(Config.SP500_STOCKS)
        self.assertGreaterEqual(sp500_percentage, 0.2)  # At least 20%
        self.assertLessEqual(sp500_percentage, 0.6)     # At most 60%

        # Crypto limit should be reasonable
        crypto_percentage = Config.BULK_ANALYSIS_CRYPTO_LIMIT / len(Config.CRYPTO_SYMBOLS)
        self.assertGreaterEqual(crypto_percentage, 0.3)  # At least 30%
        self.assertLessEqual(crypto_percentage, 0.7)     # At most 70%

        # News days should be optimized (not too many to avoid timeouts)
        self.assertLessEqual(Config.BULK_ANALYSIS_NEWS_DAYS, 7)  # At most 1 week

    def test_timeout_settings(self):
        """Test timeout settings are reasonable."""
        # API timeout should be reasonable (5-30 seconds)
        self.assertGreaterEqual(Config.API_REQUEST_TIMEOUT, 5)
        self.assertLessEqual(Config.API_REQUEST_TIMEOUT, 30)

        # Bulk analysis timeout should be longer than API timeout
        self.assertGreater(Config.BULK_ANALYSIS_TIMEOUT, Config.API_REQUEST_TIMEOUT)
        self.assertLessEqual(Config.BULK_ANALYSIS_TIMEOUT, 60)  # At most 1 minute


if __name__ == "__main__":
    unittest.main(verbosity=2)