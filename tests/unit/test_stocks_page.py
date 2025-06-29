import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestStocksPage(unittest.TestCase):
    """Integration tests for the Stocks page"""

    @classmethod
    def setUpClass(cls):
        """Set up the Selenium WebDriver with headless mode"""
        logger.info("Setting up WebDriver for stocks page tests")
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            cls.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            cls.base_url = 'http://localhost:5001'  # Updated port to 5001
            logger.info(f"WebDriver initialized, connecting to {cls.base_url}")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    @classmethod
    def tearDownClass(cls):
        """Tear down the Selenium WebDriver"""
        logger.info("Tearing down WebDriver")
        if hasattr(cls, 'driver'):
            cls.driver.quit()

    def setUp(self):
        """Navigate to the stocks page before each test"""
        logger.info("Navigating to stocks page")
        try:
            self.driver.get(f"{self.base_url}/stocks")
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info("Successfully loaded stocks page")
        except Exception as e:
            logger.error(f"Failed to navigate to stocks page: {e}")
            raise

    def test_page_title(self):
        """Test that the page title is correct"""
        logger.info("Testing page title")
        expected_title = "S&P 500 Winners & Losers - Options Trading AI"
        actual_title = self.driver.title
        logger.info(f"Page title: {actual_title}")
        self.assertEqual(expected_title, actual_title)

    def test_refresh_button_presence(self):
        """Test that the refresh button is present"""
        logger.info("Testing refresh button presence")
        try:
            refresh_btn = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "refreshBtn"))
            )
            logger.info("Refresh button found")
            self.assertIsNotNone(refresh_btn)
        except Exception as e:
            logger.error(f"Refresh button not found: {e}")
            raise

    def test_stocks_table_presence(self):
        """Test that the stocks table is present on the page"""
        logger.info("Testing stocks table presence")
        try:
            # First click the refresh button to load data
            refresh_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "refreshBtn"))
            )
            refresh_btn.click()
            logger.info("Clicked refresh button")
            
            # Wait for the table to be populated (may take some time)
            time.sleep(5)  # Give time for API call and rendering
            
            # Check for table body
            table_body = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "stocksTableBody"))
            )
            logger.info("Stock table body found")
            self.assertIsNotNone(table_body)
            
            # Check if table has rows (data loaded)
            rows = table_body.find_elements(By.TAG_NAME, "tr")
            logger.info(f"Found {len(rows)} rows in stock table")
            self.assertTrue(len(rows) > 0, "Stock table should have at least one row")
        except Exception as e:
            logger.error(f"Error checking stocks table: {e}")
            # Take screenshot for debugging
            self.driver.save_screenshot("test_stocks_table_failure.png")
            raise

    def test_winners_losers_presence(self):
        """Test that the winners and losers lists are present"""
        logger.info("Testing winners and losers presence")
        try:
            # First click the refresh button to load data
            refresh_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "refreshBtn"))
            )
            refresh_btn.click()
            logger.info("Clicked refresh button")
            
            # Wait for data to load
            time.sleep(5)  # Give time for API call and rendering
            
            # Check for winners list
            winners_list = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "winnersList"))
            )
            logger.info("Winners list found")
            self.assertIsNotNone(winners_list)
            
            # Check for losers list
            losers_list = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "losersList"))
            )
            logger.info("Losers list found")
            self.assertIsNotNone(losers_list)
            
            # Check if lists have content
            winners_content = winners_list.get_attribute('innerHTML')
            losers_content = losers_list.get_attribute('innerHTML')
            
            winners_content = winners_content.strip() if winners_content else ""
            losers_content = losers_content.strip() if losers_content else ""
            
            logger.info(f"Winners content length: {len(winners_content)}")
            logger.info(f"Losers content length: {len(losers_content)}")
            
            self.assertTrue(len(winners_content) > 0, "Winners list should have content")
            self.assertTrue(len(losers_content) > 0, "Losers list should have content")
        except Exception as e:
            logger.error(f"Error checking winners/losers lists: {e}")
            # Take screenshot for debugging
            self.driver.save_screenshot("test_winners_losers_failure.png")
            raise

if __name__ == "__main__":
    unittest.main() 