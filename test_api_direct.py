#!/usr/bin/env python3
"""
Direct API test for watchlist_opportunities endpoint
"""

import requests
import json
import sys

def test_watchlist_opportunities_api():
    """Test the watchlist_opportunities API endpoint directly"""
    
    print("🧪 Testing /api/watchlist_opportunities endpoint...")
    
    try:
        # Make the API call
        response = requests.get('http://localhost:5000/api/watchlist_opportunities')
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"❌ API returned error status: {response.status_code}")
            print(f"❌ Response text: {response.text}")
            return False
        
        # Parse JSON response
        data = response.json()
        
        print(f"📊 Response data type: {type(data)}")
        print(f"📊 Top-level keys: {list(data.keys())}")
        
        # Check if data has the expected structure
        if 'data' in data:
            print(f"📊 Data object keys: {list(data['data'].keys())}")
            opportunities = data['data'].get('opportunities', [])
        else:
            opportunities = data.get('opportunities', [])
        
        print(f"📊 Opportunities count: {len(opportunities)}")
        
        if opportunities:
            print(f"📊 First opportunity structure:")
            first_opp = opportunities[0]
            print(json.dumps(first_opp, indent=2))
            
            # Check for required fields
            required_fields = ['symbol', 'type', 'trigger', 'signal_data', 'sentiment_data', 'price_data']
            missing_fields = [field for field in required_fields if field not in first_opp]
            
            if missing_fields:
                print(f"⚠️ Missing required fields: {missing_fields}")
            else:
                print("✅ All required fields present")
                
            # Check nested structures
            if 'signal_data' in first_opp:
                print(f"📊 Signal data keys: {list(first_opp['signal_data'].keys())}")
            if 'sentiment_data' in first_opp:
                print(f"📊 Sentiment data keys: {list(first_opp['sentiment_data'].keys())}")
            if 'price_data' in first_opp:
                print(f"📊 Price data keys: {list(first_opp['price_data'].keys())}")
        else:
            print("⚠️ No opportunities found in response")
            
        # Print full response for debugging
        print(f"\n📊 Full API Response:")
        print(json.dumps(data, indent=2))
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the Flask app is running.")
        return False
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

if __name__ == "__main__":
    success = test_watchlist_opportunities_api()
    sys.exit(0 if success else 1) 