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
import json
import traceback
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

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

def validate_opportunity(opp_data: dict, symbol_type: str) -> tuple[bool, list[str]]:
    """Validate opportunity data structure and return (is_valid, error_messages)"""
    errors = []
    required_fields = {
        'symbol': str,
        'type': str,
        'price_data': dict,
        'sentiment_data': dict,
        'signal_data': dict
    }
    
    # Check required top-level fields
    for field, field_type in required_fields.items():
        if field not in opp_data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(opp_data[field], field_type):
            errors.append(f"Field {field} must be of type {field_type.__name__}")
    
    # Validate price data
    if 'price_data' in opp_data:
        price_data = opp_data['price_data']
        price_fields = ['current_price', 'price_change', 'price_change_percent', 'open', 'high', 'low', 'volume']
        for field in price_fields:
            if field not in price_data:
                errors.append(f"Missing price_data field: {field}")
            elif not isinstance(price_data[field], (int, float)):
                errors.append(f"price_data.{field} must be a number")
    
    # Validate signal data
    if 'signal_data' in opp_data:
        signal_data = opp_data['signal_data']
        if 'action' not in signal_data:
            errors.append("signal_data is missing 'action' field")
        elif signal_data['action'] not in ['BUY', 'SELL', 'HOLD']:
            errors.append(f"Invalid signal action: {signal_data['action']}")
    
    return len(errors) == 0, errors

def preload_watchlist_opportunities():
    """
    Precompute watchlist-based opportunities and save to the database.
    This runs early each trading day to have data ready for users.
    """
    start_time = datetime.now()
    logger.info(f"[PRELOAD_WATCHLIST_OPPS] Starting preload_watchlist_opportunities job at {start_time}")
    print(f"[PRELOAD_WATCHLIST_OPPS] Starting preload_watchlist_opportunities job at {start_time}")
    sys.stdout.flush()
    
    try:
        # Ensure table exists
        ensure_watchlist_opportunities_table()
        
        # Get watchlist symbols for both stocks and cryptos
        stock_symbols = watchlist_manager.get_stocks()
        crypto_symbols = watchlist_manager.get_cryptos()
        all_symbols = stock_symbols + crypto_symbols
        
        logger.info(f"[PRELOAD_WATCHLIST_OPPS] Processing {len(stock_symbols)} stock and {len(crypto_symbols)} crypto symbols")
        logger.debug(f"Stock symbols: {stock_symbols}")
        logger.debug(f"Crypto symbols: {crypto_symbols}")
        
        print(f"[PRELOAD_WATCHLIST_OPPS] Processing {len(stock_symbols)} stock and {len(crypto_symbols)} crypto symbols")
        sys.stdout.flush()

        if not all_symbols:
            logger.warning("[PRELOAD_WATCHLIST_OPPS] No watchlist symbols found")
            print("[PRELOAD_WATCHLIST_OPPS] No watchlist symbols found")
            sys.stdout.flush()
            return

        # Create and process stock tasks
        stock_tasks = create_watchlist_tasks(stock_symbols)
        logger.info(f"[PRELOAD_WATCHLIST_OPPS] Created {len(stock_tasks)} stock analysis tasks")
        print(f"[PRELOAD_WATCHLIST_OPPS] Created {len(stock_tasks)} stock analysis tasks")
        sys.stdout.flush()

        stock_batch_result = batch_processor_instance.process_batch_sync(stock_tasks, progress_callback=None)
        stock_opportunities = [
            result
            for result in stock_batch_result["results"].values()
            if result and "error" not in result
        ]
        stock_errors = [
            result
            for result in stock_batch_result["results"].values()
            if result and "error" in result
        ]

        logger.info(f"[PRELOAD_WATCHLIST_OPPS] Stock analysis completed: {len(stock_opportunities)} opportunities, {len(stock_errors)} errors")
        print(f"[PRELOAD_WATCHLIST_OPPS] Stock analysis completed: {len(stock_opportunities)} opportunities, {len(stock_errors)} errors")
        sys.stdout.flush()

        # Create and process crypto tasks
        from src.core.batch_processor import create_crypto_analysis_tasks
        crypto_tasks = create_crypto_analysis_tasks(crypto_symbols)
        logger.info(f"[PRELOAD_WATCHLIST_OPPS] Created {len(crypto_tasks)} crypto analysis tasks")
        print(f"[PRELOAD_WATCHLIST_OPPS] Created {len(crypto_tasks)} crypto analysis tasks")
        sys.stdout.flush()

        crypto_batch_result = batch_processor_instance.process_batch_sync(crypto_tasks, progress_callback=None)
        crypto_opportunities = [
            result
            for result in crypto_batch_result["results"].values()
            if result and "error" not in result
        ]
        crypto_errors = [
            result
            for result in crypto_batch_result["results"].values()
            if result and "error" in result
        ]

        logger.info(f"[PRELOAD_WATCHLIST_OPPS] Crypto analysis completed: {len(crypto_opportunities)} opportunities, {len(crypto_errors)} errors")
        print(f"[PRELOAD_WATCHLIST_OPPS] Crypto analysis completed: {len(crypto_opportunities)} opportunities, {len(crypto_errors)} errors")
        sys.stdout.flush()

        # Process and combine all opportunities
        processed_opportunities = []
        
        # Process stock opportunities
        for opp in stock_opportunities:
            if isinstance(opp, dict):
                processed_opportunities.append(opp)
        
        # Process crypto opportunities to match stock data structure
        for idx, opp in enumerate(crypto_opportunities, 1):
            if not isinstance(opp, dict):
                logger.warning(f"[PRELOAD_WATCHLIST_OPPS] Skipping invalid crypto opportunity (not a dict): {opp}")
                continue
                
            symbol = ''
            signal_data = {}
            processed_opp = None
            
            try:
                symbol = opp.get('symbol', '')
                logger.debug(f"[PRELOAD_WATCHLIST_OPPS] Processing crypto opportunity {idx}/{len(crypto_opportunities)}: {symbol}")
                
                # Get required data with defaults
                sentiment_data = opp.get('sentiment_data', {})
                signal_data = opp.get('signal_data', {})
                price_data = opp.get('price_data', {})
                news_data = opp.get('news_data', [])
                
                # Get the first 3 news articles if available
                articles = news_data[:3] if news_data else []
                news_count = len(news_data) if news_data else 0
                
                # Create the opportunity with the same structure as stocks
                processed_opp = {
                    'symbol': symbol,
                    'type': 'crypto',
                    'trigger': 'watchlist_scan',
                    'news_count': news_count,
                    'price_data': {
                        'current_price': float(price_data.get('current_price', 0.0)),
                        'price_change': float(price_data.get('price_change', 0.0)),
                        'price_change_percent': float(price_data.get('price_change_percent', 0.0)),
                        'open': float(price_data.get('open', 0.0)),
                        'high': float(price_data.get('high', 0.0)),
                        'low': float(price_data.get('low', 0.0)),
                        'volume': int(price_data.get('volume', 0)),
                        'previous_close': float(price_data.get('previous_close', 0.0)),
                        'market_cap': float(price_data.get('market_cap', 0.0))
                    },
                    'sentiment_data': {
                        'sentiment_score': float(sentiment_data.get('sentiment_score', 0.0)),
                        'confidence': float(sentiment_data.get('confidence', 0.0)),
                        'summary': str(sentiment_data.get('summary', ''))
                    },
                    'signal_data': {
                        'action': str(signal_data.get('action', 'HOLD')).upper(),
                        'confidence': float(signal_data.get('confidence', 0.0)),
                        'reasoning': str(signal_data.get('reasoning', '')),
                        'signal_strength': float(signal_data.get('confidence', 0.0))
                    },
                    'trade_signal': str(signal_data.get('action', 'HOLD')).upper(),
                    'articles': articles,
                    'timestamp': datetime.now().isoformat(),
                    'sector': 'Cryptocurrency',
                    'industry': 'Digital Assets'
                }
                
                # Validate the processed opportunity
                is_valid, validation_errors = validate_opportunity(processed_opp, 'crypto')
                if not is_valid:
                    error_msg = f"[PRELOAD_WATCHLIST_OPPS] Validation failed for {symbol}: {', '.join(validation_errors)}"
                    logger.error(error_msg)
                    print(f"ERROR: {error_msg}")
                    continue
                    
                logger.debug(f"[PRELOAD_WATCHLIST_OPPS] Successfully processed {symbol}: {processed_opp['signal_data']['action']} (Confidence: {processed_opp['signal_data']['confidence']:.2f})")
                
                # Add all crypto data for crypto dashboard (not just trading signals)
                processed_opportunities.append(processed_opp)
                    
            except Exception as e:
                logger.error(f"[PRELOAD_WATCHLIST_OPPS] Error processing {symbol}: {str(e)}")
                if hasattr(e, '__traceback__'):
                    logger.error(f"Traceback: {traceback.format_exc()}")
                continue
        
        errors = stock_errors + crypto_errors

        # Log summary and sample opportunities
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"[PRELOAD_WATCHLIST_OPPS] Processed {len(processed_opportunities)} opportunities in {duration:.2f} seconds")
        logger.info(f"[PRELOAD_WATCHLIST_OPPS] Success: {len(processed_opportunities)}, Errors: {len(errors)}")
        
        if processed_opportunities:
            # Log first 3 opportunities for debugging
            for i, opp in enumerate(processed_opportunities[:3], 1):
                if isinstance(opp, dict):
                    sample = {
                        'symbol': opp.get('symbol'),
                        'type': opp.get('type'),
                        'signal': opp.get('signal_data', {}).get('action'),
                        'confidence': f"{opp.get('signal_data', {}).get('confidence', 0) * 100:.1f}%",
                        'sentiment': f"{opp.get('sentiment_data', {}).get('sentiment_score', 0):.2f}",
                        'price': opp.get('price_data', {}).get('current_price')
                    }
                elif isinstance(opp, tuple) and len(opp) >= 4:  # Handle tuple case if needed
                    sample = {
                        'symbol': opp[0] if len(opp) > 0 else 'N/A',
                        'type': 'crypto' if 'crypto' in str(opp[0]).lower() else 'stock',
                        'signal': opp[1].get('action', 'UNKNOWN') if len(opp) > 1 and isinstance(opp[1], dict) else 'UNKNOWN',
                        'confidence': f"{opp[1].get('confidence', 0) * 100:.1f}%" if len(opp) > 1 and isinstance(opp[1], dict) else '0.0%',
                        'sentiment': f"{opp[2].get('sentiment_score', 0):.2f}" if len(opp) > 2 and isinstance(opp[2], dict) else '0.00',
                        'price': str(opp[3].get('current_price', 'N/A')) if len(opp) > 3 and isinstance(opp[3], dict) else 'N/A'
                    }
                    logger.info(f"[PRELOAD_WATCHLIST_OPPS] Sample {i}: {sample}")
                    print(f"[PRELOAD_WATCHLIST_OPPS] Sample {i}: {sample}")
        
        if errors:
            logger.warning(f"[PRELOAD_WATCHLIST_OPPS] Encountered {len(errors)} errors during processing")
            for i, error in enumerate(errors[:5], 1):  # Log first 5 errors
                logger.warning(f"[PRELOAD_WATCHLIST_OPPS] Error {i}: {error}")
        
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
                
                # Insert new data with processed opportunities
                cur.execute(f"""
                    INSERT INTO {WATCHLIST_OPPORTUNITIES_TABLE} 
                    (timestamp, opportunities, symbols_analyzed, errors_count)
                    VALUES (%s, %s, %s, %s)
                """, (
                    timestamp, 
                    Json(processed_opportunities),  # Use the processed opportunities
                    len(all_symbols),
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
        
        logger.info(f"[PRELOAD_WATCHLIST_OPPS] Successfully preloaded {len(processed_opportunities)} watchlist opportunities at {timestamp} ({len(crypto_opportunities)} crypto, {len(stock_opportunities)} stocks)")
        print(f"[PRELOAD_WATCHLIST_OPPS] Successfully preloaded {len(processed_opportunities)} watchlist opportunities at {timestamp} ({len(crypto_opportunities)} crypto, {len(stock_opportunities)} stocks)")
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

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the preload function
    preload_watchlist_opportunities()
