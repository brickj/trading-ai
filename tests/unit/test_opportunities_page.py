"""
Unit tests for opportunities page functionality
Tests news monitoring, opportunity generation, and data validation
"""
import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta

class TestOpportunitiesPage(unittest.TestCase):
    """Unit tests for opportunities page functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_news_opportunity = {
            "symbol": "AAPL",
            "headline": "Apple Reports Strong Earnings",
            "summary": "Apple exceeded analyst expectations",
            "sentiment_score": 0.85,
            "confidence": 0.92,
            "recommendation": "BUY",
            "timestamp": datetime.now().isoformat(),
            "source": "Yahoo Finance"
        }
        
        self.mock_watchlist_opportunity = {
            "symbol": "MSFT",
            "current_price": 350.0,
            "change_percent": 2.5,
            "sentiment_score": 0.75,
            "confidence": 0.88,
            "recommendation": "BUY",
            "timestamp": datetime.now().isoformat()
        }
    
    @patch('src.data.news_monitor.NewsMonitor.scan_trending_news')
    def test_news_monitoring(self, mock_scan):
        """Test news monitoring functionality"""
        mock_scan.return_value = {
            "AAPL": [
                {"headline": "Apple Reports Strong Earnings", "summary": "Positive news"},
                {"headline": "Apple Stock Rises", "summary": "More positive news"}
            ]
        }
        
        from src.data.news_monitor import NewsMonitor
        monitor = NewsMonitor()
        trending_symbols = monitor.scan_trending_news()
        
        self.assertIn("AAPL", trending_symbols)
        self.assertEqual(len(trending_symbols["AAPL"]), 2)
        mock_scan.assert_called_once()
    
    @patch('src.data.news_monitor.NewsMonitor.analyze_news_driven_opportunities')
    def test_opportunity_generation(self, mock_analyze):
        """Test opportunity generation from news"""
        mock_analyze.return_value = [self.mock_news_opportunity]
        
        from src.data.news_monitor import NewsMonitor
        monitor = NewsMonitor()
        
        trending_symbols = {"AAPL": [{"headline": "Test", "summary": "Test"}]}
        opportunities = monitor.analyze_news_driven_opportunities(trending_symbols)
        
        self.assertEqual(len(opportunities), 1)
        self.assertEqual(opportunities[0]["symbol"], "AAPL")
        self.assertEqual(opportunities[0]["recommendation"], "BUY")
        mock_analyze.assert_called_once_with(trending_symbols)
    
    @patch('src.data.preload_watchlist_opportunities.preload_watchlist_opportunities')
    def test_watchlist_opportunities(self, mock_preload):
        """Test watchlist opportunity generation"""
        mock_preload.return_value = [self.mock_watchlist_opportunity]
        
        from src.data.preload_watchlist_opportunities import preload_watchlist_opportunities
        opportunities = preload_watchlist_opportunities()
        
        self.assertEqual(len(opportunities), 1)
        self.assertEqual(opportunities[0]["symbol"], "MSFT")
        self.assertEqual(opportunities[0]["recommendation"], "BUY")
        mock_preload.assert_called_once()
    
    def test_opportunity_data_validation(self):
        """Test opportunity data validation"""
        # Test valid news opportunity
        valid_news_opp = {
            "symbol": "AAPL",
            "headline": "Test headline",
            "summary": "Test summary",
            "sentiment_score": 0.85,
            "confidence": 0.92,
            "recommendation": "BUY"
        }
        self.assertTrue(self._validate_news_opportunity(valid_news_opp))
        
        # Test invalid news opportunity
        invalid_news_opp = {
            "symbol": "",
            "headline": "",
            "sentiment_score": 2.0,  # Out of range
            "confidence": -0.1,      # Out of range
            "recommendation": "INVALID"
        }
        self.assertFalse(self._validate_news_opportunity(invalid_news_opp))
    
    def test_opportunity_filtering(self):
        """Test opportunity filtering by sentiment and confidence"""
        opportunities = [
            {"symbol": "AAPL", "sentiment_score": 0.85, "confidence": 0.92, "recommendation": "BUY"},
            {"symbol": "MSFT", "sentiment_score": 0.75, "confidence": 0.88, "recommendation": "BUY"},
            {"symbol": "GOOGL", "sentiment_score": 0.45, "confidence": 0.60, "recommendation": "HOLD"},
            {"symbol": "META", "sentiment_score": -0.30, "confidence": 0.70, "recommendation": "SELL"}
        ]
        
        # Filter high sentiment opportunities
        high_sentiment = [opp for opp in opportunities if opp["sentiment_score"] >= 0.7]
        self.assertEqual(len(high_sentiment), 2)
        self.assertIn("AAPL", [opp["symbol"] for opp in high_sentiment])
        self.assertIn("MSFT", [opp["symbol"] for opp in high_sentiment])
        
        # Filter high confidence opportunities
        high_confidence = [opp for opp in opportunities if opp["confidence"] >= 0.8]
        self.assertEqual(len(high_confidence), 2)
        self.assertIn("AAPL", [opp["symbol"] for opp in high_confidence])
        self.assertIn("MSFT", [opp["symbol"] for opp in high_confidence])
    
    @patch('src.core.database.get_db_connection')
    def test_opportunity_storage(self, mock_db):
        """Test opportunity storage in database"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        from src.data.preload_news_opportunities import preload_news_opportunities
        
        # Mock the monitor to return test opportunities
        with patch('src.data.news_monitor.NewsMonitor') as mock_monitor_class:
            mock_monitor = mock_monitor_class.return_value
            mock_monitor.scan_trending_news.return_value = {"AAPL": [{"headline": "Test", "summary": "Test"}]}
            mock_monitor.analyze_news_driven_opportunities.return_value = [self.mock_news_opportunity]
            
            preload_news_opportunities()
            
            # Verify database operations were called
            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called()
    
    def test_opportunity_timestamp_validation(self):
        """Test opportunity timestamp validation"""
        # Test recent opportunity
        recent_opp = self.mock_news_opportunity.copy()
        recent_opp["timestamp"] = datetime.now().isoformat()
        self.assertTrue(self._validate_timestamp(recent_opp["timestamp"]))
        
        # Test old opportunity
        old_opp = self.mock_news_opportunity.copy()
        old_opp["timestamp"] = (datetime.now() - timedelta(days=7)).isoformat()
        self.assertFalse(self._validate_timestamp(old_opp["timestamp"], max_age_hours=24))
    
    def _validate_news_opportunity(self, opportunity):
        """Helper method to validate news opportunity data"""
        required_fields = ["symbol", "headline", "summary", "sentiment_score", "confidence", "recommendation"]
        for field in required_fields:
            if field not in opportunity:
                return False
        
        if not opportunity["symbol"] or not opportunity["headline"]:
            return False
        
        if not (-1 <= opportunity["sentiment_score"] <= 1):
            return False
        
        if not (0 <= opportunity["confidence"] <= 1):
            return False
        
        valid_recommendations = ["BUY", "SELL", "HOLD"]
        if opportunity["recommendation"] not in valid_recommendations:
            return False
        
        return True
    
    def _validate_timestamp(self, timestamp, max_age_hours=168):  # Default 7 days
        """Helper method to validate timestamp freshness"""
        try:
            timestamp_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            age_hours = (datetime.now() - timestamp_dt).total_seconds() / 3600
            return age_hours <= max_age_hours
        except (ValueError, TypeError):
            return False

if __name__ == '__main__':
    unittest.main() 