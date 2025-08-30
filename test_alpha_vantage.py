#!/usr/bin/env python3
"""
Test Alpha Vantage API directly to see what data it returns
"""

import sys
import os
import requests
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from core.config import Config
    
    print("🔍 Testing Alpha Vantage API directly...")
    print(f"API Key: {Config.ALPHA_VANTAGE_API_KEY[:10]}...")
    
    # Test the TOP_GAINERS_LOSERS endpoint
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TOP_GAINERS_LOSERS",
        "apikey": Config.ALPHA_VANTAGE_API_KEY,
    }
    
    print(f"🌐 Making request to: {url}")
    print(f"📋 Params: {params}")
    
    response = requests.get(url, params=params)
    print(f"📡 Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API Response received")
        print(f"📊 Response keys: {list(data.keys())}")
        
        if "top_gainers" in data and "top_losers" in data:
            print(f"\n🏆 TOP GAINERS ({len(data['top_gainers'])} stocks):")
            for i, gainer in enumerate(data["top_gainers"][:5]):  # Show first 5
                ticker = gainer.get("ticker", "N/A")
                change_percent = gainer.get("change_percentage", "N/A")
                price = gainer.get("price", "N/A")
                volume = gainer.get("volume", "N/A")
                print(f"  {i+1}. {ticker}: {change_percent}% (${price}) - Volume: {volume}")
            
            print(f"\n📉 TOP LOSERS ({len(data['top_losers'])} stocks):")
            for i, loser in enumerate(data["top_losers"][:5]):  # Show first 5
                ticker = loser.get("ticker", "N/A")
                change_percent = loser.get("change_percentage", "N/A")
                price = loser.get("price", "N/A")
                volume = loser.get("volume", "N/A")
                print(f"  {i+1}. {ticker}: {change_percent}% (${price}) - Volume: {volume}")
            
            # Check if the data matches what's in our table
            print(f"\n🔍 Checking if API data matches our table...")
            from core.database import get_db_connection
            
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT symbol, type, change_percent FROM market_movers ORDER BY timestamp DESC")
                    table_data = cur.fetchall()
                    
                    print(f"📋 Table data ({len(table_data)} records):")
                    for row in table_data:
                        symbol, type_, change_percent = row
                        print(f"  {symbol}: {type_} ({change_percent}%)")
                        
                        # Find this symbol in API response
                        api_type = None
                        api_change = None
                        
                        for gainer in data["top_gainers"]:
                            if gainer.get("ticker") == symbol:
                                api_type = "GAINER"
                                api_change = gainer.get("change_percentage", "N/A")
                                break
                        
                        for loser in data["top_losers"]:
                            if loser.get("ticker") == symbol:
                                api_type = "LOSER"
                                api_change = loser.get("change_percentage", "N/A")
                                break
                        
                        if api_type:
                            print(f"    ✅ API says: {api_type} ({api_change})")
                            if api_type != type_:
                                print(f"    ❌ MISMATCH: API says {api_type}, table says {type_}")
                        else:
                            print(f"    ❌ Symbol not found in API response")
        else:
            print(f"❌ API response missing expected keys")
            print(f"📄 Full response: {json.dumps(data, indent=2)}")
    else:
        print(f"❌ API request failed: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
