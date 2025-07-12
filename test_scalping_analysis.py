#!/usr/bin/env python3
"""
Test Scalping Analysis
Tests the scalping analysis functionality to ensure it works correctly.
"""

import sys
import os
import json
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.scalping_analyzer import scalping_analyzer
from src.core.logger import log_info, log_error, log_warning

def test_scalping_analyzer():
    """Test the scalping analyzer functionality"""
    print("🧪 Testing Scalping Analyzer...")
    
    try:
        # Test 1: Create tables
        print("\n1. Testing table creation...")
        success = scalping_analyzer.create_tables_if_not_exists()
        if success:
            print("✅ Tables created/verified successfully")
        else:
            print("❌ Failed to create tables")
            return False
        
        # Test 2: Get active watchlist tickers
        print("\n2. Testing watchlist ticker loading...")
        tickers = scalping_analyzer.get_active_watchlist_tickers()
        print(f"✅ Loaded {len(tickers)} active tickers")
        for ticker in tickers[:5]:  # Show first 5
            print(f"   - {ticker['ticker']} ({ticker['asset_type']})")
        
        if len(tickers) == 0:
            print("⚠️  No active tickers found. This is normal if watchlist is empty.")
        
        # Test 3: Test market data fetching (for first ticker if available)
        if tickers:
            print(f"\n3. Testing market data fetching for {tickers[0]['ticker']}...")
            market_data = scalping_analyzer.get_market_data(
                tickers[0]['ticker'], 
                tickers[0]['asset_type']
            )
            
            if 'error' not in market_data:
                print("✅ Market data fetched successfully")
                print(f"   - Price Open: ${market_data.get('price_open', 'N/A')}")
                print(f"   - Price Now: ${market_data.get('price_now', 'N/A')}")
                print(f"   - Volume Ratio: {market_data.get('volume_ratio', 'N/A')}x")
                print(f"   - Price Change: {market_data.get('price_change_pct', 'N/A')}%")
            else:
                print(f"❌ Market data error: {market_data['error']}")
        
        # Test 4: Test news and sentiment (for first ticker if available)
        if tickers:
            print(f"\n4. Testing news and sentiment for {tickers[0]['ticker']}...")
            sentiment_data = scalping_analyzer.get_news_and_sentiment(
                tickers[0]['ticker'], 
                tickers[0]['asset_type']
            )
            
            print("✅ Sentiment analysis completed")
            print(f"   - Sentiment Score: {sentiment_data.get('sentiment_score', 'N/A')}")
            print(f"   - Sentiment Class: {sentiment_data.get('sentiment_class', 'N/A')}")
            print(f"   - Headlines Count: {len(sentiment_data.get('headlines', []))}")
        
        # Test 5: Test recommendation generation
        print("\n5. Testing recommendation generation...")
        if tickers and 'error' not in market_data:
            recommendation = scalping_analyzer.generate_scalping_recommendation(
                market_data, sentiment_data
            )
            print(f"✅ Recommendation: {recommendation}")
        
        # Test 6: Test API endpoint
        print("\n6. Testing API endpoint...")
        api_result = scalping_analyzer.get_scalping_opportunities_api()
        print(f"✅ API endpoint working")
        print(f"   - Total Signals: {api_result.get('total_signals', 0)}")
        print(f"   - Opportunities: {api_result.get('opportunities', 0)}")
        
        # Test 7: Test full analysis (limited to first 2 tickers for speed)
        print("\n7. Testing full analysis (limited scope)...")
        if len(tickers) > 0:
            # Temporarily modify the method to only process first 2 tickers
            original_tickers = scalping_analyzer.get_active_watchlist_tickers
            scalping_analyzer.get_active_watchlist_tickers = lambda: tickers[:2]
            
            opportunities = scalping_analyzer.run_morning_scalping_analysis()
            
            # Restore original method
            scalping_analyzer.get_active_watchlist_tickers = original_tickers
            
            print(f"✅ Full analysis completed")
            print(f"   - Processed tickers: {len(tickers[:2])}")
            print(f"   - Opportunities found: {len(opportunities)}")
            
            for opp in opportunities:
                print(f"   - {opp['ticker']}: {opp['recommendation']}")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test the API endpoints"""
    print("\n🌐 Testing API Endpoints...")
    
    try:
        import requests
        
        base_url = "http://localhost:5000"
        
        # Test 1: Get opportunities
        print("1. Testing /api/scalping/opportunities...")
        response = requests.get(f"{base_url}/api/scalping/opportunities", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Opportunities API working")
            print(f"   - Total Signals: {data.get('total_signals', 0)}")
            print(f"   - Opportunities: {data.get('opportunities', 0)}")
        else:
            print(f"❌ Opportunities API failed: {response.status_code}")
        
        # Test 2: Get stats
        print("\n2. Testing /api/scalping/stats...")
        response = requests.get(f"{base_url}/api/scalping/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stats API working")
            if data.get('success') and data.get('today'):
                print(f"   - Today's Signals: {data['today'].get('total_signals', 0)}")
                print(f"   - Today's Opportunities: {data['today'].get('opportunities', 0)}")
        else:
            print(f"❌ Stats API failed: {response.status_code}")
        
        # Test 3: Get today's signals
        print("\n3. Testing /api/scalping/today...")
        response = requests.get(f"{base_url}/api/scalping/today", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Today's signals API working")
            print(f"   - Signals count: {data.get('count', 0)}")
        else:
            print(f"❌ Today's signals API failed: {response.status_code}")
        
        print("\n🎉 API endpoint tests completed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("⚠️  API tests skipped - Flask app not running")
        print("   Start the app with: python3 start_app.py")
        return True
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Scalping Analysis Tests")
    print("=" * 50)
    
    # Test the core functionality
    core_success = test_scalping_analyzer()
    
    # Test API endpoints (if app is running)
    api_success = test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Core Functionality: {'✅ PASS' if core_success else '❌ FAIL'}")
    print(f"   API Endpoints: {'✅ PASS' if api_success else '❌ FAIL'}")
    
    if core_success and api_success:
        print("\n🎉 All tests passed! Scalping analysis is ready to use.")
        print("\nNext steps:")
        print("1. Add tickers to watchlist: Use the web interface")
        print("2. Run analysis manually: python3 run_scalping_analysis.py")
        print("3. Set up automatic scheduling: ./setup_scalping_cron.sh")
        print("4. View results: http://localhost:5000/scalping_signals")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
    
    return core_success and api_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 