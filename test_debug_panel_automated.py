#!/usr/bin/env python3
"""
Automated Test for /stocks Page Display
Tests that the /stocks page loads properly and displays data
"""

import sys
import os
import time
import json
import logging
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

class StocksPageTest:
    """Test class for /stocks page functionality"""
    
    def __init__(self, base_url="http://localhost:5001", headless=True):
        """Initialize the test with the base URL and headless option"""
        self.base_url = base_url
        self.headless = headless
        self.driver = None
        self.test_results = {
            "page_load": False,
            "api_response": False,
            "data_display": False,
            "refresh_button": False,
            "refresh_data": False,
            "errors": []
        }
        
    def setup_driver(self):
        """Set up the Selenium WebDriver"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            logger.info("WebDriver initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            self.test_results["errors"].append(f"WebDriver initialization failed: {e}")
            return False
            
    def test_page_load(self):
        """Test that the /stocks page loads"""
        try:
            logger.info(f"Loading page: {self.base_url}/stocks")
            self.driver.get(f"{self.base_url}/stocks")
            
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check page title
            expected_title = "S&P 500 Winners & Losers - Options Trading AI"
            actual_title = self.driver.title
            
            if expected_title == actual_title:
                logger.info(f"Page loaded successfully with correct title: {actual_title}")
                self.test_results["page_load"] = True
            else:
                logger.error(f"Page title mismatch. Expected: {expected_title}, Got: {actual_title}")
                self.test_results["errors"].append(f"Page title mismatch: {actual_title}")
                
            # Take screenshot for verification
            self.driver.save_screenshot("stocks_page_load.png")
            return self.test_results["page_load"]
            
        except Exception as e:
            logger.error(f"Error loading page: {e}")
            self.test_results["errors"].append(f"Page load failed: {e}")
            return False
            
    def test_api_response(self):
        """Test the /api/sp500_analysis endpoint directly"""
        try:
            logger.info("Testing API endpoint: /api/sp500_analysis")
            response = requests.get(f"{self.base_url}/api/sp500_analysis")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"API response status: {response.status_code}")
                
                # Check if the response has the expected structure
                if data.get('success') and 'data' in data:
                    enhanced_analysis = data['data'].get('enhanced_analysis', [])
                    logger.info(f"API returned {len(enhanced_analysis)} stock entries")
                    
                    if enhanced_analysis:
                        self.test_results["api_response"] = True
                        return True
                    else:
                        logger.warning("API returned empty enhanced_analysis list")
                        self.test_results["errors"].append("API returned empty enhanced_analysis list")
                else:
                    logger.error(f"Invalid API response structure: {data}")
                    self.test_results["errors"].append(f"Invalid API response structure: {data}")
            else:
                logger.error(f"API request failed with status code: {response.status_code}")
                self.test_results["errors"].append(f"API request failed: {response.status_code}")
                
            return False
            
        except Exception as e:
            logger.error(f"Error testing API: {e}")
            self.test_results["errors"].append(f"API test failed: {e}")
            return False
            
    def test_data_display(self):
        """Test that data is actually displayed on the page"""
        try:
            logger.info("Testing data display on page")
            
            # Wait for the refresh button to be clickable
            refresh_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "refreshBtn"))
            )
            logger.info("Refresh button found")
            
            # Click the refresh button to load data
            refresh_btn.click()
            logger.info("Clicked refresh button")
            
            # Wait for loading spinner to disappear
            WebDriverWait(self.driver, 60).until(
                EC.invisibility_of_element_located((By.ID, "loadingSpinner"))
            )
            logger.info("Loading spinner disappeared")
            
            # Take screenshot after data should be loaded
            self.driver.save_screenshot("stocks_data_loaded.png")
            
            # Check if winners list has content
            try:
                winners_list = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "winnersList"))
                )
                winners_content = winners_list.get_attribute('innerHTML').strip()
                
                if winners_content:
                    logger.info(f"Winners list has content: {len(winners_content)} characters")
                else:
                    logger.warning("Winners list is empty")
                    self.test_results["errors"].append("Winners list is empty")
            except TimeoutException:
                logger.error("Winners list element not found")
                self.test_results["errors"].append("Winners list element not found")
                winners_content = ""
            
            # Check if losers list has content
            try:
                losers_list = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "losersList"))
                )
                losers_content = losers_list.get_attribute('innerHTML').strip()
                
                if losers_content:
                    logger.info(f"Losers list has content: {len(losers_content)} characters")
                else:
                    logger.warning("Losers list is empty")
                    self.test_results["errors"].append("Losers list is empty")
            except TimeoutException:
                logger.error("Losers list element not found")
                self.test_results["errors"].append("Losers list element not found")
                losers_content = ""
            
            # Check if stocks table has rows
            try:
                stocks_table_body = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "stocksTableBody"))
                )
                rows = stocks_table_body.find_elements(By.TAG_NAME, "tr")
                
                if rows and len(rows) > 1:  # More than just the loading row
                    logger.info(f"Stocks table has {len(rows)} rows")
                else:
                    logger.warning(f"Stocks table has only {len(rows)} rows")
                    self.test_results["errors"].append(f"Stocks table has only {len(rows)} rows")
            except TimeoutException:
                logger.error("Stocks table body element not found")
                self.test_results["errors"].append("Stocks table body element not found")
                rows = []
            
            # Check if we have data in any of these elements
            if (winners_content and "div" in winners_content.lower()) or \
               (losers_content and "div" in losers_content.lower()) or \
               (rows and len(rows) > 1):
                self.test_results["data_display"] = True
                logger.info("Data is displayed on the page")
                return True
            else:
                logger.error("No data is displayed on the page")
                self.test_results["errors"].append("No data is displayed on the page")
                return False
                
        except Exception as e:
            logger.error(f"Error testing data display: {e}")
            self.test_results["errors"].append(f"Data display test failed: {e}")
            return False
    
    def test_refresh_functionality(self):
        """Test that the refresh button works and updates the data"""
        try:
            logger.info("Testing refresh functionality")
            
            # Wait for the refresh button to be clickable
            refresh_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "refreshBtn"))
            )
            
            # Get the current lastUpdated timestamp
            last_updated_elem = self.driver.find_element(By.ID, "lastUpdated")
            initial_timestamp = last_updated_elem.text
            logger.info(f"Initial timestamp: {initial_timestamp}")
            
            # Click the refresh button
            refresh_btn.click()
            logger.info("Clicked refresh button for second time")
            
            # Wait for loading spinner to disappear
            WebDriverWait(self.driver, 60).until(
                EC.invisibility_of_element_located((By.ID, "loadingSpinner"))
            )
            logger.info("Loading spinner disappeared after refresh")
            
            # Take screenshot after refresh
            self.driver.save_screenshot("stocks_after_refresh.png")
            
            # Check if the timestamp changed
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.find_element(By.ID, "lastUpdated").text != initial_timestamp
            )
            
            new_timestamp = self.driver.find_element(By.ID, "lastUpdated").text
            logger.info(f"New timestamp: {new_timestamp}")
            
            if new_timestamp != initial_timestamp:
                logger.info("Timestamp changed after refresh")
                self.test_results["refresh_data"] = True
                return True
            else:
                logger.warning("Timestamp did not change after refresh")
                self.test_results["errors"].append("Timestamp did not change after refresh")
                return False
                
        except Exception as e:
            logger.error(f"Error testing refresh functionality: {e}")
            self.test_results["errors"].append(f"Refresh test failed: {e}")
            return False
    
    def check_console_errors(self):
        """Check for JavaScript errors in the console"""
        try:
            logs = self.driver.get_log('browser')
            errors = [log for log in logs if log['level'] == 'SEVERE']
            
            if errors:
                logger.error(f"Found {len(errors)} JavaScript errors:")
                for error in errors:
                    logger.error(f"JS Error: {error['message']}")
                    self.test_results["errors"].append(f"JS Error: {error['message']}")
                return False
            else:
                logger.info("No JavaScript errors found")
                return True
                
        except Exception as e:
            logger.error(f"Error checking console logs: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        try:
            if not self.setup_driver():
                return self.test_results
                
            # Run tests in sequence
            self.test_page_load()
            self.test_api_response()
            self.test_data_display()
            self.test_refresh_functionality()
            self.check_console_errors()
            
            # Calculate overall success
            success = all([
                self.test_results["page_load"],
                self.test_results["api_response"],
                self.test_results["data_display"],
                self.test_results["refresh_data"]
            ])
            
            self.test_results["success"] = success
            
            # Log summary
            logger.info("=== TEST SUMMARY ===")
            logger.info(f"Page Load: {'✅' if self.test_results['page_load'] else '❌'}")
            logger.info(f"API Response: {'✅' if self.test_results['api_response'] else '❌'}")
            logger.info(f"Data Display: {'✅' if self.test_results['data_display'] else '❌'}")
            logger.info(f"Refresh Functionality: {'✅' if self.test_results['refresh_data'] else '❌'}")
            logger.info(f"Overall: {'✅' if success else '❌'}")
            
            if self.test_results["errors"]:
                logger.info("=== ERRORS ===")
                for error in self.test_results["errors"]:
                    logger.info(f"❌ {error}")
            
            return self.test_results
            
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            self.test_results["errors"].append(f"Test execution failed: {e}")
            self.test_results["success"] = False
            return self.test_results
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")
    
    def save_results(self, filename="stocks_page_test_results.json"):
        """Save test results to a JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            logger.info(f"Test results saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save test results: {e}")


def main():
    """Main function to run the tests"""
    logger.info("Starting /stocks page automated test")
    
    # Create and run the test
    test = StocksPageTest()
    results = test.run_all_tests()
    test.save_results()
    
    # Exit with appropriate code
    if results["success"]:
        logger.info("All tests passed!")
        sys.exit(0)
    else:
        logger.error("Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 