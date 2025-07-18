#!/usr/bin/env python3
"""
Watchlist Setup Script
======================

This script initializes the watchlist with default symbols for testing
the opportunities page functionality.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.core.watchlist_manager import watchlist_manager
from src.core.database import get_db_connection

def setup_default_watchlist():
    """Set up default watchlist symbols for testing"""
    
    # Default symbols for testing
    default_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'V', 'UNH']
    default_cryptos = ['BTCUSD', 'ETHUSD', 'ADAUSD', 'SOLUSD']
    
    print("🚀 Setting up default watchlist symbols...")
    print("=" * 50)
    
    # Ensure tables exist
    watchlist_manager.create_table_if_not_exists()
    
    # Add default stocks
    print("\n📈 Adding default stocks:")
    for symbol in default_stocks:
        success = watchlist_manager.add_stock(symbol)
        status = "✅" if success else "❌"
        print(f"  {status} {symbol}")
    
    # Add default cryptos
    print("\n💰 Adding default cryptos:")
    for symbol in default_cryptos:
        success = watchlist_manager.add_crypto(symbol)
        status = "✅" if success else "❌"
        print(f"  {status} {symbol}")
    
    # Verify setup
    print("\n🔍 Verifying watchlist setup:")
    stocks = watchlist_manager.get_stocks()
    cryptos = watchlist_manager.get_cryptos()
    
    print(f"  📈 Stocks: {len(stocks)} symbols")
    if stocks:
        print(f"     {', '.join(stocks)}")
    
    print(f"  💰 Cryptos: {len(cryptos)} symbols")
    if cryptos:
        print(f"     {', '.join(cryptos)}")
    
    print(f"\n✅ Watchlist setup completed!")
    print(f"   Total symbols: {len(stocks) + len(cryptos)}")
    
    return len(stocks) + len(cryptos) > 0

def test_watchlist_analysis():
    """Test that watchlist analysis can run"""
    print("\n🧪 Testing watchlist analysis...")
    
    try:
        from src.data.preload_watchlist_opportunities import preload_watchlist_opportunities
        print("  Running watchlist opportunities preload...")
        preload_watchlist_opportunities()
        print("  ✅ Watchlist analysis test completed")
        return True
    except Exception as e:
        print(f"  ❌ Watchlist analysis test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up Trading AI Watchlist...")
    
    if setup_default_watchlist():
        print("\n🧪 Testing watchlist functionality...")
        if test_watchlist_analysis():
            print("\n🎉 Watchlist setup and testing completed successfully!")
            print("\n📝 Next steps:")
            print("  1. Start the application: python start_app.py")
            print("  2. Visit /opportunities page to see watchlist analysis")
            print("  3. Visit /system_status to manage watchlist symbols")
        else:
            print("\n⚠️ Watchlist setup completed but analysis test failed")
            print("   Check logs for more details")
    else:
        print("\n❌ Watchlist setup failed")
        sys.exit(1) 