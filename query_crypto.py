#!/usr/bin/env python3
"""
Script to query crypto data from the trading database.
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import get_db_connection

def query_crypto_data():
    """Query crypto data from the database."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # First, list all tables to see what's available
                print("\n=== Listing all tables in the database ===")
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = cur.fetchall()
                print("\nTables in the database:")
                for table in tables:
                    print(f"- {table['table_name']}")
                
                # Check for crypto-related tables
                print("\n=== Checking for crypto data in watchlist_opportunities ===")
                try:
                    cur.execute("""
                        SELECT * FROM watchlist_opportunities 
                        WHERE type = 'crypto' 
                        LIMIT 5
                    """)
                    crypto_data = cur.fetchall()
                    if crypto_data:
                        print("\nCrypto opportunities found:")
                        for row in crypto_data:
                            print(row)
                    else:
                        print("No crypto opportunities found in watchlist_opportunities")
                except Exception as e:
                    print(f"Error querying watchlist_opportunities: {e}")
                
                # Check for any crypto symbols in the symbols table
                print("\n=== Checking for crypto symbols in symbols table ===")
                try:
                    cur.execute("""
                        SELECT * FROM symbols 
                        WHERE type = 'crypto' 
                        LIMIT 5
                    """)
                    crypto_symbols = cur.fetchall()
                    if crypto_symbols:
                        print("\nCrypto symbols found:")
                        for row in crypto_symbols:
                            print(row)
                    else:
                        print("No crypto symbols found in symbols table")
                except Exception as e:
                    print(f"Error querying symbols table: {e}")
                
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

if __name__ == "__main__":
    print("=== Starting crypto data query ===")
    query_crypto_data()
    print("\n=== Query complete ===")
