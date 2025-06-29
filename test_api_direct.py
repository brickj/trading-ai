#!/usr/bin/env python3

import requests
import json

def test_api_direct():
    print("🧪 Testing Direct API Call to /api/analyze_stock")
    print("=" * 50)
    
    # Make direct API call
    url = "http://localhost:5001/api/analyze_stock"
    data = {"symbol": "MSFT"}
    
    try:
        response = requests.post(url, json=data)
        print(f"📋 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📋 Response keys: {list(result.keys())}")
            
            if 'data' in result:
                data_keys = list(result['data'].keys())
                print(f"📋 Data keys: {data_keys}")
                
                has_options = 'options_recommendation' in result['data']
                print(f"✅ Has options_recommendation: {has_options}")
                
                if has_options:
                    options = result['data']['options_recommendation']
                    print(f"📋 Options action: {options.get('action', 'N/A')}")
                    print("🎉 SUCCESS: API response includes options_recommendation!")
                else:
                    print("❌ FAILED: API response does NOT include options_recommendation")
                    print(f"📋 Available fields: {data_keys}")
            else:
                print("❌ No 'data' field in response")
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"📋 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error making API call: {e}")

if __name__ == "__main__":
    test_api_direct() 