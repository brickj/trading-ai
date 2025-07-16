from typing import List, Dict, Optional
from datetime import datetime
import json
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
                        """,
                        (
                            stock.get('symbol'),
                            stock.get('price', 0),
                            stock.get('change_amount', 0),
                            stock.get('change_percent', 0),
                            stock.get('volume', 0),
                            stock.get('timestamp', datetime.now()),
                            json.dumps(stock.get('analysis_data', {}))
                        ))
                    
                    # Insert losers
                    for stock in losers:
                        cur.execute("""
                            INSERT INTO market_movers 
                            (symbol, type, price, change_amount, change_percent, volume, timestamp, analysis_data)
                            VALUES (%s, 'LOSER', %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (symbol, type, timestamp) DO NOTHING
                        """,
                        (
                            stock.get('symbol'),
                            stock.get('price', 0),
                            stock.get('change_amount', 0),
                            stock.get('change_percent', 0),
                            stock.get('volume', 0),
                            stock.get('timestamp', datetime.now()),
                            json.dumps(stock.get('analysis_data', {}))
                        ))
                    
                    conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save market movers: {e}")
            return False
