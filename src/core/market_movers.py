"""
Market Movers Manager for handling market movers data.
"""

import json
from datetime import datetime
from src.core.database import get_db_connection


class MarketMoversManager:
    """Manages market movers data storage and retrieval."""
    
    @staticmethod
    def save_market_movers(gainers, losers):
        """Save market movers data to the database."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Clear existing data
                    cur.execute("DELETE FROM market_movers")
                    
                    # Insert new data
                    cur.execute("""
                        INSERT INTO market_movers (gainers, losers, timestamp, source)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        json.dumps(gainers),
                        json.dumps(losers),
                        datetime.now(),
                        'alpha_vantage'
                    ))
                    
                    conn.commit()
                    return True
        except Exception as e:
            print(f"Error saving market movers: {e}")
            return False
    
    @staticmethod
    def get_market_movers():
        """Get market movers data from the database."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT gainers, losers, timestamp, source
                        FROM market_movers
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """)
                    
                    result = cur.fetchone()
                    if result:
                        return {
                            'gainers': json.loads(result[0]) if result[0] else [],
                            'losers': json.loads(result[1]) if result[1] else [],
                            'timestamp': result[2],
                            'source': result[3]
                        }
                    return None
        except Exception as e:
            print(f"Error getting market movers: {e}")
            return None
