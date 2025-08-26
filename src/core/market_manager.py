"""
Market Manager - Centralized management of foreign exchanges and markets
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from src.core.db_utils import execute_query
from src.core.logger import log_info, log_error, log_debug

logger = logging.getLogger(__name__)

class MarketManager:
    """Manages foreign exchange and market information"""
    
    @staticmethod
    def get_all_markets() -> List[Dict]:
        """Get all active foreign exchanges"""
        try:
            query = """
                SELECT code, name, country, currency, timezone, symbol_suffix, 
                       trading_hours_open, trading_hours_close, active
                FROM foreign_exchanges 
                WHERE active = TRUE 
                ORDER BY country, name
            """
            return execute_query(query) or []
        except Exception as e:
            log_error(f"Error fetching markets: {e}")
            return []
    
    @staticmethod
    def get_market_by_code(code: str) -> Optional[Dict]:
        """Get market by exchange code"""
        try:
            query = """
                SELECT code, name, country, currency, timezone, symbol_suffix, 
                       trading_hours_open, trading_hours_close, active
                FROM foreign_exchanges 
                WHERE code = %s AND active = TRUE
                LIMIT 1
            """
            result = execute_query(query, (code,))
            return result[0] if result else None
        except Exception as e:
            log_error(f"Error fetching market {code}: {e}")
            return None
    
    @staticmethod
    def get_market_by_symbol(symbol: str) -> Optional[Dict]:
        """Get market information by symbol (using suffix matching)"""
        try:
            # Try to match by symbol suffix first
            suffix_query = """
                SELECT code, name, country, currency, timezone, symbol_suffix, 
                       trading_hours_open, trading_hours_close, active
                FROM foreign_exchanges 
                WHERE symbol_suffix = %s AND active = TRUE
                LIMIT 1
            """
            result = execute_query(suffix_query, (symbol,))
            if result:
                return result[0]
            
            # If no suffix match and no dot in symbol, check US exchanges
            if '.' not in symbol:
                us_query = """
                    SELECT code, name, country, currency, timezone, symbol_suffix, 
                           trading_hours_open, trading_hours_close, active
                    FROM foreign_exchanges 
                    WHERE code IN ('NASDAQ', 'NYSE') AND active = TRUE
                    LIMIT 1
                """
                result = execute_query(us_query)
                if result:
                    return result[0]
            
            return None
        except Exception as e:
            log_error(f"Error fetching market for symbol {symbol}: {e}")
            return None
    
    @staticmethod
    def get_markets_for_dropdown() -> List[Dict]:
        """Get markets formatted for frontend dropdown"""
        try:
            query = """
                SELECT code, name, country, currency, symbol_suffix, trading_hours_open, trading_hours_close, timezone
                FROM foreign_exchanges 
                WHERE active = TRUE 
                ORDER BY code
            """
            markets = execute_query(query) or []
            
            country_code_map = {
                'LSE': 'UK',
                'TSX': 'CA',
                'TSE': 'JP',
                'HKEX': 'HK',
                'Euronext': 'FR',
                'AMS': 'NL',
                'B3': 'BR',
                'TWSE': 'TW'
            }
            
            dropdown_markets = []
            for market in markets:
                if market['code'] in ['NASDAQ', 'NYSE']:
                    dropdown_markets.append({
                        'value': 'US',
                        'label': 'US',
                        'name': market['name'],
                        'code': market['code'],
                        'currency': market['currency'],
                        'country': market['country'],
                        'symbol_suffix': market['symbol_suffix'],
                        'trading_hours_open': market.get('trading_hours_open'),
                        'trading_hours_close': market.get('trading_hours_close'),
                        'timezone': market.get('timezone')
                    })
                else:
                    country_code = country_code_map.get(market['code'], market['code'])
                    dropdown_markets.append({
                        'value': country_code,
                        'label': f"{market['country']} ({market['symbol_suffix']})",
                        'name': market['name'],
                        'code': market['code'],
                        'currency': market['currency'],
                        'country': market['country'],
                        'symbol_suffix': market['symbol_suffix'],
                        'trading_hours_open': market.get('trading_hours_open'),
                        'trading_hours_close': market.get('trading_hours_close'),
                        'timezone': market.get('timezone')
                    })
            
            return dropdown_markets
                    
        except Exception as e:
            log_error(f"Error in get_markets_for_dropdown: {e}")
            return []
    
    @staticmethod
    def get_exchange_currency_from_symbol(symbol: str) -> Tuple[str, str]:
        """Get exchange and currency from symbol (backend version)"""
        market = MarketManager.get_market_by_symbol(symbol)
        if market:
            return market['code'], market['currency']
        return 'US', 'USD'  # Default fallback
        
    @staticmethod
    def get_foreign_markets_overview() -> Dict:
        """
        Get overview of foreign markets with summary statistics
        
        Returns:
            Dict: Contains 'markets' list and 'summary' statistics
        """
        try:
            # Get all active markets
            markets = MarketManager.get_markets_for_dropdown()
            
            # Add additional fields needed by frontend
            for market in markets:
                # Set default values for required fields
                market['is_open'] = False  # Default to closed
                
                # Generate symbols for this market
                if market.get('symbol_suffix'):
                    market['symbols'] = [f"{market['code']}{market['symbol_suffix']}"]
                else:
                    market['symbols'] = [f"{market['code']}.{market['currency']}"]
                market['symbol_count'] = len(market['symbols'])
                
                # Add status and performance related fields
                market['status'] = 'Closed' if not market.get('is_open', False) else 'Open'
                market['status_class'] = 'success' if market['status'] == 'Open' else 'secondary'
                
                # Add performance data (random for demo, replace with real data)
                import random
                market['performance'] = round(random.uniform(-5, 5), 2)
                market['performance_class'] = 'success' if market['performance'] >= 0 else 'danger'
                
                # Use actual database values for trading hours and timezone
                if market.get('trading_hours_open'):
                    market['trading_hours_open'] = str(market['trading_hours_open'])[:5]  # Convert time to HH:MM format
                else:
                    market['trading_hours_open'] = '09:30'
                    
                if market.get('trading_hours_close'):
                    market['trading_hours_close'] = str(market['trading_hours_close'])[:5]  # Convert time to HH:MM format
                else:
                    market['trading_hours_close'] = '16:00'
                    
                market['timezone'] = market.get('timezone', 'UTC')
                
                # Ensure required fields exist
                market['country'] = market.get('country', 'Unknown')
                market['currency'] = market.get('currency', 'USD')
                market['symbol_suffix'] = market.get('symbol_suffix', '')
            
            # Calculate summary statistics
            total_markets = len(markets)
            open_markets = sum(1 for m in markets if m.get('is_open', False))
            
            # Count symbols across all markets
            total_symbols = sum(m.get('symbol_count', 0) for m in markets)
            
            # Group by region
            regions = {}
            for market in markets:
                country = market.get('country', 'Other')
                if country not in regions:
                    regions[country] = 0
                regions[country] += 1
            
            # Create summary
            summary = {
                'total_markets': total_markets,
                'markets_open': open_markets,
                'markets_closed': total_markets - open_markets,
                'total_foreign_symbols': total_symbols,
                'foreign_coverage': round((total_symbols / 1000) * 100, 1) if total_symbols > 0 else 0,  # Assuming 1000 as base
                'regions': [{'name': k, 'count': v} for k, v in regions.items()],
                'last_updated': datetime.utcnow().isoformat() + 'Z',
                'status': 'success'
            }
            
            return {
                'markets': markets,
                'summary': summary
            }
            
        except Exception as e:
            log_error(f"Error in get_foreign_markets_overview: {e}")
            return {
                'markets': [],
                'summary': {
                    'total_markets': 0,
                    'markets_open': 0,
                    'markets_closed': 0,
                    'total_foreign_symbols': 0,
                    'foreign_coverage': 0,
                    'regions': [],
                    'status': 'error',
                    'error': str(e)
                }
            }
