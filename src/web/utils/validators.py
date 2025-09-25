"""
Optimized validation utilities for the web application
"""

import re
import html
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union


# Precompiled regex patterns for performance
SYMBOL_PATTERN = re.compile(r'^[A-Z]{1,10}(\.[A-Z]{1,5})?$')
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
ALPHANUMERIC_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')


def validate_symbol(symbol: str, allow_crypto: bool = True) -> Tuple[bool, str]:
    """
    Optimized symbol validation with caching
    
    Args:
        symbol: Stock or crypto symbol to validate
        allow_crypto: Whether to allow crypto symbols
        
    Returns:
        Tuple of (is_valid, cleaned_symbol)
    """
    if not symbol or not isinstance(symbol, str):
        return False, ""
    
    # Clean the symbol
    cleaned = symbol.strip().upper()
    
    # Length validation
    if len(cleaned) < 1 or len(cleaned) > 15:
        return False, cleaned
    
    # Standard stock symbol pattern
    if SYMBOL_PATTERN.match(cleaned):
        return True, cleaned
    
    # Crypto symbols (if allowed)
    if allow_crypto:
        crypto_symbols = {
            'BTC', 'ETH', 'ADA', 'DOT', 'SOL', 'LINK', 'MATIC', 'AVAX',
            'ATOM', 'LUNA', 'NEAR', 'FTM', 'ALGO', 'XLM', 'VET', 'ICP',
            'THETA', 'EGLD', 'HBAR', 'ENJ', 'MANA', 'SAND', 'AXS', 'CRV',
            'SUSHIUSD', 'SOLUSD', 'BTCUSD', 'ETHUSD', 'ADAUSD', 'USDT', 'USDC'
        }
        if cleaned in crypto_symbols:
            return True, cleaned
        
        # Pattern for crypto pairs (e.g., BTCUSD, ETHUSD)
        if cleaned.endswith('USD') and len(cleaned) >= 6:
            base = cleaned[:-3]
            if base in crypto_symbols or len(base) >= 3:
                return True, cleaned
    
    return False, cleaned


def validate_email(email: str) -> bool:
    """
    Fast email validation using precompiled regex
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format
    """
    if not email or not isinstance(email, str):
        return False
    
    return bool(EMAIL_PATTERN.match(email.strip().lower()))


def validate_date_range(start_date: str, end_date: str, 
                       max_range_days: int = 365) -> Tuple[bool, str, datetime, datetime]:
    """
    Optimized date range validation
    
    Args:
        start_date: Start date string (YYYY-MM-DD or ISO format)
        end_date: End date string (YYYY-MM-DD or ISO format) 
        max_range_days: Maximum allowed range in days
        
    Returns:
        Tuple of (is_valid, error_message, start_dt, end_dt)
    """
    try:
        # Parse dates with multiple format support
        start_dt = _parse_date_flexible(start_date)
        end_dt = _parse_date_flexible(end_date)
        
        if not start_dt or not end_dt:
            return False, "Invalid date format. Use YYYY-MM-DD or ISO format.", None, None
        
        # Validate range
        if start_dt > end_dt:
            return False, "Start date must be before end date.", None, None
        
        # Check maximum range
        if (end_dt - start_dt).days > max_range_days:
            return False, f"Date range cannot exceed {max_range_days} days.", None, None
        
        # Check future dates
        if end_dt > datetime.now() + timedelta(days=1):
            return False, "End date cannot be more than 1 day in the future.", None, None
        
        return True, "", start_dt, end_dt
        
    except Exception as e:
        return False, f"Date validation error: {str(e)}", None, None


def validate_numeric_params(params: Dict[str, Any], 
                           validations: Dict[str, Dict]) -> Tuple[bool, str, Dict]:
    """
    Batch validation for numeric parameters with type conversion
    
    Args:
        params: Dictionary of parameters to validate
        validations: Validation rules per parameter
                   e.g., {'limit': {'type': int, 'min': 1, 'max': 100, 'default': 10}}
        
    Returns:
        Tuple of (is_valid, error_message, validated_params)
    """
    validated = {}
    
    for param_name, rules in validations.items():
        value = params.get(param_name)
        param_type = rules.get('type', str)
        
        # Handle None/missing values
        if value is None:
            if 'default' in rules:
                validated[param_name] = rules['default']
                continue
            elif rules.get('required', False):
                return False, f"Missing required parameter: {param_name}", {}
            else:
                continue
        
        # Type conversion
        try:
            if param_type == int:
                validated_value = int(value)
            elif param_type == float:
                validated_value = float(value)
            elif param_type == bool:
                validated_value = str(value).lower() in ('true', '1', 'yes', 'on')
            else:
                validated_value = str(value)
        except (ValueError, TypeError):
            return False, f"Invalid type for {param_name}. Expected {param_type.__name__}.", {}
        
        # Range validation for numeric types
        if param_type in (int, float):
            if 'min' in rules and validated_value < rules['min']:
                return False, f"{param_name} must be >= {rules['min']}", {}
            if 'max' in rules and validated_value > rules['max']:
                return False, f"{param_name} must be <= {rules['max']}", {}
        
        # Length validation for strings
        if param_type == str:
            if 'min_length' in rules and len(validated_value) < rules['min_length']:
                return False, f"{param_name} must be at least {rules['min_length']} characters", {}
            if 'max_length' in rules and len(validated_value) > rules['max_length']:
                return False, f"{param_name} must be at most {rules['max_length']} characters", {}
        
        # Custom validation function
        if 'validator' in rules:
            validator_func = rules['validator']
            if not validator_func(validated_value):
                error_msg = rules.get('validator_error', f"Invalid value for {param_name}")
                return False, error_msg, {}
        
        validated[param_name] = validated_value
    
    return True, "", validated


def sanitize_input(input_value: str, max_length: int = 1000, 
                  allow_html: bool = False) -> str:
    """
    Optimized input sanitization
    
    Args:
        input_value: String to sanitize
        max_length: Maximum allowed length
        allow_html: Whether to allow HTML tags
        
    Returns:
        Sanitized string
    """
    if not isinstance(input_value, str):
        return str(input_value)
    
    # Truncate if too long
    sanitized = input_value[:max_length]
    
    # HTML escape if HTML not allowed
    if not allow_html:
        sanitized = html.escape(sanitized, quote=True)
    
    # Remove null bytes and other control characters
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\t\n\r')
    
    return sanitized.strip()


def validate_pagination_params(page: Any = 1, limit: Any = 20, 
                             max_limit: int = 100) -> Tuple[bool, str, int, int]:
    """
    Optimized pagination parameter validation
    
    Args:
        page: Page number
        limit: Items per page
        max_limit: Maximum allowed limit
        
    Returns:
        Tuple of (is_valid, error_message, validated_page, validated_limit)
    """
    try:
        validated_page = int(page)
        validated_limit = int(limit)
        
        if validated_page < 1:
            return False, "Page must be >= 1", 1, limit
        
        if validated_limit < 1:
            return False, "Limit must be >= 1", page, 1
        
        if validated_limit > max_limit:
            return False, f"Limit cannot exceed {max_limit}", page, max_limit
        
        return True, "", validated_page, validated_limit
        
    except (ValueError, TypeError):
        return False, "Page and limit must be integers", 1, 20


def validate_json_schema(data: Dict, schema: Dict) -> Tuple[bool, List[str]]:
    """
    Simple JSON schema validation without external dependencies
    
    Args:
        data: Data to validate
        schema: Schema definition with 'required' and 'properties'
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Check required fields
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Check field types and constraints
    properties = schema.get('properties', {})
    for field_name, field_schema in properties.items():
        if field_name not in data:
            continue
        
        value = data[field_name]
        expected_type = field_schema.get('type')
        
        # Type checking
        if expected_type == 'string' and not isinstance(value, str):
            errors.append(f"{field_name} must be a string")
        elif expected_type == 'integer' and not isinstance(value, int):
            errors.append(f"{field_name} must be an integer")
        elif expected_type == 'number' and not isinstance(value, (int, float)):
            errors.append(f"{field_name} must be a number")
        elif expected_type == 'boolean' and not isinstance(value, bool):
            errors.append(f"{field_name} must be a boolean")
        elif expected_type == 'array' and not isinstance(value, list):
            errors.append(f"{field_name} must be an array")
        elif expected_type == 'object' and not isinstance(value, dict):
            errors.append(f"{field_name} must be an object")
        
        # String constraints
        if expected_type == 'string' and isinstance(value, str):
            min_length = field_schema.get('minLength')
            max_length = field_schema.get('maxLength')
            
            if min_length and len(value) < min_length:
                errors.append(f"{field_name} must be at least {min_length} characters")
            if max_length and len(value) > max_length:
                errors.append(f"{field_name} must be at most {max_length} characters")
        
        # Number constraints
        if expected_type in ('integer', 'number') and isinstance(value, (int, float)):
            minimum = field_schema.get('minimum')
            maximum = field_schema.get('maximum')
            
            if minimum is not None and value < minimum:
                errors.append(f"{field_name} must be >= {minimum}")
            if maximum is not None and value > maximum:
                errors.append(f"{field_name} must be <= {maximum}")
    
    return len(errors) == 0, errors


def _parse_date_flexible(date_str: str) -> Optional[datetime]:
    """
    Parse date string with multiple format support
    
    Args:
        date_str: Date string to parse
        
    Returns:
        Parsed datetime or None if invalid
    """
    if not date_str:
        return None
    
    # Common date formats
    formats = [
        '%Y-%m-%d',           # 2023-12-25
        '%Y-%m-%dT%H:%M:%S',  # 2023-12-25T10:30:00
        '%Y-%m-%dT%H:%M:%SZ', # 2023-12-25T10:30:00Z
        '%Y-%m-%d %H:%M:%S',  # 2023-12-25 10:30:00
        '%m/%d/%Y',           # 12/25/2023
        '%d/%m/%Y',           # 25/12/2023
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    return None


# Validation rule presets for common use cases
COMMON_VALIDATIONS = {
    'pagination': {
        'page': {'type': int, 'min': 1, 'default': 1},
        'limit': {'type': int, 'min': 1, 'max': 100, 'default': 20}
    },
    'date_range': {
        'start_date': {'type': str, 'required': True},
        'end_date': {'type': str, 'required': True}
    },
    'analysis_params': {
        'symbol': {'type': str, 'required': True, 'min_length': 1, 'max_length': 15},
        'days_back': {'type': int, 'min': 1, 'max': 365, 'default': 30},
        'include_news': {'type': bool, 'default': True}
    },
    'backtest_params': {
        'symbol': {'type': str, 'required': True},
        'initial_capital': {'type': float, 'min': 100, 'max': 1000000, 'default': 10000},
        'days_back': {'type': int, 'min': 1, 'max': 365, 'default': 30}
    }
}

