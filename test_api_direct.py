#!/usr/bin/env python3
"""
Direct API test to check what the JavaScript should be receiving
"""

import requests
import json

def test_api_response():
    """Test the API response directly"""
    
    print("🔍 Testing API response directly...")
    
    try:
        # Make the same request the JavaScript makes
        response = requests.get("http://localhost:5001/api/preloaded_data", timeout=10)
        
        print(f"✅ API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"📊 API Response Structure:")
            print(f"   success: {data.get('success')}")
            print(f"   message: {data.get('message')}")
            print(f"   timestamp: {data.get('timestamp')}")
            
            if 'data' in data:
                data_data = data['data']
                print(f"   data.cache_status: {data_data.get('cache_status')}")
                print(f"   data.total_analyzed: {data_data.get('total_analyzed')}")
                print(f"   data.opportunities_found: {data_data.get('opportunities_found')}")
                
                if 'enhanced_analysis' in data_data:
                    enhanced_analysis = data_data['enhanced_analysis']
                    print(f"   data.enhanced_analysis length: {len(enhanced_analysis)}")
                    
                    # Check the structure of the first item
                    if enhanced_analysis:
                        first_item = enhanced_analysis[0]
                        print(f"   First item keys: {list(first_item.keys())}")
                        print(f"   First item symbol: {first_item.get('symbol', 'No symbol')}")
                        print(f"   First item price_data: {first_item.get('price_data', 'No price_data')}")
                        print(f"   First item sentiment_data: {first_item.get('sentiment_data', 'No sentiment_data')}")
                        print(f"   First item signal_data: {first_item.get('signal_data', 'No signal_data')}")
                        print(f"   First item news_count: {first_item.get('news_count', 'No news_count')}")
                        
                        # Check if this matches what the JavaScript expects
                        print(f"\n🔍 JavaScript compatibility check:")
                        print(f"   Has symbol: {'symbol' in first_item}")
                        print(f"   Has price_data: {'price_data' in first_item}")
                        print(f"   Has sentiment_data: {'sentiment_data' in first_item}")
                        print(f"   Has signal_data: {'signal_data' in first_item}")
                        print(f"   Has news_count: {'news_count' in first_item}")
                        
                        # Check if price_data has the expected structure
                        price_data = first_item.get('price_data', {})
                        if price_data:
                            print(f"   price_data keys: {list(price_data.keys())}")
                            print(f"   Has current_price: {'current_price' in price_data}")
                            print(f"   Has change_percent: {'change_percent' in price_data}")
                        
                        # Check if sentiment_data has the expected structure
                        sentiment_data = first_item.get('sentiment_data', {})
                        if sentiment_data:
                            print(f"   sentiment_data keys: {list(sentiment_data.keys())}")
                            print(f"   Has sentiment_score: {'sentiment_score' in sentiment_data}")
                            print(f"   Has confidence: {'confidence' in sentiment_data}")
                        
                        # Check if signal_data has the expected structure
                        signal_data = first_item.get('signal_data', {})
                        if signal_data:
                            print(f"   signal_data keys: {list(signal_data.keys())}")
                            print(f"   Has action: {'action' in signal_data}")
                            print(f"   Has signal_strength: {'signal_strength' in signal_data}")
                        
                        # Simulate what the JavaScript should do
                        print(f"\n🧪 Simulating JavaScript processing:")
                        
                        # Check the condition from line 108 in stocks.js
                        condition = data.get('success') and data.get('data') and data.get('data', {}).get('enhanced_analysis')
                        print(f"   JavaScript condition (line 108): {condition}")
                        
                        if condition:
                            print(f"   ✅ JavaScript should accept this data")
                            
                            # Check if we have enough data to display
                            stocks = data['data']['enhanced_analysis']
                            winners = [s for s in stocks if s.get('price_data', {}).get('change_percent', 0) > 0]
                            losers = [s for s in stocks if s.get('price_data', {}).get('change_percent', 0) < 0]
                            
                            print(f"   📈 Winners count: {len(winners)}")
                            print(f"   📉 Losers count: {len(losers)}")
                            
                            if winners:
                                print(f"   Winners symbols: {[w.get('symbol') for w in winners]}")
                            if losers:
                                print(f"   Losers symbols: {[l.get('symbol') for l in losers]}")
                        else:
                            print(f"   ❌ JavaScript would reject this data")
                            
                            if not data.get('success'):
                                print(f"     - success is {data.get('success')}")
                            if not data.get('data'):
                                print(f"     - data is missing")
                            if not data.get('data', {}).get('enhanced_analysis'):
                                print(f"     - enhanced_analysis is missing")
                    else:
                        print(f"   ❌ No enhanced_analysis items found")
                else:
                    print(f"   ❌ No enhanced_analysis in data")
            else:
                print(f"   ❌ No data field in response")
        else:
            print(f"❌ API returned error status: {response.status_code}")
            print(f"Response text: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    test_api_response() 