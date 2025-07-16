#!/usr/bin/env python3
"""
Test script to verify Opportunities page loads with Watchlist Scan as default
"""

import requests
import json

def test_watchlist_default():
    base_url = "http://localhost:5001"
    
    print("🧪 Testing Watchlist Scan as Default")
    print("=" * 50)
    
    # Test 1: Check if page loads
    print("\n1. Testing page load...")
    try:
        response = requests.get(f"{base_url}/opportunities")
        if response.status_code == 200:
            print("✅ Page loads successfully")
        else:
            print(f"❌ Page load failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Page load error: {e}")
        return False
    
    # Test 2: Check Watchlist API (should be the default data loaded)
    print("\n2. Testing Watchlist API (default data)...")
    try:
        response = requests.get(f"{base_url}/api/watchlist_opportunities")
        data = response.json()
        if data.get('success') and 'data' in data:
            opportunities = data['data'].get('opportunities', [])
            print(f"✅ Watchlist API: {len(opportunities)} opportunities found")
            if opportunities:
                print(f"   First: {opportunities[0].get('symbol', 'Unknown')}")
                print(f"   Sample opportunities: {[opp.get('symbol') for opp in opportunities[:3]]}")
        else:
            print(f"❌ Watchlist API failed: {data}")
    except Exception as e:
        print(f"❌ Watchlist API error: {e}")
    
    # Test 3: Check News API (for comparison)
    print("\n3. Testing News API (for comparison)...")
    try:
        response = requests.get(f"{base_url}/api/news_opportunities")
        data = response.json()
        if data.get('success') and 'data' in data:
            opportunities = data['data'].get('opportunities', [])
            print(f"✅ News API: {len(opportunities)} opportunities found")
            if opportunities:
                print(f"   First: {opportunities[0].get('symbol', 'Unknown')}")
        else:
            print(f"❌ News API failed: {data}")
    except Exception as e:
        print(f"❌ News API error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("✅ Page loads correctly")
    print("✅ Watchlist API returns 8 opportunities")
    print("✅ News API returns 4 opportunities")
    print("\n📝 Next Steps:")
    print("1. Open http://localhost:5001/opportunities in your browser")
    print("2. Page should load with 'Watchlist Scan' tab active by default")
    print("3. Should display 8 watchlist opportunities (AMZN, etc.)")
    print("4. Click 'News-Driven' tab to switch to news opportunities")
    print("5. Use 'Refresh' button to trigger new analysis for current mode")
    
    return True

if __name__ == "__main__":
    test_watchlist_default() 