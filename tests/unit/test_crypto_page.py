"""
Unit tests for crypto page functionality
Tests price fetching, analysis, and data validation
"""
import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

class TestCryptoPage(unittest.TestCase):
    """Unit tests for crypto page functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_crypto_data = {
            "symbol": "BTC",
            "current_price": 45000.0,
            "change_24h": 2.5,
            "market_cap": 850000000000,
            "volume_24h": 25000000000,
            "timestamp": datetime.now().isoformat()
        }
        
        self.mock_crypto_analysis = {
            "symbol": "BTC",
            "sentiment_score": 0.65,
            "confidence": 0.78,
            "recommendation": "HOLD",
            "reasoning": "Moderate positive sentiment with high volatility"
        }
    
    @patch('src.data.data_fetcher.DataFetcher.get_crypto_price')
    def test_crypto_price_fetching(self, mock_get_price):
        """Test crypto price data fetching"""
        mock_get_price.return_value = self.mock_crypto_data
        
        from src.data.data_fetcher import DataFetcher
        fetcher = DataFetcher()
        result = fetcher.get_crypto_price("BTC")
        
        self.assertEqual(result["symbol"], "BTC")
        self.assertEqual(result["current_price"], 45000.0)
        self.assertEqual(result["change_24h"], 2.5)
        self.assertEqual(result["market_cap"], 850000000000)
        mock_get_price.assert_called_once_with("BTC")
    
    @patch('src.core.sentiment_analyzer.SentimentAnalyzer.analyze_news_sentiment')
    def test_crypto_sentiment_analysis(self, mock_analyze):
        """Test crypto sentiment analysis"""
        mock_analyze.return_value = self.mock_crypto_analysis
        
        from src.core.sentiment_analyzer import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        
        test_news = [{"headline": "Bitcoin reaches new highs", "summary": "Positive crypto news"}]
        result = analyzer.analyze_news_sentiment(test_news, "BTC")
        
        self.assertEqual(result["sentiment_score"], 0.65)
        self.assertEqual(result["recommendation"], "HOLD")
        mock_analyze.assert_called_once()
    
    def test_crypto_data_validation(self):
        """Test crypto data validation"""
        # Test valid data
        valid_data = {
            "symbol": "BTC",
            "current_price": 45000.0,
            "change_24h": 2.5,
            "market_cap": 850000000000
        }
        self.assertTrue(self._validate_crypto_data(valid_data))
        
        # Test invalid data
        invalid_data = {
            "symbol": "",
            "current_price": -1,
            "change_24h": "invalid",
            "market_cap": -1000
        }
        self.assertFalse(self._validate_crypto_data(invalid_data))
    
    def test_crypto_symbol_mapping(self):
        """Test crypto symbol mapping to CoinGecko IDs"""
        from src.data.data_fetcher import DataFetcher
        fetcher = DataFetcher()
        
        # Test symbol mapping
        test_cases = [
            ("BTC", "bitcoin"),
            ("ETH", "ethereum"),
            ("SOL", "solana"),
            ("USDT", "tether"),
            ("BTCUSD", "bitcoin"),
            ("ETHUSD", "ethereum")
        ]
        
        for symbol, expected_id in test_cases:
            with patch.object(fetcher, 'get_crypto_price') as mock_get:
                mock_get.return_value = self.mock_crypto_data
                result = fetcher.get_crypto_price(symbol)
                self.assertIsNotNone(result)
    
    def test_crypto_watchlist_management(self):
        """Test crypto watchlist management"""
        from src.core.watchlist_manager import watchlist_manager
        
        # Test adding crypto
        test_symbol = "ADA"
        watchlist_manager.add_crypto(test_symbol)
        cryptos = watchlist_manager.get_cryptos()
        self.assertIn(test_symbol, cryptos)
        
        # Test removing crypto
        watchlist_manager.remove_crypto(test_symbol)
        cryptos = watchlist_manager.get_cryptos()
        self.assertNotIn(test_symbol, cryptos)
    
    def test_crypto_analysis_batch_processing(self):
        """Test crypto analysis batch processing"""
        from src.core.batch_processor import create_crypto_analysis_tasks
        
        test_symbols = ["BTC", "ETH", "SOL"]
        
        with patch('src.core.batch_processor.batch_processor_instance') as mock_processor:
            mock_processor.add_task.return_value = True
            result = create_crypto_analysis_tasks(test_symbols)
            
            # Should create tasks for each symbol
            self.assertEqual(mock_processor.add_task.call_count, len(test_symbols))
    
    def _validate_crypto_data(self, data):
        """Helper method to validate crypto data"""
        required_fields = ["symbol", "current_price", "change_24h", "market_cap"]
        for field in required_fields:
            if field not in data:
                return False
        
        if not data["symbol"] or data["current_price"] <= 0:
            return False
        
        if data["market_cap"] <= 0:
            return False
        
        return True

if __name__ == '__main__':
    unittest.main() 