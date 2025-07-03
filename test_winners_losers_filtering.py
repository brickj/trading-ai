#!/usr/bin/env python3
"""
Test script to debug winners/losers filtering logic
"""

import json
import requests

def test_filtering_logic():
    """Test the filtering logic that the JavaScript uses"""
    
    # Get the API data
    try:
        response = requests.get('http://localhost:5001/api/preloaded_data')
        if response.status_code != 200:
            print(f"❌ API request failed: {response.status_code}")
            return
        
        data = response.json()
        stocks = data['data']['enhanced_analysis']
        print(f"✅ Got {len(stocks)} stocks from API")
        
    except Exception as e:
        print(f"❌ Error getting API data: {e}")
        return
    
    # Test the JavaScript filtering logic
    print("\n🔍 Testing JavaScript filtering logic:")
    
    winners = []
    losers = []
    
    for stock in stocks:
        print(f"\n📊 Stock: {stock.get('symbol', 'Unknown')}")
        
        # Check if stock has required data
        if not stock:
            print("  ❌ Stock is null/undefined")
            continue
            
        if 'sentiment_data' not in stock or stock['sentiment_data'].get('sentiment_score') is None:
            print("  ❌ Missing sentiment_data.sentiment_score")
            continue
            
        if 'price_data' not in stock:
            print("  ❌ Missing price_data")
            continue
            
        change_percent = stock['price_data'].get('change_percent', '0%')
        sentiment_score = stock['sentiment_data']['sentiment_score']
        
        print(f"  📈 Change percent: {change_percent}")
        print(f"  😊 Sentiment score: {sentiment_score}")
        
        # Convert string like "242.9752%" to number
        try:
            change_value = float(change_percent.replace('%', ''))
            print(f"  🔢 Parsed change value: {change_value}")
            
            if change_value > 0:
                winners.append(stock)
                print(f"  ✅ Added to winners")
            elif change_value < 0:
                losers.append(stock)
                print(f"  ✅ Added to losers")
            else:
                print(f"  ⚠️  No change (0%)")
                
        except ValueError as e:
            print(f"  ❌ Error parsing change_percent: {e}")
    
    print(f"\n📊 Results:")
    print(f"  🟢 Winners: {len(winners)}")
    for winner in winners:
        symbol = winner.get('symbol', 'Unknown')
        change = winner['price_data'].get('change_percent', '0%')
        sentiment = winner['sentiment_data'].get('sentiment_score', 0)
        print(f"    - {symbol}: {change} (sentiment: {sentiment})")
    
    print(f"  🔴 Losers: {len(losers)}")
    for loser in losers:
        symbol = loser.get('symbol', 'Unknown')
        change = loser['price_data'].get('change_percent', '0%')
        sentiment = loser['sentiment_data'].get('sentiment_score', 0)
        print(f"    - {symbol}: {change} (sentiment: {sentiment})")
    
    if len(winners) == 0:
        print("\n❌ No winners found - this explains why the page shows 'No winners data available'")
    if len(losers) == 0:
        print("\n❌ No losers found - this explains why the page shows 'No losers data available'")

if __name__ == "__main__":
    test_filtering_logic() 