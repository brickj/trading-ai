#!/usr/bin/env python3
"""
Selenium test for the /stocks page to verify data is displayed after clicking refresh
"""

import sys
import os
import time
import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def test_stocks_page_with_selenium():
    """Test the /stocks page with Selenium to verify data is displayed after clicking refresh"""
    logger.info("Starting Selenium test for /stocks page...")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    try:
        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        logger.info("WebDriver initialized successfully")
        
        # Load the page
        url = "http://localhost:5001/stocks"
        logger.info(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        logger.info("Page loaded successfully")
        
        # Take screenshot of initial page
        driver.save_screenshot("stocks_page_initial.png")
        logger.info("Initial screenshot saved")
        
        # Check if the refresh button exists
        refresh_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "refreshBtn"))
        )
        logger.info("Refresh button found")
        
        # Click the refresh button
        refresh_btn.click()
        logger.info("Clicked refresh button")
        
        # Wait for loading spinner to disappear
        WebDriverWait(driver, 60).until(
            EC.invisibility_of_element_located((By.ID, "loadingSpinner"))
        )
        logger.info("Loading spinner disappeared")
        
        # Take screenshot after data should be loaded
        driver.save_screenshot("stocks_page_after_refresh.png")
        logger.info("After-refresh screenshot saved")
        
        # Check if the winners/losers summary is now visible
        winners_losers_summary = driver.find_element(By.ID, "winnersLosersSummary")
        is_visible = winners_losers_summary.is_displayed()
        logger.info(f"Winners/losers summary is visible: {is_visible}")
        
        # Check if winners list has content
        winners_list = driver.find_element(By.ID, "winnersList")
        winners_content = winners_list.get_attribute('innerHTML').strip()
        logger.info(f"Winners list content length: {len(winners_content)}")
        
        # Check if losers list has content
        losers_list = driver.find_element(By.ID, "losersList")
        losers_content = losers_list.get_attribute('innerHTML').strip()
        logger.info(f"Losers list content length: {len(losers_content)}")
        
        # Check for JavaScript errors
        logs = driver.get_log('browser')
        js_errors = [log for log in logs if log['level'] == 'SEVERE']
        if js_errors:
            logger.error(f"Found {len(js_errors)} JavaScript errors:")
            for error in js_errors:
                logger.error(f"JS Error: {error['message']}")
        else:
            logger.info("No JavaScript errors found")
        
        # Check if the stocks table has rows
        stocks_table_body = driver.find_element(By.ID, "stocksTableBody")
        rows = stocks_table_body.find_elements(By.TAG_NAME, "tr")
        logger.info(f"Stocks table has {len(rows)} rows")
        
        # Check the console logs for debugging
        console_logs = driver.get_log('browser')
        debug_logs = [log for log in console_logs if '[DEBUG]' in log.get('message', '')]
        logger.info(f"Found {len(debug_logs)} debug logs")
        for i, log in enumerate(debug_logs[-10:]):  # Show last 10 debug logs
            logger.info(f"Debug log {i+1}: {log['message']}")
        
        # Determine test success
        success = is_visible and len(winners_content) > 0 and len(losers_content) > 0 and len(rows) > 1
        logger.info(f"Test result: {'SUCCESS' if success else 'FAILURE'}")
        
        # Save test results
        results = {
            "success": success,
            "winners_losers_visible": is_visible,
            "winners_content_length": len(winners_content),
            "losers_content_length": len(losers_content),
            "table_rows": len(rows),
            "js_errors": len(js_errors)
        }
        
        with open("stocks_page_selenium_results.json", "w") as f:
            json.dump(results, f, indent=2)
        logger.info("Results saved to stocks_page_selenium_results.json")
        
        return success
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False
        
    finally:
        # Clean up
        if 'driver' in locals():
            driver.quit()
            logger.info("WebDriver closed")

if __name__ == "__main__":
    success = test_stocks_page_with_selenium()
    sys.exit(0 if success else 1) 