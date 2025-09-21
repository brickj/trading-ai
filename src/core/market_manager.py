"""
Market Manager - Centralized management of foreign exchanges and markets
"""
from datetime import datetime
from typing import Dict, List
from src.core.database import get_db_connection
from src.core.logger import log_error

class MarketManager:
    """Manages foreign exchange and market information"""
    
    def get_markets_for_dropdown(self) -> List[Dict]:
        """Get markets formatted for frontend dropdown"""
        try:
            query = """
                SELECT code, name, country, currency, symbol_suffix, trading_hours_open, trading_hours_close, timezone
                FROM foreign_exchanges 
                WHERE active = TRUE 
                ORDER BY code
            """
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    markets = cur.fetchall() or []
            
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

    def get_foreign_markets_overview(self) -> Dict:
        """
        Get overview of foreign markets with summary statistics

        Returns:
            Dict: Contains 'markets' list and 'summary' statistics
        """
        try:
            # Get all active markets
            markets = self.get_markets_for_dropdown()
            
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
