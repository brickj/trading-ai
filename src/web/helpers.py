#!/usr/bin/env python3
"""
Helper functions for the Flask web application - optimized with utilities
"""

from flask import jsonify, request
from datetime import datetime
from functools import wraps
from typing import Tuple, List, Dict, Any

# Import optimized utilities
from .utils.formatters import format_api_response, format_error_response
from .utils.validators import validate_symbol as validate_symbol_util
from .repositories import market_data_repo
from ..core.logger import log_exception


def create_api_response(data=None, success=True, message="", error_code=None,
                        error=None, status_code=200, path: str = None,
                        method: str = None):
    """Create standardized API response using optimized formatter"""
    if error or not success:
        if path is None or method is None:
            try:
                path = path or request.path
                method = method or request.method
            except RuntimeError:
                # Request context may not be available
                pass
        response = format_error_response(
            error or "Operation failed",
            error_code=error_code,
            path=path,
            method=method
        )
        return jsonify(response), status_code

    response = format_api_response(data, message)
    return jsonify(response), status_code


def handle_api_error(e, context="API operation"):
    """Standardized error handling for API endpoints"""
    log_exception(f"Error in {context}", e)
    return create_api_response(
        success=False,
        error=str(e),
        status_code=500,
        path=request.path,
        method=request.method
    )


def get_request_params(required_params=None, optional_params=None):
    """Extract and validate request parameters"""
    params = {}
    errors = []
    
    # Handle required parameters
    if required_params:
        for param in required_params:
            value = request.args.get(param) or request.json.get(param) if request.is_json else None
            if value is None:
                errors.append(f"Missing required parameter: {param}")
            else:
                params[param] = value
    
    # Handle optional parameters
    if optional_params:
        for param, default_value in optional_params.items():
            value = request.args.get(param) or (request.json.get(param) if request.is_json else None)
            params[param] = value if value is not None else default_value
    
    return params, errors


def validate_symbol(symbol):
    """Validate stock/crypto symbol using optimized validator"""
    is_valid, cleaned_symbol = validate_symbol_util(symbol, allow_crypto=True)
    if not is_valid:
        return False, "Invalid symbol format"
    return True, cleaned_symbol


def execute_db_query(query, params=None, fetch_one=False, fetch_all=False):
    """Execute database query using optimized repository pattern"""
    from .repositories.base_repository import BaseRepository
    base_repo = BaseRepository()
    
    return base_repo.execute_query(
        query=query,
        params=params,
        fetch_one=fetch_one,
        fetch_all=fetch_all
    )


def get_preloaded_opportunities(opportunity_type=None):
    """Get preloaded opportunities using optimized repository"""
    try:
        # Use the optimized repository method
        opportunities, timestamp = market_data_repo.get_preloaded_opportunities(
            opportunity_type or 'watchlist'
        )
        
        # For backward compatibility, filter by type if specified
        if opportunity_type and opportunities:
            filtered_opps = [opp for opp in opportunities if opp.get('type') == opportunity_type]
            return filtered_opps, timestamp
        
        return opportunities, timestamp
    except Exception as e:
        log_exception("Error getting preloaded opportunities", e)
        return [], None


def api_error_handler(context="API operation"):
    """Decorator for standardized API error handling"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return handle_api_error(e, context)
        return wrapper
    return decorator
