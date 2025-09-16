#!/usr/bin/env python3
"""
Database connection manager for Trading AI Platform.
Provides connection handling for PostgreSQL database.
"""

import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from .config import Config
from typing import Dict, Any
import json
import numpy as np
# Lazy import to avoid circular dependency
# from .logger import trading_logger as logger


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
        if hasattr(Config, "DATABASE_URL") and Config.DATABASE_URL:
            conn = psycopg2.connect(
                Config.DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor
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
                cursor_factory=psycopg2.extras.RealDictCursor,
            )

        yield conn
    except psycopg2.Error as e:
        from .logger import trading_logger as logger
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
        if hasattr(Config, "DATABASE_URL") and Config.DATABASE_URL:
            conn = psycopg2.connect(
                Config.DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor
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
                cursor_factory=psycopg2.extras.RealDictCursor,
            )

        yield conn
    except psycopg2.Error as e:
        from .logger import trading_logger as logger
        logger.error(f"Database connection error: {e}")
        if conn:
            conn.rollback()
        yield None
    finally:
        if conn:
            conn.close()
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
        from .logger import trading_logger as logger
        logger.error(f"Query execution error: {e}")
        raise


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
