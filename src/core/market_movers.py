from typing import List, Dict, Optional
from datetime import datetime
from src.core.database import get_db_connection

class MarketMoversManager:
    """Manages market movers data in the database"""
    
    @staticmethod
    def save_market_movers(gainers: List[Dict], losers: List[Dict]) -> bool:
        """Save market movers to the database"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Insert gainers
                    for stock in gainers:
                        cur.execute("""
                            INSERT INTO market_movers 
                            (symbol, type, price, change_amount, change_percent, volume, timestamp, analysis_data)
                            VALUES (%s, 'GAINER', %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (symbol, type, timestamp) DO NOTHING
                        ""
