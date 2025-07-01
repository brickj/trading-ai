#!/usr/bin/env python3
"""
Test script to check if the stocks page is loading data correctly
"""

import requests
import json
import time

def test_api_endpoint():
    """Test the API endpoint that provides stock data"""
    print("Testing API endpoint...")
    
    try:
        response = requests.get("http://localhost:5001/api/preloaded_data", timeout=10)
        print(f"API Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"API Response: {json.dumps(data, indent=2)}")
            
            if 'data' in data and 'enhanced_analysis' in data['data']:
                stocks = data['data']['enhanced_analysis']
                print(f"\n✅ Found {len(stocks)} stocks in API response:")
                for stock in stocks:
                    symbol = stock.get('symbol', 'N/A')
                    stock_type = stock.get('type', 'N/A')
                    sentiment = stock.get('sentiment_analysis', {}).get('sentiment_score', 'N/A')
                    confidence = stock.get('sentiment_analysis', {}).get('confidence', 'N/A')
                    print(f"  {stock_type}: {symbol} (sentiment: {sentiment}, confidence: {confidence})")
                return True
            else:
                print("❌ No enhanced_analysis found in API response")
                return False
        else:
            print(f"❌ API request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

def test_main_page():
    """Test the main page loads correctly"""
    print("\nTesting main page...")
    
    try:
        response = requests.get("http://localhost:5001", timeout=10)
        print(f"Page Status Code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print("✅ Main page loads successfully")
            
            # Check for key elements
            if 'winnersList' in content:
                print("✅ Found winnersList container")
            else:
                print("❌ Missing winnersList container")
                
            if 'losersList' in content:
                print("✅ Found losersList container")
            else:
                print("❌ Missing losersList container")
                
            if 'stocksTableBody' in content:
                print("✅ Found stocksTableBody container")
            else:
                print("❌ Missing stocksTableBody container")
                
            if 'stocks.js' in content:
                print("✅ Found stocks.js script reference")
            else:
                print("❌ Missing stocks.js script reference")
                
            return True
        else:
            print(f"❌ Page request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing main page: {e}")
        return False

def test_stocks_page():
    """Test the stocks page specifically"""
    print("\nTesting stocks page...")
    
    try:
        response = requests.get("http://localhost:5001/stocks", timeout=10)
        print(f"Stocks Page Status Code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print("✅ Stocks page loads successfully")
            
            # Check for key elements
            if 'S&P 500 Winners & Losers' in content:
                print("✅ Found page title")
            else:
                print("❌ Missing page title")
                
            if 'winnersList' in content:
                print("✅ Found winnersList container")
            else:
                print("❌ Missing winnersList container")
                
            if 'losersList' in content:
                print("✅ Found losersList container")
            else:
                print("❌ Missing losersList container")
                
            return True
        else:
            print(f"❌ Stocks page request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing stocks page: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Stocks Page Functionality")
    print("=" * 50)
    
    # Test API endpoint
    api_ok = test_api_endpoint()
    
    # Test main page
    main_ok = test_main_page()
    
    # Test stocks page
    stocks_ok = test_stocks_page()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"API Endpoint: {'✅ PASS' if api_ok else '❌ FAIL'}")
    print(f"Main Page: {'✅ PASS' if main_ok else '❌ FAIL'}")
    print(f"Stocks Page: {'✅ PASS' if stocks_ok else '❌ FAIL'}")
    
    if api_ok and main_ok and stocks_ok:
        print("\n🎉 All tests passed! The stocks page should be working correctly.")
        print("💡 The page loads data via JavaScript, so you should see the stock data populated in the browser.")
    else:
        print("\n⚠️ Some tests failed. Check the server logs for more details.")

if __name__ == "__main__":
    main() 