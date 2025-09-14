import time
from functools import wraps
from typing import Callable
from flask import request, jsonify

from ...core.logger import trading_logger, log_exception
from .formatters import format_error_response


def handle_api_error(e: Exception, context: str = "API operation"):
    """Centralized error handler that logs and formats API errors."""
    log_exception(f"Error in {context}", e)
    path = request.path if request else None
    method = request.method if request else None
    response = format_error_response(str(e), path=path, method=method)
    return jsonify(response), 500


def api_error_handler(operation_name: str = None):
    """Decorator for consistent API error handling with performance tracking."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            request_path = request.path if request else "unknown"

            trading_logger.api_logger.info(
                f"Handling request for {op_name} at {request_path}"
            )

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                if execution_time > 1.0:
                    trading_logger.api_logger.warning(
                        f"Slow operation {op_name} at {request_path}: {execution_time:.3f}s"
                    )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                trading_logger.error_logger.error(
                    f"Error in {op_name} at {request_path} after {execution_time:.3f}s: {str(e)}"
                )
                return handle_api_error(e, op_name)
        return wrapper
    return decorator
