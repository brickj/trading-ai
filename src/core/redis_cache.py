#!/usr/bin/env python3
"""
Redis Cache Manager for Trading AI Platform.
Provides high-performance caching using Redis for maximum speed.
"""

import json
import pickle
import redis
from typing import Dict, Any, Optional, Union, List
from datetime import datetime, timedelta
from src.core.config import Config
from src.core.logger import log_error, log_debug, log_info


class RedisCache:
    """High-performance cache using Redis for maximum speed"""

    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0, 
                 password: Optional[str] = None, decode_responses: bool = True):
        """
        Initialize Redis cache manager
        
        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
            password: Redis password (if any)
            decode_responses: Whether to decode responses to strings
        """
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=decode_responses,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            log_info("Redis cache initialized successfully")
            
        except Exception as e:
            log_error(f"Failed to initialize Redis cache: {e}")
            self.redis_client = None

    def _serialize_value(self, value: Any) -> str:
        """Serialize value for Redis storage"""
        try:
            # Try JSON serialization first (faster for simple types)
            return json.dumps(value, default=self._json_serializer)
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            return pickle.dumps(value).hex()

    def _deserialize_value(self, value: str, is_pickle: bool = False) -> Any:
        """Deserialize value from Redis storage"""
        try:
            if is_pickle:
                return pickle.loads(bytes.fromhex(value))
            else:
                return json.loads(value)
        except Exception as e:
            log_error(f"Failed to deserialize value: {e}")
            return None

    def _json_serializer(self, obj):
        """Custom JSON serializer for datetime and other objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments"""
        import hashlib
        
        key_data = json.dumps((args, sorted(kwargs.items())), sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from cache
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        if not self.redis_client:
            return default
            
        try:
            # Get value and metadata
            value = self.redis_client.get(key)
            if value is None:
                return default
                
            # Check if it's a pickled value
            is_pickle = self.redis_client.get(f"{key}:pickle")
            if is_pickle:
                return self._deserialize_value(value, is_pickle=True)
            else:
                return self._deserialize_value(value, is_pickle=False)
                
        except Exception as e:
            log_error(f"Redis get error for key '{key}': {e}")
            return default

    def set(self, key: str, value: Any, ttl: int = 3600, use_pickle: bool = False) -> bool:
        """
        Set a value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            use_pickle: Whether to use pickle serialization
            
        Returns:
            True if successful
        """
        if not self.redis_client:
            return False
            
        try:
            # Serialize value
            if use_pickle:
                serialized_value = pickle.dumps(value).hex()
                # Set pickle flag
                self.redis_client.set(f"{key}:pickle", "1", ex=ttl)
            else:
                serialized_value = self._serialize_value(value)
            
            # Set value with TTL
            result = self.redis_client.set(key, serialized_value, ex=ttl)
            
            # Set metadata
            metadata = {
                "created_at": datetime.now().isoformat(),
                "ttl": ttl,
                "use_pickle": use_pickle
            }
            self.redis_client.set(f"{key}:meta", json.dumps(metadata), ex=ttl)
            
            return result
            
        except Exception as e:
            log_error(f"Redis set error for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        if not self.redis_client:
            return False
            
        try:
            # Delete value and metadata
            keys_to_delete = [key, f"{key}:meta", f"{key}:pickle"]
            return self.redis_client.delete(*keys_to_delete) > 0
            
        except Exception as e:
            log_error(f"Redis delete error for key '{key}': {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        if not self.redis_client:
            return False
            
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            log_error(f"Redis exists error for key '{key}': {e}")
            return False

    def get_ttl(self, key: str) -> int:
        """
        Get time to live for a key
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds, -1 if key doesn't exist, -2 if no TTL
        """
        if not self.redis_client:
            return -2
            
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            log_error(f"Redis TTL error for key '{key}': {e}")
            return -2

    def extend_ttl(self, key: str, ttl: int) -> bool:
        """
        Extend TTL for a key
        
        Args:
            key: Cache key
            ttl: New TTL in seconds
            
        Returns:
            True if successful
        """
        if not self.redis_client:
            return False
            
        try:
            return self.redis_client.expire(key, ttl)
        except Exception as e:
            log_error(f"Redis extend TTL error for key '{key}': {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern
        
        Args:
            pattern: Redis key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0
            
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            log_error(f"Redis clear pattern error for pattern '{pattern}': {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get Redis cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.redis_client:
            return {"error": "Redis not available"}
            
        try:
            info = self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                "hit_rate": self._calculate_hit_rate(info)
            }
        except Exception as e:
            log_error(f"Redis stats error: {e}")
            return {"error": str(e)}

    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0

    def health_check(self) -> bool:
        """
        Check if Redis is healthy
        
        Returns:
            True if Redis is responding
        """
        if not self.redis_client:
            return False
            
        try:
            return self.redis_client.ping()
        except Exception:
            return False


# Global Redis cache instance
redis_cache = RedisCache(
    host=getattr(Config, 'REDIS_HOST', 'localhost'),
    port=getattr(Config, 'REDIS_PORT', 6379),
    db=getattr(Config, 'REDIS_DB', 0),
    password=getattr(Config, 'REDIS_PASSWORD', None)
)


# Convenience functions for backward compatibility
def get_cached_result(key: str, default: Any = None) -> Any:
    """Get cached result from Redis"""
    return redis_cache.get(key, default)


def cache_result(key: str, value: Any, ttl: int = 3600, use_pickle: bool = False) -> bool:
    """Cache result in Redis"""
    return redis_cache.set(key, value, ttl, use_pickle)


def delete_cached_result(key: str) -> bool:
    """Delete cached result from Redis"""
    return redis_cache.delete(key)


def clear_cache_pattern(pattern: str) -> int:
    """Clear cache keys matching pattern"""
    return redis_cache.clear_pattern(pattern)
