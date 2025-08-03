#!/usr/bin/env python3
"""
Watchlist Manager - Handles database operations for watchlist stocks and cryptos
"""

from psycopg2.extras import RealDictCursor
from datetime import datetime
from ..core.config import Config
from ..core.database import get_db_connection
from ..core.logger import log_info, log_error, log_warning
from typing import Dict, Any

logger = None  # We'll use the individual logging functions instead


class WatchlistManager:
    """Manages watchlist stocks and cryptocurrencies in PostgreSQL database"""

    def __init__(self):
        """Initialize the watchlist manager"""
        self.db_config = Config.DATABASE_CONFIG

    def create_table_if_not_exists(self):
        """Create watchlists table if it doesn't exist"""
        try:
            with get_db_connection() as conn:
                if conn is None:
                    return False
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS watchlists (
                            id SERIAL PRIMARY KEY,
                            symbol VARCHAR(20) NOT NULL,
                            type VARCHAR(10) NOT NULL CHECK (type IN ('stock', 'crypto')),
                            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(symbol, type)
                        )
                    """
                    )
                    conn.commit()
                    log_info("Watchlists table created/verified successfully")
                    return True
        except Exception as e:
            log_error(f"Error creating watchlists table: {e}")
            return False

    def populate_default_watchlist(self):
        """Populate default watchlist with common stocks and cryptos"""
        try:
            with get_db_connection() as conn:
                if conn is None:
                    return False
                with conn.cursor() as cursor:
                    # Default stocks from config
                    default_stocks = (
                        Config.DEFAULT_CRYPTO_SYMBOLS
                    )  # Using crypto symbols as stocks for now
                    default_crypto = Config.DEFAULT_CRYPTO_SYMBOLS

                    # Insert stocks
                    for symbol in default_stocks:
                        try:
                            cursor.execute(
                                """
                                INSERT INTO watchlists (symbol, type)
                                VALUES (%s, 'stock')
                                ON CONFLICT (symbol, type) DO NOTHING
                            """,
                                (symbol,),
                            )
                        except Exception as e:
                            log_warning(f"Could not insert stock {symbol}: {e}")

                    # Insert crypto
                    for symbol in default_crypto:
                        try:
                            cursor.execute(
                                """
                                INSERT INTO watchlists (symbol, type)
                                VALUES (%s, 'crypto')
                                ON CONFLICT (symbol, type) DO NOTHING
                            """,
                                (symbol,),
                            )
                        except Exception as e:
                            log_warning(f"Could not insert crypto {symbol}: {e}")
                    conn.commit()
                    log_info("Default watchlist symbols populated successfully")
                    return True
        except Exception as e:
            log_error(f"Error populating default watchlist: {e}")
            return False

    def get_stocks(self):
        """Get all stock symbols from watchlist"""
        try:
            with get_db_connection() as conn:
                if conn is None:
                    return []
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        "SELECT symbol FROM watchlists WHERE type = 'stock' ORDER BY symbol"
                    )
                    stocks = [row["symbol"] for row in cursor.fetchall()]
                    return stocks
        except Exception as e:
            log_error(f"Error getting stocks: {e}")
            return []

    def get_cryptos(self):
        """Get all crypto symbols from watchlist"""
        try:
            with get_db_connection() as conn:
                if conn is None:
                    return []
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        "SELECT symbol FROM watchlists WHERE type = 'crypto' ORDER BY symbol"
                    )
                    cryptos = [row["symbol"] for row in cursor.fetchall()]
                    return cryptos
        except Exception as e:
            log_error(f"Error getting cryptos: {e}")
            return []

    def add_stock(self, symbol: str):
        """Add a stock to the watchlist"""
        try:
            with get_db_connection() as conn:
                if conn is None:
                    return False
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO watchlists (symbol, type, added_at) VALUES (%s, 'stock', %s) ON CONFLICT DO NOTHING",
                        (symbol.upper(), datetime.now()),
                    )
                    conn.commit()
                    log_info(f"Added stock {symbol} to watchlist")
                    return True
        except Exception as e:
            log_error(f"Error adding stock {symbol}: {e}")
            return False

    def add_crypto(self, symbol: str):
        """Add a crypto to the watchlist (admin only)"""
        try:
            with get_db_connection() as conn:
                if conn is None:
                    return False
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO watchlists (symbol, type, added_at) VALUES (%s, 'crypto', %s) ON CONFLICT DO NOTHING",
                        (symbol.upper(), datetime.now()),
                    )
                    conn.commit()
                    log_info(f"Added crypto {symbol} to watchlist")
                    return True
        except Exception as e:
            log_error(f"Error adding crypto {symbol}: {e}")
            return False

    def remove_stock(self, symbol: str):
        """Remove a stock from the watchlist"""
        try:
            with get_db_connection() as conn:
                if conn is None:
                    return False
                with conn.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM watchlists WHERE symbol = %s AND type = 'stock'",
                        (symbol.upper(),),
                    )
                    conn.commit()
                    log_info(f"Removed stock {symbol} from watchlist")
                    return True
        except Exception as e:
            log_error(f"Error removing stock {symbol}: {e}")
            return False

    def remove_crypto(self, symbol: str):
        """Remove a crypto from the watchlist (admin only)"""
        try:
            with get_db_connection() as conn:
                if conn is None:
                    return False
                with conn.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM watchlists WHERE symbol = %s AND type = 'crypto'",
                        (symbol.upper(),),
                    )
                    conn.commit()
                    log_info(f"Removed crypto {symbol} from watchlist")
                    return True
        except Exception as e:
            log_error(f"Error removing crypto {symbol}: {e}")
            return False

    def get_watchlist_summary(self) -> Dict[str, Any]:
        """Get a summary of the watchlist"""
        stocks = self.get_stocks()
        crypto = self.get_cryptos()
        return {
            "stocks": stocks,
            "crypto": crypto,
            "total_symbols": len(stocks) + len(crypto),
        }

    def get_all_symbols(self):
        """Get all symbols from watchlist"""
        try:
            with get_db_connection() as conn:
                if conn is None:
                    return []
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        "SELECT symbol, type FROM watchlists ORDER BY type, symbol"
                    )
                    symbols = cursor.fetchall()
                    return symbols
        except Exception as e:
            log_error(f"Error getting all symbols: {e}")
            return []

    def symbol_exists(self, symbol: str, symbol_type: str = None):
        """Check if a symbol exists in the watchlist"""
        try:
            with get_db_connection() as conn:
                if conn is None:
                    return False
                with conn.cursor() as cursor:
                    if symbol_type:
                        cursor.execute(
                            "SELECT COUNT(*) FROM watchlists WHERE symbol = %s AND type = %s",
                            (symbol.upper(), symbol_type),
                        )
                    else:
                        cursor.execute(
                            "SELECT COUNT(*) FROM watchlists WHERE symbol = %s",
                            (symbol.upper(),),
                        )
                    count = cursor.fetchone()[0]
                    return count > 0
        except Exception as e:
            log_error(f"Error checking symbol {symbol}: {e}")
            return False


# Global instance
watchlist_manager = WatchlistManager()
