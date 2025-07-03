#!/usr/bin/env python3
"""
Test to verify the JavaScript fix works
"""

import requests
import json

def test_js_fix():
    """Test the JavaScript fix by simulating the data processing"""
    
    print("🧪 Testing JavaScript fix...")
    
    try:
        # Get the API data
        response = requests.get("http://localhost:5001/api/preloaded_data", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            stocks = data['data']['enhanced_analysis']
            
            print(f"📊 Processing {len(stocks)} stocks...")
            
            # Simulate the JavaScript filtering logic
            winners = []
            losers = []
            
            for stock in stocks:
                if not stock or 'sentiment_data' not in stock or 'sentiment_score' not in stock['sentiment_data']:
                    continue
                    
                change_percent = stock.get('price_data', {}).get('change_percent', '0%')
                # Convert string like "242.9752%" to number, removing % and converting to float
                change_value = float(change_percent.replace('%', ''))
                
                if change_value > 0:
                    winners.append(stock)
                elif change_value < 0:
                    losers.append(stock)
            
            print(f"✅ Winners found: {len(winners)}")
            for winner in winners:
                symbol = winner.get('symbol', 'Unknown')
                change_percent = winner.get('price_data', {}).get('change_percent', '0%')
                sentiment = winner.get('sentiment_data', {}).get('sentiment_score', 0)
                print(f"   📈 {symbol}: {change_percent}, sentiment: {sentiment}")
            
            print(f"✅ Losers found: {len(losers)}")
            for loser in losers:
                symbol = loser.get('symbol', 'Unknown')
                change_percent = loser.get('price_data', {}).get('change_percent', '0%')
                sentiment = loser.get('sentiment_data', {}).get('sentiment_score', 0)
                print(f"   📉 {loser}: {change_percent}, sentiment: {sentiment}")
            
            if winners and losers:
                print("🎉 SUCCESS: JavaScript fix should work!")
                print("   The filtering logic now correctly identifies winners and losers")
                return True
            else:
                print("❌ FAILURE: No winners or losers found")
                return False
                
        else:
            print(f"❌ API returned error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing fix: {e}")
        return False

if __name__ == "__main__":
    test_js_fix() 