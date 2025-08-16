"""
Market Manager - Centralized management of foreign exchanges and markets
"""
import logging
from typing import Dict, List, Optional, Tuple
from src.core.database import get_db_connection
from src.core.logger import log_info, log_error, log_debug

logger = logging.getLogger(__name__)

class MarketManager:
    """Manages foreign exchange and market information"""
    
    @staticmethod
    def get_all_markets() -> List[Dict]:
        """Get all active foreign exchanges"""
        try:
            with get_db_connection() as conn:
                if conn is None:
                    return []
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT code, name, country, currency, timezone, symbol_suffix, 
                               trading_hours_open, trading_hours_close, active
                        FROM foreign_exchanges 
                        WHERE active = TRUE 
                        ORDER BY country, name
                    """)
                    markets = []
                    for row in cursor.fetchall():
                        markets.append(dict(row))
                    return markets
        except Exception as e:
            log_error(f"Error fetching markets: {e}")
            return []
    
    @staticmethod
    def get_market_by_code(code: str) -> Optional[Dict]:
        """Get market by exchange code"""
        try:
            with get_db_connection() as conn:
                if conn is None:
                    return None
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT code, name, country, currency, timezone, symbol_suffix, 
                               trading_hours_open, trading_hours_close, active
                        FROM foreign_exchanges 
                        WHERE code = %s AND active = TRUE
                    """, (code,))
                    row = cursor.fetchone()
                    if row:
                        return dict(row)
                    return None
        except Exception as e:
            log_error(f"Error fetching market {code}: {e}")
            return None
    
    @staticmethod
    def get_market_by_symbol(symbol: str) -> Optional[Dict]:
        """Get market information by symbol (using suffix matching)"""
        try:
            with get_db_connection() as conn:
                if conn is None:
                    return None
                with conn.cursor() as cursor:
                    # Try to match by symbol suffix
                    cursor.execute("""
                        SELECT code, name, country, currency, timezone, symbol_suffix, 
                               trading_hours_open, trading_hours_close, active
                        FROM foreign_exchanges 
                        WHERE symbol_suffix = %s AND active = TRUE
                    """, (symbol,))
                    row = cursor.fetchone()
                    if row:
                        return dict(row)
                    
                    # If no suffix match, check if it's a US stock (no suffix)
                    if '.' not in symbol:
                        cursor.execute("""
                            SELECT code, name, country, currency, timezone, symbol_suffix, 
                                   trading_hours_open, trading_hours_close, active
                            FROM foreign_exchanges 
                            WHERE code IN ('NASDAQ', 'NYSE') AND active = TRUE
                            LIMIT 1
                        """)
                        row = cursor.fetchone()
                        if row:
                            return dict(row)
                    
                    return None
        except Exception as e:
            log_error(f"Error fetching market for symbol {symbol}: {e}")
            return None
    
    @staticmethod
    def get_markets_for_dropdown() -> List[Dict]:
        """Get markets formatted for frontend dropdown"""
        try:
            # Test direct database query first
            with get_db_connection() as conn:
                if conn is None:
                    return []
                with conn.cursor() as cursor:
                    cursor.execute("SELECT code, name, country, currency, symbol_suffix FROM foreign_exchanges WHERE active = TRUE ORDER BY code")
                    rows = cursor.fetchall()
                    
                    # Debug: print raw rows
                    print(f"DEBUG: Raw rows from database: {rows[:2]}")
                    
                    dropdown_markets = []
                    for row in rows:
                        market_dict = dict(row)
                        print(f"DEBUG: Market dict: {market_dict}")
                        
                        if market_dict['code'] in ['NASDAQ', 'NYSE']:
                            dropdown_markets.append({
                                'value': 'US',
                                'label': 'US',
                                'code': market_dict['code'],
                                'currency': market_dict['currency']
                            })
                        else:
                            # Foreign markets
                            country_code = market_dict['code']
                            if market_dict['code'] == 'LSE':
                                country_code = 'UK'
                            elif market_dict['code'] == 'TSX':
                                country_code = 'CA'
                            elif market_dict['code'] == 'TSE':
                                country_code = 'JP'
                            elif market_dict['code'] == 'HKEX':
                                country_code = 'HK'
                            elif market_dict['code'] == 'Euronext':
                                country_code = 'FR'
                            elif market_dict['code'] == 'AMS':
                                country_code = 'NL'
                            elif market_dict['code'] == 'B3':
                                country_code = 'BR'
                            elif market_dict['code'] == 'TWSE':
                                country_code = 'TW'
                            
                            dropdown_markets.append({
                                'value': country_code,
                                'label': f"{market_dict['country']} ({market_dict['symbol_suffix']})",
                                'code': market_dict['code'],
                                'currency': market_dict['currency']
                            })
                    
                    print(f"DEBUG: Final dropdown markets: {dropdown_markets[:2]}")
                    return dropdown_markets
                    
        except Exception as e:
            print(f"ERROR in get_markets_for_dropdown: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_exchange_currency_from_symbol(symbol: str) -> Tuple[str, str]:
        """Get exchange and currency from symbol (backend version)"""
        market = MarketManager.get_market_by_symbol(symbol)
        if market:
            return market['code'], market['currency']
        return 'US', 'USD'  # Default fallback
