"""
Redis cache management routes
"""

from flask import Blueprint, jsonify
from datetime import datetime
from ...core.redis_cache import redis_cache
from ..helpers import create_api_response

redis_bp = Blueprint('redis', __name__)


@redis_bp.route("/api/redis/health")
def redis_health():
    """Check Redis connection health"""
    try:
        is_healthy = redis_cache.health_check()
        stats = redis_cache.get_stats() if is_healthy else {"error": "Redis not available"}
        
        return create_api_response(
            data={
                "healthy": is_healthy,
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        return create_api_response(
            error=f"Redis health check failed: {str(e)}",
            status_code=500
        )


@redis_bp.route("/api/redis/stats")
def redis_stats():
    """Get Redis cache statistics"""
    try:
        stats = redis_cache.get_stats()
        return create_api_response(data=stats)
    except Exception as e:
        return create_api_response(
            error=f"Failed to get Redis stats: {str(e)}",
            status_code=500
        )


@redis_bp.route("/api/redis/clear", methods=["POST"])
def clear_redis_cache():
    """Clear Redis cache (admin function)"""
    try:
        # Clear all cache keys
        cleared_count = redis_cache.clear_pattern("*")
        return create_api_response(
            data={
                "message": f"Cleared {cleared_count} cache entries",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        return create_api_response(
            error=f"Failed to clear Redis cache: {str(e)}",
            status_code=500
        )


@redis_bp.route("/api/redis/clear/<pattern>", methods=["POST"])
def clear_redis_pattern(pattern):
    """Clear Redis cache entries matching pattern"""
    try:
        cleared_count = redis_cache.clear_pattern(pattern)
        return create_api_response(
            data={
                "message": f"Cleared {cleared_count} cache entries matching pattern: {pattern}",
                "pattern": pattern,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        return create_api_response(
            error=f"Failed to clear Redis pattern '{pattern}': {str(e)}",
            status_code=500
        )
