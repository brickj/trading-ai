#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.resolve()
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from src.core.database import get_db_connection
from src.data.preload_watchlist_opportunities import get_latest_preloaded_watchlist_opportunities
import psycopg2.extras

def debug_watchlist_data():
    print("=== Debugging Watchlist Opportunities ===")
    
    # Test the function directly
    print("\n1. Testing get_latest_preloaded_watchlist_opportunities():")
    try:
        data = get_latest_preloaded_watchlist_opportunities()
        print(f"Function result: {data}")
    except Exception as e:
        print(f"Function error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test database connection directly
    print("\n2. Testing database connection directly:")
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if table has data
                cur.execute("SELECT COUNT(*) FROM preloaded_watchlist_opportunities")
                count = cur.fetchone()
                print(f"Total records: {count[0] if count else 0}")
                
                if count and count[0] > 0:
                    # Get the latest record
                    cur.execute("""
                        SELECT timestamp, opportunities, symbols_analyzed, errors_count 
                        FROM preloaded_watchlist_opportunities 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """)
                    row = cur.fetchone()
                    
                    if row:
                        timestamp, opportunities, symbols_analyzed, errors_count = row
                        print(f"Raw timestamp: {timestamp} (type: {type(timestamp)})")
                        print(f"Raw opportunities: {opportunities} (type: {type(opportunities)})")
                        print(f"Raw symbols_analyzed: {symbols_analyzed} (type: {type(symbols_analyzed)})")
                        print(f"Raw errors_count: {errors_count} (type: {type(errors_count)})")
                        
                        # Test JSON parsing
                        if opportunities:
                            print(f"\n3. Testing JSON parsing:")
                            try:
                                if isinstance(opportunities, str):
                                    import json
                                    parsed = json.loads(opportunities)
                                else:
                                    parsed = opportunities
                                print(f"Parsed opportunities: {parsed}")
                                print(f"Number of opportunities: {len(parsed) if isinstance(parsed, list) else 'Not a list'}")
                            except Exception as e:
                                print(f"JSON parsing error: {e}")
                                import traceback
                                traceback.print_exc()
                else:
                    print("No data found in database")
                    
    except Exception as e:
        print(f"Database error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_watchlist_data() 