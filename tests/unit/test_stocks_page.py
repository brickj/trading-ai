import unittest
import json
import time
from unittest.mock import patch, MagicMock
import sys
import os
import requests
from bs4 import BeautifulSoup

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.web.app import app
from src.core.logger import trading_logger

class TestStocksPage(unittest.TestCase):
    """Test the /stocks page functionality"""

    def setUp(self):
        """Set up the test client"""
        self.app = app.test_client()
        # Configure logger for testing
        trading_logger.api_logger.info("Setting up TestStocksPage")

    def test_stocks_page_loads(self):
        """Test that the /stocks page loads correctly"""
        trading_logger.api_logger.info("Testing /stocks page load")
        response = self.app.get('/stocks')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'S&P 500 Winners & Losers Analysis', response.data)
        trading_logger.api_logger.info("Stocks page loaded successfully")

    @patch('src.data.data_fetcher.DataFetcher')
    def test_sp500_analysis_api(self, mock_data_fetcher_class):
        """Test the /api/sp500_analysis endpoint"""
        trading_logger.api_logger.info("Testing /api/sp500_analysis endpoint")
        
        # Create a mock instance
        mock_data_fetcher = mock_data_fetcher_class.return_value
        
        # Mock the data_fetcher.get_top_gainers_losers method
        mock_data_fetcher.get_top_gainers_losers.return_value = {
            "gainers": ["AAPL", "MSFT", "GOOGL"],
            "losers": ["META", "NVDA", "JPM"],
            "timestamp": "2025-06-29T12:00:00",
            "source": "test"
        }
        
        # Mock other necessary methods to prevent actual API calls
        mock_data_fetcher.get_stock_price.return_value = {
            "current_price": 150.0,
            "previous_close": 145.0,
            "change": 5.0,
            "change_percent": 3.45,
            "volume": 1000000
        }
        
        mock_data_fetcher.get_company_news.return_value = [
            {"title": "Test News", "url": "http://example.com", "source": "test"}
        ]
        
        # Test the API endpoint
        response = self.app.get('/api/sp500_analysis')
        self.assertEqual(response.status_code, 200)
        
        # Parse the response JSON
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        
        # Verify the response structure
        self.assertIn('enhanced_analysis', data['data'])
        trading_logger.api_logger.info("SP500 analysis API endpoint tested successfully")
        
        # Verify that the enhanced_analysis list contains data
        enhanced_analysis = data['data']['enhanced_analysis']
        self.assertTrue(len(enhanced_analysis) > 0, "Enhanced analysis list should not be empty")
        
        # Check if we have winners and losers
        winners = [s for s in enhanced_analysis if s.get('type') == 'winner']
        losers = [s for s in enhanced_analysis if s.get('type') == 'loser']
        
        self.assertTrue(len(winners) > 0, "Should have winners in the enhanced analysis")
        self.assertTrue(len(losers) > 0, "Should have losers in the enhanced analysis")
        
        # Verify data structure of a stock entry
        if enhanced_analysis:
            stock = enhanced_analysis[0]
            self.assertIn('symbol', stock, "Stock should have a symbol")
            self.assertIn('price_data', stock, "Stock should have price data")
            self.assertIn('sentiment_data', stock, "Stock should have sentiment data")

    def test_full_interaction_sequence(self):
        """
        Test the full interaction sequence:
        1. Load the page
        2. Wait for data to load
        3. Verify initial data
        4. Click refresh button
        5. Wait for new data
        6. Verify updated data
        """
        trading_logger.api_logger.info("Testing full interaction sequence")
        
        # Skip this test if we're running in a CI environment without a browser
        if os.environ.get('CI') == 'true':
            trading_logger.api_logger.warning("Running in CI environment, skipping Selenium test")
            self.skipTest("Running in CI environment, skipping Selenium test")
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.wait import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.common.exceptions import TimeoutException
        except ImportError:
            trading_logger.api_logger.warning("Selenium not installed, skipping full interaction test")
            self.skipTest("Selenium not installed")
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        driver = None
        try:
            # Initialize driver
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            trading_logger.api_logger.info("WebDriver initialized successfully")
            
            # Load the page
            url = "http://localhost:5001/stocks"
            trading_logger.api_logger.info(f"Loading page: {url}")
            driver.get(url)
            
            # Wait for the page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            trading_logger.api_logger.info("Page loaded successfully")
            
            # Wait for the auto-load to complete (we added setTimeout(loadSP500Data, 1000))
            try:
                # Wait for loading spinner to disappear
                WebDriverWait(driver, 60).until(
                    EC.invisibility_of_element_located((By.ID, "loadingSpinner"))
                )
                trading_logger.api_logger.info("Loading spinner disappeared after auto-load")
            except TimeoutException:
                trading_logger.api_logger.warning("Loading spinner timeout, trying to click refresh button")
                
                # If auto-load didn't work, try clicking the refresh button
                refresh_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "refreshBtn"))
                )
                trading_logger.api_logger.info("Refresh button found")
                
                # Click the refresh button
                refresh_btn.click()
                trading_logger.api_logger.info("Clicked refresh button")
                
                # Wait for loading spinner to disappear
                WebDriverWait(driver, 60).until(
                    EC.invisibility_of_element_located((By.ID, "loadingSpinner"))
                )
                trading_logger.api_logger.info("Loading spinner disappeared after clicking refresh")
            
            # Check if the winners/losers summary is now visible
            winners_losers_summary = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "winnersLosersSummary"))
            )
            is_visible = winners_losers_summary.is_displayed()
            trading_logger.api_logger.info(f"Winners/losers summary is visible: {is_visible}")
            self.assertTrue(is_visible, "Winners/losers summary should be visible")
            
            # Check if winners list has content
            winners_list = driver.find_element(By.ID, "winnersList")
            winners_content = winners_list.get_attribute('innerHTML').strip()
            trading_logger.api_logger.info(f"Winners list content length: {len(winners_content)}")
            self.assertTrue(len(winners_content) > 0, "Winners list should have content")
            
            # Check if losers list has content
            losers_list = driver.find_element(By.ID, "losersList")
            losers_content = losers_list.get_attribute('innerHTML').strip()
            trading_logger.api_logger.info(f"Losers list content length: {len(losers_content)}")
            self.assertTrue(len(losers_content) > 0, "Losers list should have content")
            
            # Check if the stocks table has rows
            stocks_table_body = driver.find_element(By.ID, "stocksTableBody")
            rows = stocks_table_body.find_elements(By.TAG_NAME, "tr")
            trading_logger.api_logger.info(f"Stocks table has {len(rows)} rows")
            self.assertTrue(len(rows) > 1, "Stocks table should have more than one row")
            
            trading_logger.api_logger.info("Full interaction sequence tested successfully")
            
        except Exception as e:
            trading_logger.api_logger.error(f"Selenium test failed: {e}")
            self.fail(f"Selenium test failed: {e}")
            
        finally:
            # Clean up
            if driver:
                driver.quit()
                trading_logger.api_logger.info("WebDriver closed")

    def test_stocks_js_functionality(self):
        """Test the stocks.js functionality directly"""
        trading_logger.api_logger.info("Testing stocks.js functionality")
        
        # Read the stocks.js file
        with open('src/web/static/js/stocks.js', 'r') as f:
            js_content = f.read()
            
        # Verify the key functions exist
        self.assertIn('loadSP500Data', js_content)
        self.assertIn('displaySP500Table', js_content)
        self.assertIn('displayWinnersLosers', js_content)
        
        # Check for potential error sources
        self.assertIn('document.addEventListener', js_content)
        
        # Check for proper error handling
        self.assertIn('try {', js_content)
        self.assertIn('catch (err) {', js_content)
        self.assertIn('finally {', js_content)
        
        # Check for specific safety checks that prevent crashes
        self.assertIn('if (!Array.isArray(stocks))', js_content, 
                      "stocks.js should check if stocks is an array")
        self.assertIn('if (winners.length === 0)', js_content, 
                      "stocks.js should handle empty winners list")
        self.assertIn('if (losers.length === 0)', js_content, 
                      "stocks.js should handle empty losers list")
        
        trading_logger.api_logger.info("Stocks.js functionality verified")

if __name__ == '__main__':
    unittest.main() 