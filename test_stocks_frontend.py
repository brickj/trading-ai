#!/usr/bin/env python3
"""
Test script to simulate frontend data processing for stocks page
"""

import requests
import json

def test_sp500_analysis():
    """Test the sp500_analysis endpoint and simulate frontend processing"""
    
    print("Testing sp500_analysis endpoint...")
    
    # Test the API endpoint
    response = requests.get("http://localhost:5001/api/sp500_analysis?limit=3")
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
    
    result = response.json()
    print(f"Response status: {result.get('status')}")
    
    if result.get('status') != 'success':
        print(f"API error: {result.get('message', 'Unknown error')}")
        return
    
    data = result.get('data', {})
    print(f"Data keys: {list(data.keys())}")
    
    enhanced_analysis = data.get('enhanced_analysis', [])
    print(f"Enhanced analysis count: {len(enhanced_analysis)}")
    
    if not enhanced_analysis:
        print("No enhanced analysis data found")
        return
    
    # Simulate frontend processing
    print("\n=== Simulating Frontend Processing ===")
    
    for i, stock in enumerate(enhanced_analysis):
        print(f"\nStock {i+1}: {stock.get('symbol', 'N/A')}")
        print(f"  Type: {stock.get('type', 'N/A')}")
        print(f"  Keys: {list(stock.keys())}")
        
        # Check price data
        price_data = stock.get('price_data', {})
        print(f"  Price data keys: {list(price_data.keys())}")
        print(f"  Current price: {price_data.get('current_price', 'N/A')}")
        print(f"  Change percent: {price_data.get('change_percent', 'N/A')}")
        
        # Check sentiment data
        sentiment_data = stock.get('sentiment_data', {})
        print(f"  Sentiment data keys: {list(sentiment_data.keys())}")
        print(f"  Sentiment score: {sentiment_data.get('sentiment_score', 'N/A')}")
        print(f"  Confidence: {sentiment_data.get('confidence', 'N/A')}")
        
        # Check signal data
        signal_data = stock.get('signal_data', {})
        print(f"  Signal data keys: {list(signal_data.keys())}")
        print(f"  Action: {signal_data.get('action', 'N/A')}")
    
    # Simulate winners/losers filtering
    print("\n=== Simulating Winners/Losers Filtering ===")
    
    winners = []
    losers = []
    
    for stock in enhanced_analysis:
        stock_type = stock.get('type')
        if stock_type == 'winner':
            winners.append(stock)
        elif stock_type == 'loser':
            losers.append(stock)
        else:
            print(f"Warning: Stock {stock.get('symbol')} has unknown type: {stock_type}")
    
    print(f"Winners found: {len(winners)}")
    for winner in winners:
        print(f"  {winner.get('symbol')}: {winner.get('price_data', {}).get('change_percent', 'N/A')}")
    
    print(f"Losers found: {len(losers)}")
    for loser in losers:
        print(f"  {loser.get('symbol')}: {loser.get('price_data', {}).get('change_percent', 'N/A')}")
    
    # Check if data matches what frontend expects
    print("\n=== Data Structure Validation ===")
    
    required_fields = ['symbol', 'type', 'price_data', 'sentiment_data', 'signal_data']
    missing_fields = []
    
    for stock in enhanced_analysis:
        for field in required_fields:
            if field not in stock:
                missing_fields.append(f"{stock.get('symbol', 'Unknown')}.{field}")
    
    if missing_fields:
        print(f"Missing fields: {missing_fields}")
    else:
        print("All required fields present")
    
    # Check price_data structure
    price_data_fields = ['current_price', 'change_percent']
    missing_price_fields = []
    
    for stock in enhanced_analysis:
        price_data = stock.get('price_data', {})
        for field in price_data_fields:
            if field not in price_data:
                missing_price_fields.append(f"{stock.get('symbol', 'Unknown')}.price_data.{field}")
    
    if missing_price_fields:
        print(f"Missing price data fields: {missing_price_fields}")
    else:
        print("All required price data fields present")

if __name__ == "__main__":
    test_sp500_analysis()
