#!/usr/bin/env python3
"""
Script to query crypto data from the trading database.
"""
import sys
import os
import json
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import get_db_connection

def query_crypto_data():
    """Query crypto data from the database."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get the most recent preloaded opportunities
                print("\n=== Checking for crypto opportunities ===")
                try:
                    # Get the most recent record
                    cur.execute("""
                        SELECT timestamp, opportunities 
                        FROM preloaded_watchlist_opportunities 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """)
                    latest_data = cur.fetchone()
                    
                    if latest_data and latest_data['opportunities']:
                        print(f"\nLatest data from: {latest_data['timestamp']}")
                        
                        # Parse the JSON data
                        opportunities = latest_data['opportunities']
                        if isinstance(opportunities, str):
                            opportunities = json.loads(opportunities)
                        
                        # Filter for crypto opportunities
                        crypto_opps = [opp for opp in opportunities if isinstance(opp, dict) and opp.get('type') == 'crypto']
                        
                        if crypto_opps:
                            print(f"\nFound {len(crypto_opps)} crypto opportunities:")
                            for i, opp in enumerate(crypto_opps[:5], 1):  # Show first 5
                                print(f"\n{i}. {opp.get('symbol', 'N/A')} - {opp.get('name', 'Unnamed')}")
                                print(f"   Sentiment: {opp.get('sentiment_score', 'N/A')}")
                                print(f"   Signal: {opp.get('signal', 'N/A')}")
                                print(f"   Price: {opp.get('price', 'N/A')}")
                        else:
                            print("\nNo crypto opportunities found in the latest data")
                            
                            # Print available opportunity types for debugging
                            if opportunities and len(opportunities) > 0:
                                types = set(opp.get('type', 'unknown') for opp in opportunities if isinstance(opp, dict))
                                print(f"\nAvailable opportunity types: {', '.join(types) if types else 'None'}")
                    else:
                        print("\nNo preloaded opportunities found in the database")
                        
                except Exception as e:
                    print(f"Error querying opportunities: {e}")
                
                # Check market movers for crypto
                print("\n=== Checking crypto market movers ===")
                try:
                    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
                    cur.execute("""
                        SELECT symbol, type, price, change_percent, volume, timestamp 
                        FROM market_movers 
                        WHERE type = 'crypto' 
                        OR symbol IN ('BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'DOT', 'AVAX', 'LTC', 'UNI')
                        AND timestamp >= %s
                        ORDER BY ABS(change_percent) DESC
                        LIMIT 10
                    """, (one_hour_ago,))
                    
                    movers = cur.fetchall()
                    if movers:
                        print("\nTop crypto market movers (last hour):")
                        for i, mover in enumerate(movers, 1):
                            change = float(mover['change_percent'])
                            change_str = f"↑ {change:.2f}%" if change >= 0 else f"↓ {abs(change):.2f}%"
                            print(f"{i}. {mover['symbol']}: {change_str}")
                            print(f"   Price: ${float(mover['price']):,.2f}" if mover['price'] else "   No price data")
                            print(f"   Volume: {mover['volume']:,}" if mover['volume'] else "   No volume data")
                            print(f"   Last updated: {mover['timestamp']}")
                    else:
                        print("\nNo recent crypto market movers found")
                        
                except Exception as e:
                    print(f"Error querying market movers: {e}")
                
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

if __name__ == "__main__":
    print("=== Starting crypto data query ===")
    query_crypto_data()
    print("\n=== Query complete ===")
