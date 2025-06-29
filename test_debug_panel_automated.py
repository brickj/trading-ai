#!/usr/bin/env python3
"""
Automated test to verify debug panel actually shows requests and responses
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import re

def test_debug_panel_automated():
    """Automated test using Selenium to verify debug panel functionality"""
    
    print("🧪 Automated Debug Panel Test (Standard + Enhanced)")
    print("=" * 50)
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("http://localhost:5001")
        
        print("✅ Page loaded successfully")
        
        # Wait for page to load
        time.sleep(3)
        
        # Find the stock symbol input and set value
        symbol_input = driver.find_element(By.ID, "stockSymbol")
        symbol_input.clear()
        symbol_input.send_keys("MSFT")
        print("✅ Set stock symbol to MSFT")
        
        # Test 1: Standard Analysis
        print("\n1. Testing Standard Analysis...")
        
        # Click Standard button
        standard_button = driver.find_element(By.ID, "standardAnalysisBtn")
        standard_button.click()
        print("✅ Clicked Standard button")
        
        # Wait for response
        time.sleep(3)
        
        # Get debug panel content
        debug_panel = driver.find_element(By.ID, "debugPanelBody")
        debug_content = debug_panel.get_attribute("innerHTML")
        
        if debug_content is None:
            debug_content = ""
        
        print(f"📋 Debug Panel Content Length: {len(debug_content)}")
        
        # Check for Standard request and response
        has_standard_request = "POST" in debug_content and "/api/analyze_stock" in debug_content
        has_standard_response = "Response received" in debug_content and "Status: 200" in debug_content
        has_symbol = "MSFT" in debug_content
        
        print(f"✅ Standard Request found: {has_standard_request}")
        print(f"✅ Standard Response found: {has_standard_response}")
        print(f"✅ Symbol found: {has_symbol}")
        
        # Extract and show Standard response details
        options_recommendation_found = False
        if "Response Data" in debug_content:
            # Extract all <pre> blocks
            matches = list(re.finditer(r'<pre[^>]*>(.*?)</pre>', debug_content, re.DOTALL))
            if len(matches) >= 2:
                json_str = matches[1].group(1)  # The second <pre> is the response
                try:
                    response_json = json.loads(json_str)
                    print(f"📋 Parsed Standard Response JSON keys: {list(response_json.keys())}")
                    print(f"📋 Standard Response 'data' keys: {list(response_json.get('data', {}).keys())}")
                    if 'data' in response_json and 'options_recommendation' in response_json['data']:
                        options_recommendation_found = True
                    print(f"✅ Options Recommendation in Standard Response: {options_recommendation_found}")
                    if options_recommendation_found:
                        options = response_json['data']['options_recommendation']
                        print(f"📋 Options recommendation action: {options.get('action', 'N/A')}")
                    else:
                        print("⚠️  WARNING: Standard Analysis response doesn't contain options_recommendation field")
                        print(f"📋 Available fields in 'data': {list(response_json.get('data', {}).keys())}")
                except json.JSONDecodeError as e:
                    print(f"❌ Error parsing Standard response JSON: {e}")
                    print(f"📋 Raw response text: {json_str[:500]}...")
            else:
                print("❌ Could not extract response JSON from debug panel <pre> tag.")
        
        if not (has_standard_request and has_standard_response and has_symbol):
            print("❌ Standard Analysis test failed")
            return False
        
        # Clear debug panel for next test
        clear_btn = driver.find_element(By.XPATH, "//button[contains(., 'Clear')]")
        driver.execute_script("arguments[0].scrollIntoView(true);", clear_btn)
        time.sleep(0.5)
        clear_btn.click()
        time.sleep(1)
        
        # Test 2: Enhanced Analysis
        print("\n2. Testing Enhanced Analysis...")
        enhanced_btn = driver.find_element(By.ID, "enhancedAnalysisBtn")
        enhanced_btn.click()
        print("✅ Clicked Enhanced button")
        
        # Wait for response
        time.sleep(15)
        
        # Check debug panel again
        debug_content = driver.find_element(By.ID, "debugPanelBody").text
        
        print(f"📋 Enhanced Debug Panel Content Length: {len(debug_content)}")
        print(f"📋 Enhanced Debug Panel Content:\n{debug_content}")
        
        has_enhanced_request = "Method: POST" in debug_content and "URL: /api/enhanced_analysis" in debug_content
        has_enhanced_response = "Status: 200" in debug_content and not ("Waiting for response..." in debug_content)
        
        print(f"✅ Enhanced Request found: {has_enhanced_request}")
        print(f"✅ Enhanced Response found: {has_enhanced_response}")
        
        # Final assessment
        all_tests_passed = (has_standard_request and has_standard_response and has_symbol and 
                           has_enhanced_request and has_enhanced_response)
        
        print("\n" + "=" * 50)
        if all_tests_passed:
            print("🎉 ALL TESTS PASSED - Debug panel is working correctly!")
        else:
            print("❌ TESTS FAILED - Debug panel is not working properly")
            print("   Debug panel content:")
            print(debug_content)
        
        driver.quit()
        return all_tests_passed
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        try:
            driver.quit()
        except:
            pass
        return False

if __name__ == "__main__":
    success = test_debug_panel_automated()
    exit(0 if success else 1) 