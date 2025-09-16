"""
Base repository class with optimized database operations
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from contextlib import contextmanager

from ...core.database import get_db_connection
from ...core.logger import trading_logger, log_exception


class BaseRepository:
    """
    Base repository with optimized database operations and connection pooling
    """
    
    def __init__(self):
        self._connection_cache = {}
        self._query_cache = {}
        self._cache_timeout = 300  # 5 minutes
    
    @contextmanager
    def get_connection(self):
        """
        Get a database connection using the core database module
        """
        return get_db_connection()
    
    def execute_query(self, query: str, params: List = None, 
                     fetch_one: bool = False, fetch_all: bool = True,
                     use_cache: bool = False, cache_key: str = None) -> Any:
        """
        Optimized query execution with caching and error handling
        
        Args:
            query: SQL query string
            params: Query parameters
            fetch_one: Whether to fetch only one row
            fetch_all: Whether to fetch all rows
            use_cache: Whether to use query result caching
            cache_key: Custom cache key
            
        Returns:
            Query results
        """
        start_time = time.time()
        
        # Check cache if enabled
        if use_cache and cache_key:
            cached_result = self._get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result
        
        try:
            # Use the context manager directly
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or [])
                    
                    if fetch_one:
                        result = cursor.fetchone()
                    elif fetch_all:
                        result = cursor.fetchall()
                    else:
                        result = cursor.rowcount
                    
                    # Commit for non-SELECT queries
                    if not query.strip().upper().startswith('SELECT'):
                        conn.commit()
                    
                    # Cache result if requested
                    if use_cache and cache_key and result is not None:
                        self._cache_result(cache_key, result)
                    
                    # Log slow queries
                    execution_time = time.time() - start_time
                    if execution_time > 1.0:
                        trading_logger.api_logger.warning(
                            f"Slow query ({execution_time:.3f}s): {query[:100]}..."
                        )
                    
                    return result
                    
        except Exception as e:
            execution_time = time.time() - start_time
            trading_logger.error_logger.error(
                f"Query failed after {execution_time:.3f}s: {str(e)}"
            )
            log_exception(f"Query execution error: {query[:100]}", e)
            raise
    
    def bulk_insert(self, table: str, data: List[Dict],
                   conflict_resolution: str = "IGNORE") -> int:
        """
        Optimized bulk insert with conflict resolution
        
        Args:
            table: Table name
            data: List of dictionaries to insert
            conflict_resolution: How to handle conflicts (IGNORE, REPLACE, UPDATE)
            
        Returns:
            Number of rows inserted
        """
        if not data:
            return 0
        
        # Get column names from first record
        columns = list(data[0].keys())
        
        # Build query based on conflict resolution
        placeholders = ", ".join(["%s"] * len(columns))
        column_list = ", ".join(columns)
        
        if conflict_resolution == "IGNORE":
            query = f"""
                INSERT INTO {table} ({column_list}) 
                VALUES ({placeholders})
                ON CONFLICT DO NOTHING
            """
        elif conflict_resolution == "REPLACE":
            query = f"""
                INSERT INTO {table} ({column_list}) 
                VALUES ({placeholders})
                ON CONFLICT DO UPDATE SET
                {', '.join(f"{col} = EXCLUDED.{col}" for col in columns)}
            """
        else:  # Standard insert
            query = f"""
                INSERT INTO {table} ({column_list}) 
                VALUES ({placeholders})
            """
        
        # Prepare data for bulk insert
        values_list = []
        for record in data:
            values = [record.get(col) for col in columns]
            values_list.append(values)
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.executemany(query, values_list)
                    conn.commit()
                    return cursor.rowcount
                    
        except Exception as e:
            log_exception(f"Bulk insert error for table {table}", e)
            raise
    
    def get_table_stats(self, table: str) -> Dict:
        """
        Get table statistics for monitoring
        
        Args:
            table: Table name
            
        Returns:
            Dictionary with table statistics
        """
        try:
            stats_query = f"""
                SELECT 
                    COUNT(*) as row_count,
                    MAX(timestamp) as latest_timestamp,
                    MIN(timestamp) as earliest_timestamp
                FROM {table}
                WHERE timestamp IS NOT NULL
            """
            
            result = self.execute_query(stats_query, fetch_one=True)
            
            if result:
                return {
                    "table": table,
                    "row_count": result[0] or 0,
                    "latest_timestamp": result[1].isoformat() if result[1] else None,
                    "earliest_timestamp": result[2].isoformat() if result[2] else None,
                    "checked_at": datetime.now().isoformat()
                }
            else:
                return {
                    "table": table,
                    "row_count": 0,
                    "error": "Unable to get stats"
                }
                
        except Exception as e:
            return {
                "table": table,
                "error": str(e)
            }
    
    def _get_cached_result(self, cache_key: str) -> Any:
        """Get result from query cache"""
        if cache_key in self._query_cache:
            cached_data, timestamp = self._query_cache[cache_key]
            if time.time() - timestamp < self._cache_timeout:
                return cached_data
            else:
                # Remove expired cache entry
                del self._query_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: Any) -> None:
        """Cache query result with timestamp"""
        self._query_cache[cache_key] = (result, time.time())
        
        # Simple cache cleanup - remove oldest entries if cache gets too large
        if len(self._query_cache) > 100:
            oldest_key = min(self._query_cache.keys(), 
                           key=lambda k: self._query_cache[k][1])
            del self._query_cache[oldest_key]
    
