#!/usr/bin/env python3
"""
Test script to debug the Analyze button functionality
"""

import requests
import json
import time

def test_analyze_button():
    """Test the Analyze button functionality"""
    
    print("🔍 Testing Analyze button functionality...")
    
    # Test 1: Check if the comprehensive analysis endpoint works
    print("\n1️⃣ Testing comprehensive analysis endpoint...")
    try:
        response = requests.post(
            'http://localhost:5001/api/comprehensive_analysis',
            headers={'Content-Type': 'application/json'},
            json={'symbol': 'AAPL', 'ai_provider': 'ollama'},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API call successful")
            print(f"📊 Response keys: {list(data.keys())}")
            
            if 'data' in data:
                data_keys = list(data['data'].keys())
                print(f"📊 Data keys: {data_keys}")
                
                if 'comprehensive_recommendations' in data['data']:
                    comp_keys = list(data['data']['comprehensive_recommendations'].keys())
                    print(f"📊 Comprehensive recommendations keys: {comp_keys}")
                    
                    # Check for required keys
                    has_options = 'options_recommendations' in comp_keys
                    has_stocks = 'stock_recommendations' in comp_keys
                    print(f"📊 Has options recommendations: {has_options}")
                    print(f"📊 Has stock recommendations: {has_stocks}")
                    
                    if has_options:
                        options_count = len(data['data']['comprehensive_recommendations']['options_recommendations'])
                        print(f"📊 Options recommendations count: {options_count}")
                    
                    if has_stocks:
                        stocks_count = len(data['data']['comprehensive_recommendations']['stock_recommendations'])
                        print(f"📊 Stock recommendations count: {stocks_count}")
                else:
                    print("❌ No comprehensive_recommendations in response")
            else:
                print("❌ No 'data' key in response")
        else:
            print(f"❌ API call failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
    
    # Test 2: Check if the stocks page loads correctly
    print("\n2️⃣ Testing stocks page load...")
    try:
        response = requests.get('http://localhost:5001/stocks')
        if response.status_code == 200:
            print("✅ Stocks page loads successfully")
            
            # Check if the enhanced analysis elements are in the HTML
            html = response.text
            has_enhanced_section = 'enhancedAnalysisResults' in html
            has_enhanced_container = 'enhancedAnalysisContainer' in html
            
            print(f"📊 Has enhanced analysis section: {has_enhanced_section}")
            print(f"📊 Has enhanced analysis container: {has_enhanced_container}")
            
        else:
            print(f"❌ Stocks page failed to load: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing stocks page: {e}")
    
    # Test 3: Check if preloaded data is available
    print("\n3️⃣ Testing preloaded data...")
    try:
        response = requests.get('http://localhost:5001/api/preloaded_data')
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stocks_count = len(data.get('data', {}).get('enhanced_analysis', []))
                print(f"✅ Preloaded data available: {stocks_count} stocks")
                
                if stocks_count > 0:
                    # Check if stocks have the required data for Analyze button
                    first_stock = data['data']['enhanced_analysis'][0]
                    has_symbol = 'symbol' in first_stock
                    has_price_data = 'price_data' in first_stock
                    has_sentiment_data = 'sentiment_data' in first_stock
                    
                    print(f"📊 First stock has symbol: {has_symbol}")
                    print(f"📊 First stock has price_data: {has_price_data}")
                    print(f"📊 First stock has sentiment_data: {has_sentiment_data}")
                    
                    if has_symbol:
                        symbol = first_stock['symbol']
                        print(f"📊 First stock symbol: {symbol}")
            else:
                print("❌ Preloaded data not successful")
        else:
            print(f"❌ Preloaded data request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing preloaded data: {e}")

if __name__ == "__main__":
    test_analyze_button() 