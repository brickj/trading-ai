"""
Database utilities - simplified wrapper around core database functions.
All database operations should use get_db_connection() from database.py directly.
This file provides only the execute_query function for backward compatibility.
"""
from src.core.database import get_db_connection
from src.core.logger import log_error


def execute_query(query: str, params=None, fetch_all=True):
    """
    Execute a database query using the core database connection.
    This is a simplified wrapper for backward compatibility.
    
    Args:
        query: SQL query string
        params: Query parameters
        fetch_all: Whether to fetch all results (True) or just one (False)
        
    Returns:
        Query results as list of dictionaries
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or [])
                
                if fetch_all:
                    return cursor.fetchall()
                else:
                    result = cursor.fetchone()
                    return result if result else None
                    
    except Exception as e:
        log_error(f"Query execution failed: {str(e)}")
        raise