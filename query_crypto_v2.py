#!/usr/bin/env python3
"""
Script to query crypto data from the trading database.
"""
import sys
import os
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import get_db_connection

def query_crypto_data():
    """Query crypto data from the database."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check preloaded_watchlist_opportunities for crypto data
                print("\n=== Checking preloaded_watchlist_opportunities for crypto data ===")
                try:
                    cur.execute("""
                        SELECT symbol, type, timestamp, 
                               sentiment_data->>'sentiment_score' as sentiment_score,
                               signal_data->>'action' as signal_action,
                               signal_data->'confidence' as signal_confidence
                        FROM preloaded_watchlist_opportunities 
                        WHERE type = 'crypto' 
                        ORDER BY timestamp DESC 
                        LIMIT 5
                    """)
                    crypto_data = cur.fetchall()
                    if crypto_data:
                        print("\nLatest crypto opportunities:")
                        for row in crypto_data:
                            print(f"\nSymbol: {row['symbol']}")
                            print(f"Type: {row['type']}")
                            print(f"Timestamp: {row['timestamp']}")
                            print(f"Sentiment Score: {row['sentiment_score']}")
                            print(f"Signal Action: {row['signal_action']}")
                            print(f"Signal Confidence: {row['signal_confidence']}")
                            print("-" * 40)
                    else:
                        print("No crypto opportunities found in preloaded_watchlist_opportunities")
                except Exception as e:
                    print(f"Error querying preloaded_watchlist_opportunities: {e}")
                
                # Check market_movers for any crypto data
                print("\n=== Checking market_movers for crypto data ===")
                try:
                    cur.execute("""
                        SELECT * FROM market_movers 
                        WHERE source = 'crypto' 
                        OR symbol IN ('BTC', 'ETH', 'SOL', 'XRP', 'ADA')
                        ORDER BY timestamp DESC 
                        LIMIT 5
                    """)
                    market_movers = cur.fetchall()
                    if market_movers:
                        print("\nCrypto market movers:")
                        for row in market_movers:
                            print(f"\n{row['symbol']}: {row.get('price_change_percent', 'N/A')}%")
                            print(f"Price: ${row.get('price', 'N/A'):,.2f}" if 'price' in row else "No price data")
                            print(f"Volume: {row.get('volume', 'N/A'):,}" if 'volume' in row else "No volume data")
                            print(f"Source: {row.get('source', 'N/A')}")
                            print(f"Timestamp: {row.get('timestamp', 'N/A')}")
                            print("-" * 40)
                    else:
                        print("No crypto market movers found")
                except Exception as e:
                    print(f"Error querying market_movers: {e}")
                
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

if __name__ == "__main__":
    print("=== Starting crypto data query ===")
    query_crypto_data()
    print("\n=== Query complete ===")
