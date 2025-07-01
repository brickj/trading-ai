#!/usr/bin/env python3
"""
Database connection manager for Trading AI Platform.
Provides connection handling for PostgreSQL database.
"""

import psycopg2
import psycopg2.extras
import logging
from contextlib import contextmanager
from .config import Config
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """
    Get a PostgreSQL database connection with automatic cleanup.
    
    Yields:
        Connection: PostgreSQL database connection
    """
    conn = None
    try:
        # Use individual connection parameters or DATABASE_URL if available
        if hasattr(Config, 'DATABASE_URL') and Config.DATABASE_URL:
            conn = psycopg2.connect(
                Config.DATABASE_URL,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
        else:
            # Use individual connection parameters from Config.DATABASE_CONFIG
            db_cfg = Config.DATABASE_CONFIG
            conn = psycopg2.connect(
                host=db_cfg["host"],
                port=db_cfg["port"],
                database=db_cfg["database"],
                user=db_cfg["user"],
                password=db_cfg["password"],
                cursor_factory=psycopg2.extras.RealDictCursor
            )
        
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

@contextmanager
def get_db_connection_silent():
    """
    Get a PostgreSQL database connection with automatic cleanup (silent version).
    Returns None if connection fails instead of raising an exception.
    
    Yields:
        Connection or None: PostgreSQL database connection or None if failed
    """
    conn = None
    try:
        # Use individual connection parameters or DATABASE_URL if available
        if hasattr(Config, 'DATABASE_URL') and Config.DATABASE_URL:
            conn = psycopg2.connect(
                Config.DATABASE_URL,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
        else:
            # Use individual connection parameters from Config.DATABASE_CONFIG
            db_cfg = Config.DATABASE_CONFIG
            conn = psycopg2.connect(
                host=db_cfg["host"],
                port=db_cfg["port"],
                database=db_cfg["database"],
                user=db_cfg["user"],
                password=db_cfg["password"],
                cursor_factory=psycopg2.extras.RealDictCursor
            )
        
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        if conn:
            conn.rollback()
        yield None
    finally:
        if conn:
            conn.close()

# Module-level function to check database connection
def check_database_connection():
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False

# Module-level function to execute a query and return results
def execute_query(query, params=None, fetch_all=True):
    """
    Execute a database query and return results.
    
    Args:
        query (str): SQL query to execute
        params (tuple, optional): Query parameters
        fetch_all (bool): Whether to fetch all results or just one
    
    Returns:
        list or dict: Query results
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                
                # For non-SELECT queries (INSERT, UPDATE, DELETE), commit and return None
                if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                    conn.commit()
                    return None
                
                # For SELECT queries, fetch results
                if fetch_all:
                    return cur.fetchall()
                else:
                    return cur.fetchone()
    except Exception as e:
        logger.error(f"Query execution error: {e}")
        raise

def get_database_connection():
    """Get a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            Config.DATABASE_URL,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return None

def get_database_stats() -> Dict[str, Any]:
    """Get database statistics and health information."""
    stats = {
        "status": "unavailable",
        "connection": False,
        "tables": [],
        "size": "0 bytes",
        "version": "Unknown"
    }
    
    conn = get_database_connection()
    if not conn:
        return stats
    
    try:
        with conn.cursor() as cur:
            # Check connection
            stats["connection"] = True
            stats["status"] = "connected"
            
            # Get PostgreSQL version
            cur.execute("SELECT version()")
            version_info = cur.fetchone()
            stats["version"] = version_info["version"] if version_info else "Unknown"
            
            # Get database size
            cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            size_info = cur.fetchone()
            stats["size"] = size_info["pg_size_pretty"] if size_info else "0 bytes"
            
            # Get table information
            cur.execute("""
                SELECT table_name, 
                       pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC
            """)
            tables = cur.fetchall()
            stats["tables"] = [dict(table) for table in tables]
            
            # Count rows in cache table if it exists
            try:
                cur.execute("SELECT COUNT(*) as count FROM cache")
                cache_info = cur.fetchone()
                stats["cache_entries"] = cache_info["count"] if cache_info else 0
            except:
                stats["cache_entries"] = 0
                
            return stats
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        stats["error"] = str(e)
        return stats
    finally:
        if conn:
            conn.close()

def get_system_flag(flag_name: str) -> Optional[str]:
    """
    Get the value of a system flag from the system_flags table.
    Returns the flag_value as a string, or None if not found.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT flag_value FROM system_flags WHERE flag_name = %s",
                    (flag_name,)
                )
                result = cur.fetchone()
                if result:
                    # result can be a dict or tuple depending on cursor_factory
                    return result[0] if isinstance(result, (list, tuple)) else result.get("flag_value")
                return None
    except Exception as e:
        logger.error(f"Error getting system flag '{flag_name}': {e}")
        return None

def set_system_flag(flag_name: str, flag_value: str, description: Optional[str] = None):
    """
    Set or update the value of a system flag in the system_flags table.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO system_flags (flag_name, flag_value, description, updated_at)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (flag_name)
                    DO UPDATE SET flag_value = EXCLUDED.flag_value, description = EXCLUDED.description, updated_at = NOW()
                    """,
                    (flag_name, flag_value, description)
                )
                conn.commit()
    except Exception as e:
        logger.error(f"Error setting system flag '{flag_name}': {e}") 