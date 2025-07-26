#!/usr/bin/env python3
"""
Integration tests for the tier system functionality.
Tests the complete tier management workflow including access control.
"""

import unittest
import requests
import json
import time
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.core.config import Config

class BaseIntegrationTest(unittest.TestCase):
    """Base class for integration tests with Flask app connectivity"""

    BASE_URL = "http://localhost:5001"
    MAX_WAIT_TIME = 30  # seconds

    @classmethod
    def setUpClass(cls):
        """Wait for Flask app to be available before running tests"""
        print(f"\n🔗 Waiting for Flask app at {cls.BASE_URL}...")

        for attempt in range(cls.MAX_WAIT_TIME):
            try:
                response = requests.get(f"{cls.BASE_URL}/api/tier/status", timeout=2)
                if response.status_code in [200, 404, 500]:  # Any response means app is running
                    print(f"✅ Flask app is responding (status: {response.status_code})")
                    return
            except requests.exceptions.RequestException:
                if attempt < cls.MAX_WAIT_TIME - 1:
                    print(f"⏳ Attempt {attempt + 1}/{cls.MAX_WAIT_TIME} - Flask app not ready, waiting...")
                    time.sleep(1)
                else:
                    print(f"❌ Flask app not available after {cls.MAX_WAIT_TIME} seconds")
                    print("🚀 Please start the Flask app with:")
                    print("   python3 -m flask --app src.web.app run --host=0.0.0.0 --port=5001 --debug")
                    raise unittest.SkipTest("Flask app is not running - integration tests skipped")

    def make_request(self, method, endpoint, **kwargs):
        """Make a request with proper error handling"""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = requests.request(method, url, timeout=10, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            self.fail(f"Failed to connect to Flask app at {url}: {e}")


class TierSystemIntegrationTest(BaseIntegrationTest):
    """Integration tests for tier system functionality."""

    def setUp(self):
        """Set up test environment."""
        self.test_start_time = time.time()

    def tearDown(self):
        """Clean up after test."""
        # Reset to free tier after each test
        try:
            self.make_request('POST', '/api/tier/toggle',
                            json={'tier': 'free'})
        except:
            pass  # Ignore cleanup errors

    def test_tier_status_endpoint(self):
        """Test tier status endpoint returns correct information."""
        response = self.make_request('GET', '/api/tier/status')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('current_tier', data)
        self.assertIn('features', data)
        self.assertIn('status', data)

        # Verify tier information
        self.assertIn(data['current_tier'], ['free', 'paid'])

        # Verify features structure
        features = data['features']
        self.assertIsInstance(features, dict)
        self.assertIn('dashboard', features)
        self.assertIn('stocks', features)
        self.assertIn('crypto', features)
        self.assertIn('portfolio', features)
        self.assertIn('backtesting', features)
        self.assertIn('opportunities', features)
        self.assertIn('system_status', features)

    def test_tier_toggle_to_paid(self):
        """Test toggling to paid tier."""
        response = self.make_request('POST', '/api/tier/toggle', json={'tier': 'paid'})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'success')

        # Verify tier was actually changed
        status_response = self.make_request('GET', '/api/tier/status')
        status_data = status_response.json()
        self.assertEqual(status_data['current_tier'], 'paid')

    def test_tier_toggle_to_free(self):
        """Test toggling to free tier."""
        response = self.make_request('POST', '/api/tier/toggle', json={'tier': 'free'})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'success')

        # Verify tier was actually changed
        status_response = self.make_request('GET', '/api/tier/status')
        status_data = status_response.json()
        self.assertEqual(status_data['current_tier'], 'free')

    def test_invalid_tier_toggle(self):
        """Test toggling to invalid tier returns error."""
        response = self.make_request('POST', '/api/tier/toggle', json={'tier': 'invalid'})
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn('error', data)

    def test_tier_features_access(self):
        """Test that tier features are properly configured."""
        # Test free tier features
        status_response = self.make_request('GET', '/api/tier/status')
        free_data = status_response.json()

        self.assertIn('features', free_data)
        features = free_data['features']

        # Free tier should have limited features
        self.assertTrue(features.get('dashboard', False))
        self.assertTrue(features.get('system_status', False))

        # Switch to paid tier
        self.make_request('POST', '/api/tier/toggle',
                        json={'tier': 'paid'})

        # Test paid tier features
        status_response = self.make_request('GET', '/api/tier/status')
        paid_data = status_response.json()

        paid_features = paid_data['features']

        # Paid tier should have all features
        self.assertTrue(paid_features.get('dashboard', False))
        self.assertTrue(paid_features.get('system_status', False))
        self.assertTrue(paid_features.get('stocks', False))
        self.assertTrue(paid_features.get('crypto', False))
        self.assertTrue(paid_features.get('portfolio', False))
        self.assertTrue(paid_features.get('backtesting', False))
        self.assertTrue(paid_features.get('opportunities', False))

    def test_tier_system_persistence(self):
        """Test that tier changes persist across requests."""
        # Set to paid tier
        self.make_request('POST', '/api/tier/toggle',
                        json={'tier': 'paid'})

        # Make multiple status requests to verify persistence
        for _ in range(3):
            response = self.make_request('GET', '/api/tier/status')
            data = response.json()
            self.assertEqual(data['current_tier'], 'paid')
            time.sleep(0.1)  # Small delay between requests

    def test_free_tier_access_control(self):
        """Test access control for free tier users."""
        # Set to free tier
        self.make_request('POST', '/api/tier/toggle',
                        json={'tier': 'free'})

        # Test that free tier can access allowed pages
        free_pages = ['/', '/system_status']
        for page in free_pages:
            response = self.make_request('GET', page)
            self.assertIn(response.status_code, [200, 302],
                         f"Free tier should access {page}")

        # Test that free tier is redirected from restricted pages
        restricted_pages = ['/stocks', '/crypto', '/portfolio_page',
                          '/backtest', '/opportunities']
        for page in restricted_pages:
            response = self.make_request('GET', page, allow_redirects=False)
            # Should be redirected (302) or forbidden (403)
            self.assertIn(response.status_code, [302, 403],
                         f"Free tier should be restricted from {page}")

    def test_paid_tier_full_access(self):
        """Test that paid tier has full access."""
        # Set to paid tier
        self.make_request('POST', '/api/tier/toggle',
                        json={'tier': 'paid'})

        # Test that paid tier can access all pages
        all_pages = ['/', '/system_status', '/stocks', '/crypto',
                    '/portfolio_page', '/backtest', '/opportunities']
        for page in all_pages:
            response = self.make_request('GET', page)
            self.assertEqual(response.status_code, 200,
                           f"Paid tier should access {page}")

    @unittest.skip("Performance test - uncomment to run")
    def test_tier_system_performance(self):
        """Test tier system performance under load."""
        import concurrent.futures
        import statistics

        def check_tier_status():
            start_time = time.time()
            response = self.make_request('GET', '/api/tier/status')
            end_time = time.time()

            self.assertEqual(response.status_code, 200)
            return end_time - start_time

        # Run concurrent requests
        response_times = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(check_tier_status) for _ in range(20)]
            for future in concurrent.futures.as_completed(futures):
                response_times.append(future.result())

        # Check performance metrics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)

        print(f"\nTier System Performance:")
        print(f"  Average response time: {avg_time:.3f}s")
        print(f"  Maximum response time: {max_time:.3f}s")
        print(f"  Total requests: {len(response_times)}")

        # Assert reasonable performance
        self.assertLess(avg_time, 0.5, "Average response time should be under 500ms")
        self.assertLess(max_time, 2.0, "Maximum response time should be under 2s")


class StockAnalysisIntegrationTest(unittest.TestCase):
    """Integration tests for stock analysis functionality."""

    BASE_URL = "http://localhost:5001"

    def setUp(self):
        """Set up test environment."""
        self.session = requests.Session()

    def test_stock_analysis_with_ollama(self):
        """Test stock analysis using Ollama AI provider."""
        response = self.session.post(
            f"{self.BASE_URL}/api/analyze_stock",
            json={"symbol": "AAPL", "ai_provider": "ollama"},
            headers={"Content-Type": "application/json"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify response structure - data is now wrapped in 'data' field
        self.assertIn("data", data)
        self.assertIn("status", data)
        self.assertIn("cache_status", data)

        stock_data = data["data"]

        # Verify required fields in the data section
        required_fields = [
            "symbol", "price_data", "sentiment_analysis", "trading_recommendation",
            "news_count", "timestamp"
        ]
        for field in required_fields:
            self.assertIn(field, stock_data, f"Missing required field: {field}")

        # Verify data types and values
        self.assertEqual(stock_data["symbol"], "AAPL")
        self.assertEqual(stock_data["sentiment_analysis"]["provider"], "ollama")
        self.assertIsInstance(stock_data["news_count"], int)
        self.assertGreater(stock_data["news_count"], 0)

        # Verify price data structure
        price_data = stock_data["price_data"]
        self.assertIn("current_price", price_data)
        self.assertIn("symbol", price_data)
        self.assertIsInstance(price_data["current_price"], (int, float))

        # Verify sentiment analysis structure
        sentiment_analysis = stock_data["sentiment_analysis"]
        self.assertIn("sentiment_score", sentiment_analysis)
        self.assertIn("confidence", sentiment_analysis)
        self.assertIsInstance(sentiment_analysis["sentiment_score"], (int, float))
        self.assertIsInstance(sentiment_analysis["confidence"], (int, float))

        # Verify trading recommendation structure
        trading_recommendation = stock_data["trading_recommendation"]
        self.assertIn("action", trading_recommendation)
        self.assertIn("confidence", trading_recommendation)
        self.assertIn(trading_recommendation["action"], ["BUY", "SELL", "HOLD", "CALL", "PUT"])

    def test_stock_analysis_invalid_symbol(self):
        """Test stock analysis with invalid symbol."""
        response = self.session.post(
            f"{self.BASE_URL}/api/analyze_stock",
            json={"symbol": "", "ai_provider": "ollama"},
            headers={"Content-Type": "application/json"}
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Symbol cannot be empty", data["error"])

    def test_stock_analysis_multiple_symbols(self):
        """Test stock analysis with multiple different symbols."""
        symbols = ["AAPL", "TSLA", "MSFT", "GOOGL"]

        for symbol in symbols:
            with self.subTest(symbol=symbol):
                response = self.session.post(
                    f"{self.BASE_URL}/api/analyze_stock",
                    json={"symbol": symbol, "ai_provider": "ollama"},
                    headers={"Content-Type": "application/json"}
                )

                # Some symbols might fail due to API limits, but structure should be consistent
                if response.status_code == 200:
                    data = response.json()
                    self.assertIn("data", data)
                    stock_data = data["data"]
                    self.assertEqual(stock_data["symbol"], symbol)
                    self.assertIn("sentiment_analysis", stock_data)
                    self.assertIn("trading_recommendation", stock_data)


class SystemHealthIntegrationTest(unittest.TestCase):
    """Integration tests for system health and monitoring."""

    BASE_URL = "http://localhost:5001"

    def setUp(self):
        """Set up test environment."""
        self.session = requests.Session()

    def test_go_services_health_endpoint(self):
        """Test Go services health monitoring."""
        response = self.session.get(f"{self.BASE_URL}/api/go_services/health")

        # Should return data even if Go services are not running
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Should contain service information
        self.assertIsInstance(data, dict)
        # Basic structure validation - specific services depend on actual implementation

    def test_telegram_test_endpoint(self):
        """Test Telegram functionality endpoint."""
        response = self.session.get(f"{self.BASE_URL}/api/telegram/test")

        # Should return status information
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("working", data)
        self.assertIsInstance(data["working"], bool)

    def test_news_services_status_endpoint(self):
        """Test news services status endpoint."""
        response = self.session.get(f"{self.BASE_URL}/api/news_services/status")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("services", data)
        self.assertIn("total_services", data)
        self.assertIn("active_services", data)

        # Verify service structure
        services = data["services"]
        expected_services = [
            "finnhub_news", "yahoo_news", "alpha_vantage_news",
            "reddit_news", "reddit_options_news", "crypto_news", "news_api"
        ]

        for service in expected_services:
            self.assertIn(service, services)
            service_data = services[service]
            self.assertIn("name", service_data)
            self.assertIn("enabled", service_data)
            self.assertIn("status", service_data)
            self.assertIn("description", service_data)

    def test_performance_status_endpoint(self):
        """Test performance monitoring endpoint."""
        response = self.session.get(f"{self.BASE_URL}/api/performance_status")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("config", data)
        self.assertIn("cache", data)
        self.assertIn("database", data)

        # Verify config structure
        config = data["config"]
        self.assertIn("cache_enabled", config)
        self.assertIn("debug_mode", config)
        self.assertIn("tier", config)
        self.assertIn("version", config)

        # Verify cache structure
        cache = data["cache"]
        self.assertIn("type", cache)
        self.assertIn("entries", cache)
        self.assertIsInstance(cache["entries"], int)


class PerformanceIntegrationTest(unittest.TestCase):
    """Integration tests for performance optimizations."""

    BASE_URL = "http://localhost:5001"

    def setUp(self):
        """Set up test environment."""
        self.session = requests.Session()

    def test_bulk_analysis_caching(self):
        """Test that bulk analysis results are properly cached."""
        # First call - should take longer (no cache)
        start_time = time.time()
        response1 = self.session.get(f"{self.BASE_URL}/api/sp500_analysis")
        first_call_time = time.time() - start_time

        self.assertEqual(response1.status_code, 200)
        data1 = response1.json()
        self.assertIn("results", data1)
        self.assertIn("cached", data1)
        self.assertFalse(data1.get("cached", True))  # First call should not be cached

        # Second call - should be much faster (cached)
        start_time = time.time()
        response2 = self.session.get(f"{self.BASE_URL}/api/sp500_analysis")
        second_call_time = time.time() - start_time

        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()

        # Second call should be significantly faster
        self.assertLess(second_call_time, first_call_time * 0.5)  # At least 50% faster

        # Results should be consistent
        self.assertEqual(data1["total_analyzed"], data2["total_analyzed"])

    def test_bulk_analysis_performance_limits(self):
        """Test that bulk analysis respects performance limits."""
        # Test S&P 500 analysis
        response = self.session.get(f"{self.BASE_URL}/api/sp500_analysis")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("total_analyzed", data)
        self.assertIn("note", data)

        # Should process limited number of stocks for performance
        self.assertLessEqual(data["total_analyzed"], 10)  # Should be limited
        self.assertIn("limited for performance", data["note"])

        # Test Crypto analysis
        response = self.session.get(f"{self.BASE_URL}/api/crypto_analysis")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertLessEqual(data["total_analyzed"], 8)  # Should be limited

    def test_bulk_analysis_timeout_prevention(self):
        """Test that bulk analysis completes within reasonable time."""
        endpoints = [
            "/api/sp500_analysis",
            "/api/crypto_analysis",
            "/api/watchlist_opportunities"
        ]

        for endpoint in endpoints:
            start_time = time.time()
            response = self.session.get(f"{self.BASE_URL}{endpoint}")
            execution_time = time.time() - start_time

            # Should complete within 15 seconds (our optimization target)
            self.assertLess(execution_time, 15, f"{endpoint} took too long: {execution_time:.2f}s")
            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertIn("results", data)  # Should have results

    def test_individual_stock_analysis_performance(self):
        """Test individual stock analysis performance (should be fast)."""
        start_time = time.time()

        response = self.session.post(
            f"{self.BASE_URL}/api/analyze_stock",
            json={"symbol": "AAPL"},
            headers={"Content-Type": "application/json"}
        )

        analysis_time = time.time() - start_time

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify response structure
        self.assertIn("data", data)
        self.assertIn("status", data)
        self.assertIn("cache_status", data)

        stock_data = data["data"]
        self.assertIn("symbol", stock_data)
        self.assertEqual(stock_data["symbol"], "AAPL")

        # Performance check - should complete within 30 seconds
        self.assertLess(analysis_time, 30, f"Analysis took {analysis_time:.2f}s, should be under 30s")

    def test_cache_expiration_behavior(self):
        """Test cache expiration and refresh behavior."""
        response = self.session.get(f"{self.BASE_URL}/api/performance_status")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("config", data)
        self.assertIn("cache", data)

        # Verify cache configuration
        config = data["config"]
        cache = data["cache"]

        # Check that cache is enabled and has entries
        self.assertTrue(config["cache_enabled"])
        self.assertIsInstance(cache["entries"], int)
        self.assertGreaterEqual(cache["entries"], 0)


class NewsSourcesIntegrationTest(unittest.TestCase):
    """Integration tests for news sources functionality."""

    BASE_URL = "http://localhost:5001"

    def setUp(self):
        """Set up test environment."""
        self.session = requests.Session()

    def test_news_services_testing_endpoints(self):
        """Test individual news service testing."""
        services_to_test = [
            "finnhub_news",
            "yahoo_news",
            "alpha_vantage_news",
            "reddit_news"
        ]

        for service in services_to_test:
            response = self.session.post(
                f"{self.BASE_URL}/api/news_services/test",
                json={"service_id": service},
                headers={"Content-Type": "application/json"}
            )

            # Should return test results
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("success", data)
            self.assertIn("message", data)

            # If successful, should have article count
            if data["success"]:
                self.assertIn("articles_count", data)
                self.assertGreaterEqual(data["articles_count"], 0)

    def test_sentiment_analysis_with_different_providers(self):
        """Test sentiment analysis with different AI providers."""
        providers = ["ollama", "deepseek"]

        for provider in providers:
            with self.subTest(provider=provider):
                response = self.session.post(
                    f"{self.BASE_URL}/api/analyze_stock",
                    json={"symbol": "AAPL", "ai_provider": provider},
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    data = response.json()
                    self.assertIn("data", data)
                    stock_data = data["data"]
                    self.assertIn("sentiment_analysis", stock_data)
                    sentiment = stock_data["sentiment_analysis"]
                    self.assertEqual(sentiment["provider"], provider)

    def test_mock_provider_rejection(self):
        """Test that mock provider is properly rejected."""
        response = self.session.post(
            f"{self.BASE_URL}/api/analyze_stock",
            json={"symbol": "AAPL", "ai_provider": "mock"},
            headers={"Content-Type": "application/json"}
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Mock provider is not allowed for security reasons", data["error"])


if __name__ == "__main__":
    # Run specific test suites
    import sys

    if len(sys.argv) > 1:
        # Run specific test class
        test_class = sys.argv[1]
        if test_class == "tier":
            suite = unittest.TestLoader().loadTestsFromTestCase(TierSystemIntegrationTest)
        elif test_class == "stock":
            suite = unittest.TestLoader().loadTestsFromTestCase(StockAnalysisIntegrationTest)
        elif test_class == "health":
            suite = unittest.TestLoader().loadTestsFromTestCase(SystemHealthIntegrationTest)
        elif test_class == "performance":
            suite = unittest.TestLoader().loadTestsFromTestCase(PerformanceIntegrationTest)
        elif test_class == "news":
            suite = unittest.TestLoader().loadTestsFromTestCase(NewsSourcesIntegrationTest)
        else:
            print(f"Unknown test class: {test_class}")
            sys.exit(1)
    else:
        # Run all tests
        suite = unittest.TestSuite()
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TierSystemIntegrationTest))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(StockAnalysisIntegrationTest))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(SystemHealthIntegrationTest))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(PerformanceIntegrationTest))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(NewsSourcesIntegrationTest))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)