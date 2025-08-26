#!/usr/bin/env python3
"""
Cache Manager for Trading AI Platform.
Provides high-performance caching for API responses and analysis results.
"""

import json
from typing import Dict, Any
from datetime import datetime, timedelta
from src.core.database import get_db_connection, get_db_connection_silent
from src.core.logger import log_error, log_debug


class Cache:
    """High-performance cache using PostgreSQL for persistence"""

    def __init__(self):
        """Initialize the cache manager"""
        self.cache_table = "api_cache"
        self._ensure_cache_table()

    def _ensure_cache_table(self):
        """Ensure the cache table exists"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS api_cache (
                            key_hash VARCHAR(64) PRIMARY KEY,
                            data JSONB NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP NOT NULL,
                            access_count INTEGER DEFAULT 0,
                            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """
                    )
                    conn.commit()
        except Exception as e:
            log_error(f"Failed to create cache table: {e}")

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments"""
        import hashlib

        key_data = json.dumps((args, sorted(kwargs.items())), sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _serialize_datetime(self, obj):
        """Serialize datetime objects for JSON"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            # Handle objects with datetime attributes
            result = {}
            for key, value in obj.__dict__.items():
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
                else:
                    result[key] = value
            return result
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from cache
        Args:
            key: Cache key
            default: Default value if not found
        Returns:
            Cached value or default
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT data, expires_at FROM api_cache
                        WHERE key_hash = %s AND expires_at > CURRENT_TIMESTAMP
                    """,
                        (key,),
                    )
                    result = cursor.fetchone()

                    if result:
                        # Handle RealDictRow from RealDictCursor
                        data = result["data"]
                        expires_at = result["expires_at"]

                        # Update access stats
                        cursor.execute(
                            """
                            UPDATE api_cache
                            SET access_count = access_count + 1,
                                last_accessed = CURRENT_TIMESTAMP
                            WHERE key_hash = %s
                        """,
                            (key,),
                        )
                        conn.commit()

                        # Deserialize JSON data - ensure we always get proper data structure
                        try:
                            if isinstance(data, str):
                                deserialized = json.loads(data)
                            else:
                                # If it's already a dict/object from JSONB, use it directly
                                deserialized = data

                            # Validate that stock price data has the expected structure
                            if key.startswith("stock_price_") and isinstance(
                                deserialized, dict
                            ):
                                # Ensure it has required fields for stock price
                                if (
                                    "symbol" in deserialized
                                    and "current_price" in deserialized
                                ):
                                    return deserialized
                                else:
                                    log_error(
                                        f"Invalid stock price data structure in cache for key '{key}': {deserialized}"
                                    )
                                    # Delete invalid cache entry
                                    self.delete(key)
                                    return default

                            return deserialized

                        except (json.JSONDecodeError, TypeError) as e:
                            log_error(
                                f"Failed to deserialize cache data for key '{key}': {e}"
                            )
                            # Delete corrupted cache entry
                            self.delete(key)
                            return default

                    return default

        except Exception as e:
            log_error(f"Cache get error for key '{key}': {e}")
            return default

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set a value in cache
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        Returns:
            True if successful
        """
        try:
            expires_at = datetime.now() + timedelta(seconds=ttl)
            # Use custom serialization to handle datetime objects
            serialized_data = json.dumps(value, default=self._serialize_datetime)

            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Insert or update the cache entry
                    cursor.execute(
                        """
                        INSERT INTO api_cache (key_hash, data, expires_at)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (key_hash)
                        DO UPDATE SET
                            data = EXCLUDED.data,
                            expires_at = EXCLUDED.expires_at,
                            access_count = 0,
                            last_accessed = CURRENT_TIMESTAMP
                        """,
                        (key, serialized_data, expires_at),
                    )
                    conn.commit()
                    return True
        except Exception as e:
            log_error(f"Cache set error for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a value from cache
        Args:
            key: Cache key to delete
        Returns:
            True if successful
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM api_cache WHERE key_hash = %s", (key,))
                    conn.commit()
                    return True
        except Exception as e:
            log_error(f"Cache delete error: {e}")
            return False

    def clear(self) -> bool:
        """
        Clear all cache entries
        Returns:
            True if successful
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM api_cache")
                    conn.commit()
                    return True
        except Exception as e:
            log_error(f"Cache clear error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        Returns:
            Dictionary with cache stats
        """
        try:
            with get_db_connection_silent() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT
                            COUNT(*) as total_entries,
                            COUNT(CASE WHEN expires_at > CURRENT_TIMESTAMP
                                THEN 1 END) as active_entries,
                            COUNT(CASE WHEN expires_at <= CURRENT_TIMESTAMP
                                THEN 1 END) as expired_entries,
                            AVG(access_count) as avg_access_count,
                            MAX(access_count) as max_access_count,
                            MIN(created_at) as oldest_entry,
                            MAX(created_at) as newest_entry
                        FROM api_cache
                        """
                    )
                    result = cursor.fetchone()
                    if result:
                        return {
                            "total_entries": result[0],
                            "active_entries": result[1],
                            "expired_entries": result[2],
                            "avg_access_count": float(result[3] or 0),
                            "max_access_count": result[4] or 0,
                            "oldest_entry": (
                                result[5].isoformat() if result[5] else None
                            ),
                            "newest_entry": (
                                result[6].isoformat() if result[6] else None
                            ),
                        }
                    return {}
        except Exception as e:
            log_debug(f"Cache stats unavailable: {e}")
            return {}

    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries
        Returns:
            Number of entries removed
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM api_cache
                        WHERE expires_at <= CURRENT_TIMESTAMP
                    """
                    )
                    deleted_count = cursor.rowcount
                    conn.commit()
                    return deleted_count
        except Exception as e:
            log_error(f"Cache cleanup error: {e}")
            return 0


# Global cache instance
cache = Cache()


# Convenience functions for backward compatibility
def get_cached_result(cache_key: str, default: Any = None) -> Any:
    """Get a cached result by key"""
    return cache.get(cache_key, default)


def cache_result(cache_key: str, data: Any, ttl: int = 3600) -> bool:
    """Cache a result with a key"""
    return cache.set(cache_key, data, ttl)


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    return cache.get_stats()


def clear_cache() -> bool:
    """Clear all cache entries"""
    return cache.clear()
