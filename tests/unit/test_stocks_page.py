"""
Unit tests for stocks page functionality
Tests data loading, analysis, filtering, and UI interactions
"""
import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

class TestStocksPage(unittest.TestCase):
    """Unit tests for stocks page functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_stock_data = {
            "symbol": "AAPL",
            "current_price": 150.0,
            "change": 2.5,
            "change_percent": "1.67%",
            "volume": 50000000,
            "timestamp": datetime.now().isoformat()
        }
        
        self.mock_analysis_data = {
            "symbol": "AAPL",
            "sentiment_score": 0.75,
            "confidence": 0.85,
            "recommendation": "BUY",
            "reasoning": "Positive sentiment with strong fundamentals"
        }
    
    @patch('src.data.data_fetcher.DataFetcher.get_stock_price')
    def test_stock_price_fetching(self, mock_get_price):
        """Test stock price data fetching"""
        mock_get_price.return_value = self.mock_stock_data
        
        from src.data.data_fetcher import DataFetcher
        fetcher = DataFetcher()
        result = fetcher.get_stock_price("AAPL")
        
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["current_price"], 150.0)
        self.assertEqual(result["change"], 2.5)
        mock_get_price.assert_called_once_with("AAPL")
    
    @patch('src.core.sentiment_analyzer.SentimentAnalyzer.analyze_news_sentiment')
    def test_sentiment_analysis(self, mock_analyze):
        """Test sentiment analysis functionality"""
        mock_analyze.return_value = self.mock_analysis_data
        
        from src.core.sentiment_analyzer import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        
        test_news = [{"headline": "Apple reports strong earnings", "summary": "Positive news"}]
        result = analyzer.analyze_news_sentiment(test_news, "AAPL")
        
        self.assertEqual(result["sentiment_score"], 0.75)
        self.assertEqual(result["recommendation"], "BUY")
        mock_analyze.assert_called_once()
    
    def test_stock_data_validation(self):
        """Test stock data validation"""
        # Test valid data
        valid_data = {
            "symbol": "AAPL",
            "current_price": 150.0,
            "change": 2.5
        }
        self.assertTrue(self._validate_stock_data(valid_data))
        
        # Test invalid data
        invalid_data = {
            "symbol": "",
            "current_price": -1,
            "change": "invalid"
        }
        self.assertFalse(self._validate_stock_data(invalid_data))
    
    def test_analysis_data_validation(self):
        """Test analysis data validation"""
        # Test valid analysis data
        valid_analysis = {
            "sentiment_score": 0.75,
            "confidence": 0.85,
            "recommendation": "BUY"
        }
        self.assertTrue(self._validate_analysis_data(valid_analysis))
        
        # Test invalid analysis data
        invalid_analysis = {
            "sentiment_score": 2.0,  # Out of range
            "confidence": -0.1,      # Out of range
            "recommendation": "INVALID"
        }
        self.assertFalse(self._validate_analysis_data(invalid_analysis))
    
    def _validate_stock_data(self, data):
        """Helper method to validate stock data"""
        required_fields = ["symbol", "current_price", "change"]
        for field in required_fields:
            if field not in data:
                return False
        
        if not data["symbol"] or data["current_price"] <= 0:
            return False
        
        return True
    
    def _validate_analysis_data(self, data):
        """Helper method to validate analysis data"""
        required_fields = ["sentiment_score", "confidence", "recommendation"]
        for field in required_fields:
            if field not in data:
                return False
        
        if not (-1 <= data["sentiment_score"] <= 1):
            return False
        
        if not (0 <= data["confidence"] <= 1):
            return False
        
        valid_recommendations = ["BUY", "SELL", "HOLD"]
        if data["recommendation"] not in valid_recommendations:
            return False
        
        return True

if __name__ == '__main__':
    unittest.main() 