#!/usr/bin/env python3
"""
Debug script to check the exact content being displayed on the stocks page
"""

import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def debug_stocks_content():
    """Debug the exact content being displayed on the stocks page"""
    
    print("🔍 Debugging stocks page content...")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Load the stocks page
        print("📄 Loading stocks page...")
        driver.get("http://localhost:5001/stocks")
        
        # Wait for page to load
        time.sleep(3)
        
        # Wait for the winners and losers sections
        wait = WebDriverWait(driver, 30)
        
        try:
            # Wait for winners list to be populated
            winners_list = wait.until(
                EC.presence_of_element_located((By.ID, "winnersList"))
            )
            
            # Wait a bit more for data to populate
            time.sleep(5)
            
            # Get winners content
            winners_content = winners_list.get_attribute('innerHTML')
            print(f"\n🟢 WINNERS SECTION:")
            print(f"Content length: {len(winners_content)}")
            print(f"Full content:")
            print("=" * 50)
            print(winners_content)
            print("=" * 50)
            
            # Check losers content
            losers_list = driver.find_element(By.ID, "losersList")
            losers_content = losers_list.get_attribute('innerHTML')
            print(f"\n🔴 LOSERS SECTION:")
            print(f"Content length: {len(losers_content)}")
            print(f"Full content:")
            print("=" * 50)
            print(losers_content)
            print("=" * 50)
            
            # Check for specific error messages
            if "No winners data available" in winners_content:
                print("\n❌ FOUND: 'No winners data available' in winners section")
            elif "Loading winners" in winners_content:
                print("\n⚠️  FOUND: 'Loading winners' in winners section")
            else:
                print("\n✅ Winners section appears to have data")
                
            if "No losers data available" in losers_content:
                print("❌ FOUND: 'No losers data available' in losers section")
            elif "Loading losers" in losers_content:
                print("⚠️  FOUND: 'Loading losers' in losers section")
            else:
                print("✅ Losers section appears to have data")
            
            # Check if we can find stock symbols in the content
            import re
            winners_symbols = re.findall(r'<strong>([A-Z]+)</strong>', winners_content)
            losers_symbols = re.findall(r'<strong>([A-Z]+)</strong>', losers_content)
            
            print(f"\n📊 Found symbols:")
            print(f"  Winners: {winners_symbols}")
            print(f"  Losers: {losers_symbols}")
            
        except Exception as e:
            print(f"❌ Error during content analysis: {e}")
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"❌ Web page test failed: {e}")

if __name__ == "__main__":
    debug_stocks_content() 