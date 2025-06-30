#!/usr/bin/env python3
"""
Comprehensive test for the /stocks page
This test will verify that the page loads and displays data correctly
"""

import sys
import os
import time
import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

class StocksPageTest:
    """Test class for the /stocks page"""
    
    def __init__(self, base_url="http://localhost:5001", headless=True):
        """Initialize the test with the base URL and headless option"""
        self.base_url = base_url
        self.headless = headless
        self.driver = None
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "api_test": {
                "success": False,
                "response_time_ms": 0,
                "data_count": 0,
                "winners_count": 0,
                "losers_count": 0,
                "error": None
            },
            "page_test": {
                "success": False,
                "page_load_time_ms": 0,
                "data_load_time_ms": 0,
                "winners_displayed": False,
                "losers_displayed": False,
                "table_rows": 0,
                "error": None
            },
            "js_errors": []
        }
    
    def test_api_endpoint(self):
        """Test the /api/sp500_analysis endpoint directly"""
        logger.info("Testing /api/sp500_analysis endpoint...")
        
        try:
            # Make a direct request to the API
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/sp500_analysis")
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            self.test_results["api_test"]["response_time_ms"] = response_time_ms
            logger.info(f"API response status code: {response.status_code} (took {response_time_ms}ms)")
            
            if response.status_code == 200:
                # Parse the response
                data = response.json()
                logger.info(f"API response success: {data.get('success', False)}")
                
                # Check if the response has the expected structure
                if data.get('success') and 'data' in data:
                    enhanced_analysis = data['data'].get('enhanced_analysis', [])
                    self.test_results["api_test"]["data_count"] = len(enhanced_analysis)
                    logger.info(f"Enhanced analysis entries: {len(enhanced_analysis)}")
                    
                    # Check for winners and losers
                    winners = [s for s in enhanced_analysis if s.get('type') == 'winner']
                    losers = [s for s in enhanced_analysis if s.get('type') == 'loser']
                    self.test_results["api_test"]["winners_count"] = len(winners)
                    self.test_results["api_test"]["losers_count"] = len(losers)
                    logger.info(f"Winners: {len(winners)}, Losers: {len(losers)}")
                    
                    # Print some details about the winners and losers
                    for i, winner in enumerate(winners):
                        logger.info(f"Winner {i+1}: {winner.get('symbol')} - Price: {winner.get('price_data', {}).get('current_price')}")
                    
                    for i, loser in enumerate(losers):
                        logger.info(f"Loser {i+1}: {loser.get('symbol')} - Price: {loser.get('price_data', {}).get('current_price')}")
                    
                    # Check for errors
                    errors = data['data'].get('errors', [])
                    logger.info(f"Errors: {len(errors)}")
                    for error in errors:
                        logger.info(f"Error: {error}")
                    
                    self.test_results["api_test"]["success"] = True
                    return True
                else:
                    error_msg = f"Invalid API response structure: {data}"
                    logger.error(error_msg)
                    self.test_results["api_test"]["error"] = error_msg
                    return False
            else:
                error_msg = f"API request failed with status code: {response.status_code}"
                logger.error(error_msg)
                self.test_results["api_test"]["error"] = error_msg
                return False
        
        except Exception as e:
            error_msg = f"Exception during API test: {e}"
            logger.error(error_msg)
            self.test_results["api_test"]["error"] = error_msg
            return False
    
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
            error_msg = f"Failed to initialize WebDriver: {e}"
            logger.error(error_msg)
            self.test_results["page_test"]["error"] = error_msg
            return False
    
    def test_page_load(self):
        """Test that the /stocks page loads and displays data"""
        logger.info("Testing /stocks page load and data display...")
        
        try:
            # Load the page
            start_time = time.time()
            self.driver.get(f"{self.base_url}/stocks")
            
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            page_load_time = time.time() - start_time
            self.test_results["page_test"]["page_load_time_ms"] = int(page_load_time * 1000)
            logger.info(f"Page loaded in {page_load_time:.2f} seconds")
            
            # Take screenshot of initial page
            self.driver.save_screenshot("stocks_page_initial.png")
            logger.info("Initial screenshot saved")
            
            # Wait for data to load (either auto-load or click refresh)
            try:
                data_load_start = time.time()
                
                # First, check if data is already loaded (auto-load)
                winners_list = self.driver.find_element(By.ID, "winnersList")
                initial_content = winners_list.get_attribute('innerHTML')
                
                # If we see loading spinners, wait for them to disappear
                if "Loading winners" in initial_content or "spinner-border" in initial_content:
                    logger.info("Waiting for auto-load to complete...")
                    
                    # Wait for loading spinner to disappear
                    WebDriverWait(self.driver, 60).until(
                        EC.invisibility_of_element_located((By.ID, "loadingSpinner"))
                    )
                    logger.info("Loading spinner disappeared")
                    
                    # Wait a bit more for content to render
                    time.sleep(1)
                else:
                    logger.info("No loading indicators found, checking if we need to click refresh")
                    
                    # Check if we have actual data
                    if "alert-info" in initial_content or "alert-warning" in initial_content or "alert-danger" in initial_content:
                        logger.info("Found alert message, clicking refresh button")
                        
                        # Click the refresh button
                        refresh_btn = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.ID, "refreshBtn"))
                        )
                        refresh_btn.click()
                        logger.info("Clicked refresh button")
                        
                        # Wait for loading spinner to disappear
                        WebDriverWait(self.driver, 60).until(
                            EC.invisibility_of_element_located((By.ID, "loadingSpinner"))
                        )
                        logger.info("Loading spinner disappeared after clicking refresh")
                        
                        # Wait a bit more for content to render
                        time.sleep(1)
                
                data_load_time = time.time() - data_load_start
                self.test_results["page_test"]["data_load_time_ms"] = int(data_load_time * 1000)
                logger.info(f"Data loaded in {data_load_time:.2f} seconds")
                
            except TimeoutException:
                error_msg = "Timeout waiting for data to load"
                logger.error(error_msg)
                self.test_results["page_test"]["error"] = error_msg
                
                # Take screenshot of timeout state
                self.driver.save_screenshot("stocks_page_timeout.png")
                logger.info("Timeout screenshot saved")
                return False
            
            # Take screenshot after data should be loaded
            self.driver.save_screenshot("stocks_page_data_loaded.png")
            logger.info("Data loaded screenshot saved")
            
            # Check if the winners/losers lists have content
            try:
                winners_list = self.driver.find_element(By.ID, "winnersList")
                winners_content = winners_list.get_attribute('innerHTML')
                has_winners = len(winners_content) > 0 and "alert-danger" not in winners_content and "Loading winners" not in winners_content
                self.test_results["page_test"]["winners_displayed"] = has_winners
                logger.info(f"Winners displayed: {has_winners} (content length: {len(winners_content)})")
                
                if not has_winners:
                    logger.warning(f"Winners content: {winners_content[:200]}...")
            except Exception as e:
                logger.error(f"Error checking winners list: {e}")
                self.test_results["page_test"]["winners_displayed"] = False
            
            try:
                losers_list = self.driver.find_element(By.ID, "losersList")
                losers_content = losers_list.get_attribute('innerHTML')
                has_losers = len(losers_content) > 0 and "alert-danger" not in losers_content and "Loading losers" not in losers_content
                self.test_results["page_test"]["losers_displayed"] = has_losers
                logger.info(f"Losers displayed: {has_losers} (content length: {len(losers_content)})")
                
                if not has_losers:
                    logger.warning(f"Losers content: {losers_content[:200]}...")
            except Exception as e:
                logger.error(f"Error checking losers list: {e}")
                self.test_results["page_test"]["losers_displayed"] = False
            
            # Check if the stocks table has rows
            try:
                stocks_table_body = self.driver.find_element(By.ID, "stocksTableBody")
                rows = stocks_table_body.find_elements(By.TAG_NAME, "tr")
                row_count = len(rows)
                self.test_results["page_test"]["table_rows"] = row_count
                logger.info(f"Stocks table has {row_count} rows")
                
                if row_count <= 1:  # Only the loading row
                    table_content = stocks_table_body.get_attribute('innerHTML')
                    logger.warning(f"Table content: {table_content[:200]}...")
            except Exception as e:
                logger.error(f"Error checking stocks table: {e}")
                self.test_results["page_test"]["table_rows"] = 0
            
            # Check for JavaScript errors
            try:
                logs = self.driver.get_log('browser')
                js_errors = [log for log in logs if log['level'] == 'SEVERE']
                self.test_results["js_errors"] = js_errors
                
                if js_errors:
                    logger.error(f"Found {len(js_errors)} JavaScript errors:")
                    for error in js_errors:
                        logger.error(f"JS Error: {error['message']}")
                else:
                    logger.info("No JavaScript errors found")
            except Exception as e:
                logger.error(f"Error checking JavaScript errors: {e}")
            
            # Check console logs for debugging
            try:
                console_logs = self.driver.get_log('browser')
                debug_logs = [log for log in console_logs if '[DEBUG]' in log.get('message', '')]
                logger.info(f"Found {len(debug_logs)} debug logs")
                
                # Show last 10 debug logs
                for i, log in enumerate(debug_logs[-10:]):
                    logger.info(f"Debug log {i+1}: {log['message']}")
            except Exception as e:
                logger.error(f"Error checking console logs: {e}")
            
            # Determine test success
            success = self.test_results["page_test"]["winners_displayed"] and self.test_results["page_test"]["losers_displayed"] and self.test_results["page_test"]["table_rows"] > 1
            self.test_results["page_test"]["success"] = success
            logger.info(f"Page test result: {'SUCCESS' if success else 'FAILURE'}")
            
            return success
            
        except Exception as e:
            error_msg = f"Exception during page test: {e}"
            logger.error(error_msg)
            self.test_results["page_test"]["error"] = error_msg
            
            # Take screenshot of error state
            if self.driver:
                self.driver.save_screenshot("stocks_page_error.png")
                logger.info("Error screenshot saved")
            
            return False
    
    def run_tests(self):
        """Run all tests"""
        logger.info("Running comprehensive stocks page test...")
        
        # Test the API endpoint
        api_success = self.test_api_endpoint()
        logger.info(f"API test result: {'SUCCESS' if api_success else 'FAILURE'}")
        
        # Set up the WebDriver
        if not self.setup_driver():
            logger.error("Failed to set up WebDriver, skipping page test")
            return self.test_results
        
        try:
            # Test the page load and data display
            page_success = self.test_page_load()
            logger.info(f"Page test result: {'SUCCESS' if page_success else 'FAILURE'}")
            
            # Overall success
            overall_success = api_success and page_success
            logger.info(f"Overall test result: {'SUCCESS' if overall_success else 'FAILURE'}")
            
            return self.test_results
        finally:
            # Clean up
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")
    
    def save_results(self, filename=None):
        """Save test results to a JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stocks_page_test_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            logger.info(f"Test results saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save test results: {e}")
            return False

def main():
    """Main function"""
    logger.info("Starting comprehensive stocks page test...")
    
    # Create and run the test
    test = StocksPageTest(headless=True)
    results = test.run_tests()
    test.save_results()
    
    # Calculate overall success
    api_success = results["api_test"]["success"]
    page_success = results["page_test"]["success"]
    overall_success = api_success and page_success
    
    # Print summary
    print("\n=== TEST SUMMARY ===")
    print(f"API Test: {'✅' if api_success else '❌'}")
    print(f"  - Response Time: {results['api_test']['response_time_ms']}ms")
    print(f"  - Data Count: {results['api_test']['data_count']}")
    print(f"  - Winners: {results['api_test']['winners_count']}")
    print(f"  - Losers: {results['api_test']['losers_count']}")
    if results["api_test"]["error"]:
        print(f"  - Error: {results['api_test']['error']}")
    
    print(f"Page Test: {'✅' if page_success else '❌'}")
    print(f"  - Page Load Time: {results['page_test']['page_load_time_ms']}ms")
    print(f"  - Data Load Time: {results['page_test']['data_load_time_ms']}ms")
    print(f"  - Winners Displayed: {'✅' if results['page_test']['winners_displayed'] else '❌'}")
    print(f"  - Losers Displayed: {'✅' if results['page_test']['losers_displayed'] else '❌'}")
    print(f"  - Table Rows: {results['page_test']['table_rows']}")
    if results["page_test"]["error"]:
        print(f"  - Error: {results['page_test']['error']}")
    
    print(f"JS Errors: {len(results['js_errors'])}")
    print(f"Overall Result: {'✅ SUCCESS' if overall_success else '❌ FAILURE'}")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main()) 