from contextlib import contextmanager
import psycopg2
from src.core.database import get_db_connection
from src.core.config import Config


class DBManager:
    """Reusable database connection manager for web components."""

    def __init__(self):
        self.db_url = getattr(Config, "DATABASE_URL", None)
        self.db_cfg = getattr(Config, "DATABASE_CONFIG", {})

    @contextmanager
    def connect(self, dict_cursor: bool = True):
        """Yield a database connection.

        Args:
            dict_cursor: When True, use core get_db_connection which returns
                RealDictCursor. When False, return a basic psycopg2 connection
                without special cursor factory for raw access.
        """
        if dict_cursor:
            with get_db_connection() as conn:
                yield conn
        else:
            conn = None
            try:
                if self.db_url:
                    conn = psycopg2.connect(self.db_url)
                else:
                    conn = psycopg2.connect(
                        host=self.db_cfg.get("host"),
                        port=self.db_cfg.get("port"),
                        database=self.db_cfg.get("database"),
                        user=self.db_cfg.get("user"),
                        password=self.db_cfg.get("password"),
                    )
                yield conn
            finally:
                if conn:
                    conn.close()
