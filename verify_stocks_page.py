#!/usr/bin/env python3
"""
Comprehensive verification script for the /stocks page
This script will verify the functionality of the /stocks page, including:
1. API response from /api/sp500_analysis
2. Page loading and data display
3. Refresh functionality
"""

import sys
import os
import time
import json
import logging
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StocksPageVerifier:
    """Verifier for the /stocks page functionality"""
    
    def __init__(self, base_url="http://localhost:5001", headless=False):
        """Initialize the verifier"""
        self.base_url = base_url
        self.headless = headless
        self.driver = None
        self.results = {
            "api_test": {
                "success": False,
                "data": None,
                "error": None
            },
            "page_load_test": {
                "success": False,
                "error": None
            },
            "winners_losers_test": {
                "success": False,
                "winners_count": 0,
                "losers_count": 0,
                "error": None
            },
            "table_test": {
                "success": False,
                "rows_count": 0,
                "error": None
            },
            "refresh_test": {
                "success": False,
                "error": None
            }
        }
    
    def verify_api(self):
        """Verify the API response from /api/sp500_analysis"""
        logger.info("Verifying API response from /api/sp500_analysis...")
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/sp500_analysis")
            elapsed_time = time.time() - start_time
            
            logger.info(f"API response received in {elapsed_time:.2f} seconds with status code {response.status_code}")
            
            if response.status_code != 200:
                self.results["api_test"]["error"] = f"API returned status code {response.status_code}"
                return False
            
            data = response.json()
            if not data.get("success"):
                self.results["api_test"]["error"] = f"API returned success=False: {data.get('error')}"
                return False
            
            if not data.get("data") or not data["data"].get("enhanced_analysis"):
                self.results["api_test"]["error"] = "API response missing enhanced_analysis data"
                return False
            
            enhanced_analysis = data["data"]["enhanced_analysis"]
            winners = [s for s in enhanced_analysis if s.get("type") == "winner"]
            losers = [s for s in enhanced_analysis if s.get("type") == "loser"]
            
            logger.info(f"API returned {len(winners)} winners and {len(losers)} losers")
            
            if len(winners) == 0 and len(losers) == 0:
                self.results["api_test"]["error"] = "API returned no winners or losers"
                return False
            
            self.results["api_test"]["data"] = data["data"]
            self.results["api_test"]["success"] = True
            return True
        
        except Exception as e:
            logger.error(f"Error verifying API: {e}")
            self.results["api_test"]["error"] = str(e)
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
            logger.error(f"Error setting up WebDriver: {e}")
            return False
    
    def verify_page_load(self):
        """Verify that the /stocks page loads correctly"""
        logger.info("Verifying page load...")
        try:
            self.driver.get(f"{self.base_url}/stocks")
            
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Take a screenshot for verification
            self.driver.save_screenshot("stocks_page_initial.png")
            logger.info("Page loaded successfully, screenshot saved")
            
            # Check for page title
            title = self.driver.title
            logger.info(f"Page title: {title}")
            
            if "S&P 500 Winners & Losers" not in title:
                self.results["page_load_test"]["error"] = f"Unexpected page title: {title}"
                return False
            
            self.results["page_load_test"]["success"] = True
            return True
        
        except Exception as e:
            logger.error(f"Error verifying page load: {e}")
            self.results["page_load_test"]["error"] = str(e)
            return False
    
    def verify_winners_losers(self):
        """Verify that winners and losers are displayed correctly"""
        logger.info("Verifying winners and losers display...")
        try:
            # Wait for data to load
            time.sleep(5)  # Give some time for data to load
            
            # Check if winners list is populated
            winners_list = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "winnersList"))
            )
            
            # Check if losers list is populated
            losers_list = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "losersList"))
            )
            
            # Wait a bit more to ensure data is loaded
            time.sleep(2)
            
            # Take a screenshot after data should be loaded
            self.driver.save_screenshot("stocks_page_data_loaded.png")
            
            # Check winners content
            winners_content = winners_list.get_attribute('innerHTML')
            winners_empty = "No winners data available" in winners_content or "Loading winners" in winners_content
            
            # Check losers content
            losers_content = losers_list.get_attribute('innerHTML')
            losers_empty = "No losers data available" in losers_content or "Loading losers" in losers_content
            
            logger.info(f"Winners empty: {winners_empty}, Losers empty: {losers_empty}")
            
            if winners_empty and losers_empty:
                self.results["winners_losers_test"]["error"] = "Both winners and losers lists are empty"
                return False
            
            # Count winners (look for strong tags which contain symbols)
            winners_symbols = winners_list.find_elements(By.TAG_NAME, "strong")
            self.results["winners_losers_test"]["winners_count"] = len(winners_symbols)
            
            # Count losers (look for strong tags which contain symbols)
            losers_symbols = losers_list.find_elements(By.TAG_NAME, "strong")
            self.results["winners_losers_test"]["losers_count"] = len(losers_symbols)
            
            logger.info(f"Found {len(winners_symbols)} winners and {len(losers_symbols)} losers")
            
            if len(winners_symbols) == 0 and len(losers_symbols) == 0:
                self.results["winners_losers_test"]["error"] = "No winners or losers symbols found"
                return False
            
            self.results["winners_losers_test"]["success"] = True
            return True
        
        except Exception as e:
            logger.error(f"Error verifying winners and losers: {e}")
            self.results["winners_losers_test"]["error"] = str(e)
            return False
    
    def verify_table(self):
        """Verify that the stocks table is populated correctly"""
        logger.info("Verifying stocks table...")
        try:
            # Find the table body
            table_body = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "stocksTableBody"))
            )
            
            # Check if table is populated
            rows = table_body.find_elements(By.TAG_NAME, "tr")
            self.results["table_test"]["rows_count"] = len(rows)
            
            logger.info(f"Found {len(rows)} rows in the stocks table")
            
            if len(rows) <= 1:
                # Check if the single row is a loading or error message
                if len(rows) == 1:
                    row_content = rows[0].get_attribute('innerHTML')
                    if "Loading" in row_content:
                        self.results["table_test"]["error"] = "Table still shows loading message"
                        return False
                    if "Error" in row_content:
                        self.results["table_test"]["error"] = "Table shows error message"
                        return False
                else:
                    self.results["table_test"]["error"] = "No rows found in the stocks table"
                    return False
            
            self.results["table_test"]["success"] = True
            return True
        
        except Exception as e:
            logger.error(f"Error verifying stocks table: {e}")
            self.results["table_test"]["error"] = str(e)
            return False
    
    def verify_refresh(self):
        """Verify that the refresh button works correctly"""
        logger.info("Verifying refresh functionality...")
        try:
            # Find the refresh button
            refresh_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "refreshBtn"))
            )
            
            # Click the refresh button
            refresh_button.click()
            logger.info("Clicked refresh button")
            
            # Wait for loading spinner
            loading_spinner = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "loadingSpinner"))
            )
            logger.info("Loading spinner visible")
            
            # Wait for loading spinner to disappear
            WebDriverWait(self.driver, 60).until(
                EC.invisibility_of_element_located((By.ID, "loadingSpinner"))
            )
            logger.info("Loading spinner disappeared")
            
            # Take a screenshot after refresh
            self.driver.save_screenshot("stocks_page_refreshed.png")
            
            # Verify that data is still displayed
            self.verify_winners_losers()
            self.verify_table()
            
            self.results["refresh_test"]["success"] = True
            return True
        
        except Exception as e:
            logger.error(f"Error verifying refresh functionality: {e}")
            self.results["refresh_test"]["error"] = str(e)
            return False
    
    def check_console_errors(self):
        """Check for console errors"""
        logger.info("Checking for console errors...")
        try:
            logs = self.driver.get_log('browser')
            errors = [log for log in logs if log['level'] == 'SEVERE']
            
            if errors:
                logger.warning(f"Found {len(errors)} console errors:")
                for error in errors[:5]:  # Show first 5 errors
                    logger.warning(f"Console error: {error['message']}")
            else:
                logger.info("No console errors found")
            
            return errors
        except Exception as e:
            logger.error(f"Error checking console errors: {e}")
            return []
    
    def run_verification(self):
        """Run all verification steps"""
        logger.info("Starting verification of /stocks page...")
        
        # Step 1: Verify API
        api_success = self.verify_api()
        logger.info(f"API verification: {'SUCCESS' if api_success else 'FAILURE'}")
        
        # Step 2: Set up WebDriver
        if not self.setup_driver():
            logger.error("Failed to set up WebDriver, skipping browser tests")
            return self.results
        
        try:
            # Step 3: Verify page load
            page_load_success = self.verify_page_load()
            logger.info(f"Page load verification: {'SUCCESS' if page_load_success else 'FAILURE'}")
            
            # Step 4: Verify winners and losers
            winners_losers_success = self.verify_winners_losers()
            logger.info(f"Winners/losers verification: {'SUCCESS' if winners_losers_success else 'FAILURE'}")
            
            # Step 5: Verify table
            table_success = self.verify_table()
            logger.info(f"Table verification: {'SUCCESS' if table_success else 'FAILURE'}")
            
            # Step 6: Verify refresh functionality
            refresh_success = self.verify_refresh()
            logger.info(f"Refresh verification: {'SUCCESS' if refresh_success else 'FAILURE'}")
            
            # Step 7: Check for console errors
            console_errors = self.check_console_errors()
            
            # Overall success
            overall_success = (
                api_success and 
                page_load_success and 
                winners_losers_success and 
                table_success and 
                refresh_success and
                len(console_errors) == 0
            )
            
            logger.info(f"Overall verification: {'SUCCESS' if overall_success else 'FAILURE'}")
            
            return self.results
        
        finally:
            # Clean up
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")
    
    def save_results(self, filename=None):
        """Save verification results to a JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stocks_page_verification_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            logger.info(f"Verification results saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save verification results: {e}")
            return False

def main():
    """Main function"""
    logger.info("Starting stocks page verification...")
    
    # Create and run the verifier
    verifier = StocksPageVerifier(headless=False)  # Set to True for headless mode
    results = verifier.run_verification()
    verifier.save_results()
    
    # Calculate overall success
    api_success = results["api_test"]["success"]
    page_load_success = results["page_load_test"]["success"]
    winners_losers_success = results["winners_losers_test"]["success"]
    table_success = results["table_test"]["success"]
    refresh_success = results["refresh_test"]["success"]
    
    overall_success = (
        api_success and 
        page_load_success and 
        winners_losers_success and 
        table_success and 
        refresh_success
    )
    
    # Print summary
    print("\n=== VERIFICATION SUMMARY ===")
    print(f"API Test: {'✅' if api_success else '❌'}")
    if not api_success:
        print(f"  - Error: {results['api_test']['error']}")
    
    print(f"Page Load Test: {'✅' if page_load_success else '❌'}")
    if not page_load_success:
        print(f"  - Error: {results['page_load_test']['error']}")
    
    print(f"Winners/Losers Test: {'✅' if winners_losers_success else '❌'}")
    print(f"  - Winners: {results['winners_losers_test']['winners_count']}")
    print(f"  - Losers: {results['winners_losers_test']['losers_count']}")
    if not winners_losers_success:
        print(f"  - Error: {results['winners_losers_test']['error']}")
    
    print(f"Table Test: {'✅' if table_success else '❌'}")
    print(f"  - Rows: {results['table_test']['rows_count']}")
    if not table_success:
        print(f"  - Error: {results['table_test']['error']}")
    
    print(f"Refresh Test: {'✅' if refresh_success else '❌'}")
    if not refresh_success:
        print(f"  - Error: {results['refresh_test']['error']}")
    
    print(f"Overall Result: {'✅ SUCCESS' if overall_success else '❌ FAILURE'}")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main()) 