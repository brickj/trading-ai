#!/usr/bin/env python3
import requests
import json

def test_foreign_markets():
    print("🌍 Testing Foreign Markets Functionality")
    print("=" * 50)
    
    # Test 1: Check watchlist configuration
    print("\n1. Testing Watchlist Configuration...")
    try:
        response = requests.get("http://localhost:5001/api/watchlist/config")
        if response.status_code == 200:
            data = response.json()
            stocks = data['data']['stocks']
            foreign_stocks = [s['symbol'] for s in stocks if '.' in s['symbol']]
            print(f"   ✅ Total stocks: {len(stocks)}")
            print(f"   🌍 Foreign stocks: {len(foreign_stocks)}")
            print(f"   📊 Foreign symbols: {foreign_stocks[:10]}")
        else:
            print(f"   ❌ Failed to get watchlist config: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Check watchlist opportunities
    print("\n2. Testing Watchlist Opportunities...")
    try:
        response = requests.get("http://localhost:5001/api/watchlist_opportunities")
        if response.status_code == 200:
            data = response.json()
            opportunities = data['data']['opportunities']
            foreign_opps = [o for o in opportunities if '.' in o.get('symbol', '')]
            print(f"   ✅ Total opportunities: {len(opportunities)}")
            print(f"   🌍 Foreign opportunities: {len(foreign_opps)}")
            
            if foreign_opps:
                print("   📊 Sample foreign opportunities:")
                for opp in foreign_opps[:5]:
                    symbol = opp.get('symbol', 'N/A')
                    price = opp.get('price_data', {}).get('current_price', 'N/A')
                    print(f"      {symbol}: ${price}")
            else:
                print("   ⚠️  No foreign opportunities found")
        else:
            print(f"   ❌ Failed to get opportunities: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Test individual foreign stock analysis
    print("\n3. Testing Individual Foreign Stock Analysis...")
    test_symbols = ['HSBA.L', '7203.T', 'SAP.DE']
    for symbol in test_symbols:
        try:
            response = requests.post("http://localhost:5001/api/analyze_stock", 
                                   json={"symbol": symbol})
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"   ✅ {symbol}: Analysis successful")
                else:
                    print(f"   ⚠️  {symbol}: {data.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ {symbol}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {symbol}: Error - {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Foreign Markets Test Complete!")

if __name__ == "__main__":
    test_foreign_markets()

