#!/usr/bin/env python3
"""Script to check the contents of the preloaded_data table."""

import json
from src.core.database import get_db_connection

def check_preloaded_data():
    """Query and display the latest preloaded data."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get the most recent entry
                cur.execute("""
                    SELECT id, timestamp, jsonb_pretty(data::jsonb) 
                    FROM preloaded_data 
                    ORDER BY timestamp DESC 
                    LIMIT 1;
                """)
                row = cur.fetchone()
                
                if row:
                    print(f"Found data (ID: {row[0]}, Timestamp: {row[1]})")
                    print("=" * 80)
                    print(row[2])
                else:
                    print("No data found in preloaded_data table.")
                    
                # Get count of entries
                cur.execute("SELECT COUNT(*) FROM preloaded_data;")
                count = cur.fetchone()[0]
                print(f"\nTotal entries in preloaded_data: {count}")
                
    except Exception as e:
        print(f"Error querying database: {e}")

if __name__ == "__main__":
    check_preloaded_data()
