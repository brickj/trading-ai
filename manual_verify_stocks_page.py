#!/usr/bin/env python3
"""
Manual verification script for the /stocks page
This script will check the API and open the browser for manual verification
"""

import sys
import os
import time
import json
import logging
import requests
import webbrowser
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_api(base_url="http://localhost:5001"):
    """Verify the API response from /api/sp500_analysis"""
    logger.info("Verifying API response from /api/sp500_analysis...")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/api/sp500_analysis")
        elapsed_time = time.time() - start_time
        
        logger.info(f"API response received in {elapsed_time:.2f} seconds with status code {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"API returned status code {response.status_code}")
            return False, None
        
        data = response.json()
        if not data.get("success"):
            logger.error(f"API returned success=False: {data.get('error')}")
            return False, None
        
        if not data.get("data") or not data["data"].get("enhanced_analysis"):
            logger.error("API response missing enhanced_analysis data")
            return False, None
        
        enhanced_analysis = data["data"]["enhanced_analysis"]
        winners = [s for s in enhanced_analysis if s.get("type") == "winner"]
        losers = [s for s in enhanced_analysis if s.get("type") == "loser"]
        
        logger.info(f"API returned {len(winners)} winners and {len(losers)} losers")
        
        if len(winners) == 0 and len(losers) == 0:
            logger.error("API returned no winners or losers")
            return False, None
        
        # Save API response to file for inspection
        with open("stocks_api_response.json", "w") as f:
            json.dump(data, f, indent=2)
        logger.info("API response saved to stocks_api_response.json")
        
        return True, data["data"]
    
    except Exception as e:
        logger.error(f"Error verifying API: {e}")
        return False, None

def open_browser(base_url="http://localhost:5001"):
    """Open the browser to the stocks page"""
    url = f"{base_url}/stocks"
    logger.info(f"Opening browser to {url}")
    webbrowser.open(url)
    return True

def display_manual_verification_steps():
    """Display manual verification steps"""
    print("\n" + "="*80)
    print("MANUAL VERIFICATION STEPS")
    print("="*80)
    print("1. Wait for the page to fully load (5-10 seconds)")
    print("2. Check that the 'Top 3 Winners Today' section shows data")
    print("   - Should show 3 stocks with their symbols and prices")
    print("   - Each winner should have a green arrow and positive percentage")
    print()
    print("3. Check that the 'Bottom 3 Losers Today' section shows data")
    print("   - Should show 3 stocks with their symbols and prices")
    print("   - Each loser should have a red arrow and negative percentage")
    print()
    print("4. Check that the main table shows stock data")
    print("   - Should have at least 6 rows (3 winners + 3 losers)")
    print("   - Each row should show a stock with symbol, price, sentiment, etc.")
    print()
    print("5. Click the 'Refresh Data' button")
    print("   - Should show a loading spinner")
    print("   - After a few seconds, should show updated data")
    print()
    print("6. Check for any errors in the browser console (F12 > Console)")
    print("   - Should not have any red error messages")
    print("="*80)
    
    # Ask for user input
    print("Did all verification steps pass? (y/n): ", end="")
    result = input().strip().lower()
    return result == 'y'

def main():
    """Main function"""
    logger.info("Starting manual verification of /stocks page...")
    
    # Step 1: Verify API
    api_success, api_data = verify_api()
    logger.info(f"API verification: {'SUCCESS' if api_success else 'FAILURE'}")
    
    if not api_success:
        logger.error("API verification failed, cannot proceed with manual verification")
        return 1
    
    # Step 2: Open browser
    browser_success = open_browser()
    logger.info(f"Browser opened: {'SUCCESS' if browser_success else 'FAILURE'}")
    
    # Step 3: Display manual verification steps
    print("\nPlease verify the following in the browser:")
    manual_success = display_manual_verification_steps()
    logger.info(f"Manual verification: {'SUCCESS' if manual_success else 'FAILURE'}")
    
    # Overall success
    overall_success = api_success and browser_success and manual_success
    
    # Print summary
    print("\n=== VERIFICATION SUMMARY ===")
    print(f"API Test: {'✅' if api_success else '❌'}")
    if api_success and api_data:
        winners = [s for s in api_data["enhanced_analysis"] if s.get("type") == "winner"]
        losers = [s for s in api_data["enhanced_analysis"] if s.get("type") == "loser"]
        print(f"  - Winners: {len(winners)}")
        print(f"  - Losers: {len(losers)}")
    
    print(f"Browser Test: {'✅' if browser_success else '❌'}")
    print(f"Manual Verification: {'✅' if manual_success else '❌'}")
    print(f"Overall Result: {'✅ SUCCESS' if overall_success else '❌ FAILURE'}")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main()) 