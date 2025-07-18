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
    Returns a consistent dictionary structure even on error.
    """
    default_response = {
        "timestamp": datetime.utcnow().isoformat(),
        "opportunities": [],
        "symbols_analyzed": 0,
        "errors_count": 0,
        "cached": False,
        "success": False,
        "error": None
    }
    
    try:
        # Ensure table exists before querying
        ensure_watchlist_opportunities_table()
        
        with get_db_connection() as conn:
            if not conn:
                error_msg = "Failed to establish database connection"
                logger.error(f"[PRELOAD_WATCHLIST_OPPS] {error_msg}")
                return {**default_response, "error": error_msg}
                
            with conn.cursor() as cur:
                logger.debug("[PRELOAD_WATCHLIST_OPPS] Querying for latest watchlist opportunities")
                cur.execute("""
                    SELECT 
                        timestamp,
                        opportunities,
                        symbols_analyzed,
                        errors_count
                    FROM preloaded_watchlist_opportunities
                    ORDER BY timestamp DESC
                    LIMIT 1
                """)
                
                result = cur.fetchone()
                
                if result:
                    # Extract data from result dictionary (RealDictCursor)
                    timestamp = result.get('timestamp')
                    opportunities = result.get('opportunities', [])
                    symbols_analyzed = result.get('symbols_analyzed', 0)
                    errors_count = result.get('errors_count', 0)
                    
                    # Log basic info about the data
                    logger.info(
                        f"[PRELOAD_WATCHLIST_OPPS] Found opportunities for {symbols_analyzed} symbols "
                        f"(errors: {errors_count}, timestamp: {timestamp})"
                    )
                    
                    # Handle opportunities data - ensure it's a list
                    if opportunities is None:
                        opportunities = []
                        logger.warning("[PRELOAD_WATCHLIST_OPPS] No opportunities found in database record")
                    elif isinstance(opportunities, str):
                        # If it's a string, try to parse it as JSON
                        import json
                        try:
                            opportunities = json.loads(opportunities)
                            if not isinstance(opportunities, list):
                                logger.error(f"[PRELOAD_WATCHLIST_OPPS] Parsed opportunities is not a list: {type(opportunities)}")
                                opportunities = []
                        except json.JSONDecodeError as je:
                            logger.error(f"[PRELOAD_WATCHLIST_OPPS] Failed to parse opportunities JSON: {str(je)}")
                            opportunities = []
                    
                    # Ensure counts are integers
                    try:
                        symbols_analyzed = int(symbols_analyzed) if symbols_analyzed is not None else 0
                        errors_count = int(errors_count) if errors_count is not None else 0
                    except (ValueError, TypeError) as ve:
                        logger.error(f"[PRELOAD_WATCHLIST_OPPS] Invalid count values: {ve}")
                        symbols_analyzed = 0
                        errors_count = 0
                    
                    # Format timestamp for JSON serialization
                    timestamp_str = (
                        timestamp.isoformat() 
                        if hasattr(timestamp, 'isoformat') 
                        else str(timestamp)
                    )
                    
                    return {
                        "timestamp": timestamp_str,
                        "opportunities": opportunities if isinstance(opportunities, list) else [],
                        "symbols_analyzed": symbols_analyzed,
                        "errors_count": errors_count,
                        "cached": True,
                        "success": True,
                        "error": None
                    }
                else:
                    logger.warning("[PRELOAD_WATCHLIST_OPPS] No watchlist opportunities found in database")
                    return {**default_response, "error": "No watchlist opportunities found"}
                    
    except Exception as e:
        error_msg = f"Error fetching watchlist opportunities: {str(e)}"
        logger.exception(f"[PRELOAD_WATCHLIST_OPPS] {error_msg}")
        return {**default_response, "error": error_msg}
