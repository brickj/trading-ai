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
import json
import numpy as np
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)


def convert_numpy_values(value):
    """Convert numpy values to Python native types for database storage"""
    if isinstance(value, (np.integer, np.floating)):
        return float(value)
    elif isinstance(value, np.ndarray):
        return value.tolist()
    elif value is None:
        return None
    else:
        return value


def convert_numpy_in_dict(data):
    """Convert all numpy types in a nested dictionary structure"""
    if isinstance(data, dict):
        return {key: convert_numpy_in_dict(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_numpy_in_dict(item) for item in data]
    else:
        return convert_numpy_values(data)


def _init_sqlite_db(conn: sqlite3.Connection) -> None:
    """Create market_movers table with sample data for SQLite fallback."""
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS market_movers (
            symbol TEXT,
            type TEXT,
            change_percent REAL,
            price REAL,
            volume INTEGER,
            timestamp TEXT
        )
        """
    )
    cur.execute("DELETE FROM market_movers")
    now = datetime.now().isoformat()
    sample_gainers = [
        ("AAPL", "GAINER", 2.5, 150.0, 1000000, now),
        ("MSFT", "GAINER", 1.8, 280.0, 800000, now),
        ("GOOGL", "GAINER", 1.2, 2700.0, 500000, now),
    ]
    sample_losers = [
        ("TSLA", "LOSER", -3.4, 700.0, 1200000, now),
        ("AMZN", "LOSER", -2.1, 3300.0, 900000, now),
        ("META", "LOSER", -1.5, 250.0, 700000, now),
    ]
    cur.executemany(
        "INSERT INTO market_movers (symbol, type, change_percent, price, volume, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        sample_gainers + sample_losers,
    )
    conn.commit()


class SQLiteCursorWrapper:
    def __init__(self, cursor: sqlite3.Cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc, tb):
        self.cursor.close()


class SQLiteConnectionWrapper:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def cursor(self, *args, **kwargs):
        return SQLiteCursorWrapper(self.conn.cursor())

    def commit(self):
        return self.conn.commit()

    def rollback(self):
        return self.conn.rollback()

    def close(self):
        return self.conn.close()


@contextmanager
def get_db_connection():
    """Get a database connection with automatic cleanup.

    Tries PostgreSQL using configuration; falls back to an in-memory SQLite database
    populated with sample market_movers data when PostgreSQL is unavailable.
    """
    conn = None
    try:
        try:
            # Attempt PostgreSQL connection first
            if hasattr(Config, "DATABASE_URL") and Config.DATABASE_URL:
                conn = psycopg2.connect(
                    Config.DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor
                )
            else:
                db_cfg = Config.DATABASE_CONFIG
                conn = psycopg2.connect(
                    host=db_cfg["host"],
                    port=db_cfg["port"],
                    database=db_cfg["database"],
                    user=db_cfg["user"],
                    password=db_cfg["password"],
                    cursor_factory=psycopg2.extras.RealDictCursor,
                )
            yield conn
        except Exception as e:
            logger.error(f"PostgreSQL unavailable, falling back to SQLite: {e}")
            sqlite_conn = sqlite3.connect(":memory:")
            sqlite_conn.row_factory = sqlite3.Row
            _init_sqlite_db(sqlite_conn)
            conn = SQLiteConnectionWrapper(sqlite_conn)
            yield conn
    finally:
        if conn:
            conn.close()


@contextmanager
def get_db_connection_silent():
    """Silent wrapper around get_db_connection.

    Returns a connection if available, otherwise yields None without raising.
    """
    try:
        with get_db_connection() as conn:
            yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        yield None


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
                if (
                    query.strip()
                    .upper()
                    .startswith(("INSERT", "UPDATE", "DELETE", "CREATE", "DROP"))
                ):
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
            Config.DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor
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
        "version": "Unknown",
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
            stats["version"] = (
                version_info.get("version")
                if version_info and isinstance(version_info, dict)
                else "Unknown"
            )

            # Get database size
            cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            size_info = cur.fetchone()
            stats["size"] = (
                size_info.get("pg_size_pretty")
                if size_info and isinstance(size_info, dict)
                else "0 bytes"
            )

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
                stats["cache_entries"] = (
                    cache_info.get("count")
                    if cache_info and isinstance(cache_info, dict)
                    else 0
                )
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
                    (flag_name,),
                )
                result = cur.fetchone()
                if result:
                    # result can be a dict or tuple depending on cursor_factory
                    return (
                        result[0]
                        if isinstance(result, (list, tuple))
                        else result.get("flag_value")
                    )
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
                    (flag_name, flag_value, description),
                )
                conn.commit()
    except Exception as e:
        logger.error(f"Error setting system flag '{flag_name}': {e}")


def save_backtest_result(result_dict):
    """
    Save a backtest result to the backtest_results table.
    """
    query = """
        INSERT INTO backtest_results (
            stock_symbol, period_days, timestamp, initial_capital, final_capital, total_return, win_rate, total_trades, trades
        ) VALUES (%s, %s, NOW(), %s, %s, %s, %s, %s, %s)
    """
    params = (
        result_dict.get("symbol"),
        result_dict.get("period_days", 730),
        convert_numpy_values(result_dict.get("initial_capital")),
        convert_numpy_values(result_dict.get("final_capital")),
        convert_numpy_values(result_dict.get("total_return")),
        convert_numpy_values(result_dict.get("win_rate")),
        convert_numpy_values(result_dict.get("total_trades")),
        json.dumps(convert_numpy_in_dict(result_dict.get("trades", []))),
    )
    execute_query(query, params, fetch_all=False)


def get_latest_backtest(symbol, period_days):
    """
    Fetch the most recent backtest result for a given symbol and period_days.
    """
    query = """
        SELECT * FROM backtest_results
        WHERE stock_symbol = %s AND period_days = %s
        ORDER BY timestamp DESC
        LIMIT 1
    """
    params = (symbol, period_days)
    result = execute_query(query, params, fetch_all=False)
    if result and isinstance(result, dict):
        trades_val = result.get("trades")
        if isinstance(trades_val, str):
            try:
                trades_json = json.loads(trades_val)
            except Exception:
                trades_json = []
            # Use .update() to avoid direct item assignment
            result.update({"trades": trades_json})
        return result
    return None


def ensure_job_schedules_table():
    """
    Ensure the job_schedules table exists for backend job scheduling.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS job_schedules (
                    id SERIAL PRIMARY KEY,
                    job_name TEXT NOT NULL,
                    run_time TIME NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    last_run TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
