"""
Optimized data formatting utilities for the web application
"""

import json
import decimal
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union


def format_currency(amount: Union[int, float, str], currency: str = "USD", 
                   precision: int = 2) -> str:
    """
    Optimized currency formatting
    
    Args:
        amount: Amount to format
        currency: Currency code
        precision: Decimal places
        
    Returns:
        Formatted currency string
    """
    try:
        num_amount = float(amount)
        
        # Handle different currency symbols
        symbols = {
            'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥',
            'CAD': 'C$', 'AUD': 'A$', 'CHF': 'CHF', 'CNY': '¥'
        }
        
        symbol = symbols.get(currency.upper(), currency)
        
        # Format with thousands separators
        if precision == 0:
            formatted = f"{num_amount:,.0f}"
        else:
            formatted = f"{num_amount:,.{precision}f}"
        
        return f"{symbol}{formatted}"
        
    except (ValueError, TypeError):
        return f"{currency} 0.00"


def format_percentage(value: Union[int, float, str], precision: int = 2, 
                     include_sign: bool = True) -> str:
    """
    Optimized percentage formatting with sign handling
    
    Args:
        value: Value to format as percentage
        precision: Decimal places
        include_sign: Whether to include + sign for positive values
        
    Returns:
        Formatted percentage string
    """
    try:
        num_value = float(value)
        
        if precision == 0:
            formatted = f"{num_value:.0f}"
        else:
            formatted = f"{num_value:.{precision}f}"
        
        if include_sign and num_value > 0:
            return f"+{formatted}%"
        else:
            return f"{formatted}%"
            
    except (ValueError, TypeError):
        return "0.00%"


def format_datetime(dt: Union[datetime, str], format_type: str = "api") -> str:
    """
    Optimized datetime formatting with multiple output formats
    
    Args:
        dt: Datetime object or ISO string
        format_type: Output format type (api, display, short, timestamp)
        
    Returns:
        Formatted datetime string
    """
    try:
        # Convert string to datetime if needed
        if isinstance(dt, str):
            # Try to parse ISO format
            if 'T' in dt:
                dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            else:
                dt_obj = datetime.fromisoformat(dt)
        elif isinstance(dt, datetime):
            dt_obj = dt
        else:
            return ""
        
        # Format based on type
        formats = {
            'api': '%Y-%m-%dT%H:%M:%S',      # 2023-12-25T10:30:00
            'display': '%B %d, %Y %I:%M %p', # December 25, 2023 10:30 AM
            'short': '%m/%d/%Y %H:%M',       # 12/25/2023 10:30
            'date_only': '%Y-%m-%d',         # 2023-12-25
            'time_only': '%H:%M:%S',         # 10:30:00
            'timestamp': '%Y%m%d_%H%M%S'     # 20231225_103000
        }
        
        format_str = formats.get(format_type, formats['api'])
        return dt_obj.strftime(format_str)
        
    except (ValueError, TypeError, AttributeError):
        return ""


def format_api_response(data: Any = None, message: str = "Success", 
                       status: str = "success", metadata: Dict = None) -> Dict:
    """
    Optimized standard API response formatter
    
    Args:
        data: Response data
        message: Response message
        status: Response status
        metadata: Additional metadata
        
    Returns:
        Formatted API response dictionary
    """
    response = {
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    if metadata:
        response.update(metadata)
    
    return response


def format_error_response(error: Union[str, Exception], error_code: str = None,
                         details: Dict = None) -> Dict:
    """
    Optimized error response formatter
    
    Args:
        error: Error message or exception
        error_code: Optional error code
        details: Additional error details
        
    Returns:
        Formatted error response dictionary
    """
    error_message = str(error)
    
    response = {
        "status": "error",
        "error": error_message,
        "timestamp": datetime.now().isoformat()
    }
    
    if error_code:
        response["error_code"] = error_code
    
    if details:
        response["details"] = details
    
    return response


def serialize_for_json(obj: Any) -> Any:
    """
    Optimized JSON serialization with custom type handling
    
    Args:
        obj: Object to serialize
        
    Returns:
        JSON-serializable object
    """
    if obj is None:
        return None
    
    # Handle datetime objects
    if isinstance(obj, datetime):
        return obj.isoformat()
    
    if isinstance(obj, date):
        return obj.isoformat()
    
    # Handle decimal objects
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    
    # Handle sets
    if isinstance(obj, set):
        return list(obj)
    
    # Handle dictionaries recursively
    if isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    
    # Handle lists/tuples recursively
    if isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]
    
    # Handle objects with __dict__
    if hasattr(obj, '__dict__'):
        return serialize_for_json(obj.__dict__)
    
    # Default: convert to string
    return str(obj)


def format_number(value: Union[int, float, str], precision: int = 2, 
                 thousands_sep: bool = True, unit: str = "") -> str:
    """
    Optimized number formatting with units
    
    Args:
        value: Number to format
        precision: Decimal places
        thousands_sep: Whether to include thousands separator
        unit: Unit suffix (e.g., 'K', 'M', 'B')
        
    Returns:
        Formatted number string
    """
    try:
        num_value = float(value)
        
        # Auto-scale large numbers
        if not unit and abs(num_value) >= 1000000000:
            num_value /= 1000000000
            unit = "B"
            precision = min(precision, 1)
        elif not unit and abs(num_value) >= 1000000:
            num_value /= 1000000
            unit = "M"
            precision = min(precision, 1)
        elif not unit and abs(num_value) >= 1000:
            num_value /= 1000
            unit = "K"
            precision = min(precision, 1)
        
        # Format the number
        if precision == 0:
            formatted = f"{num_value:.0f}"
        else:
            formatted = f"{num_value:.{precision}f}"
        
        # Add thousands separator if requested and no unit scaling
        if thousands_sep and not unit:
            try:
                parts = formatted.split('.')
                parts[0] = f"{int(parts[0]):,}"
                formatted = '.'.join(parts)
            except:
                pass
        
        return f"{formatted}{unit}"
        
    except (ValueError, TypeError):
        return "0"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    try:
        size = float(size_bytes)
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                if unit == 'B':
                    return f"{int(size)} {unit}"
                else:
                    return f"{size:.1f} {unit}"
            size /= 1024.0
        
        return f"{size:.1f} PB"
        
    except (ValueError, TypeError):
        return "0 B"


def format_duration(seconds: Union[int, float]) -> str:
    """
    Format duration in human-readable format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    try:
        total_seconds = int(float(seconds))
        
        if total_seconds < 60:
            return f"{total_seconds}s"
        
        minutes = total_seconds // 60
        remaining_seconds = total_seconds % 60
        
        if minutes < 60:
            if remaining_seconds > 0:
                return f"{minutes}m {remaining_seconds}s"
            else:
                return f"{minutes}m"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if hours < 24:
            if remaining_minutes > 0:
                return f"{hours}h {remaining_minutes}m"
            else:
                return f"{hours}h"
        
        days = hours // 24
        remaining_hours = hours % 24
        
        if remaining_hours > 0:
            return f"{days}d {remaining_hours}h"
        else:
            return f"{days}d"
            
    except (ValueError, TypeError):
        return "0s"


def format_table_data(data: List[Dict], headers: List[str] = None,
                     max_col_width: int = 30) -> str:
    """
    Format data as ASCII table for logging/debugging
    
    Args:
        data: List of dictionaries to format
        headers: Optional custom headers
        max_col_width: Maximum column width
        
    Returns:
        Formatted table string
    """
    if not data:
        return "No data"
    
    # Get headers
    if not headers:
        headers = list(data[0].keys()) if data else []
    
    # Calculate column widths
    col_widths = {}
    for header in headers:
        col_widths[header] = min(len(header), max_col_width)
        
        for row in data:
            value_str = str(row.get(header, ""))
            col_widths[header] = max(col_widths[header], min(len(value_str), max_col_width))
    
    # Build table
    lines = []
    
    # Header row
    header_line = " | ".join(header.ljust(col_widths[header]) for header in headers)
    lines.append(header_line)
    
    # Separator
    separator = "-+-".join("-" * col_widths[header] for header in headers)
    lines.append(separator)
    
    # Data rows
    for row in data:
        data_line = " | ".join(
            str(row.get(header, ""))[:max_col_width].ljust(col_widths[header]) 
            for header in headers
        )
        lines.append(data_line)
    
    return "\n".join(lines)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Intelligently truncate text at word boundaries
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to append when truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    # Find last space before max_length
    truncate_at = max_length - len(suffix)
    space_index = text.rfind(' ', 0, truncate_at)
    
    if space_index > truncate_at * 0.7:  # Only use space if it's not too early
        return text[:space_index] + suffix
    else:
        return text[:truncate_at] + suffix

