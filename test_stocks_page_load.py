#!/usr/bin/env python3
"""
Test script to check stocks page loading and data display
"""

import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_stocks_page():
    """Test the stocks page loading and data display"""
    
    print("🔍 Testing stocks page loading and data display...")
    
    # First, check if the API is working
    print("\n1️⃣ Testing API endpoint...")
    try:
        response = requests.get('http://localhost:5001/api/preloaded_data')
        if response.status_code == 200:
            data = response.json()
            stocks = data['data']['enhanced_analysis']
            print(f"✅ API working - {len(stocks)} stocks available")
            
            # Count winners and losers
            winners = [s for s in stocks if s['price_data']['change_percent'].replace('%', '').startswith('-') == False]
            losers = [s for s in stocks if s['price_data']['change_percent'].replace('%', '').startswith('-')]
            print(f"   🟢 Winners: {len(winners)}")
            print(f"   🔴 Losers: {len(losers)}")
            
        else:
            print(f"❌ API returned status {response.status_code}")
            return
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return
    
    # Now test the web page
    print("\n2️⃣ Testing web page...")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Load the stocks page
        print("   📄 Loading stocks page...")
        driver.get("http://localhost:5001/stocks")
        
        # Wait for page to load
        time.sleep(3)
        
        # Check if the page loaded correctly
        title = driver.title
        print(f"   📋 Page title: {title}")
        
        # Wait for the winners and losers sections to load
        print("   ⏳ Waiting for data to load...")
        wait = WebDriverWait(driver, 30)
        
        try:
            # Wait for winners list to be populated
            winners_list = wait.until(
                EC.presence_of_element_located((By.ID, "winnersList"))
            )
            
            # Wait a bit more for data to populate
            time.sleep(5)
            
            # Check winners content
            winners_content = winners_list.get_attribute('innerHTML')
            print(f"   🟢 Winners content length: {len(winners_content)}")
            print(f"   🟢 Winners content preview: {winners_content[:200]}...")
            
            # Check losers content
            losers_list = driver.find_element(By.ID, "losersList")
            losers_content = losers_list.get_attribute('innerHTML')
            print(f"   🔴 Losers content length: {len(losers_content)}")
            print(f"   🔴 Losers content preview: {losers_content[:200]}...")
            
            # Check if we have actual data or error messages
            if "No winners data available" in winners_content:
                print("   ❌ Winners section shows 'No winners data available'")
            elif "Loading winners" in winners_content:
                print("   ⚠️  Winners section still shows 'Loading winners'")
            else:
                print("   ✅ Winners section has data")
                
            if "No losers data available" in losers_content:
                print("   ❌ Losers section shows 'No losers data available'")
            elif "Loading losers" in losers_content:
                print("   ⚠️  Losers section still shows 'Loading losers'")
            else:
                print("   ✅ Losers section has data")
            
            # Take a screenshot
            driver.save_screenshot("stocks_page_test.png")
            print("   📸 Screenshot saved as stocks_page_test.png")
            
        except Exception as e:
            print(f"   ❌ Error waiting for data: {e}")
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"❌ Web page test failed: {e}")

if __name__ == "__main__":
    test_stocks_page() 