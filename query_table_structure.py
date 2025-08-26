#!/usr/bin/env python3
"""
Script to check the structure of database tables.
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import get_db_connection

def check_table_structure():
    """Check the structure of relevant database tables."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check preloaded_watchlist_opportunities structure
                print("\n=== Structure of preloaded_watchlist_opportunities ===")
                try:
                    cur.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'preloaded_watchlist_opportunities'
                    """)
                    columns = cur.fetchall()
                    if columns:
                        print("\nColumns in preloaded_watchlist_opportunities:")
                        for col in columns:
                            print(f"- {col['column_name']} ({col['data_type']})")
                    else:
                        print("Could not find preloaded_watchlist_opportunities table")
                except Exception as e:
                    print(f"Error checking table structure: {e}")
                
                # Check market_movers structure
                print("\n=== Structure of market_movers ===")
                try:
                    cur.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'market_movers'
                    """)
                    columns = cur.fetchall()
                    if columns:
                        print("\nColumns in market_movers:")
                        for col in columns:
                            print(f"- {col['column_name']} ({col['data_type']})")
                    else:
                        print("Could not find market_movers table")
                except Exception as e:
                    print(f"Error checking table structure: {e}")
                
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

if __name__ == "__main__":
    print("=== Checking database table structures ===")
    check_table_structure()
    print("\n=== Structure check complete ===")
