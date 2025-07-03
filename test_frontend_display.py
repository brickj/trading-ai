#!/usr/bin/env python3
"""
Test script to verify that the frontend correctly displays target_gain and stop_loss values
from the standard analysis endpoint.
"""
import sys
import os
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_frontend_display():
    """Test if the frontend correctly displays target_gain and stop_loss values"""
    print("Starting frontend display test...")
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    
    try:
        # Start the webdriver
        driver = webdriver.Chrome(options=chrome_options)
        print("WebDriver started successfully")
        
        # Navigate to the dashboard page
        driver.get("http://localhost:5000")
        print("Navigated to dashboard page")
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "stockSymbol"))
        )
        print("Page loaded successfully")
        
        # Enter a stock symbol
        symbol_input = driver.find_element(By.ID, "stockSymbol")
        symbol_input.clear()
        symbol_input.send_keys("AAPL")
        print("Entered stock symbol: AAPL")
        
        # Click the standard analysis button
        standard_btn = driver.find_element(By.ID, "standardAnalysisBtn")
        standard_btn.click()
        print("Clicked standard analysis button")
        
        # Wait for the analysis to complete and results to display
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "analysisResults"))
        )
        print("Analysis results loaded")
        
        # Wait a bit more for the results to fully render
        time.sleep(2)
        
        # Get the analysis results HTML
        results_html = driver.find_element(By.ID, "analysisResults").get_attribute("innerHTML")
        
        # Check if target_gain and stop_loss are displayed
        target_gain_present = "Target Gain:" in results_html
        stop_loss_present = "Stop Loss:" in results_html
        
        # Take a screenshot of the results
        driver.save_screenshot("analysis_results.png")
        print(f"Screenshot saved to analysis_results.png")
        
        # Check if the values are not empty or N/A
        if target_gain_present:
            # Extract the target_gain value using JavaScript
            target_gain = driver.execute_script("""
                const elements = document.querySelectorAll('p');
                for (const el of elements) {
                    if (el.textContent.includes('Target Gain:')) {
                        return el.textContent.split('Target Gain:')[1].trim();
                    }
                }
                return 'Not found';
            """)
            print(f"Target Gain value: {target_gain}")
        else:
            print("Target Gain field not found in the results")
        
        if stop_loss_present:
            # Extract the stop_loss value using JavaScript
            stop_loss = driver.execute_script("""
                const elements = document.querySelectorAll('p');
                for (const el of elements) {
                    if (el.textContent.includes('Stop Loss:')) {
                        return el.textContent.split('Stop Loss:')[1].trim();
                    }
                }
                return 'Not found';
            """)
            print(f"Stop Loss value: {stop_loss}")
        else:
            print("Stop Loss field not found in the results")
        
        # Check if the values are properly displayed (not empty or N/A)
        target_gain_valid = target_gain_present and "N/A" not in target_gain and target_gain != "Not found"
        stop_loss_valid = stop_loss_present and "N/A" not in stop_loss and stop_loss != "Not found"
        
        # Print the test results
        print("\nTest Results:")
        print(f"Target Gain field present: {target_gain_present}")
        print(f"Target Gain value valid: {target_gain_valid}")
        print(f"Stop Loss field present: {stop_loss_present}")
        print(f"Stop Loss value valid: {stop_loss_valid}")
        
        # Overall test result
        if target_gain_valid and stop_loss_valid:
            print("\n✅ TEST PASSED: Frontend correctly displays target_gain and stop_loss values")
        else:
            print("\n❌ TEST FAILED: Frontend does not correctly display target_gain and stop_loss values")
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
    finally:
        # Close the webdriver
        if 'driver' in locals():
            driver.quit()
            print("WebDriver closed")

if __name__ == "__main__":
    test_frontend_display()
