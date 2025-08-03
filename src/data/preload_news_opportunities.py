import logging
from datetime import datetime
from src.data.news_monitor import NewsMonitor
from src.core.database import get_db_connection
from psycopg2.extras import Json

NEWS_OPPORTUNITIES_TABLE = "preloaded_news_opportunities"

logger = logging.getLogger(__name__)


def ensure_news_opportunities_table():
    """
    Ensure the preloaded_news_opportunities table exists.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {NEWS_OPPORTUNITIES_TABLE} (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP NOT NULL,
                        opportunities JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Create index on timestamp for fast queries
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{NEWS_OPPORTUNITIES_TABLE}_timestamp 
                    ON {NEWS_OPPORTUNITIES_TABLE} (timestamp DESC)
                """)
                conn.commit()
        logger.info(
            f"[PRELOAD_NEWS_OPPS] Ensured table {NEWS_OPPORTUNITIES_TABLE} exists"
        )
    except Exception as e:
        logger.error(f"[PRELOAD_NEWS_OPPS] Failed to ensure table exists: {e}")


def preload_news_opportunities():
    """
    Precompute news-driven opportunities and save to the database.
    """
    logger.info("[PRELOAD_NEWS_OPPS] Starting preload_news_opportunities job...")

    # Ensure table exists
    ensure_news_opportunities_table()

    monitor = NewsMonitor()
    trending_symbols = monitor.scan_trending_news()
    logger.info(
        f"[PRELOAD_NEWS_OPPS] Trending symbols: {list(trending_symbols.keys()) if trending_symbols else 'None'}"
    )
    opportunities = monitor.analyze_news_driven_opportunities(trending_symbols)
    logger.info(f"[PRELOAD_NEWS_OPPS] Opportunities generated: {len(opportunities)}")
    if opportunities:
        logger.info(f"[PRELOAD_NEWS_OPPS] First opportunity: {opportunities[0]}")
    timestamp = datetime.now()
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {NEWS_OPPORTUNITIES_TABLE} (timestamp, opportunities)
                    VALUES (%s, %s)
                """,
                    (timestamp, Json(opportunities)),
                )

                # Clean up old entries (keep only last 10)
                cur.execute(f"""
                    DELETE FROM {NEWS_OPPORTUNITIES_TABLE}
                    WHERE id NOT IN (
                        SELECT id FROM {NEWS_OPPORTUNITIES_TABLE}
                        ORDER BY timestamp DESC
                        LIMIT 10
                    )
                """)

                conn.commit()
        logger.info(
            f"[PRELOAD_NEWS_OPPS] Preloaded {len(opportunities)} news-driven opportunities at {timestamp}"
        )
    except Exception as e:
        logger.error(
            f"[PRELOAD_NEWS_OPPS] Failed to preload news-driven opportunities: {e}"
        )


def get_latest_preloaded_news_opportunities():
    """
    Fetch the most recent preloaded news-driven opportunities from the database.
    Returns a consistent dictionary structure even on error.
    """
    default_response = {
        "timestamp": datetime.utcnow().isoformat(),
        "opportunities": [],
        "error": None,
        "success": False,
    }

    try:
        # Ensure table exists before querying
        ensure_news_opportunities_table()

        with get_db_connection() as conn:
            if not conn:
                error_msg = "Failed to establish database connection"
                logger.error(f"[PRELOAD_NEWS_OPPS] {error_msg}")
                return {**default_response, "error": error_msg}

            with conn.cursor() as cur:
                logger.debug(
                    f"[PRELOAD_NEWS_OPPS] Querying {NEWS_OPPORTUNITIES_TABLE} for latest opportunities"
                )
                cur.execute(f"""
                    SELECT timestamp, opportunities
                    FROM {NEWS_OPPORTUNITIES_TABLE}
                    ORDER BY timestamp DESC
                    LIMIT 1
                """)
                row = cur.fetchone()

                if row and row.get(
                    "opportunities"
                ):  # Check both row exists and has opportunities
                    timestamp = row.get("timestamp")
                    timestamp_str = (
                        timestamp.isoformat()
                        if hasattr(timestamp, "isoformat")
                        else str(timestamp)
                    )
                    opportunities = (
                        row.get("opportunities")
                        if isinstance(row.get("opportunities"), list)
                        else []
                    )

                    logger.info(
                        f"[PRELOAD_NEWS_OPPS] Found {len(opportunities)} opportunities (timestamp: {timestamp_str})"
                    )

                    return {
                        "timestamp": timestamp_str,
                        "opportunities": opportunities,
                        "error": None,
                        "success": True,
                    }
                else:
                    logger.warning(
                        "[PRELOAD_NEWS_OPPS] No opportunities found in database"
                    )
                    return {
                        **default_response,
                        "error": "No opportunities found in database",
                    }

    except Exception as e:
        error_msg = f"Error fetching news opportunities: {str(e)}"
        logger.exception(f"[PRELOAD_NEWS_OPPS] {error_msg}")
        return {**default_response, "error": error_msg}
