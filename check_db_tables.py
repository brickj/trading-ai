#!/usr/bin/env python3
"""Check if opportunities tables exist and have data"""

from src.core.database import get_db_connection

def check_opportunities_tables():
    """Check if opportunities tables exist and have data"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if tables exist
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE '%opportunities%'
                """)
                tables = cur.fetchall()
                print("Opportunities tables found:", [t[0] for t in tables])
                
                # Check news opportunities table
                if any('news' in t[0] for t in tables):
                    cur.execute("SELECT COUNT(*) FROM preloaded_news_opportunities")
                    count = cur.fetchone()
                    print(f"News opportunities records: {count[0] if count else 0}")
                    
                    if count and count[0] > 0:
                        cur.execute("SELECT timestamp, opportunities FROM preloaded_news_opportunities ORDER BY timestamp DESC LIMIT 1")
                        latest = cur.fetchone()
                        if latest:
                            print(f"Latest news opportunities timestamp: {latest[0]}")
                            print(f"Latest news opportunities count: {len(latest[1]) if latest[1] else 0}")
                
                # Check watchlist opportunities table
                if any('watchlist' in t[0] for t in tables):
                    cur.execute("SELECT COUNT(*) FROM preloaded_watchlist_opportunities")
                    count = cur.fetchone()
                    print(f"Watchlist opportunities records: {count[0] if count else 0}")
                    
                    if count and count[0] > 0:
                        cur.execute("SELECT timestamp, opportunities FROM preloaded_watchlist_opportunities ORDER BY timestamp DESC LIMIT 1")
                        latest = cur.fetchone()
                        if latest:
                            print(f"Latest watchlist opportunities timestamp: {latest[0]}")
                            print(f"Latest watchlist opportunities count: {len(latest[1]) if latest[1] else 0}")
                
    except Exception as e:
        print(f"Error checking tables: {e}")

if __name__ == "__main__":
    check_opportunities_tables() 