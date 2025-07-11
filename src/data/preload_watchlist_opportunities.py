#!/usr/bin/env python3
"""
Preload Watchlist Opportunities Module
=====================================

This module handles preloading and caching of watchlist-based trading opportunities
to the database for fast retrieval. The opportunities are calculated early each
trading day and stored for quick access.
"""

import logging
import sys
from datetime import datetime
from src.core.database import get_db_connection
from src.core.watchlist_manager import watchlist_manager
from src.core.batch_processor import (
    batch_processor_instance,
    create_watchlist_tasks,
)
from psycopg2.extras import Json

WATCHLIST_OPPORTUNITIES_TABLE = "preloaded_watchlist_opportunities"

logger = logging.getLogger(__name__)

def ensure_watchlist_opportunities_table():
    """
    Ensure the preloaded_watchlist_opportunities table exists.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {WATCHLIST_OPPORTUNITIES_TABLE} (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP NOT NULL,
                        opportunities JSONB NOT NULL,
                        symbols_analyzed INTEGER DEFAULT 0,
                        errors_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Create index on timestamp for fast queries
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{WATCHLIST_OPPORTUNITIES_TABLE}_timestamp 
                    ON {WATCHLIST_OPPORTUNITIES_TABLE} (timestamp DESC)
                """)
                conn.commit()
        logger.info(f"[PRELOAD_WATCHLIST_OPPS] Ensured table {WATCHLIST_OPPORTUNITIES_TABLE} exists")
    except Exception as e:
        logger.error(f"[PRELOAD_WATCHLIST_OPPS] Failed to ensure table exists: {e}")

def preload_watchlist_opportunities():
    """
    Precompute watchlist-based opportunities and save to the database.
    This runs early each trading day to have data ready for users.
    """
    try:
        logger.info("[PRELOAD_WATCHLIST_OPPS] Starting preload_watchlist_opportunities job...")
        print("[PRELOAD_WATCHLIST_OPPS] Starting preload_watchlist_opportunities job...")
        sys.stdout.flush()
        
        # Ensure table exists
        ensure_watchlist_opportunities_table()
        
        # Get watchlist symbols (stocks only, no crypto)
        watchlist_symbols = watchlist_manager.get_stocks()
        logger.info(f"[PRELOAD_WATCHLIST_OPPS] Processing {len(watchlist_symbols)} watchlist symbols: {watchlist_symbols}")
        print(f"[PRELOAD_WATCHLIST_OPPS] Processing {len(watchlist_symbols)} watchlist symbols: {watchlist_symbols}")
        sys.stdout.flush()
        
        if not watchlist_symbols:
            logger.warning("[PRELOAD_WATCHLIST_OPPS] No watchlist symbols found")
            print("[PRELOAD_WATCHLIST_OPPS] No watchlist symbols found")
            sys.stdout.flush()
            return
        
        # Create batch tasks for analysis
        tasks = create_watchlist_tasks(watchlist_symbols)
        logger.info(f"[PRELOAD_WATCHLIST_OPPS] Created {len(tasks)} analysis tasks")
        print(f"[PRELOAD_WATCHLIST_OPPS] Created {len(tasks)} analysis tasks")
        sys.stdout.flush()
        
        # Process batch analysis
        batch_result = batch_processor_instance.process_batch_sync(tasks, progress_callback=None)
        
        # Filter out successful opportunities (no errors)
        # These are now nested dicts matching the news-driven structure
        opportunities = [
            result
            for result in batch_result["results"].values()
            if result and "error" not in result
        ]
        
        # Get error count for logging
        errors = [
            result
            for result in batch_result["results"].values()
            if result and "error" in result
        ]
        
        logger.info(f"[PRELOAD_WATCHLIST_OPPS] Analysis completed: {len(opportunities)} opportunities, {len(errors)} errors")
        print(f"[PRELOAD_WATCHLIST_OPPS] Analysis completed: {len(opportunities)} opportunities, {len(errors)} errors")
        sys.stdout.flush()
        
        # Log sample opportunity for debugging
        if opportunities:
            logger.info(f"[PRELOAD_WATCHLIST_OPPS] Sample opportunity: {opportunities[0]}")
            print(f"[PRELOAD_WATCHLIST_OPPS] Sample opportunity: {opportunities[0]}")
            sys.stdout.flush()
        
        # Save to database
        timestamp = datetime.now()
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Create table if it doesn't exist
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {WATCHLIST_OPPORTUNITIES_TABLE} (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP NOT NULL,
                        opportunities JSONB NOT NULL,
                        symbols_analyzed INTEGER DEFAULT 0,
                        errors_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert new data
                cur.execute(f"""
                    INSERT INTO {WATCHLIST_OPPORTUNITIES_TABLE} 
                    (timestamp, opportunities, symbols_analyzed, errors_count)
                    VALUES (%s, %s, %s, %s)
                """, (
                    timestamp, 
                    Json(opportunities), 
                    len(watchlist_symbols),
                    len(errors),
                ))
                
                # Clean up old entries (keep only last 10)
                cur.execute(f"""
                    DELETE FROM {WATCHLIST_OPPORTUNITIES_TABLE}
                    WHERE id NOT IN (
                        SELECT id FROM {WATCHLIST_OPPORTUNITIES_TABLE}
                        ORDER BY timestamp DESC
                        LIMIT 10
                    )
                """)
                
                conn.commit()
        
        logger.info(f"[PRELOAD_WATCHLIST_OPPS] Successfully preloaded {len(opportunities)} watchlist opportunities at {timestamp}")
        print(f"[PRELOAD_WATCHLIST_OPPS] Successfully preloaded {len(opportunities)} watchlist opportunities at {timestamp}")
        sys.stdout.flush()
        
    except Exception as e:
        logger.error(f"[PRELOAD_WATCHLIST_OPPS] Failed to preload watchlist opportunities: {e}")
        print(f"[PRELOAD_WATCHLIST_OPPS] Failed to preload watchlist opportunities: {e}")
        sys.stdout.flush()
        import traceback
        traceback.print_exc()

def get_latest_preloaded_watchlist_opportunities():
    """
    Fetch the most recent preloaded watchlist opportunities from the database.
    Returns None if no data is available.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT timestamp, opportunities::text, symbols_analyzed, errors_count
                    FROM {WATCHLIST_OPPORTUNITIES_TABLE}
                    ORDER BY timestamp DESC
                    LIMIT 1
                """)
                row = cur.fetchone()
                
                if row:
                    timestamp, opportunities, symbols_analyzed, errors_count = row
                    
                    # Handle opportunities data - it might be a string or already parsed
                    if isinstance(opportunities, str):
                        import json
                        try:
                            opportunities = json.loads(opportunities)
                        except json.JSONDecodeError:
                            logger.error(f"[PRELOAD_WATCHLIST_OPPS] Failed to parse opportunities JSON: {opportunities[:100]}")
                            opportunities = []
                    
                    return {
                        "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
                        "opportunities": opportunities,
                        "symbols_analyzed": symbols_analyzed,
                        "errors_count": errors_count,
                        "cached": True
                    }
                else:
                    logger.warning("[PRELOAD_WATCHLIST_OPPS] No preloaded watchlist opportunities found in database")
                    return None
                    
    except Exception as e:
        logger.error(f"[PRELOAD_WATCHLIST_OPPS] Failed to retrieve preloaded watchlist opportunities: {e}")
        return None
