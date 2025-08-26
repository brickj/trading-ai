"""
Repository for market data with optimized queries
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from .base_repository import BaseRepository


class MarketDataRepository(BaseRepository):
    """
    Optimized repository for market data operations
    """
    
    def __init__(self):
        super().__init__()
    
    def get_preloaded_opportunities(self, opportunity_type: str = 'watchlist') -> Tuple[List[Dict], datetime]:
        """
        Get preloaded opportunities with optimized query
        
        Args:
            opportunity_type: Type of opportunities (watchlist, news, crypto)
            
        Returns:
            Tuple of (opportunities_list, timestamp)
        """
        table_map = {
            'watchlist': 'preloaded_watchlist_opportunities',
            'news': 'preloaded_news_opportunities', 
            'crypto': 'preloaded_watchlist_opportunities'  # Crypto uses watchlist table
        }
        
        table = table_map.get(opportunity_type, 'preloaded_watchlist_opportunities')
        
        query = f"""
            SELECT opportunities, timestamp
            FROM {table}
            ORDER BY timestamp DESC
            LIMIT 1
        """
        
        result = self.execute_query(query, fetch_one=True, use_cache=True, 
                                  cache_key=f"preloaded_{opportunity_type}")
        
        if result and result['opportunities']:
            try:
                # Check if opportunities is already a list (not JSON string)
                if isinstance(result['opportunities'], list):
                    opportunities = result['opportunities']
                else:
                    # Parse as JSON if it's a string
                    opportunities = json.loads(result['opportunities'])
                return opportunities, result['timestamp']
            except (json.JSONDecodeError, TypeError):
                return [], datetime.now()
        
        return [], datetime.now()
    
    def save_preloaded_opportunities(self, opportunities: List[Dict], 
                                   opportunity_type: str = 'watchlist') -> bool:
        """
        Save preloaded opportunities with optimized batch insert
        
        Args:
            opportunities: List of opportunity dictionaries
            opportunity_type: Type of opportunities
            
        Returns:
            True if successful
        """
        table_map = {
            'watchlist': 'preloaded_watchlist_opportunities',
            'news': 'preloaded_news_opportunities',
            'crypto': 'preloaded_watchlist_opportunities'
        }
        
        table = table_map.get(opportunity_type, 'preloaded_watchlist_opportunities')
        
        try:
            # Clear old data first
            self.execute_query(f"DELETE FROM {table}", fetch_all=False)
            
            # Insert new data
            query = f"""
                INSERT INTO {table} (opportunities, timestamp)
                VALUES (%s, %s)
            """
            
            opportunities_json = json.dumps(opportunities)
            
            self.execute_query(query, [opportunities_json, datetime.now()], fetch_all=False)
            
            # Clear cache for this type
            cache_key = f"preloaded_{opportunity_type}"
            if hasattr(self, '_query_cache') and cache_key in self._query_cache:
                del self._query_cache[cache_key]
            
            return True
            
        except Exception:
            return False
    
    def get_market_movers(self, limit: int = 10) -> Dict:
        """
        Get latest market movers data
        
        Args:
            limit: Number of movers per category
            
        Returns:
            Dictionary with gainers and losers
        """
        query = """
            SELECT gainers, losers, timestamp, source
            FROM market_movers
            ORDER BY timestamp DESC
            LIMIT 1
        """
        
        result = self.execute_query(query, fetch_one=True, use_cache=True,
                                  cache_key="latest_market_movers")
        
        if result:
            try:
                gainers = json.loads(result['gainers']) if result['gainers'] else []
                losers = json.loads(result['losers']) if result['losers'] else []
                
                return {
                    'gainers': gainers[:limit],
                    'losers': losers[:limit],
                    'timestamp': result['timestamp'].isoformat() if result['timestamp'] else None,
                    'source': result['source']
                }
            except json.JSONDecodeError:
                pass
        
        return {'gainers': [], 'losers': [], 'timestamp': None, 'source': None}
    
    def save_market_movers(self, gainers: List[str], losers: List[str], 
                          source: str = 'api') -> bool:
        """
        Save market movers data
        
        Args:
            gainers: List of gaining symbols
            losers: List of losing symbols
            source: Data source
            
        Returns:
            True if successful
        """
        try:
            # Clean old data (keep only last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.execute_query(
                "DELETE FROM market_movers WHERE timestamp < %s",
                [cutoff_time], fetch_all=False
            )
            
            # Insert new data
            query = """
                INSERT INTO market_movers (gainers, losers, timestamp, source)
                VALUES (%s, %s, %s, %s)
            """
            
            gainers_json = json.dumps(gainers)
            losers_json = json.dumps(losers)
            
            self.execute_query(
                query, [gainers_json, losers_json, datetime.now(), source],
                fetch_all=False
            )
            
            # Clear cache
            if hasattr(self, '_query_cache') and "latest_market_movers" in self._query_cache:
                del self._query_cache["latest_market_movers"]
            
            return True
            
        except Exception:
            return False
    
    def get_symbol_price_history(self, symbol: str, days_back: int = 30) -> List[Dict]:
        """
        Get price history for a symbol (placeholder for future implementation)
        
        Args:
            symbol: Stock/crypto symbol
            days_back: Number of days of history
            
        Returns:
            List of price data dictionaries
        """
        # This would be implemented when price history table is added
        # For now, return empty list
        return []
    
    def get_watchlist_symbols(self, watchlist_type: str = 'stocks') -> List[str]:
        """
        Get symbols from watchlist (placeholder for future implementation)
        
        Args:
            watchlist_type: Type of watchlist (stocks, crypto)
            
        Returns:
            List of symbols
        """
        # This would integrate with actual watchlist table
        # For now, return sample data
        if watchlist_type == 'crypto':
            return ['BTC', 'ETH', 'SOL', 'SOLUSD', 'USDT']
        else:
            return [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA',
                'JPM', 'V', 'UNH', 'HD', 'PG', 'MA', 'DIS', 'PYPL'
            ]
    
    def get_news_data(self, symbol: str = None, hours_back: int = 24) -> List[Dict]:
        """
        Get recent news data (placeholder for future implementation)
        
        Args:
            symbol: Optional symbol filter
            hours_back: Hours of news to retrieve
            
        Returns:
            List of news dictionaries
        """
        # This would be implemented when news table is added
        return []
    
    def get_sector_data(self, sector: str = None) -> Dict:
        """
        Get sector performance data (placeholder for future implementation)
        
        Args:
            sector: Optional sector filter
            
        Returns:
            Sector performance dictionary
        """
        # This would integrate with sector data
        return {}
    
    def get_market_status(self) -> Dict:
        """
        Get current market status
        
        Returns:
            Market status dictionary
        """
        # Simple market status based on time
        now = datetime.now()
        weekday = now.weekday()  # 0 = Monday, 6 = Sunday
        hour = now.hour
        
        is_market_open = (
            weekday < 5 and  # Monday to Friday
            9 <= hour < 16   # 9 AM to 4 PM (simplified)
        )
        
        return {
            'is_open': is_market_open,
            'session': 'regular' if is_market_open else 'closed',
            'next_open': 'Next trading day 9:00 AM' if not is_market_open else None,
            'timezone': 'Eastern',
            'timestamp': now.isoformat()
        }
    
    def get_data_freshness_status(self) -> Dict:
        """
        Get status of data freshness across tables
        
        Returns:
            Data freshness status dictionary
        """
        tables_to_check = [
            'preloaded_watchlist_opportunities',
            'preloaded_news_opportunities', 
            'market_movers',
            'recommendations'
        ]
        
        status = {}
        
        for table in tables_to_check:
            try:
                stats = self.get_table_stats(table)
                status[table] = {
                    'row_count': stats.get('row_count', 0),
                    'latest_update': stats.get('latest_timestamp'),
                    'status': 'active' if stats.get('row_count', 0) > 0 else 'empty'
                }
            except Exception as e:
                status[table] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return {
            'tables': status,
            'overall_status': 'healthy' if all(
                t.get('status') in ['active', 'empty'] for t in status.values()
            ) else 'degraded',
            'checked_at': datetime.now().isoformat()
        }
    
    def cleanup_old_market_data(self, days_to_keep: int = 7) -> Dict:
        """
        Clean up old market data to maintain performance
        
        Args:
            days_to_keep: Number of days to keep
            
        Returns:
            Cleanup results dictionary
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        results = {}
        
        # Clean market movers
        try:
            deleted_movers = self.execute_query(
                "DELETE FROM market_movers WHERE timestamp < %s",
                [cutoff_date], fetch_all=False
            )
            results['market_movers'] = {'deleted': deleted_movers, 'status': 'success'}
        except Exception as e:
            results['market_movers'] = {'deleted': 0, 'status': 'error', 'error': str(e)}
        
        # Clean old preloaded data (keep only latest)
        for table in ['preloaded_watchlist_opportunities', 'preloaded_news_opportunities']:
            try:
                # Keep only the most recent entry
                cleanup_query = f"""
                    DELETE FROM {table} 
                    WHERE id NOT IN (
                        SELECT id FROM {table} 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    )
                """
                deleted_count = self.execute_query(cleanup_query, fetch_all=False)
                results[table] = {'deleted': deleted_count, 'status': 'success'}
            except Exception as e:
                results[table] = {'deleted': 0, 'status': 'error', 'error': str(e)}
        
        return results

