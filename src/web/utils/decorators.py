"""
Optimized decorators for the web application
"""

import time
import functools
from datetime import datetime
from typing import Callable, Any, Dict, Optional
from flask import request, jsonify

from ...core.logger import trading_logger
from ...core.cache import get_cached_result, cache_result


def cache_response(cache_key_prefix: str = None, timeout: int = 300, 
                  use_request_args: bool = True):
    """
    Optimized caching decorator with intelligent key generation
    
    Args:
        cache_key_prefix: Prefix for cache key
        timeout: Cache timeout in seconds
        use_request_args: Whether to include request args in cache key
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            prefix = cache_key_prefix or func.__name__
            key_parts = [prefix]
            
            # Add request arguments if specified
            if use_request_args and request:
                if request.args:
                    sorted_args = sorted(request.args.items())
                    key_parts.append(str(hash(frozenset(sorted_args))))
                
                if request.method == 'POST' and request.json:
                    # Create deterministic hash of JSON data
                    json_str = str(sorted(request.json.items())) if isinstance(request.json, dict) else str(request.json)
                    key_parts.append(str(hash(json_str)))
            
            # Add function arguments
            if args or kwargs:
                args_str = f"{args}_{sorted(kwargs.items())}"
                key_parts.append(str(hash(args_str)))
            
            cache_key = "_".join(key_parts)
            
            # Try to get from cache
            cached_result = get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            # Only cache successful responses
            if hasattr(result, 'status_code'):
                if result.status_code == 200:
                    cache_result(cache_key, result, ttl=timeout)
            elif isinstance(result, (dict, list)):
                # Cache JSON responses that don't have error indicators
                if not (isinstance(result, dict) and result.get('error')):
                    cache_result(cache_key, result, ttl=timeout)
            
            return result
        
        return wrapper
    return decorator


def validate_request(required_fields: list = None, optional_fields: list = None):
    """
    Optimized request validation decorator
    
    Args:
        required_fields: List of required fields in request
        optional_fields: List of optional fields with default values
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not required_fields:
                return func(*args, **kwargs)
            
            # Validate request data
            if request.method == 'POST':
                data = request.get_json()
                if not data:
                    from .formatters import format_error_response
                    response = format_error_response("Request body is required")
                    return jsonify(response), 400
            else:
                data = request.args.to_dict()
            
            # Check required fields
            missing_fields = []
            for field in required_fields or []:
                if field not in data or not data[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                from .formatters import format_error_response
                response = format_error_response(f"Missing required fields: {', '.join(missing_fields)}")
                return jsonify(response), 400
            
            # Set optional fields with defaults
            if optional_fields:
                for field, default_value in (optional_fields or {}).items():
                    if field not in data:
                        data[field] = default_value
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def timing_decorator(log_slow_threshold: float = 1.0):
    """
    Performance timing decorator with configurable threshold
    
    Args:
        log_slow_threshold: Threshold in seconds to log slow operations
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log slow operations
            if execution_time > log_slow_threshold:
                trading_logger.api_logger.warning(
                    f"Slow function {func.__name__}: {execution_time:.3f}s"
                )
            
            # Add timing info to response if it's a dict
            if isinstance(result, dict) and 'timestamp' in result:
                result['execution_time'] = round(execution_time, 3)
            
            return result
        
        return wrapper
    return decorator


def log_request(include_response: bool = False, log_level: str = "info"):
    """
    Optimized request logging decorator
    
    Args:
        include_response: Whether to log response data
        log_level: Logging level (info, debug, warning)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Log request info
            log_data = {
                "function": func.__name__,
                "method": request.method if request else "N/A",
                "path": request.path if request else "N/A",
                "timestamp": datetime.now().isoformat()
            }
            
            # Add request args for GET requests
            if request and request.method == 'GET' and request.args:
                log_data["args"] = dict(request.args)
            
            logger = getattr(trading_logger.api_logger, log_level, trading_logger.api_logger.info)
            logger(f"Request: {log_data}")
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Log response if requested
            if include_response:
                execution_time = time.time() - start_time
                response_log = {
                    "function": func.__name__,
                    "execution_time": round(execution_time, 3),
                    "status": "success" if not (isinstance(result, dict) and result.get('error')) else "error"
                }
                logger(f"Response: {response_log}")
            
            return result
        
        return wrapper
    return decorator


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """
    Simple rate limiting decorator using in-memory storage
    Note: For production, use Redis or similar for distributed rate limiting
    
    Args:
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
    """
    # Simple in-memory storage for rate limiting
    _rate_limit_storage = {}
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not request:
                return func(*args, **kwargs)
            
            # Use IP address as identifier
            client_id = request.remote_addr or "unknown"
            current_time = time.time()
            
            # Clean old entries
            if client_id in _rate_limit_storage:
                _rate_limit_storage[client_id] = [
                    req_time for req_time in _rate_limit_storage[client_id]
                    if current_time - req_time < window_seconds
                ]
            else:
                _rate_limit_storage[client_id] = []
            
            # Check rate limit
            if len(_rate_limit_storage[client_id]) >= max_requests:
                from .formatters import format_error_response
                response = format_error_response("Rate limit exceeded. Please try again later.")
                return jsonify(response), 429
            
            # Record this request
            _rate_limit_storage[client_id].append(current_time)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_auth(auth_header_name: str = "Authorization"):
    """
    Simple authentication decorator (placeholder for future auth implementation)
    
    Args:
        auth_header_name: Name of the auth header to check
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # For now, just pass through - auth can be implemented later
            # if request and auth_header_name in request.headers:
            #     auth_token = request.headers[auth_header_name]
            #     if not validate_auth_token(auth_token):
            #         from .formatters import format_error_response
            #         response = format_error_response("Invalid authentication token")
            #         return jsonify(response), 401
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
