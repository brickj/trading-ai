#!/usr/bin/env python3
"""
Manual test script for the /stocks page
This script will launch a browser and open the stocks page for manual verification
"""

import sys
import os
import time
import webbrowser
import requests
import json
from datetime import datetime

def check_api_endpoint(base_url="http://localhost:5001"):
    """Check if the API endpoint is working"""
    print("Checking API endpoint...")
    try:
        response = requests.get(f"{base_url}/api/sp500_analysis")
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'data' in data:
                enhanced_analysis = data['data'].get('enhanced_analysis', [])
                winners = [s for s in enhanced_analysis if s.get('type') == 'winner']
                losers = [s for s in enhanced_analysis if s.get('type') == 'loser']
                print(f"✅ API is working! Found {len(winners)} winners and {len(losers)} losers")
                return True
        print(f"❌ API returned status code {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ Error checking API: {e}")
        return False

def open_browser(base_url="http://localhost:5001"):
    """Open the browser to the stocks page"""
    url = f"{base_url}/stocks"
    print(f"Opening browser to {url}")
    webbrowser.open(url)

def display_test_instructions():
    """Display test instructions"""
    print("\n" + "="*80)
    print("MANUAL TEST INSTRUCTIONS")
    print("="*80)
    print("Please verify the following:")
    print()
    print("1. WINNERS SECTION:")
    print("   - The 'Top 3 Winners Today' section should be visible")
    print("   - It should show 3 stocks with their symbols, prices, and change percentages")
    print("   - Each winner should have a green arrow and positive percentage")
    print()
    print("2. LOSERS SECTION:")
    print("   - The 'Bottom 3 Losers Today' section should be visible")
    print("   - It should show 3 stocks with their symbols, prices, and change percentages")
    print("   - Each loser should have a red arrow and negative percentage")
    print()
    print("3. MAIN TABLE:")
    print("   - The main table should be populated with stock data")
    print("   - Each row should show a stock with symbol, price, sentiment, etc.")
    print("   - The table should have at least 6 rows (3 winners + 3 losers)")
    print()
    print("4. FUNCTIONALITY:")
    print("   - Click the 'Refresh Data' button")
    print("   - Verify that the loading spinner appears and then disappears")
    print("   - Verify that the data refreshes")
    print()
    print("5. ERROR HANDLING:")
    print("   - Check the browser console for any JavaScript errors")
    print("   - There should be no red error messages")
    print("="*80)
    print("Enter 'y' if all tests pass, 'n' if any test fails:")

def main():
    """Main function"""
    print("Starting manual test for stocks page...")
    
    # Check if API is working
    if not check_api_endpoint():
        print("❌ API is not working. Please fix API issues before continuing.")
        return 1
    
    # Open browser
    open_browser()
    
    # Display test instructions
    display_test_instructions()
    
    # Get user input
    result = input().strip().lower()
    
    if result == 'y':
        print("✅ All tests passed! The stocks page is working correctly.")
        return 0
    else:
        print("❌ Tests failed. Please check the console for errors and fix the issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 