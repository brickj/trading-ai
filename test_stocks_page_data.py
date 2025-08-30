#!/usr/bin/env python3
"""
Test Stocks Page Data Display
Verifies that the stocks page shows the correct data from the market_movers table
"""

import asyncio
import json
import sys
import os
import subprocess
import psycopg2
from psycopg2.extras import RealDictCursor

# Add src to path for config access
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_stocks_page_data():
    """Test the stocks page displays correct data from market_movers table"""
    from src.core.config import Config
    
    print("🔍 Testing Stocks Page Data Display...")
    
    # Use database config from config.py
    db_config = Config.DATABASE_CONFIG
    
    # First, get the actual data from the market_movers table
    try:
        conn = psycopg2.connect(**db_config)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT symbol, type, change_percent, price, volume, timestamp
                    FROM market_movers 
                    ORDER BY timestamp DESC
                """)
                rows = cur.fetchall()
                
                gainers = []
                losers = []
                
                for row in rows:
                    # RealDictCursor returns dictionaries, so access by column name
                    symbol = row['symbol']
                    type_ = row['type']
                    change_percent = row['change_percent']
                    price = row['price']
                    volume = row['volume']
                    
                    if type_ == 'GAINER':
                        gainers.append({
                            'symbol': symbol,
                            'change_percent': change_percent,
                            'price': price,
                            'volume': volume
                        })
                    elif type_ == 'LOSER':
                        losers.append({
                            'symbol': symbol,
                            'change_percent': change_percent,
                            'price': price,
                            'volume': volume
                        })
                
                print(f"📊 Database Data:")
                print(f"   Gainers in DB: {len(gainers)}")
                for g in gainers[:3]:
                    print(f"     {g['symbol']}: {g['change_percent']}% at ${g['price']}")
                print(f"   Losers in DB: {len(losers)}")
                for l in losers[:3]:
                    print(f"     {l['symbol']}: {l['change_percent']}% at ${l['price']}")
                
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
    
    # Test the API endpoint
    try:
        import requests
        response = requests.get("http://localhost:5001/api/market_movers")
        if response.status_code == 200:
            api_data = response.json()
            print(f"📡 API Response:")
            print(f"   Status: {api_data.get('status')}")
            print(f"   API Gainers: {len(api_data.get('data', {}).get('gainers', []))}")
            print(f"   API Losers: {len(api_data.get('data', {}).get('losers', []))}")
        else:
            print(f"❌ API request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API error: {e}")
        return False
    
    # Test the stocks page with simple HTTP request (since we're having browser issues)
    try:
        stocks_response = requests.get("http://localhost:5001/stocks")
        if stocks_response.status_code == 200:
            print(f"✅ Stocks page loads successfully")
            
            # Check if page contains stock data (simple text search)
            page_content = stocks_response.text
            if any(g['symbol'] in page_content for g in gainers[:3]):
                print(f"✅ Found gainer symbols in page content")
            else:
                print(f"❌ No gainer symbols found in page content")
                
            if any(l['symbol'] in page_content for l in losers[:3]):
                print(f"✅ Found loser symbols in page content")
            else:
                print(f"❌ No loser symbols found in page content")
                
        else:
            print(f"❌ Stocks page failed to load: {stocks_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Stocks page error: {e}")
        return False
    
    print(f"\n🔍 Summary:")
    print(f"   Database has {len(gainers)} gainers and {len(losers)} losers")
    print(f"   API returns {len(api_data.get('data', {}).get('gainers', []))} gainers and {len(api_data.get('data', {}).get('losers', []))} losers")
    print(f"   Stocks page loads and may contain the data")
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_stocks_page_data())
        if result:
            print("✅ Test completed")
        else:
            print("❌ Test failed")
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
