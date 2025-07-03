#!/usr/bin/env python3
"""
Script to check market_movers table data
"""

from src.core.database import get_db_connection
import json

def check_market_movers_data():
    """Check the market_movers table for data"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check total count
                cur.execute("SELECT COUNT(*) FROM market_movers")
                total_count = cur.fetchone()['count']
                print(f"Total market_movers records: {total_count}")
                
                if total_count == 0:
                    print("❌ No data found in market_movers table!")
                    return
                
                # Check records by type
                cur.execute("SELECT type, COUNT(*) as count FROM market_movers GROUP BY type")
                type_counts = cur.fetchall()
                print("\nRecords by type:")
                for row in type_counts:
                    print(f"  {row['type']}: {row['count']}")
                
                # Check recent records
                cur.execute("""
                    SELECT symbol, type, change_percent, timestamp 
                    FROM market_movers 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                """)
                recent_records = cur.fetchall()
                print("\nRecent records:")
                for row in recent_records:
                    print(f"  {row['symbol']} ({row['type']}): {row['change_percent']}% at {row['timestamp']}")
                
                # Check if we have both gainers and losers
                cur.execute("SELECT type FROM market_movers GROUP BY type")
                types = [row['type'] for row in cur.fetchall()]
                print(f"\nTypes found: {types}")
                
                if 'GAINER' not in types:
                    print("❌ No GAINER records found!")
                if 'LOSER' not in types:
                    print("❌ No LOSER records found!")
                
                # Check the most recent timestamp
                cur.execute("SELECT MAX(timestamp) as latest FROM market_movers")
                latest = cur.fetchone()['latest']
                print(f"\nLatest data timestamp: {latest}")
                
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_market_movers_data() 