#!/usr/bin/env python3
import requests
import json

try:
    response = requests.get("http://localhost:5001/api/preloaded_data")
    data = response.json()
    
    print("✅ API Response Summary:")
    print(f"Success: {data['success']}")
    print(f"Total Stocks: {data['data']['total_analyzed']}")
    print(f"Message: {data['message']}")
    print()
    
    print("📊 Stocks Data:")
    for stock in data['data']['enhanced_analysis']:
        symbol = stock['symbol']
        price = stock['price_data']['current_price']
        change = stock['price_data']['change_percent']
        print(f"  {symbol}: ${price:.2f} ({change:+.2f}%)")
        
    print()
    print("🎯 Summary:")
    gainers = [s for s in data['data']['enhanced_analysis'] if s['price_data']['change_percent'] > 0]
    losers = [s for s in data['data']['enhanced_analysis'] if s['price_data']['change_percent'] < 0]
    print(f"  Gainers: {len(gainers)}")
    print(f"  Losers: {len(losers)}")
    print(f"  Total: {len(gainers) + len(losers)}")
    
except Exception as e:
    print(f"Error: {e}") 