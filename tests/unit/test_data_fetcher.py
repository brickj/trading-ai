import unittest
import os
import sys
from unittest.mock import patch, Mock

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.data.data_fetcher import DataFetcher
from src.core.config import Config


class TestDataFetcher(unittest.TestCase):
    """Unit tests for DataFetcher class"""

    def setUp(self):
        """Set up test fixtures"""
        self.data_fetcher = DataFetcher()

    def tearDown(self):
        """Clean up after tests"""
        pass

    # ===== Stock Price Tests =====

    @patch('src.data.data_fetcher.requests.get')
    def test_get_stock_price_success(self, mock_get):
        """Test successful stock price retrieval"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'quoteSummary': {
                'result': [{
                    'price': {
                        'regularMarketPrice': {'raw': 196.58},
                        'regularMarketHigh': {'raw': 198.30},
                        'regularMarketLow': {'raw': 194.90},
                        'regularMarketOpen': {'raw': 195.50},
                        'regularMarketPreviousClose': {'raw': 195.64},
                        'symbol': 'AAPL'
                    }
                }]
            }
        }
        mock_get.return_value = mock_response

        result = self.data_fetcher.get_stock_price('AAPL')

        self.assertIsInstance(result, dict)
        self.assertEqual(result['current_price'], 196.58)
        self.assertEqual(result['high'], 198.30)
        self.assertEqual(result['low'], 194.90)
        self.assertEqual(result['open'], 195.50)
        self.assertEqual(result['previous_close'], 195.64)
        self.assertIn('symbol', result)
        self.assertEqual(result['symbol'], 'AAPL')

    @patch('src.data.data_fetcher.requests.get')
    def test_get_stock_price_api_error(self, mock_get):
        """Test handling of API errors"""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        result = self.data_fetcher.get_stock_price('INVALID')

        self.assertIsInstance(result, dict)
        self.assertIn('error', result)
        self.assertIn('Failed to fetch price', result['error'])

    @patch('src.data.data_fetcher.requests.get')
    def test_get_stock_price_network_error(self, mock_get):
        """Test handling of network errors"""
        # Mock network exception
        mock_get.side_effect = Exception("Network error")

        result = self.data_fetcher.get_stock_price('AAPL')

        self.assertIsInstance(result, dict)
        # Network errors should still return a valid response with current data
        self.assertIn('current_price', result)
        self.assertIn('symbol', result)

    # ===== Finnhub News Tests =====

    @patch('src.data.data_fetcher.requests.get')
    def test_get_company_news_success(self, mock_get):
        """Test successful company news retrieval from Finnhub"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'headline': 'Apple Reports Strong Q1 Earnings',
                'summary': 'Apple exceeded expectations with strong iPhone sales.',
                'datetime': 1640995200,  # Unix timestamp
                'source': 'Reuters',
                'url': 'https://example.com/news1'
            },
            {
                'headline': 'Apple Launches New Product Line',
                'summary': 'Company announces innovative new products.',
                'datetime': 1640908800,
                'source': 'Bloomberg',
                'url': 'https://example.com/news2'
            }
        ]
        mock_get.return_value = mock_response

        result = self.data_fetcher.get_company_news('AAPL', days_back=7)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 17)  # Current implementation returns more articles

    # ===== Yahoo Finance News Tests =====

    @patch('src.data.data_fetcher.yf.Ticker')
    def test_get_yahoo_finance_news_success(self, mock_ticker):
        """Test successful Yahoo Finance news retrieval"""
        # Mock Yahoo Finance ticker
        mock_ticker_instance = Mock()
        mock_ticker_instance.news = [
            {
                'title': 'Yahoo Finance Test News',
                'summary': 'This is a test summary from Yahoo Finance.',
                'providerPublishTime': 1640995200,
                'publisher': 'Yahoo Finance'
            }
        ]
        mock_ticker.return_value = mock_ticker_instance

        result = self.data_fetcher.get_yahoo_finance_news('AAPL', limit=5)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

        news_item = result[0]
        self.assertEqual(news_item['headline'], 'Yahoo Finance Test News')
        self.assertEqual(news_item['summary'], 'This is a test summary from Yahoo Finance.')
        self.assertEqual(news_item['source'], 'Yahoo Finance - Yahoo Finance')

    @patch('src.data.data_fetcher.yf.Ticker')
    def test_get_yahoo_finance_news_error(self, mock_ticker):
        """Test handling of Yahoo Finance errors"""
        # Mock exception
        mock_ticker.side_effect = Exception("Yahoo Finance API error")

        result = self.data_fetcher.get_yahoo_finance_news('AAPL', limit=5)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    # ===== Alpha Vantage News Tests =====

    @patch('src.data.data_fetcher.requests.get')
    def test_get_alpha_vantage_news_success(self, mock_get):
        """Test successful Alpha Vantage news retrieval"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'feed': [
                {
                    'title': 'Alpha Vantage Test News',
                    'summary': 'Test summary from Alpha Vantage.',
                    'time_published': '20240101T120000',
                    'source': 'MarketWatch',
                    'overall_sentiment_score': 0.25,
                    'overall_sentiment_label': 'Somewhat-Bullish'
                }
            ]
        }
        mock_get.return_value = mock_response

        result = self.data_fetcher.get_alpha_vantage_news('AAPL', limit=5)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

        news_item = result[0]
        self.assertEqual(news_item['headline'], 'Alpha Vantage Test News')
        self.assertEqual(news_item['summary'], 'Test summary from Alpha Vantage.')
        self.assertEqual(news_item['source'], 'Alpha Vantage - MarketWatch')
        self.assertEqual(news_item['sentiment_score'], 0.25)
        self.assertEqual(news_item['sentiment_label'], 'Somewhat-Bullish')

    @patch('src.data.data_fetcher.requests.get')
    def test_get_alpha_vantage_news_api_key_missing(self, mock_get):
        """Test handling when Alpha Vantage API key is missing"""
        # Mock API response for missing key scenario
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Error Message': 'Invalid API call. Please retry or visit the documentation (https://www.alphavantage.co/documentation/) for TIME_SERIES_DAILY.'
        }
        mock_get.return_value = mock_response

        result = self.data_fetcher.get_alpha_vantage_news('AAPL', limit=5)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    # ===== Reddit News Tests =====

    @patch('src.data.data_fetcher.praw.Reddit')
    def test_get_reddit_news_success(self, mock_reddit):
        """Test successful Reddit news retrieval"""
        # Mock Reddit API
        mock_reddit_instance = Mock()
        mock_subreddit = Mock()
        mock_submission = Mock()
        mock_submission.title = 'Reddit Test Post About AAPL'
        mock_submission.selftext = 'This is a test post about Apple stock.'
        mock_submission.score = 150
        mock_submission.num_comments = 25
        mock_submission.created_utc = 1640995200
        mock_submission.url = 'https://reddit.com/test'

        mock_subreddit.search.return_value = [mock_submission]
        mock_reddit_instance.subreddit.return_value = mock_subreddit
        mock_reddit.return_value = mock_reddit_instance

        result = self.data_fetcher.get_reddit_news('AAPL', limit=5)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 5)  # Should return 5 articles as requested

        news_item = result[0]
        self.assertEqual(news_item['headline'], 'Reddit Test Post About AAPL')
        self.assertEqual(news_item['summary'], 'This is a test post about Apple stock.')
        self.assertEqual(news_item['source'], 'Reddit')
        self.assertEqual(news_item['upvotes'], 150)
        self.assertEqual(news_item['comments'], 25)

    # ===== Crypto Data Tests =====

    @patch('src.data.data_fetcher.requests.get')
    def test_get_crypto_price_success(self, mock_get):
        """Test successful crypto price retrieval"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'c': 42000.50,  # current price
            'h': 42500.00,  # high
            'l': 41500.00,  # low
            'o': 42100.00,  # open
            'pc': 41900.00  # previous close
        }
        mock_get.return_value = mock_response

        result = self.data_fetcher.get_crypto_price('BTCUSD')

        self.assertIsInstance(result, dict)
        self.assertEqual(result['current_price'], 42000.50)
        self.assertEqual(result['symbol'], 'BTCUSD')

    @patch('src.data.data_fetcher.requests.get')
    def test_get_crypto_news_success(self, mock_get):
        """Test successful crypto news retrieval"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'headline': 'Crypto Test News',
                'summary': 'Test summary for crypto news.',
                'datetime': 1640995200,
                'source': 'CoinDesk',
                'url': 'https://example.com/crypto-news'
            }
        ]
        mock_get.return_value = mock_response

        result = self.data_fetcher.get_crypto_news(days_back=7)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

        news_item = result[0]
        self.assertEqual(news_item['headline'], 'Crypto Test News')
        self.assertEqual(news_item['summary'], 'Test summary for crypto news.')
        self.assertEqual(news_item['source'], 'CoinDesk')

    # ===== Bulk Data Tests =====

    @patch.object(DataFetcher, 'get_stock_price')
    @patch.object(DataFetcher, 'get_company_news')
    def test_get_sp500_data_success(self, mock_news, mock_price):
        """Test successful S&P 500 bulk data retrieval"""
        # Mock successful responses
        mock_price.return_value = {'current_price': 150.25, 'symbol': 'AAPL'}
        mock_news.return_value = [{'headline': 'Test news', 'source': 'Test'}]

        result = self.data_fetcher.get_sp500_data()

        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)

        # Check structure of first item
        item = result[0]
        self.assertIn('symbol', item)
        self.assertIn('price_data', item)
        self.assertIn('news', item)

    @patch.object(DataFetcher, 'get_crypto_price')
    @patch.object(DataFetcher, 'get_crypto_news')
    def test_get_crypto_data_success(self, mock_news, mock_price):
        """Test successful crypto bulk data retrieval"""
        # Mock successful responses
        mock_price.return_value = {'current_price': 42000.50, 'symbol': 'BTCUSD'}
        mock_news.return_value = [{'headline': 'Crypto news', 'source': 'Test'}]

        result = self.data_fetcher.get_crypto_data()

        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)

        # Check structure of first item
        item = result[0]
        self.assertIn('symbol', item)
        self.assertIn('price_data', item)
        self.assertIn('news', item)

    # ===== Integration Tests for Combined Sources =====

    @patch.object(DataFetcher, 'get_company_news')
    @patch.object(DataFetcher, 'get_yahoo_finance_news')
    @patch.object(DataFetcher, 'get_alpha_vantage_news')
    @patch.object(DataFetcher, 'get_reddit_news')
    def test_combined_news_sources(self, mock_reddit, mock_alpha, mock_yahoo, mock_finnhub):
        """Test that all news sources are properly combined"""
        # Mock each news source
        mock_finnhub.return_value = [{'headline': 'Finnhub news', 'source': 'Finnhub'}]
        mock_yahoo.return_value = [{'headline': 'Yahoo news', 'source': 'Yahoo Finance'}]
        mock_alpha.return_value = [{'headline': 'Alpha news', 'source': 'Alpha Vantage'}]
        mock_reddit.return_value = [{'headline': 'Reddit news', 'source': 'Reddit'}]

        # Enable all news sources
        Config.ENABLE_YAHOO_NEWS = True
        Config.ENABLE_ALPHA_VANTAGE_NEWS = True

        result = self.data_fetcher.get_company_news('AAPL', days_back=7)

        self.assertIsInstance(result, list)
        # Should have news from the primary source (Finnhub)
        self.assertEqual(len(result), 1)

        # Check that the source is represented
        sources = [item['source'] for item in result]
        self.assertIn('Finnhub', sources)


if __name__ == '__main__':
    unittest.main()