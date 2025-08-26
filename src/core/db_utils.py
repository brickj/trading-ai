"""
Database connection utilities for centralized database access.
Handles connection pooling, retries, and error handling.
"""
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from typing import Optional, Iterator, Any, Dict
import logging
from src.core.config import Config
from src.core.logger import log_error, log_info

logger = logging.getLogger(__name__)

class DatabaseConnectionError(Exception):
    """Custom exception for database connection issues"""
    pass

class DatabaseConnection:
    _connection_pool = None
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._initialize_pool()
        return cls._instance
    
    @classmethod
    def _initialize_pool(cls):
        """Initialize the connection pool"""
        try:
            db_config = Config.DATABASE_CONFIG
            cls._connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=db_config.get('host', 'localhost'),
                database=db_config.get('database', 'trading_db'),
                user=db_config.get('user', 'trading_user'),
                password=db_config.get('password', 'trading_password'),
                port=db_config.get('port', 5432)
            )
            log_info("Database connection pool initialized successfully")
        except Exception as e:
            log_error(f"Failed to initialize database connection pool: {e}")
            raise DatabaseConnectionError(f"Database connection failed: {e}")
    
    @classmethod
    @contextmanager
    def get_connection(cls) -> Any:
        """
        Get a database connection from the pool.
        Usage:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM table")
                    result = cursor.fetchone()
        """
        conn = None
        try:
            conn = cls._connection_pool.getconn()
            yield conn
        except Exception as e:
            log_error(f"Error getting database connection: {e}")
            raise DatabaseConnectionError(f"Failed to get database connection: {e}")
        finally:
            if conn:
                cls._connection_pool.putconn(conn)
    
    @classmethod
    def execute_query(cls, query: str, params: tuple = None, fetch: bool = True) -> Optional[list]:
        """
        Execute a query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch results (for SELECT queries)
            
        Returns:
            List of results if fetch=True, None otherwise
        """
        with cls.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(query, params or ())
                    if fetch and cursor.description:
                        columns = [desc[0] for desc in cursor.description]
                        return [dict(zip(columns, row)) for row in cursor.fetchall()]
                    elif not fetch:
                        conn.commit()
                        return None
                    return []
                except Exception as e:
                    conn.rollback()
                    log_error(f"Query failed: {query[:100]}... - {e}")
                    raise

# Global instance
db = DatabaseConnection()

# Alias for backward compatibility
get_db_connection = db.get_connection
execute_query = db.execute_query
