#!/usr/bin/env python3
"""
Trading AI Flask Web Application
Enhanced with comprehensive logging and monitoring
"""
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
from datetime import datetime, timedelta
import time
import sys
import threading
import traceback
import json
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
# Essential imports for remaining functionality
from src.data.data_fetcher import DataFetcher
from src.core.config import Config
from src.core.logger import log_user_actions, log_timing
from src.core.recommendation_manager import RecommendationManager
from src.core.database import save_backtest_result, get_latest_backtest, get_db_connection, ensure_job_schedules_table
from .utils.page_logger import page_logger
from .utils.db_manager import DBManager
from src.core.cache import cache_result, get_cached_result
from src.trading.trading_strategy import TradingStrategy
from src.core.market_manager import MarketManager
from src.core.watchlist_manager import watchlist_manager
# Import helper functions
from .helpers import create_api_response, handle_api_error
# Import and register route blueprints
from .routes import register_routes

# Initialize logging aliases and database manager
log_info = page_logger.info
log_error = page_logger.error
log_exception = page_logger.exception
trading_logger = page_logger.logger
app = Flask(__name__)
# Register route blueprints
register_routes(app)
# --- Client Error Logging Endpoint ---
@app.route("/api/log_client_error", methods=["POST"])
def log_client_error():
    """Log client-side JS errors from the frontend."""
    try:
        data = request.get_json(force=True)
        page = data.get("page", "unknown")
        error = data.get("error", "No error message")
        stack = data.get("stack", "No stack trace")
        timestamp = data.get("timestamp", datetime.now().isoformat())
        log_message = f"[CLIENT ERROR] Page: {page} | Error: {error} | Stack: {stack} | Timestamp: {timestamp}"
        trading_logger.error_logger.error(log_message)
        log_exception(f"Client error on {page}", error)
        return create_api_response(message="Error logged successfully")
    except Exception as e:
        return handle_api_error(e, "log_client_error endpoint")
@app.route("/api/frontend_logs", methods=["POST"])
def frontend_logs():
    """Alternative endpoint for frontend logging (compatibility)"""
    return log_client_error()
# Enable CORS for all routes
CORS(
    app,
    origins="*",
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)
# TEMPORARILY ENABLE DEBUG MODE FOR TEMPLATE RELOADING
app.debug = True
app.config["DEBUG"] = True
app.config["ENV"] = "development"
app.config["SECRET_KEY"] = "trading_ai_secret_key_change_in_production"
# 1 year cache for static files
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 31536000
# Configure app timeouts for long-running enhanced analysis
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=10)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    ping_timeout=Config.ENHANCED_ANALYSIS_TIMEOUT,
    ping_interval=25,
)
# Essential component for remaining functionality
data_fetcher = DataFetcher()
trading_strategy = TradingStrategy()
recommendation_manager = RecommendationManager()
db_manager = DBManager()
# index route moved to routes/page_routes.py
@app.route("/api/dashboard/data")
def get_dashboard_data():
    """Get dashboard data for homepage with real data"""
    try:
        from datetime import datetime
        # Get system stats
        system_metrics = get_system_metrics()
        # Get recent activity from recommendations table
        recent_analyses = []
        try:
            with recommendation_manager._get_connection() as conn:
                with conn.cursor() as cur:
                    # Get the 3 most recent analyses
                    cur.execute("""
                        SELECT DISTINCT symbol, recommendation_type, timestamp, 
                               final_confidence, action
                        FROM recommendations 
                        ORDER BY timestamp DESC 
                        LIMIT 3
                    """)
                    rows = cur.fetchall()
                    for row in rows:
                        recent_analyses.append(
                            {
                                "symbol": row["symbol"],
                                "timestamp": row["timestamp"].isoformat()
                                if row["timestamp"]
                                else datetime.now().isoformat(),
                                "type": row["recommendation_type"]
                                or "Standard Analysis",
                                "status": "completed",
                                "confidence": float(row["final_confidence"])
                                if row["final_confidence"]
                                else None,
                                "action": row["action"],
                            }
                        )
        except Exception as e:
            log_exception("Error fetching recent analyses", e)
            # Fallback to empty list if database error
            recent_analyses = []
        # Get market overview from real data
        market_overview = {}
        try:
            with recommendation_manager._get_connection() as conn:
                with conn.cursor() as cur:
                    # Get total unique stocks analyzed
                    cur.execute("SELECT COUNT(DISTINCT symbol) FROM recommendations")
                    total_stocks_result = cur.fetchone()
                    total_stocks = (
                        total_stocks_result["count"] if total_stocks_result else 0
                    )
                    # Get analyses in last 24 hours
                    cur.execute("""
                        SELECT COUNT(*) FROM recommendations 
                        WHERE timestamp >= NOW() - INTERVAL '24 hours'
                    """)
                    recent_analyses_result = cur.fetchone()
                    recent_count = (
                        recent_analyses_result["count"] if recent_analyses_result else 0
                    )
                    # Get success rate (profitable recommendations)
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total,
                            COUNT(CASE WHEN profitable = TRUE THEN 1 END) as profitable_count
                        FROM recommendations 
                        WHERE profitable IS NOT NULL
                    """)
                    success_result = cur.fetchone()
                    if success_result and success_result["total"] > 0:
                        success_rate = (
                            success_result["profitable_count"] / success_result["total"]
                        ) * 100
                        success_rate_str = f"{success_rate:.1f}%"
                    else:
                        success_rate_str = "N/A"
                    market_overview = {
                        "total_stocks": total_stocks,
                        "active_analyses": recent_count,
                        "success_rate": success_rate_str,
                        "last_updated": datetime.now().isoformat(),
                    }
        except Exception as e:
            log_exception("Error fetching market overview", e)
            # Fallback to basic stats
            market_overview = {
                "total_stocks": len(recent_analyses),
                "active_analyses": len(recent_analyses),
                "success_rate": "N/A",
                "last_updated": datetime.now().isoformat(),
            }
        # Get last analysis for homepage display
        last_analysis = None
        if recent_analyses:
            last_analysis = recent_analyses[0]
        return create_api_response(
            data={
                "system_metrics": system_metrics,
                "recent_analyses": recent_analyses,
                "market_overview": market_overview,
                "last_analysis": last_analysis,
                "feature_cards": [
                    {
                        "title": "Real-Time Analysis",
                        "description": "Get instant sentiment analysis and trading recommendations",
                        "icon": "fas fa-chart-line",
                        "status": "active",
                        "last_updated": datetime.now().isoformat(),
                    },
                    {
                        "title": "Enhanced Strategies",
                        "description": "Advanced backtesting with historical data",
                        "icon": "fas fa-rocket",
                        "status": "active",
                        "last_updated": datetime.now().isoformat(),
                    },
                    {
                        "title": "AI-Powered",
                        "description": "Multiple AI models for comprehensive analysis",
                        "icon": "fas fa-robot",
                        "status": "active",
                        "last_updated": datetime.now().isoformat(),
                    },
                ],
            }
        )
    except Exception as e:
        log_exception("Dashboard data endpoint", e)
        return create_api_response(error=str(e), status_code=500)
# Tier Management API Endpoints
@app.route("/api/tier/status", methods=["GET"])
def get_tier_status():
    """Get current tier status for the user."""
    try:
        user_id = request.args.get("user_id", "default")
        tier_info = tier_manager.get_user_tier(user_id)
        # Format features for frontend
        features = tier_info.get("features", {})
        if isinstance(features, dict):
            feature_list = features.get("features", [])
        else:
            feature_list = features if isinstance(features, list) else []
        # Create feature access map
        feature_access = {
            "dashboard": "dashboard" in feature_list,
            "stocks": "enhanced_analysis" in feature_list,
            "crypto": "enhanced_analysis" in feature_list,
            "portfolio": "portfolio" in feature_list,
            "backtesting": "backtest" in feature_list,
            "opportunities": "opportunities" in feature_list,
            "system_status": "system_status" in feature_list,
        }
        return create_api_response(
            data={
                "current_tier": tier_info["current_tier"],
                "tier_level": tier_info["tier_level"],
                "features": feature_access,
                "status": tier_info["status"],
                "updated_at": tier_info["updated_at"],
            }
        )
    except Exception as e:
        log_exception("Tier status endpoint", e)
        return create_api_response(error=str(e), status_code=500)
@app.route("/api/tier/toggle", methods=["POST"])
def toggle_tier():
    """Toggle between free and paid tiers."""
    try:
        data = request.get_json()
        if not data:
            return create_api_response(error="No data provided", status_code=400)
        tier = data.get("tier", "").lower()
        user_id = data.get("user_id", "default")
        if tier not in ["free", "paid"]:
            return create_api_response(
                error=f"Invalid tier: {tier}. Must be 'free' or 'paid'", status_code=400
            )
        tier_info = tier_manager.upgrade_tier(user_id, tier)
        return create_api_response(
            data=tier_info, message=f"Successfully switched to {tier} tier"
        )
    except Exception as e:
        log_exception("Tier toggle endpoint", e)
        return create_api_response(error=str(e), status_code=500)
@app.route("/api/tier/check_access", methods=["POST"])
def check_feature_access():
    """Check if user has access to a specific feature."""
    try:
        data = request.get_json()
        if not data:
            return create_api_response(error="No data provided", status_code=400)
        feature = data.get("feature", "")
        user_id = data.get("user_id", "default")
        if not feature:
            return create_api_response(
                error="Feature parameter is required", status_code=400
            )
        has_access = tier_manager.check_feature_access(user_id, feature)
        return create_api_response(
            data={"feature": feature, "has_access": has_access, "user_id": user_id}
        )
    except Exception as e:
        log_exception("Feature access check endpoint", e)
        return create_api_response(error=str(e), status_code=500)
@app.route("/api/tier/stats", methods=["GET"])
def get_tier_stats():
    """Get tier usage statistics."""
    try:
        user_id = request.args.get("user_id", "default")
        stats = tier_manager.get_tier_stats(user_id)
        return create_api_response(data=stats)
    except Exception as e:
        log_exception("Tier stats endpoint", e)
        return create_api_response(error=str(e), status_code=500)
@app.route("/api/tier/list", methods=["GET"])
def get_available_tiers():
    """Get all available tier configurations."""
    try:
        tiers = tier_manager.get_all_tiers()
        return create_api_response(data={"tiers": tiers})
    except Exception as e:
        log_exception("Available tiers endpoint", e)
        return create_api_response(error=str(e), status_code=500)
# analyze_stock route moved to routes/analysis_routes.py
# analyze_bulk route moved to routes/analysis_routes.py
@app.route("/api/stock/<symbol>/analysis")
def analyze_stock_by_symbol(symbol):
    """Get stock analysis by symbol"""
    try:
        # Normalize symbol
        symbol = symbol.upper()
        # Get AI provider from query params (default to ollama)
        ai_provider = request.args.get("ai_provider", "ollama")
        # Get news data
        news_data = data_fetcher.get_company_news(symbol)
        # Get price data first (needed for fallback)
        price_data = data_fetcher.get_stock_price(symbol)
        # Validate price_data is a dictionary with required fields
        if not isinstance(price_data, dict) or "current_price" not in price_data:
            return create_api_response(
                error=f"Invalid price data received for {symbol}: type={type(price_data)}",
                status_code=500,
            )
        # Get sentiment data with fallback to price-based analysis
        sentiment_data = analyze_sentiment_with_fallback(news_data, price_data, symbol)
        # Generate trading signal
        signal_data = sentiment_analyzer.get_trading_signal(sentiment_data)
        # Get trade signal
        trade_signal = trading_strategy.get_options_recommendation(
            symbol, price_data["current_price"], sentiment_data
        )
        return create_api_response(
            data={
                "symbol": symbol,
                "price_data": price_data,
                "sentiment_data": sentiment_data,
                "signal_data": signal_data,
                "trade_signal": trade_signal,
                "news_count": len(news_data),
                "ai_provider_used": ai_provider,
            }
        )
    except Exception as e:
        log_exception("Stock analysis for {symbol}", e)
        return create_api_response(error=str(e), status_code=500)

@app.route("/api/market_movers")
def market_movers():
    """API endpoint for market movers (winners and losers) from the database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                print(f"[DEBUG] Executing database query...")
                
                # First, let's check if the table exists and has data
                try:
                    cur.execute("SELECT COUNT(*) as count FROM market_movers")
                    count_result = cur.fetchone()
                    if count_result is None:
                        print(f"[DEBUG] COUNT query returned None")
                        return create_api_response(error="Database query failed", status_code=500)

                    # Debug: see what count_result actually contains
                    print(f"[DEBUG] count_result type: {type(count_result)}")
                    print(f"[DEBUG] count_result content: {count_result}")

                    # Handle dict, tuple/list, or sqlite3.Row results
                    if isinstance(count_result, dict):
                        count = count_result.get('count', 0)
                    elif isinstance(count_result, (tuple, list)):
                        count = count_result[0] if count_result else 0
                    else:
                        try:
                            count = count_result['count']
                        except Exception:
                            count = count_result[0] if hasattr(count_result, '__getitem__') else 0

                    print(f"[DEBUG] Table has {count} total rows")
                    
                    if count == 0:
                        print(f"[DEBUG] No data in market_movers table")
                        return create_api_response(data={
                            'gainers': [],
                            'losers': [],
                            'total_gainers': 0,
                            'total_losers': 0,
                            'timestamp': datetime.now().isoformat(),
                            'source': 'market_movers_table',
                            'message': 'No market movers data available'
                        })
                    
                    # Now let's check the actual data
                    cur.execute("""
                        SELECT symbol, type, change_percent, price, volume, timestamp
                        FROM market_movers 
                        ORDER BY timestamp DESC
                    """)
                    rows = cur.fetchall()
                    print(f"[DEBUG] Query returned {len(rows)} rows")
                    if rows:
                        print(f"[DEBUG] First row: {rows[0]}")
                    else:
                        print(f"[DEBUG] No rows returned from query")
                        
                    # Let's also check what tables exist
                    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                    tables = cur.fetchall()
                    print(f"[DEBUG] Available tables: {[t['table_name'] for t in tables]}")
                    
                except Exception as e:
                    print(f"[DEBUG] Database error: {e}")
                    import traceback
                    traceback.print_exc()
                    return create_api_response(error=f"Database error: {e}", status_code=500)
                
                gainers = []
                losers = []
                
                for row in rows:
                    # RealDictCursor returns dictionaries, so access by column name
                    symbol = row['symbol']
                    type_ = row['type']
                    change_percent = row['change_percent']
                    price = row['price']
                    volume = row['volume']
                    timestamp = row['timestamp']
                    
                    print(f"[DEBUG] Processing row: symbol={symbol}, type={type_}, timestamp={timestamp}, timestamp_type={type(timestamp)}")
                    
                    stock_data = {
                        'symbol': symbol,
                        'type': type_.lower() if type_ else 'unknown',  # Convert GAINER/LOSER to winner/loser
                        'change_percent': change_percent,
                        'price': price,
                        'volume': volume,
                        'timestamp': timestamp.isoformat()
                    }
                    
                    if type_ == 'GAINER':
                        gainers.append(stock_data)
                    elif type_ == 'LOSER':
                        losers.append(stock_data)
                
                # Sort by change percentage (highest gainers first, lowest losers first)
                gainers.sort(key=lambda x: x['change_percent'], reverse=True)
                losers.sort(key=lambda x: x['change_percent'])
                
                response_data = {
                    'gainers': gainers[:3],  # Top 3 gainers
                    'losers': losers[:3],    # Top 3 losers
                    'total_gainers': len(gainers),
                    'total_losers': len(losers),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'market_movers_table'
                }
                
                return create_api_response(data=response_data)
                
    except Exception as e:
        trading_logger.error_logger.error(f"Error in market_movers endpoint: {e}")
        import traceback
        trading_logger.error_logger.error(f"Traceback: {traceback.format_exc()}")
        return create_api_response(error=str(e), status_code=500)

@app.route("/api/sp500_analysis")
def sp500_analysis():
    """API endpoint for S&P 500 winners and losers analysis"""
    trading_logger.api_logger.info("[STOCKS_PAGE] ===== ENTERED sp500_analysis endpoint =====")
    try:
        # Get limit parameter for testing purposes
        limit = request.args.get("limit", type=int)
        refresh = request.args.get("refresh", default=0, type=int)
        trading_logger.api_logger.info(
            f"[STOCKS_PAGE] Request params: limit={limit}, refresh={refresh}"
        )
        if limit and limit > 0:
            trading_logger.api_logger.info(
                f"[STOCKS_PAGE] TEST MODE: Limiting analysis to {limit} stocks"
            )
        cache_key = "sp500_analysis"
        # Only clear cache if refresh=1 is passed
        if refresh:
            trading_logger.api_logger.info(
                "[STOCKS_PAGE] Manual refresh requested, clearing cache..."
            )
            try:
                clear_cache()
            except Exception as e:
                trading_logger.error_logger.error(f"[STOCKS_PAGE] Cache clear failed: {e}")
        # Check cache first
        cached_result = get_cached_result(cache_key)
        if cached_result and not refresh:
            # Ensure cached_result is a dictionary, not a string
            if isinstance(cached_result, dict):
                # Modify cached result to indicate it came from cache
                cached_result["cached"] = True
                cached_result["cache_timestamp"] = datetime.now().isoformat()
                trading_logger.api_logger.info(
                    f"[STOCKS_PAGE] Returning cached result with {len(cached_result.get('enhanced_analysis', []))} stocks"
                )
                trading_logger.api_logger.info(
                    f"[STOCKS_PAGE] Cached data structure: {list(cached_result.keys())}"
                )
                # Still emit cached progress for UI consistency
                socketio.emit(
                    "sp500_progress",
                    {
                        "current": cached_result.get("opportunities_found", 0),
                        "total": cached_result.get("total_analyzed", 0),
                        "symbol": "CACHED",
                        "status": "completed",
                        "cached": True,
                    },
                )
                return create_api_response(data=cached_result)
            else:
                # If cached result is not a dict (e.g., string), clear cache and proceed
                trading_logger.error_logger.error(
                    f"[STOCKS_PAGE] Invalid cached data type: {type(cached_result)}"
                )
                cached_result = None
        # Get top gainers and losers from Alpha Vantage API (much faster!)
        if cached_result and not refresh:
            # Still emit cached progress for UI consistency
            socketio.emit(
                "sp500_progress",
                {
                    "current": cached_result.get("opportunities_found", 0),
                    "total": cached_result.get("total_analyzed", 0),
                    "symbol": "CACHED",
                    "status": "completed",
                    "cached": True,
                },
            )
            return create_api_response(data=cached_result)
        # Get top gainers and losers from Alpha Vantage API (much faster!)
        limit_per_category = (
            3  # Reduced from 5 to 3 (keeping 3 winners + 3 losers = 6 total)
        )
        try:
            trading_logger.api_logger.info(
                "[STOCKS_PAGE] Fetching top gainers/losers from Alpha Vantage API"
            )
            winners_losers = data_fetcher.get_top_gainers_losers(
                limit=limit_per_category
            )
            trading_logger.api_logger.info(
                f"[STOCKS_PAGE] Alpha Vantage response: gainers={winners_losers.get('gainers', [])}, losers={winners_losers.get('losers', [])}"
            )
        except Exception as e:
            trading_logger.error_logger.error(
                f"[STOCKS_PAGE] Error getting top gainers/losers: {e}"
            )
            # Return error instead of mock data
            return create_api_response(
                error=f"Failed to get market movers data: {str(e)}", 
                status_code=500
            )
        # Ensure winners_losers is a dictionary
        if not isinstance(winners_losers, dict):
            trading_logger.error_logger.error(
                f"[STOCKS_PAGE] Invalid top_gainers_losers data type: {type(winners_losers)}"
            )
            # Return error instead of mock data
            return create_api_response(
                error="Invalid market movers data format", 
                status_code=500
            )
        if not winners_losers.get("gainers") and not winners_losers.get("losers"):
            trading_logger.error_logger.error("[STOCKS_PAGE] No gainers/losers data returned")
            # Return error instead of mock data
            return create_api_response(
                error="No market movers data available", 
                status_code=500
            )
        # Combine gainers and losers for analysis
        symbols_to_analyze = []
        symbols_to_analyze.extend(winners_losers.get("gainers", []))
        symbols_to_analyze.extend(winners_losers.get("losers", []))
        
        # Debug logging for winners_losers data
        trading_logger.api_logger.info(f"[STOCKS_PAGE] DEBUG: winners_losers data: {winners_losers}")
        trading_logger.api_logger.info(f"[STOCKS_PAGE] DEBUG: gainers list: {winners_losers.get('gainers', [])}")
        trading_logger.api_logger.info(f"[STOCKS_PAGE] DEBUG: losers list: {winners_losers.get('losers', [])}")
        trading_logger.api_logger.info(f"[STOCKS_PAGE] DEBUG: combined symbols: {symbols_to_analyze}")
        
        # Apply limit if specified (for testing)
        if limit and limit > 0:
            symbols_to_analyze = symbols_to_analyze[:limit]
            trading_logger.api_logger.info(
                f"[STOCKS_PAGE] TEST MODE: Limited to {len(symbols_to_analyze)} symbols: {symbols_to_analyze}"
            )
        trading_logger.api_logger.info(
            f"[STOCKS_PAGE] Running optimized analysis for {len(symbols_to_analyze)} symbols: {symbols_to_analyze}"
        )
        # Progress callback for WebSocket updates
        def progress_callback(symbol, completed, total, result):
            socketio.emit(
                "sp500_progress",
                {
                    "current": completed,
                    "total": total,
                    "symbol": symbol,
                    "status": "completed" if completed == total else "processing",
                    "has_error": "error" in result if result else False,
                    "is_opportunity": (
                        result is not None and "error" not in result
                        if result
                        else False
                    ),
                    "cached": False,
                },
            )
        # Run optimized analysis for each symbol
        enhanced_results = []
        errors = []
        start_time = time.time()
        for i, symbol in enumerate(symbols_to_analyze):
            # Initialize symbol_type with a default value
            symbol_type = "unknown"
            try:
                trading_logger.api_logger.info(f"[STOCKS_PAGE] 🔍 Analyzing {symbol} ({i + 1}/{len(symbols_to_analyze)})...")
                # OPTIMIZATION 1: Get price data first (fast)
                price_data = data_fetcher.get_stock_price(symbol)
                if "error" in price_data:
                    raise Exception(f"Error getting price data: {price_data['error']}")
                # Validate price_data is a dictionary with required fields
                if (
                    not isinstance(price_data, dict)
                    or "current_price" not in price_data
                ):
                    raise Exception(
                        f"Invalid price data received for {symbol}: type={type(price_data)}"
                    )
                trading_logger.api_logger.info(f"[STOCKS_PAGE] ✅ Got price data for {symbol}: ${price_data.get('current_price', 'N/A')}")
                # OPTIMIZATION 2: Get news data with shorter timeframe (3 days instead of 7)
                news_data = data_fetcher.get_company_news(symbol, days_back=3)
                # OPTIMIZATION 3: Skip AI sentiment analysis if no news (use price-based only)
                if not news_data or len(news_data) == 0:
                    trading_logger.api_logger.info(
                        f"[STOCKS_PAGE] 📊 No news articles for {symbol}, using price-based sentiment analysis only"
                    )
                    # Use price-based sentiment analysis (much faster)
                    sentiment_data = {
                        "sentiment_score": 0.0,
                        "sentiment_label": "neutral",
                        "confidence": 0.5,
                        "analysis_method": "price_based",
                        "news_count": 0,
                    }
                else:
                    trading_logger.api_logger.info(f"[STOCKS_PAGE] 🔍 Analyzing {symbol} using {len(news_data)} news articles...")
                    # Only use AI sentiment if we have news (but with timeout)
                    try:
                        sentiment_data = analyze_sentiment_with_fallback(
                            news_data, price_data, symbol
                        )
                    except Exception as e:
                        trading_logger.api_logger.info(
                            f"[STOCKS_PAGE] ⚠️ AI sentiment failed for {symbol}, using price-based: {e}"
                        )
                        sentiment_data = {
                            "sentiment_score": 0.0,
                            "sentiment_label": "neutral",
                            "confidence": 0.5,
                            "analysis_method": "price_based_fallback",
                            "news_count": len(news_data),
                        }
                # OPTIMIZATION 4: Use faster signal generation
                signal_data = sentiment_analyzer.get_trading_signal(sentiment_data)
                # OPTIMIZATION 5: Skip historical data testing for speed (not needed for basic analysis)
                # Historical data testing is very slow and not essential for S&P 500 overview
                historical_data = []
                # Generate comprehensive recommendations with position sizes and trading notes
                comprehensive_result = (
                    enhanced_trading_strategy.get_comprehensive_recommendations(
                        symbol, price_data["current_price"], sentiment_data, signal_data
                    )
                )
                trading_logger.api_logger.info(f"[STOCKS_PAGE] ✅ Generated comprehensive recommendations for {symbol}")
                # Determine if this is a winner or loser based on the actual price change
                change_percent = price_data.get("change_percent", "0%")
                
                # Debug logging for symbol type determination
                trading_logger.api_logger.info(f"[STOCKS_PAGE] DEBUG: Processing {symbol}, winners_losers gainers: {winners_losers.get('gainers', [])}")
                trading_logger.api_logger.info(f"[STOCKS_PAGE] DEBUG: Processing {symbol}, winners_losers losers: {winners_losers.get('losers', [])}")
                trading_logger.api_logger.info(f"[STOCKS_PAGE] DEBUG: Processing {symbol}, symbol in gainers: {symbol in winners_losers.get('gainers', [])}")
                trading_logger.api_logger.info(f"[STOCKS_PAGE] DEBUG: Processing {symbol}, symbol in losers: {symbol in winners_losers.get('losers', [])}")
                
                # First, try to determine type from winners_losers data (more reliable)
                if symbol in winners_losers.get("gainers", []):
                    symbol_type = "winner"
                    trading_logger.api_logger.info(f"[STOCKS_PAGE] 📊 {symbol}: categorized as winner from Alpha Vantage data")
                elif symbol in winners_losers.get("losers", []):
                    symbol_type = "loser"
                    trading_logger.api_logger.info(f"[STOCKS_PAGE] 📊 {symbol}: categorized as loser from Alpha Vantage data")
                else:
                    # Fallback to price-based determination
                    if isinstance(change_percent, str):
                        # Remove % sign and convert to float
                        change_percent_clean = change_percent.replace("%", "")
                        try:
                            change_percent_float = float(change_percent_clean)
                            symbol_type = "winner" if change_percent_float > 0 else "loser"
                            trading_logger.api_logger.info(f"[STOCKS_PAGE] 📊 {symbol}: change_percent={change_percent} -> type={symbol_type} (price-based)")
                        except ValueError:
                            # Final fallback - default to loser if we can't determine
                            symbol_type = "loser"
                            trading_logger.api_logger.info(f"[STOCKS_PAGE] 📊 {symbol}: fallback type={symbol_type} (default)")
                    else:
                        # If change_percent is already a number
                        symbol_type = "winner" if change_percent > 0 else "loser"
                        trading_logger.api_logger.info(f"[STOCKS_PAGE] 📊 {symbol}: change_percent={change_percent} -> type={symbol_type} (price-based)")
                
                # Ensure symbol_type is set, fallback to checking gainers/losers lists if still unknown
                if symbol_type == "unknown":
                    trading_logger.api_logger.info(f"[STOCKS_PAGE] 🔍 {symbol}: symbol_type is unknown, using fallback logic")
                    trading_logger.api_logger.info(f"[STOCKS_PAGE] 🔍 {symbol}: winners_losers={winners_losers}")
                    trading_logger.api_logger.info(f"[STOCKS_PAGE] 🔍 {symbol}: gainers={winners_losers.get('gainers', [])}")
                    trading_logger.api_logger.info(f"[STOCKS_PAGE] 🔍 {symbol}: losers={winners_losers.get('losers', [])}")
                    symbol_type = "winner" if symbol in winners_losers.get("gainers", []) else "loser"
                    trading_logger.api_logger.info(f"[STOCKS_PAGE] 🔍 {symbol}: fallback symbol_type={symbol_type}")
                
                trading_logger.api_logger.info(f"[STOCKS_PAGE] 🔍 {symbol}: Final symbol_type={symbol_type}")
                
                result = {
                    "symbol": symbol,
                    "type": symbol_type,
                    "price_data": price_data,
                    "sentiment_data": sentiment_data,
                    "signal_data": signal_data,
                    "news_count": len(news_data) if news_data else 0,
                    "comprehensive_analysis": comprehensive_result,
                    "timestamp": datetime.now().isoformat(),
                }
                enhanced_results.append(result)
                trading_logger.api_logger.info(f"[STOCKS_PAGE] ✅ Added {symbol} to results. Total results: {len(enhanced_results)}")
                # Call progress callback
                progress_callback(symbol, i + 1, len(symbols_to_analyze), result)
            except Exception as e:
                trading_logger.error_logger.error(
                    f"[STOCKS_PAGE] Error analyzing {symbol}: {e}"
                )
                errors.append({"symbol": symbol, "error": str(e)})
                # Call progress callback with error
                progress_callback(
                    symbol, i + 1, len(symbols_to_analyze), {"error": str(e)}
                )
        # Ensure we have valid results
        if not enhanced_results:
            enhanced_results = []
        # Create the final response
        response_data = {
            "enhanced_analysis": enhanced_results,
            "errors": errors,
            "total_analyzed": len(symbols_to_analyze),
            "opportunities_found": len(enhanced_results),
            "errors_count": len(errors),
            "performance": {
                "execution_time": round(time.time() - start_time, 2),
                "success_rate": f"{round(len(enhanced_results) / len(symbols_to_analyze) * 100, 1)}%"
                if len(symbols_to_analyze) > 0
                else "0%",
            },
            "timestamp": datetime.now().isoformat(),
        }
        # Cache the results for future use
        cache_result(cache_key, response_data)  # Cache for 5 minutes
        trading_logger.api_logger.info(
            f"[STOCKS_PAGE] ===== RETURNING sp500_analysis result ====="
        )
        trading_logger.api_logger.info(
            f"[STOCKS_PAGE] Total stocks analyzed: {len(symbols_to_analyze)}"
        )
        trading_logger.api_logger.info(
            f"[STOCKS_PAGE] Successful results: {len(enhanced_results)}"
        )
        trading_logger.api_logger.info(
            f"[STOCKS_PAGE] Errors: {len(errors)}"
        )
        trading_logger.api_logger.info(
            f"[STOCKS_PAGE] Response data keys: {list(response_data.keys())}"
        )
        trading_logger.api_logger.info(
            f"[STOCKS_PAGE] First result structure: {list(enhanced_results[0].keys()) if enhanced_results else 'No results'}"
        )
        return create_api_response(data=response_data)
    except Exception as e:
        trading_logger.error_logger.error(
            f"[STOCKS_PAGE] ===== ERROR in sp500_analysis endpoint: {str(e)} ====="
        )
        return create_api_response(
            error=f"Failed to analyze S&P 500: {str(e)}", status_code=500
        )
@app.route("/api/crypto_analysis")
def crypto_analysis():
    """Analyze cryptocurrencies for trading opportunities with fast preload"""
    try:
        # Get crypto symbols from database instead of config
        crypto_symbols = watchlist_manager.get_cryptos()
        if not crypto_symbols:
            return create_api_response(
                data={
                    "opportunities": [],
                    "errors": [],
                    "timestamp": datetime.now().isoformat(),
                    "total_analyzed": 0,
                    "opportunities_found": 0,
                    "errors_count": 0,
                    "cached": False,
                    "message": (
                        "No cryptocurrencies in watchlist. "
                        "Contact administrator to add crypto symbols."
                    ),
                }
            )
        # Always preload from the table unless explicitly requested to refresh
        cache_key = "crypto_analysis"
        refresh_requested = request.args.get('refresh', '0') == '1'
        if not refresh_requested:
            print("⚡ Preloading crypto opportunities from table...")
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(f"""
                            SELECT opportunities, timestamp
                            FROM preloaded_watchlist_opportunities
                            ORDER BY timestamp DESC
                            LIMIT 1
                        """)
                        row = cur.fetchone()
                        if row:
                            # Filter only crypto opportunities
                            all_opps = row['opportunities']
                            timestamp = row['timestamp']
                            crypto_opps = [opp for opp in all_opps if opp.get('type') == 'crypto']
                            # Restructure the data to match frontend expectations
                            restructured_opps = []
                            for opp in crypto_opps:
                                # Extract sentiment data from the nested structure
                                sentiment_data = opp.get('sentiment_data', {})
                                signal_data = opp.get('signal_data', {})
                                # Create the properly structured opportunity
                                restructured_opp = {
                                    "symbol": opp.get('symbol'),
                                    "type": opp.get('type'),
                                    "timestamp": opp.get('timestamp'),
                                    "sentiment_data": {
                                        "sentiment_score": sentiment_data.get('sentiment_score', 0.0),
                                        "confidence": sentiment_data.get('confidence', 0.0),
                                        "summary": sentiment_data.get('summary', '')
                                    },
                                    "signal_data": {
                                        "action": signal_data.get('action', 'HOLD'),
                                        "confidence": signal_data.get('confidence', 0.0),
                                        "reasoning": signal_data.get('reasoning', '')
                                    },
                                    "price_data": opp.get('price_data', {}),
                                    "news_data": opp.get('news_data', [])
                                }
                                restructured_opps.append(restructured_opp)
                            # Cache the result for consistency
                            cache_result(cache_key, {
                                "opportunities": restructured_opps,
                                "timestamp": timestamp,
                                "cached": True,
                                "message": "Preloaded crypto opportunities from table."
                            })
                            return create_api_response(data={
                                "opportunities": restructured_opps,
                                "timestamp": timestamp,
                                "cached": True,
                                "message": "Preloaded crypto opportunities from table."
                            })
                        else:
                            cache_result(cache_key, {
                                "opportunities": [],
                                "timestamp": datetime.now().isoformat(),
                                "cached": True,
                                "message": "No preloaded crypto opportunities found."
                            })
                            return create_api_response(data={
                                "opportunities": [],
                                "timestamp": datetime.now().isoformat(),
                                "cached": True,
                                "message": "No preloaded crypto opportunities found."
                            })
            except Exception as e:
                print(f"Error loading preloaded crypto opportunities: {e}")
                # NO FALLBACK - return error if database connection fails
                return create_api_response(
                    error=f"Database connection failed: {str(e)}. Cannot load crypto data.",
                    status_code=500
                )
        # If refresh is requested, run full analysis
        print("🚀 Refresh requested: Starting full crypto analysis with smart batching...")
        limited_cryptos = crypto_symbols
        tasks = create_crypto_analysis_tasks(
            limited_cryptos, Config.BULK_ANALYSIS_NEWS_DAYS
        )
        print(f"🚀 Processing {len(tasks)} cryptocurrencies concurrently")
        def progress_callback(symbol, completed, total, result):
            socketio.emit(
                "crypto_progress",
                {
                    "current": completed,
                    "total": total,
                    "symbol": symbol,
                    "status": "completed" if completed == total else "processing",
                    "has_error": "error" in result if result else False,
                    "is_opportunity": (
                        result is not None and "error" not in result
                        if result
                        else False
                    ),
                    "cached": False,
                },
            )
        batch_result = batch_processor_instance.process_batch_sync(
            tasks, progress_callback
        )
        opportunities = []
        errors = []
        for symbol, result in batch_result["results"].items():
            if result and "error" not in result:
                opportunities.append(result)
                print(
                    f"✅ Found opportunity: {symbol} - {result.get('action', 'UNKNOWN')}"
                )
            elif result and "error" in result:
                if "401" in str(result.get("error")):
                    errors.append(
                        {
                            "symbol": symbol,
                            "error": "API access restricted - requires premium subscription",
                        }
                    )
                    print(f"⚠️ {symbol} - API access restricted (requires premium)")
                else:
                    errors.append(
                        {
                            "symbol": symbol,
                            "error": result.get("error", "unknown error"),
                        }
                    )
                    print(
                        f"❌ Error analyzing {symbol}: {result.get('error', 'unknown error')}"
                    )
            else:
                print(f"⚪ {symbol} - No strong signal found")
        # Save crypto opportunities to preloaded table for future requests
        if opportunities:
            try:
                from src.data.preload_watchlist_opportunities import get_latest_preloaded_watchlist_opportunities
                from src.core.database import get_db_connection
                from psycopg2.extras import Json
                # Get existing opportunities from preloaded table
                existing_data = get_latest_preloaded_watchlist_opportunities()
                existing_opportunities = existing_data.get("opportunities", [])
                # Filter out old crypto opportunities and add new ones
                non_crypto_opportunities = [opp for opp in existing_opportunities if opp.get("type") != "crypto"]
                all_opportunities = non_crypto_opportunities + opportunities
                # Save updated opportunities to database
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(f"""
                            INSERT INTO preloaded_watchlist_opportunities 
                            (timestamp, opportunities, symbols_analyzed, errors_count)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            datetime.now(), 
                            Json(all_opportunities), 
                            len(all_opportunities),
                            len(errors),
                        ))
                        conn.commit()
                print(f"💾 Saved {len(opportunities)} crypto opportunities to preloaded table")
            except Exception as e:
                print(f"⚠️ Warning: Failed to save crypto opportunities to preloaded table: {e}")
                # Continue with the response even if saving fails
        result_data = {
            "opportunities": opportunities,
            "errors": errors,
            "timestamp": datetime.now().isoformat(),
            "total_analyzed": len(limited_cryptos),
            "opportunities_found": len(opportunities),
            "errors_count": len(errors),
            "cached": False,
            "batch_stats": batch_result["stats"],
            "performance": {
                "time_taken": batch_result["stats"]["time_taken"],
                "avg_time_per_crypto": batch_result["stats"]["avg_time_per_task"],
                "success_rate": (
                    f"{(batch_result['stats']['successful'] / batch_result['stats']['total_tasks'] * 100):.1f}%"
                ),
                "opportunity_rate": (
                    f"{(len(opportunities) / len(limited_cryptos) * 100):.1f}%"
                ),
            },
            "note": (
                f"Analyzed {len(limited_cryptos)} of {len(crypto_symbols)} total "
                "cryptocurrencies with smart batching"
            ),
        }
        cache_result(cache_key, result_data)
        socketio.emit(
            "crypto_progress",
            {
                "current": len(limited_cryptos),
                "total": len(tasks),
                "symbol": "COMPLETED",
                "status": "completed",
                "opportunities_found": len(opportunities),
                "errors_count": len(errors),
                "batch_stats": batch_result["stats"],
                "cached": False,
            },
        )
        return create_api_response(data=result_data)
        print("[CRYPTO_ANALYSIS] Data sent to frontend:")
        print(json.dumps(result_data, indent=2, default=str))
        trading_logger.api_logger.info("[CRYPTO_ANALYSIS] Data sent to frontend:")
        trading_logger.api_logger.info(json.dumps(result_data, indent=2, default=str))
    except Exception as e:
        traceback.print_exc()
        log_exception("Crypto analysis", e)
        return create_api_response(error=str(e), status_code=500)
@app.route("/api/execute_trade", methods=["POST"])
def execute_trade():
    """Execute a trade based on analysis"""
    try:
        data = request.get_json()
        symbol = data.get("symbol", "").upper()
        # Get fresh analysis
        price_data = data_fetcher.get_stock_price(symbol)
        # Validate price_data is a dictionary with required fields
        if not isinstance(price_data, dict) or "current_price" not in price_data:
            return create_api_response(
                error=f"Invalid price data received for {symbol}: type={type(price_data)}",
                status_code=500,
            )
        news_data = data_fetcher.get_company_news(symbol, days_back=7)
        sentiment_data = analyze_sentiment_with_fallback(news_data, price_data, symbol)
        signal_data = sentiment_analyzer.get_trading_signal(sentiment_data)
        # Generate and execute trade
        trade_signal = trading_strategy.generate_trade_signal(
            symbol, price_data["current_price"], sentiment_data, signal_data
        )
        execution_result = trading_strategy.execute_trade(trade_signal)
        portfolio_summary = trading_strategy.get_portfolio_summary()
        return jsonify(
            {
                "trade_signal": trade_signal,
                "execution_result": execution_result,
                "portfolio_summary": portfolio_summary,
                "simulation_notice": {
                    "message": "🚨 IMPORTANT: This is a SIMULATED trade for educational purposes only.",
                    "details": [
                        "❌ No real broker API is connected",
                        "❌ No actual money is being traded",
                        "❌ This is paper trading simulation only",
                        "⚠️ To enable real trading, integrate with:",
                        "   • Robinhood API",
                        "   • Interactive Brokers API",
                        "   • TD Ameritrade API",
                        "   • E*TRADE API",
                        "   • Schwab API",
                        "   • Or other broker APIs",
                    ],
                    "next_steps": "Contact the developer to add real trade execution API integration for live trading.",
                    "disclaimer": "Trading options involves substantial risk of loss and is not suitable for all investors.",
                },
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": str(e),
                    "simulation_notice": {
                        "message": "🚨 This would have been a simulated trade - no real trading API is connected.",
                        "details": [
                            "Real trade execution API integration needed for live trading"
                        ],
                    },
                }
            ),
            500,
        )
@app.route("/api/backtest", methods=["POST"])
def backtest():
    """Run backtest for a symbol, with DB persistence and prepopulation."""
    try:
        data = request.get_json()
        symbol = data.get("symbol", "").upper()
        days_back = int(data.get("days_back", 730))
        # Try to load the latest result from DB
        latest = get_latest_backtest(symbol, days_back)
        if latest and not data.get("force_rerun"):
            # Return the latest saved result
            return create_api_response(data=latest)
        # Run new backtest
        backtest_results = trading_strategy.backtest_strategy(symbol, days_back)
        # Add period_days for DB
        backtest_results["period_days"] = days_back
        # Save to DB
        save_backtest_result(backtest_results)
        return create_api_response(data=backtest_results)
    except Exception as e:
        log_exception("Backtest endpoint", e)
        return create_api_response(error=str(e), status_code=500)
@app.route("/api/backtest/historical", methods=["POST"])
def backtest_historical_recommendations():
    """Run backtest based on historical recommendations from the database."""
    try:
        data = request.get_json()
        symbol = data.get("symbol", "").upper()
        days_back = int(data.get("days_back", 30))
        strategy_type = data.get("strategy_type", "all")  # all, stocks, crypto
        # Create a connection without RealDictCursor for this function
        with db_manager.connect(dict_cursor=False) as conn:
            with conn.cursor() as cur:
                # Build query based on parameters
                query = """
                    SELECT
                        id, symbol, timestamp, recommendation_type, action,
                        strike_price, days_to_expiry, option_price, sentiment_confidence,
                        historical_confidence, final_confidence, sentiment_score,
                        current_stock_price, reasoning, actual_outcome, 
                        outcome_timestamp, profitable
                    FROM recommendations 
                    WHERE timestamp >= NOW() - INTERVAL %s
                """
                params = [f"{days_back} days"]
                # Add symbol filter if provided
                if symbol:
                    query += " AND symbol = %s"
                    params.append(symbol)
                if strategy_type != "all":
                    if strategy_type == "stocks":
                        query += " AND recommendation_type NOT LIKE 'crypto%'"
                    elif strategy_type == "crypto":
                        query += " AND recommendation_type LIKE 'crypto%'"
                query += " ORDER BY timestamp DESC"
                cur.execute(query, params)
                recommendations = cur.fetchall()
                # Debug: Print first recommendation if available
                if recommendations:
                    first_rec = recommendations[0]
                    print(f"  rec[0] (id): {first_rec[0]}")
                    print(f"  rec[1] (symbol): {first_rec[1]}")
                    print(f"  rec[2] (timestamp): {first_rec[2]}")
                    print(f"  rec[3] (recommendation_type): {first_rec[3]}")
                    print(f"  rec[4] (action): {first_rec[4]}")
                    print(f"  rec[5] (strike_price): {first_rec[5]}")
                    print(f"  rec[6] (days_to_expiry): {first_rec[6]}")
                    print(f"  rec[7] (option_price): {first_rec[7]}")
                    print(f"  rec[8] (sentiment_confidence): {first_rec[8]}")
                    print(f"  rec[9] (historical_confidence): {first_rec[9]}")
                    print(f"  rec[10] (final_confidence): {first_rec[10]}")
                    print(
                        f"  rec[11] (sentiment_score): {first_rec[11]} (type: {type(first_rec[11])})"
                    )
                    print(f"  rec[12] (current_stock_price): {first_rec[12]}")
                    print(f"  rec[13] (reasoning): {first_rec[13]}")
                    print(f"  rec[14] (actual_outcome): {first_rec[14]}")
                    print(f"  rec[15] (outcome_timestamp): {first_rec[15]}")
                    print(f"  rec[16] (profitable): {first_rec[16]}")
        if not recommendations:
            return create_api_response(
                data={
                    "message": f"No historical recommendations found for {symbol or 'all symbols'} in the last {days_back} days",
                    "total_recommendations": 0,
                    "backtest_results": {},
                }
            )
        # Process recommendations into backtest results
        backtest_results = process_historical_recommendations(recommendations)
        # Debug: Print first 3 trades from backtest_results before returning
        if "trades" in backtest_results and backtest_results["trades"]:
            for i, trade in enumerate(backtest_results["trades"][:3]):
                print(
                    f"  [{i}] action={trade.get('action')}, sentiment={trade.get('sentiment')}, symbol={trade.get('symbol')}"
                )
        else:
            print("  No trades found in backtest_results")
        # Debug: Print the full trades payload being sent to the frontend
        if "trades" in backtest_results:
            print("DEBUG: FULL TRADES PAYLOAD SENT TO FRONTEND:")
            print(json.dumps(backtest_results["trades"][:10], indent=2, default=str))
            sys.stdout.flush()
        else:
            print("DEBUG: No trades in backtest_results")
            sys.stdout.flush()
        return create_api_response(data=backtest_results)
    except Exception as e:
        log_exception("Historical backtest endpoint", e)
        return create_api_response(error=str(e), status_code=500)
@app.route("/api/backtest/recommendations", methods=["GET"])
def get_backtest_recommendations():
    """Get historical recommendations for backtesting analysis."""
    try:
        symbol = request.args.get("symbol", "").upper()
        days_back = int(request.args.get("days_back", 30))
        limit = int(request.args.get("limit", 100))
        # Create a connection without RealDictCursor for this function
        with db_manager.connect(dict_cursor=False) as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT
                        id, symbol, timestamp, recommendation_type, action,
                        strike_price, current_stock_price, sentiment_confidence,
                        final_confidence, sentiment_score, reasoning,
                        actual_outcome, outcome_timestamp, profitable
                    FROM recommendations 
                    WHERE timestamp >= NOW() - INTERVAL %s days
                """
                params = [days_back]
                if symbol:
                    query += " AND symbol = %s"
                    params.append(symbol)
                query += " ORDER BY timestamp DESC LIMIT %s"
                params.append(limit)
                cur.execute(query, params)
                recommendations = cur.fetchall()
        # Convert to list of dictionaries
        results = []
        for rec in recommendations:
            results.append(
                {
                    "id": rec[0],
                    "symbol": rec[1],
                    "timestamp": rec[2].isoformat() if rec[2] else None,
                    "recommendation_type": rec[3],
                    "action": rec[4],
                    "strike_price": float(rec[5]) if rec[5] else None,
                    "current_stock_price": float(rec[6]) if rec[6] else None,
                    "sentiment_confidence": float(rec[7]) if rec[7] else None,
                    "final_confidence": float(rec[8]) if rec[8] else None,
                    "sentiment_score": float(rec[9]) if rec[9] else None,
                    "reasoning": rec[10],
                    "actual_outcome": float(rec[11]) if rec[11] else None,
                    "outcome_timestamp": rec[12].isoformat() if rec[12] else None,
                    "profitable": rec[13],
                }
            )
        return create_api_response(
            data={
                "recommendations": results,
                "total_count": len(results),
                "symbol": symbol,
                "days_back": days_back,
            }
        )
    except Exception as e:
        log_exception("Get backtest recommendations endpoint", e)
        return create_api_response(error=str(e), status_code=500)
@app.route("/api/backtest/stats", methods=["GET"])
def get_backtest_statistics():
    """Get comprehensive backtesting statistics from historical recommendations."""
    try:
        days_back = int(request.args.get("days_back", 30))
        symbol = request.args.get("symbol", "").upper()
        # Create a connection without RealDictCursor for this function
        with db_manager.connect(dict_cursor=False) as conn:
            with conn.cursor() as cur:
                # Build base query
                base_query = f"""
                    FROM recommendations
                    WHERE timestamp >= NOW() - INTERVAL '{days_back} days'
                """
                params = []
                if symbol:
                    base_query += " AND symbol = %s"
                    params.append(symbol)
                # Overall statistics
                cur.execute(f"SELECT COUNT(*) {base_query}", params)
                result = cur.fetchone()
                total_recommendations = result[0] if result else 0
                cur.execute(
                    f"SELECT COUNT(*) {base_query} AND profitable = true", params
                )
                result = cur.fetchone()
                profitable_count = result[0] if result else 0
                cur.execute(
                    f"SELECT COUNT(*) {base_query} AND profitable = false", params
                )
                result = cur.fetchone()
                unprofitable_count = result[0] if result else 0
                # Success rate
                success_rate = (
                    (profitable_count / total_recommendations * 100)
                    if total_recommendations > 0
                    else 0
                )
                # Average confidence scores
                cur.execute(
                    f"""
                    SELECT 
                        AVG(sentiment_confidence) as avg_sentiment_confidence,
                        AVG(final_confidence) as avg_final_confidence,
                        AVG(sentiment_score) as avg_sentiment_score
                    {base_query}
                """,
                    params,
                )
                avg_scores = cur.fetchone()
                # Action breakdown
                cur.execute(
                    f"""
                    SELECT action, COUNT(*) as count
                    {base_query}
                    GROUP BY action
                    ORDER BY count DESC
                """,
                    params,
                )
                action_breakdown = cur.fetchall()
                # Recommendation type breakdown
                cur.execute(
                    f"""
                    SELECT recommendation_type, COUNT(*) as count
                    {base_query}
                    GROUP BY recommendation_type
                    ORDER BY count DESC
                """,
                    params,
                )
                type_breakdown = cur.fetchall()
                # Top performing symbols
                cur.execute(
                    f"""
                    SELECT symbol, COUNT(*) as total, 
                           SUM(CASE WHEN profitable = true THEN 1 ELSE 0 END) as profitable_count
                    {base_query}
                    GROUP BY symbol
                    HAVING COUNT(*) >= 5
                    ORDER BY (SUM(CASE WHEN profitable = true THEN 1 ELSE 0 END)::float / COUNT(*)) DESC
                    LIMIT 10
                """,
                    params,
                )
                top_symbols = cur.fetchall()
        stats = {
            "total_recommendations": total_recommendations,
            "profitable_count": profitable_count,
            "unprofitable_count": unprofitable_count,
            "success_rate": round(success_rate, 2),
            "average_scores": {
                "sentiment_confidence": round(float(avg_scores[0] or 0), 3),
                "final_confidence": round(float(avg_scores[1] or 0), 3),
                "sentiment_score": round(float(avg_scores[2] or 0), 3),
            },
            "action_breakdown": [
                {"action": row[0], "count": row[1]} for row in action_breakdown
            ],
            "type_breakdown": [
                {"type": row[0], "count": row[1]} for row in type_breakdown
            ],
            "top_performing_symbols": [
                {
                    "symbol": row[0],
                    "total_recommendations": row[1],
                    "profitable_count": row[2],
                    "success_rate": round((row[2] / row[1]) * 100, 2),
                }
                for row in top_symbols
                if len(row) >= 3
            ],
            "period_days": days_back,
            "symbol": symbol,
        }
        return create_api_response(data=stats)
    except Exception as e:
        log_exception("Backtest statistics endpoint", e)
        return create_api_response(error=str(e), status_code=500)
def process_historical_recommendations(recommendations):
    """Process historical recommendations into backtest results with trade simulation."""
    try:
        print(f"DEBUG: Processing {len(recommendations)} recommendations")
        if recommendations:
            print(f"DEBUG: First recommendation: {recommendations[0]}")
            print(f"DEBUG: Length of first recommendation: {len(recommendations[0])}")
        # Debug: Print first 5 actions and sentiment scores before processing
        print("DEBUG: First 5 recommendations before processing:")
        for i, rec in enumerate(recommendations[:5]):
            action = rec[4] if len(rec) > 4 else "N/A"
            sentiment = rec[11] if len(rec) > 11 else "N/A"
            print(f"  [{i}] action: {action}, sentiment: {sentiment}")
        # Initialize backtest parameters
        initial_capital = 10000  # $10,000 starting capital
        current_capital = initial_capital
        position_size = 0.02  # 2% of capital per trade
        trades = []  # Ensure trades list is empty at the start
        cumulative_capital = [initial_capital]
        # Sort recommendations by timestamp in ascending order (oldest first) for proper chronological processing
        sorted_recommendations = sorted(
            recommendations, key=lambda x: x[2] if x[2] else datetime.min
        )
        # Process each recommendation as a trade
        processed_trades = 0
        skipped_trades = 0
        for i, rec in enumerate(sorted_recommendations):
            if len(rec) != 17:
                print(f"SKIP: Recommendation {i} has {len(rec)} columns, expected 17")
                skipped_trades += 1
                continue
            try:
                # Debug: Print first 10 recommendations being processed
                if i < 10:
                    print(
                        f"DEBUG: Processing recommendation [{i}]: action={rec[4]}, sentiment={rec[11]}, symbol={rec[1]}"
                    )
                try:
                    symbol = rec[1]  # symbol (index 1)
                    timestamp = rec[2]  # timestamp (index 2)
                    action = rec[4]  # action (index 4)
                    confidence = (
                        float(rec[10]) if rec[10] is not None else 0.5
                    )  # final_confidence (index 10)
                    sentiment_score_raw = rec[11]  # sentiment_score (index 11)
                    # Improved sentiment score conversion
                    if sentiment_score_raw is None:
                        # Use action-based defaults for NULL sentiment scores
                        if action in ["BUY", "CALL"]:
                            sentiment_score = 0.3  # Slightly positive for buy actions
                        elif action in ["SELL", "PUT", "SELL_SHORT"]:
                            sentiment_score = -0.3  # Slightly negative for sell actions
                        else:
                            sentiment_score = 0  # Neutral for other actions
                        # Debug: Log when using defaults
                        if i < 10:  # Only log first 10 for debugging
                            print(
                                f"DEBUG: Using default sentiment for {action}: NULL -> {sentiment_score}"
                            )
                    else:
                        try:
                            # Handle both Decimal and float types
                            if hasattr(sentiment_score_raw, "quantize"):
                                # It's a Decimal object
                                sentiment_score = float(sentiment_score_raw)
                            else:
                                # It's already a float or other numeric type
                                sentiment_score = float(sentiment_score_raw)
                            # Ensure sentiment is in valid range [-1, 1]
                            sentiment_score = max(-1.0, min(1.0, sentiment_score))
                            # Debug: Log successful conversion for non-HOLD actions
                            if i < 5:  # Only log first 5 for debugging
                                print(
                                    f"DEBUG: Successfully converted sentiment_score for {action}: {sentiment_score_raw} -> {sentiment_score}"
                                )
                        except (TypeError, ValueError) as e:
                            # Debug: Log the error for non-HOLD actions
                            print(
                                f"DEBUG: Failed to convert sentiment_score for {action}: {sentiment_score_raw} (type: {type(sentiment_score_raw)}) - Error: {e}"
                            )
                            # Skip silently for invalid sentiment scores to reduce noise
                            skipped_trades += 1
                            continue
                    current_price = (
                        float(rec[12]) if rec[12] is not None else 100
                    )  # current_stock_price (index 12)
                except Exception as e:
                    print(f"ERROR: Failed to parse recommendation {i}: {rec}")
                    print(f"ERROR: Exception: {e}")
                    skipped_trades += 1
                    continue
                # Skip if no valid action
                if not action:
                    continue
                # Skip HOLD actions entirely - they don't represent actual trades
                if action == "HOLD":
                    skipped_trades += 1
                    continue
                # Calculate position size based on confidence
                trade_amount = current_capital * position_size * confidence
                shares = int(trade_amount / current_price) if current_price > 0 else 0
                # Ensure minimum position size of 1 share/contract
                if shares == 0 and trade_amount > 0:
                    shares = 1
                if shares == 0:
                    skipped_trades += 1
                    continue
                # Simulate trade outcome based on sentiment and confidence
                # Higher sentiment + higher confidence = better chance of profit
                profit_probability = (
                    (sentiment_score + 1) / 2 * confidence
                )  # Convert -1 to 1 range to 0 to 1
                # Simulate price movement
                if action in ["BUY", "CALL"]:
                    # For buy/call actions, positive sentiment should lead to price increase
                    if sentiment_score > 0:
                        price_change_pct = (
                            sentiment_score * confidence * 0.1
                        )  # 0-10% change
                    else:
                        price_change_pct = (
                            sentiment_score * confidence * 0.05
                        )  # 0-5% change
                else:  # SELL, PUT, SELL_SHORT
                    # For sell/put actions, negative sentiment should lead to price decrease (profit)
                    if sentiment_score < 0:
                        price_change_pct = (
                            abs(sentiment_score) * confidence * 0.1
                        )  # 0-10% change
                    else:
                        price_change_pct = (
                            -sentiment_score * confidence * 0.05
                        )  # 0-5% change
                # Calculate profit/loss
                if action in ["BUY", "CALL"]:
                    # Profit if price goes up
                    profit = shares * current_price * price_change_pct
                else:  # SELL, PUT, SELL_SHORT
                    # Profit if price goes down
                    profit = shares * current_price * price_change_pct
                # Add some randomness to make it more realistic
                import random
                random_factor = random.uniform(0.8, 1.2)
                profit *= random_factor
                # Update capital
                current_capital += profit
                cumulative_capital.append(current_capital)
                # Create trade record
                trade = {
                    "date": timestamp.isoformat() if timestamp else f"Trade_{i + 1}",
                    "action": action,
                    "symbol": symbol,
                    "entry_price": current_price,
                    "strike_price": current_price,  # Simplified for simulation
                    "option_price": current_price
                    * 0.1,  # 10% of stock price for options
                    "position_size": shares,
                    "cost": trade_amount,
                    "exit_price": current_price * (1 + price_change_pct),
                    "profit": profit,
                    "sentiment": sentiment_score,
                    "confidence": confidence,
                }
                trades.append(trade)
                processed_trades += 1
                # Debug: Log non-HOLD trades
                if action != "HOLD" and processed_trades <= 5:
                    print(
                        f"DEBUG: Created trade for {action}: shares={shares}, sentiment={sentiment_score}, profit={profit}"
                    )
                # Debug: Print first 5 trade objects after creation
                if processed_trades <= 5:
                    print(
                        f"DEBUG: Trade object [{processed_trades - 1}]: action={trade['action']}, sentiment={trade['sentiment']}"
                    )
            except Exception as e:
                print(f"Error processing recommendation {i}: {e}")
                skipped_trades += 1
                continue
        print(
            f"DEBUG: Processed {processed_trades} trades, skipped {skipped_trades} trades"
        )
        # Calculate statistics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t["profit"] > 0])
        losing_trades = len([t for t in trades if t["profit"] <= 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        total_return = (
            ((current_capital - initial_capital) / initial_capital * 100)
            if initial_capital > 0
            else 0
        )
        # Calculate trade statistics
        if trades:
            avg_trade = sum(t["profit"] for t in trades) / len(trades)
            best_trade = max(t["profit"] for t in trades)
            worst_trade = min(t["profit"] for t in trades)
        else:
            avg_trade = best_trade = worst_trade = 0
        # Action breakdown
        actions = {}
        for rec in recommendations:
            action = rec[4]  # action field
            if action and action != "HOLD":  # Exclude HOLD from action breakdown
                actions[action] = actions.get(action, 0) + 1
        # Symbol breakdown
        symbols = {}
        for rec in recommendations:
            symbol = rec[1]  # symbol field (index 1)
            if symbol:
                if symbol not in symbols:
                    symbols[symbol] = {"total": 0, "profitable": 0, "unprofitable": 0}
                symbols[symbol]["total"] += 1
        # Calculate symbol success rates from trades
        for trade in trades:
            symbol = trade["symbol"]
            if symbol not in symbols:
                symbols[symbol] = {"total": 0, "profitable": 0, "unprofitable": 0}
            symbols[symbol]["total"] += 1
            if trade["profit"] > 0:
                symbols[symbol]["profitable"] += 1
            else:
                symbols[symbol]["unprofitable"] += 1
        for symbol in symbols:
            total = symbols[symbol]["total"]
            profitable = symbols[symbol]["profitable"]
            symbols[symbol]["success_rate"] = (
                (profitable / total * 100) if total > 0 else 0
            )
        # Sort symbols by success rate
        sorted_symbols = sorted(
            symbols.items(), key=lambda x: x[1]["success_rate"], reverse=True
        )
        # Debug: Print first 3 trades from the main trades list before filtering
        print("DEBUG: First 3 trades from main trades list before filtering:")
        for i, trade in enumerate(trades[:3]):
            print(
                f"  [{i}] action={trade.get('action')}, sentiment={trade.get('sentiment')}, symbol={trade.get('symbol')}"
            )
        # Return recent trades (no filtering needed since we excluded HOLD)
        final_trades = trades[-20:]  # Last 20 trades
        # Debug: Print first 3 final_trades
        print("DEBUG: First 3 final_trades:")
        for i, trade in enumerate(final_trades[:3]):
            print(
                f"  [{i}] action={trade.get('action')}, sentiment={trade.get('sentiment')}, symbol={trade.get('symbol')}"
            )
        return {
            "initial_capital": initial_capital,
            "final_capital": current_capital,
            "total_return": round(total_return, 2),
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate, 2),
            "avg_trade": round(avg_trade, 2),
            "best_trade": round(best_trade, 2),
            "worst_trade": round(worst_trade, 2),
            "trades": final_trades,
            "cumulative_capital": cumulative_capital,
            "total_recommendations": len(recommendations),
            "profitable_count": winning_trades,
            "unprofitable_count": losing_trades,
            "success_rate": round(win_rate, 2),
            "average_scores": {
                "sentiment_confidence": 0.694,  # From original data
                "final_confidence": 0.521,
                "sentiment_score": -0.009,
            },
            "action_breakdown": [
                {"action": action, "count": count} for action, count in actions.items()
            ],
            "symbol_performance": [
                {
                    "symbol": symbol,
                    "total_recommendations": symbol_data["total"],
                    "profitable_count": symbol_data["profitable"],
                    "unprofitable_count": symbol_data["unprofitable"],
                    "success_rate": round(symbol_data["success_rate"], 2),
                }
                for symbol, symbol_data in sorted_symbols[:20]  # Top 20 symbols
            ],
            "recommendations_sample": [
                {
                    "symbol": rec[1],
                    "timestamp": str(rec[2]) if rec[2] else None,
                    "action": rec[4],
                    "confidence": float(rec[10]) if rec[10] else None,
                    "profitable": rec[16],
                }
                for rec in recommendations[:10]
            ],
        }
    except Exception as e:
        log_exception("Process historical recommendations", e)
        return {
            "error": str(e),
            "total_recommendations": 0,
            "success_rate": 0,
            "trades": [],
        }
@app.route("/api/portfolio")
def portfolio():
    """Get current portfolio status with mock data for demo purposes"""
    try:
        # MOCK DATA: Portfolio summary (no real portfolio tracking yet)
        portfolio_summary = {
            "current_capital": 125000,
            "initial_capital": 100000,
            "open_positions": 8,
            "positions_value": 85000,
            "total_trades": 45,
            "total_value": 125000,
            "unrealized_pnl": 25000,
            "note": "🔴 MOCK DATA - No real portfolio tracking implemented"
        }
        
        # MOCK DATA: Recent trades
        recent_trades = [
            {
                "symbol": "AAPL",
                "action": "BUY",
                "quantity": 100,
                "price": 175.50,
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "pnl": 250.00,
                "status": "closed"
            },
            {
                "symbol": "TSLA",
                "action": "SELL",
                "quantity": 50,
                "price": 245.75,
                "timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
                "pnl": -125.00,
                "status": "closed"
            },
            {
                "symbol": "NVDA",
                "action": "BUY",
                "quantity": 75,
                "price": 890.25,
                "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
                "pnl": 1875.00,
                "status": "closed"
            },
            {
                "symbol": "META",
                "action": "BUY",
                "quantity": 120,
                "price": 485.30,
                "timestamp": (datetime.now() - timedelta(hours=8)).isoformat(),
                "pnl": 456.00,
                "status": "closed"
            },
            {
                "symbol": "GOOGL",
                "action": "SELL",
                "quantity": 80,
                "price": 142.80,
                "timestamp": (datetime.now() - timedelta(hours=10)).isoformat(),
                "pnl": 320.00,
                "status": "closed"
            }
        ]
        
        # MOCK DATA: Open positions
        open_positions = [
            {
                "symbol": "AAPL",
                "quantity": 100,
                "avg_price": 175.50,
                "current_price": 178.25,
                "unrealized_pnl": 275.00,
                "position_value": 17825.00
            },
            {
                "symbol": "NVDA",
                "quantity": 75,
                "avg_price": 890.25,
                "current_price": 925.50,
                "unrealized_pnl": 2643.75,
                "position_value": 69412.50
            },
            {
                "symbol": "META",
                "quantity": 120,
                "avg_price": 485.30,
                "current_price": 492.15,
                "unrealized_pnl": 822.00,
                "position_value": 59058.00
            },
            {
                "symbol": "AMZN",
                "quantity": 60,
                "avg_price": 145.80,
                "current_price": 148.90,
                "unrealized_pnl": 186.00,
                "position_value": 8934.00
            },
            {
                "symbol": "MSFT",
                "quantity": 90,
                "avg_price": 380.45,
                "current_price": 385.20,
                "unrealized_pnl": 427.50,
                "position_value": 34668.00
            }
        ]
        
        return create_api_response(
            data={
                "portfolio_summary": portfolio_summary,
                "recent_trades": recent_trades,
                "open_positions": open_positions,
            }
        )
    except Exception as e:
        log_exception("Portfolio endpoint", e)
        return create_api_response(error=str(e), status_code=500)
@app.route("/api/telegram/test")
def test_telegram():
    """Test Telegram bot connectivity"""
    try:
        result = telegram_alerter.test_connection()
        return jsonify(
            {
                "status": "success",
                "working": result.get("working", True),
                "data": {
                    "bot_name": result.get("bot_name", "my_telegram"),
                    "username": result.get("username", "RickJamesBot"),
                    "chat_count": result.get("chat_count", 2),
                    "working": result.get("working", True),
                },
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        log_error("Error testing Telegram: {str(e)}")
        return jsonify({"status": "error", "working": False, "error": str(e)}), 500
@app.route("/api/telegram/toggle", methods=["POST"])
def toggle_telegram_alerts():
    """Toggle Telegram alerts on/of"""
    try:
        data = request.get_json()
        enabled = data.get("enabled", False)
        # Update the config (this would normally be saved to a database or
        # config file)
        Config.TELEGRAM_ALERTS_ENABLED = enabled
        if enabled:
            # Send a test message to confirm it's working
            test_message = "🎉 Telegram alerts have been enabled! You'll now receive trading signals with >70% confidence."
            success = telegram_alerter.send_message(test_message)
            if success:
                return jsonify(
                    {
                        "success": True,
                        "message": "Telegram alerts enabled successfully",
                        "test_sent": True,
                    }
                )
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Failed to send test message",
                            "test_sent": False,
                        }
                    ),
                    500,
                )
        else:
            return jsonify(
                {
                    "success": True,
                    "message": "Telegram alerts disabled",
                    "test_sent": False,
                }
            )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
@app.route("/api/telegram/send_test", methods=["POST"])
def send_test_telegram():
    """Send a test Telegram message"""
    try:
        data = request.get_json()
        message = data.get("message", "🧪 Test message from Trading AI")
        success = telegram_alerter.send_message(message)
        if success:
            return jsonify(
                {
                    "success": True,
                    "message": "Test message sent successfully",
                    "recipients": len(telegram_alerter.chat_ids),
                }
            )
        else:
            return (
                jsonify({"success": False, "message": "Failed to send test message"}),
                500,
            )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
@app.route("/api/telegram/chat_ids", methods=["GET"])
def get_telegram_chat_ids():
    """Get current Telegram chat IDs"""
    try:
        return jsonify(
            {
                "chat_ids": telegram_alerter.chat_ids,
                "count": len(telegram_alerter.chat_ids),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/telegram/add_chat_id", methods=["POST"])
def add_telegram_chat_id():
    """Add a new Telegram chat ID"""
    try:
        data = request.get_json()
        new_chat_id = data.get("chat_id", "").strip()
        if not new_chat_id:
            return jsonify({"success": False, "error": "Chat ID is required"}), 400
        if new_chat_id in telegram_alerter.chat_ids:
            return jsonify({"success": False, "error": "Chat ID already exists"}), 400
        # Test the new chat ID by sending a welcome message
        test_payload = {
            "chat_id": new_chat_id,
            "text": "🎉 Welcome! You have been added to Trading AI alerts.",
            "parse_mode": "HTML",
        }
        response = requests.post(
            telegram_alerter.api_url,
            json=test_payload,
            timeout=10,
        )
        if response.status_code == 200:
            telegram_alerter.chat_ids.append(new_chat_id)
            return jsonify(
                {
                    "success": True,
                    "message": (
                        "Chat ID added and welcome message sent successfully. "
                        "You will now receive alerts."
                    ),
                    "chat_id": new_chat_id,
                }
            )
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": (
                            "Failed to send welcome message. "
                            "Check the chat ID and try again."
                        ),
                    }
                ),
                500,
            )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
@app.route("/api/telegram/remove_chat_id", methods=["POST"])
def remove_telegram_chat_id():
    """Remove a Telegram chat ID"""
    try:
        data = request.get_json()
        chat_id_to_remove = data.get("chat_id", "").strip()
        if not chat_id_to_remove:
            return create_api_response(error="Chat ID is required", status_code=400)
        if chat_id_to_remove not in telegram_alerter.chat_ids:
            return create_api_response(error="Chat ID not found", status_code=404)
        telegram_alerter.chat_ids.remove(chat_id_to_remove)
        return create_api_response(
            data={"total_chats": len(telegram_alerter.chat_ids)},
            message="Chat ID {chat_id_to_remove} removed successfully",
        )
    except Exception as e:
        log_exception("Remove Telegram chat ID endpoint", e)
        return create_api_response(error=str(e), status_code=500)
@app.route("/api/telegram/send_raw_message", methods=["POST"])
def send_raw_telegram_message():
    """Send a custom raw message via Telegram to all recipients"""
    try:
        if not telegram_alerter.is_enabled():
            return create_api_response(
                error="Telegram alerts are disabled", status_code=400
            )
        data = request.get_json()
        message = data.get("message", "")
        if not message:
            return create_api_response(
                error="Message content is required", status_code=400
            )
        # Optional parameters
        parse_mode = data.get("parse_mode", "HTML")
        symbol = data.get("symbol", "CUSTOM")
        message_type = data.get("message_type", "custom_message")
        # Send the message
        success = telegram_alerter.send_message(
            message=message,
            message_type=message_type,
            symbol=symbol,
            parse_mode=parse_mode,
        )
        if success:
            return create_api_response(
                data={
                    "recipients": len(telegram_alerter.chat_ids),
                    "sent_to": telegram_alerter.chat_ids,
                },
                message="Raw message sent successfully",
            )
        else:
            return create_api_response(
                error="Failed to send message to any recipients", status_code=500
            )
    except Exception as e:
        log_exception("Send raw Telegram message endpoint", e)
        return create_api_response(
            error="Error sending raw message: {str(e)}", status_code=500
        )
@app.route("/stocks")
def stocks_page():
    """S&P 500 stocks analysis page"""
    try:
        trading_logger.api_logger.info("[DEBUG] Entering stocks_page route handler")
        # Check if preloaded data is available and log its status
        try:
            if preloaded_data:
                trading_logger.api_logger.info(
                    f"[DEBUG] Preloaded data available for stocks page: {len(preloaded_data.get('enhanced_analysis', []))} stocks"
                )
            else:
                trading_logger.api_logger.warning(
                    "[DEBUG] No preloaded data available for stocks page"
                )
        except Exception as e:
            trading_logger.error_logger.error(
                f"[DEBUG] Error checking preloaded_data: {str(e)}"
            )
        trading_logger.api_logger.info("[DEBUG] Rendering stocks.html template")
        return render_template(
            "stocks.html", historical_lookback_days=Config.HISTORICAL_LOOKBACK_DAYS
        )
    except Exception as e:
        trading_logger.error_logger.error(
            f"[CRITICAL] Error rendering stocks page: {str(e)}"
        )
        # Return a simple error page instead of crashing
        return (
            f"<html><body><h1>Error loading stocks page</h1><p>Please try again later. Error: {str(e)}</p></body></html>",
            500,
        )
# crypto route moved to routes/page_routes.py
# portfolio route moved to routes/page_routes.py
# backtest route moved to routes/backtest_routes.py
@app.route("/foreign_markets_overview")
def foreign_markets_overview_page():
    """Foreign markets overview page"""
    try:
        trading_logger.api_logger.info(
            "[DEBUG] Entering foreign_markets_overview_page route handler"
        )
        return render_template("foreign_markets_overview.html")
    except Exception as e:
        trading_logger.error_logger.error(
            f"[ERROR] Failed to render foreign markets overview page: {str(e)}"
        )
        return "Error loading foreign markets overview page", 500
@app.route("/api/foreign_markets/overview")
def foreign_markets_overview_api():
    """Get foreign markets overview data with summary statistics"""
    try:
        # Get markets data from MarketManager
        markets_data = MarketManager.get_foreign_markets_overview()
        # Add US market indices
        us_market_indices = [
            {
                "code": "SPY", 
                "currency": "USD", 
                "label": "S&P 500 ETF", 
                "value": "US",
                "name": "S&P 500 ETF",
                "country": "United States",
                "status": "Closed",
                "status_class": "secondary",
                "performance": 1.25,
                "performance_class": "success",
                "symbol_count": 1,
                "symbols": ["SPY"],
                "trading_hours_open": "09:30",
                "trading_hours_close": "16:00",
                "timezone": "EST",
                "is_open": False,
                "symbol_suffix": ""
            },
        ]
        # Add sample symbols to markets for demo purposes
        for market in markets_data['markets']:
            if 'symbols' not in market or not market['symbols']:
                market['symbols'] = [f"{market['code']}.{market['currency']}"]
                market['symbol_count'] = len(market['symbols'])
        # Add US indices to the markets list for the frontend
        markets_data['markets'].extend(us_market_indices)
        # Update summary with US indices
        markets_data['summary']['total_markets'] += len(us_market_indices)
        markets_data['summary']['markets_open'] += len(us_market_indices)  # Assuming all US indices are open
        response = {
            "success": True,
            "data": {
                "markets": markets_data['markets'],
                "us_indices": us_market_indices,
                "summary": markets_data['summary']
            },
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
        return jsonify(response)
    except Exception as e:
        error_msg = f"Error in foreign_markets_overview_api: {str(e)}"
        trading_logger.error_logger.error(error_msg, exc_info=True)
        return jsonify({
            "success": False,
            "error": "Failed to fetch foreign markets data",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }), 500
    """Trading opportunities page"""
    try:
        # Preload data server-side to avoid frontend API timeouts
        try:
            # Use placeholder data for now - modules moved to routes/services
            news_opps = {"success": False, "error": "Moved to service layer", "opportunities": []}
            watchlist_opps = {"success": False, "error": "Moved to service layer", "opportunities": []}
            # Extract data for template rendering
            # Extract data with proper error handling
            news_opps_list = (
                news_opps.get("opportunities", [])
                if news_opps and isinstance(news_opps, dict)
                else []
            )
            watchlist_opps_list = (
                watchlist_opps.get("opportunities", [])
                if watchlist_opps and isinstance(watchlist_opps, dict)
                else []
            )
            news_count = len(news_opps_list)
            watchlist_count = len(watchlist_opps_list)
            # Log any errors from the preload functions
            if news_opps and not news_opps.get("success", False):
                trading_logger.error_logger.error(
                    f"[ERROR] News opportunities preload failed: {news_opps.get('error', 'Unknown error')}"
                )
            if watchlist_opps and not watchlist_opps.get("success", False):
                trading_logger.error_logger.error(
                    f"[ERROR] Watchlist opportunities preload failed: {watchlist_opps.get('error', 'Unknown error')}"
                )
            trading_logger.api_logger.info(
                f"[DEBUG] Opportunities page - loaded: {news_count} news, {watchlist_count} watchlist opportunities"
            )
            # Prepare data for template with proper structure
            preloaded_data = {
                "data": {
                    "news_opportunities": news_opps_list or [],
                    "watchlist_opportunities": watchlist_opps_list or [],
                    "news_count": news_count,
                    "watchlist_count": watchlist_count,
                    "news_timestamp": news_opps.get("timestamp")
                    if isinstance(news_opps, dict)
                    else None,
                    "watchlist_timestamp": watchlist_opps.get("timestamp")
                    if isinstance(watchlist_opps, dict)
                    else None,
                    "news_success": news_opps.get("success", False)
                    if isinstance(news_opps, dict)
                    else False,
                    "watchlist_success": watchlist_opps.get("success", False)
                    if isinstance(watchlist_opps, dict)
                    else False,
                    "news_error": "Yahoo Finance API rate limit reached. Please try again later."
                    if "Too Many Requests" in str(news_opps.get("error", ""))
                    else (
                        news_opps.get("error")
                        if isinstance(news_opps, dict)
                        and not news_opps.get("success", False)
                        else None
                    ),
                    "watchlist_error": watchlist_opps.get("error")
                    if isinstance(watchlist_opps, dict)
                    and not watchlist_opps.get("success", False)
                    else None,
                },
                "news_count": news_count,
                "watchlist_count": watchlist_count,
                "news_timestamp": news_opps.get("timestamp")
                if isinstance(news_opps, dict)
                else None,
                "watchlist_timestamp": watchlist_opps.get("timestamp")
                if isinstance(watchlist_opps, dict)
                else None,
                "news_success": news_opps.get("success", False)
                if isinstance(news_opps, dict)
                else False,
                "watchlist_success": watchlist_opps.get("success", False)
                if isinstance(watchlist_opps, dict)
                else False,
                "news_error": "Yahoo Finance API rate limit reached. Please try again later."
                if "Too Many Requests" in str(news_opps.get("error", ""))
                else (
                    news_opps.get("error")
                    if isinstance(news_opps, dict)
                    and not news_opps.get("success", False)
                    else None
                ),
                "watchlist_error": watchlist_opps.get("error")
                if isinstance(watchlist_opps, dict)
                and not watchlist_opps.get("success", False)
                else None,
            }
            trading_logger.api_logger.info(
                "[DEBUG] Rendering opportunities.html template with preloaded data"
            )
            trading_logger.api_logger.info(
                f"[EXTRA DEBUG] preloaded_data: news_count={preloaded_data['news_count']}, watchlist_count={preloaded_data['watchlist_count']}"
            )
            # Safe debug logging for opportunities data
            try:
                if preloaded_data.get("data", {}).get("news_opportunities"):
                    trading_logger.api_logger.info(
                        f"[EXTRA DEBUG] First news opportunity: {str(preloaded_data['data']['news_opportunities'][0])}"
                    )
                else:
                    trading_logger.api_logger.info(
                        "[EXTRA DEBUG] No news opportunities found"
                    )
            except Exception as debug_e:
                trading_logger.api_logger.warning(
                    f"[EXTRA DEBUG] Error logging news opportunities: {debug_e}"
                )
            try:
                if preloaded_data.get("data", {}).get("watchlist_opportunities"):
                    trading_logger.api_logger.info(
                        f"[EXTRA DEBUG] First watchlist opportunity: {str(preloaded_data['data']['watchlist_opportunities'][0])}"
                    )
                else:
                    trading_logger.api_logger.info(
                        "[EXTRA DEBUG] No watchlist opportunities found"
                    )
            except Exception as debug_e:
                trading_logger.api_logger.warning(
                    f"[EXTRA DEBUG] Error logging watchlist opportunities: {debug_e}"
                )
            # Ensure all data is JSON serializable
            def safe_serialize(obj):
                if obj is None or isinstance(obj, (str, int, float, bool)):
                    return obj
                elif isinstance(obj, dict):
                    return {k: safe_serialize(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [safe_serialize(item) for item in obj]
                elif hasattr(obj, "isoformat"):
                    return obj.isoformat()
                elif hasattr(obj, "to_dict"):
                    return safe_serialize(obj.to_dict())
                else:
                    return str(obj)
            serialized_data = safe_serialize(preloaded_data)
            preloaded_json = json.dumps(serialized_data)
            trading_logger.api_logger.info(
                f"[DEBUG] Serialized preloaded data: {preloaded_json[:500]}..."
            )
        except Exception as e:
            trading_logger.error_logger.error(
                f"[ERROR] Error serializing preloaded data: {str(e)}"
            )
            preloaded_json = '{"error": "Failed to load opportunities data"}'
        return render_template(
            "opportunities.html",
            historical_lookback_days=Config.HISTORICAL_LOOKBACK_DAYS,
            preloaded_json=preloaded_json,
        )
    except Exception as e:
        trading_logger.error_logger.error(
            f"[CRITICAL] Error rendering opportunities page: {str(e)}"
        )
        # Return a simple error page instead of crashing
        return (
            f"<html><body><h1>Error loading opportunities page</h1><p>Please try again later. Error: {str(e)}</p></body></html>",
            500,
        )
@app.route("/weekly_plan")
def weekly_plan_page():
    """Weekly Market Plan page"""
    try:
        trading_logger.api_logger.info(
            "[DEBUG] Entering weekly_plan_page route handler"
        )
        return render_template("weekly_plan.html")
    except Exception as e:
        trading_logger.error_logger.error(
            f"[CRITICAL] Error rendering weekly plan page: {str(e)}"
        )
        return (
            f"<html><body><h1>Error loading weekly plan page</h1><p>Please try again later. Error: {str(e)}</p></body></html>",
            500,
        )
@app.route("/api/weekly_events")
def weekly_events_api():
    """Get weekly market events"""
    try:
        trading_logger.api_logger.info("[DEBUG] Entered weekly_events API endpoint")
        # Get start_date parameter (optional)
        start_date_str = request.args.get("start_date")
        start_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except ValueError:
                return create_api_response(
                    success=False,
                    message="Invalid date format. Use YYYY-MM-DD",
                    status_code=400,
                )
        # For now, return mock data since WeeklyPlanPopulator is not available
        # In the future, this should fetch from weekly_plan_events table
        mock_events = {
            "earnings": [
                {
                    "date": "2025-08-19",
                    "name": "AAPL Earnings",
                    "event_type": "earnings",
                    "impact": "high",
                    "symbol": "AAPL",
                    "timing": "after_market"
                },
                {
                    "date": "2025-08-20",
                    "name": "NVDA Earnings",
                    "event_type": "earnings",
                    "impact": "high",
                    "symbol": "NVDA",
                    "timing": "after_market"
                }
            ],
            "federal_reserve": [
                {
                    "date": "2025-08-21",
                    "name": "FOMC Meeting Minutes",
                    "event_type": "federal_reserve",
                    "impact": "high",
                    "symbol": None,
                    "timing": "all_day"
                }
            ],
            "economic": [
                {
                    "date": "2025-08-22",
                    "name": "CPI Data Release",
                    "event_type": "economic_data",
                    "impact": "high",
                    "symbol": None,
                    "timing": "market_open"
                }
            ],
            "options_expiration": [
                {
                    "date": "2025-08-23",
                    "name": "Weekly Options Expiration",
                    "event_type": "options_expiration",
                    "impact": "medium",
                    "symbol": None,
                    "timing": "market_close"
                }
            ],
            "market_holidays": []
        }
        trading_logger.api_logger.info(
            f"[DEBUG] Successfully fetched mock weekly events: {len(mock_events.get('earnings', []))} earnings, {len(mock_events.get('economic', []))} economic events"
        )
        return create_api_response(
            data=mock_events, message="Weekly events retrieved successfully (mock data)"
        )
    except Exception as e:
        trading_logger.error_logger.error(
            f"[ERROR] Failed to fetch weekly events: {str(e)}"
        )
        return create_api_response(
            success=False,
            message=f"Failed to fetch weekly events: {str(e)}",
            status_code=500,
        )
@app.route("/api/weekly_plan/populate", methods=["POST"])
def populate_weekly_plan():
    """Populate weekly plan data (admin endpoint)"""
    try:
        # from src.data.weekly_plan_populator import WeeklyPlanPopulator  # Module not available
        trading_logger.api_logger.info("[DEBUG] Populating weekly plan data")
        # populator = WeeklyPlanPopulator()  # Module not available
        # results = populator.populate_advance_data()  # Module not available
        trading_logger.api_logger.info("[DEBUG] Weekly plan populated: (module not available)")
        return create_api_response(
            data={"status": "module_not_available"}, message="Weekly plan module not available"
        )
    except Exception as e:
        trading_logger.error_logger.error(
            f"[ERROR] Failed to populate weekly plan: {str(e)}"
        )
        return create_api_response(
            success=False,
            message=f"Failed to populate weekly plan: {str(e)}",
            status_code=500,
        )
@app.route("/api/weekly_plan/available_weeks")
def available_weeks_api():
    """Get list of available weeks for selection"""
    try:
        # from src.data.weekly_plan_populator import WeeklyPlanPopulator  # Module not available
        weeks_back = int(request.args.get("weeks_back", 4))
        weeks_ahead = int(request.args.get("weeks_ahead", 8))
        # populator = WeeklyPlanPopulator()  # Module not available
        # available_weeks = populator.get_available_weeks(weeks_back, weeks_ahead)  # Module not available
        return create_api_response(
            data={"weeks": []}, message="Weekly plan module not available"
        )
    except Exception as e:
        trading_logger.error_logger.error(
            f"[ERROR] Failed to get available weeks: {str(e)}"
        )
        return create_api_response(
            success=False,
            message=f"Failed to get available weeks: {str(e)}",
            status_code=500,
        )
@app.route("/api/market_calendar/<date_str>")
def market_calendar_api(date_str):
    """Get market events for a specific date"""
    try:
        trading_logger.api_logger.info(
            f"[DEBUG] Entered market_calendar API endpoint for date: {date_str}"
        )
        # Parse date
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return create_api_response(
                success=False,
                message="Invalid date format. Use YYYY-MM-DD",
                status_code=400,
            )
        # For now, return mock data since market_calendar is not available
        # In the future, this should fetch from weekly_plan_events table
        mock_events = [
            {
                "name": "Market Open",
                "event_type": "market_open",
                "impact": "low",
                "timing": "market_open"
            }
        ]
        trading_logger.api_logger.info(
            f"[DEBUG] Successfully fetched {len(mock_events)} mock events for {date_str}"
        )
        return create_api_response(
            data={"date": date_str, "events": mock_events},
            message=f"Events for {date_str} retrieved successfully (mock data)",
        )
    except Exception as e:
        trading_logger.error_logger.error(
            f"[ERROR] Failed to fetch events for {date_str}: {str(e)}"
        )
        return create_api_response(
            success=False,
            message=f"Failed to fetch events for {date_str}: {str(e)}",
            status_code=500,
        )
@app.route("/api/earnings_calendar")
def earnings_calendar_api():
    """Get earnings calendar for watchlist symbols"""
    try:
        trading_logger.api_logger.info("[DEBUG] Entered earnings_calendar API endpoint")
        # Get watchlist symbols
        try:
            watchlist_symbols = Config.WATCHLIST_STOCKS or []
        except AttributeError:
            watchlist_symbols = [
                "AAPL",
                "MSFT",
                "GOOGL",
                "AMZN",
                "TSLA",
            ]  # Default symbols
        # Get days_ahead parameter (optional, default 30)
        days_ahead = int(request.args.get("days_ahead", 30))
        # For now, return mock data since market_calendar is not available
        # In the future, this should fetch from weekly_plan_events table
        mock_earnings = [
            {
                "symbol": "AAPL",
                "date": "2025-08-19",
                "estimate": 1.25,
                "previous": 1.20,
                "impact": "high"
            },
            {
                "symbol": "MSFT",
                "date": "2025-08-20",
                "estimate": 2.85,
                "previous": 2.75,
                "impact": "high"
            }
        ]
        earnings = mock_earnings
        trading_logger.api_logger.info(
            f"[DEBUG] Successfully fetched {len(earnings)} earnings events for watchlist"
        )
        return create_api_response(
            data={"earnings": earnings, "symbols": watchlist_symbols},
            message="Earnings calendar retrieved successfully",
        )
    except Exception as e:
        trading_logger.error_logger.error(
            f"[ERROR] Failed to fetch earnings calendar: {str(e)}"
        )
        return create_api_response(
            success=False,
            message=f"Failed to fetch earnings calendar: {str(e)}",
            status_code=500,
        )
@app.route("/api/news_opportunities")
def news_opportunities():
    """Get news-driven trading opportunities from preloaded data (fast)."""
    trading_logger.api_logger.info(
        "[DEBUG] Entered news_opportunities endpoint (preloaded mode)"
    )
    try:
        ip = request.remote_addr or "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")
        trading_logger.api_logger.info(
            f"[DEBUG] news_opportunities request | IP: {ip} | UA: {user_agent}"
        )
        # Optionally allow force refresh (manual re-analysis)
        refresh = request.args.get("refresh", default=0, type=int)
        if not refresh:
            # Serve preloaded data from DB
            from src.data.preload_news_opportunities import (
                get_latest_preloaded_news_opportunities,
            )
            preloaded = get_latest_preloaded_news_opportunities()
            if preloaded and preloaded.get("opportunities") is not None:
                trading_logger.api_logger.info(
                    f"[DEBUG] Returning preloaded news opportunities (count={len(preloaded['opportunities'])})"
                )
                return create_api_response(
                    data={
                        "opportunities": preloaded["opportunities"],
                        "count": len(preloaded["opportunities"]),
                        "cached": True,
                        "cache_timestamp": preloaded["timestamp"],
                    }
                )
            else:
                trading_logger.api_logger.warning(
                    "[DEBUG] No preloaded news opportunities found in DB!"
                )
        # If refresh=1 or no preloaded data, run a fresh analysis and update cache
        trading_logger.api_logger.info(
            "[DEBUG] Running fresh news opportunities analysis and updating cache..."
        )
        if refresh:
            # Refresh requested - run preload function to update database
            trading_logger.api_logger.info(
                "[DEBUG] Refresh requested - running preload to update database"
            )
            from src.data.preload_news_opportunities import preload_news_opportunities
            preload_news_opportunities()
            # Get the newly cached data
            from src.data.preload_news_opportunities import (
                get_latest_preloaded_news_opportunities,
            )
            preloaded = get_latest_preloaded_news_opportunities()
            if preloaded and preloaded.get("opportunities") is not None:
                return create_api_response(
                    data={
                        "opportunities": preloaded["opportunities"],
                        "count": len(preloaded["opportunities"]),
                        "cached": True,
                        "refreshed": True,
                        "cache_timestamp": preloaded["timestamp"],
                    }
                )
        # Fallback: direct analysis (no database update)
        trading_logger.api_logger.info(
            "[DEBUG] Running fallback real-time news opportunities analysis (slow)"
        )
        trending_symbols = news_monitor.scan_trending_news()
        opportunities = news_monitor.analyze_news_driven_opportunities(trending_symbols)
        return create_api_response(
            data={
                "opportunities": opportunities,
                "count": len(opportunities),
                "cached": False,
                "cache_timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        trading_logger.error_logger.error(
            f"[ERROR] Error in news_opportunities endpoint: {str(e)}"
        )
        log_exception("News opportunities endpoint", e)
        return create_api_response(error=str(e), status_code=500)
@app.route("/api/watchlist_opportunities")
def watchlist_opportunities():
    """Get watchlist-based trading opportunities from preloaded data (fast)."""
    trading_logger.api_logger.info(
        "[DEBUG] Entered watchlist_opportunities endpoint (preloaded mode)"
    )
    try:
        ip = request.remote_addr or "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")
        trading_logger.api_logger.info(
            f"[DEBUG] watchlist_opportunities request | IP: {ip} | UA: {user_agent}"
        )
        # Check if refresh is requested (force real-time analysis)
        refresh = request.args.get("refresh", default=0, type=int)
        if not refresh:
            # Serve preloaded data from DB
            from src.data.preload_watchlist_opportunities import (
                get_latest_preloaded_watchlist_opportunities,
            )
            preloaded = get_latest_preloaded_watchlist_opportunities()
            if preloaded and preloaded.get("opportunities") is not None:
                trading_logger.api_logger.info(
                    f"[DEBUG] Returning preloaded watchlist opportunities (count={len(preloaded['opportunities'])})"
                )
                return create_api_response(
                    data={
                        "opportunities": preloaded["opportunities"],
                        "count": len(preloaded["opportunities"]),
                        "opportunities_found": len(preloaded["opportunities"]),
                        "total_analyzed": preloaded.get("symbols_analyzed", 0),
                        "errors_count": preloaded.get("errors_count", 0),
                        "cached": True,
                        "cache_timestamp": preloaded["timestamp"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            else:
                trading_logger.api_logger.warning(
                    "[DEBUG] No preloaded watchlist opportunities found in DB!"
                )
        # If refresh=1 or no preloaded data, run fresh analysis and update cache
        if refresh:
            # Refresh requested - run preload function to update database
            trading_logger.api_logger.info(
                "[DEBUG] Refresh requested - running watchlist preload to update database"
            )
            from src.data.preload_watchlist_opportunities import (
                preload_watchlist_opportunities,
            )
            preload_watchlist_opportunities()
            # Get the newly cached data
            from src.data.preload_watchlist_opportunities import (
                get_latest_preloaded_watchlist_opportunities,
            )
            preloaded = get_latest_preloaded_watchlist_opportunities()
            if preloaded and preloaded.get("opportunities") is not None:
                trading_logger.api_logger.info(
                    f"[DEBUG] Returning preloaded watchlist opportunities (count={len(preloaded['opportunities'])})"
                )
                return create_api_response(
                    data={
                        "opportunities": preloaded["opportunities"],
                        "count": len(preloaded["opportunities"]),
                        "opportunities_found": len(preloaded["opportunities"]),
                        "total_analyzed": preloaded.get("symbols_analyzed", 0),
                        "errors_count": preloaded.get("errors_count", 0),
                        "cached": True,
                        "cache_timestamp": preloaded["timestamp"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )
        # Fallback: direct analysis without database update
        trading_logger.api_logger.info(
            "[DEBUG] Running fallback real-time watchlist opportunities analysis (slow)"
        )
        # Get watchlist symbols (stocks only, no crypto)
        watchlist_symbols = watchlist_manager.get_stocks()
        trading_logger.api_logger.info(
            f"[DEBUG] Processing watchlist symbols: {watchlist_symbols}"
        )
        if not watchlist_symbols:
            return create_api_response(
                data={
                    "opportunities": [],
                    "count": 0,
                    "opportunities_found": 0,
                    "total_analyzed": 0,
                    "errors_count": 0,
                    "cached": False,
                    "message": "No watchlist symbols configured",
                }
            )
        # Create tasks and process
        tasks = create_watchlist_tasks(watchlist_symbols)
        # Progress callback for real-time updates
        def progress_callback(symbol, completed, total, result):
            socketio.emit(
                "watchlist_progress",
                {
                    "symbol": symbol,
                    "completed": completed,
                    "total": total,
                    "status": "processing",
                },
            )
        # Execute the batch analysis
        trading_logger.api_logger.info(
            "[DEBUG] Starting real-time batch analysis for watchlist opportunities..."
        )
        batch_result = batch_processor_instance.process_batch_sync(
            tasks, progress_callback
        )
        # Filter out successful opportunities
        opportunities = [
            result
            for result in batch_result["results"].values()
            if result and "error" not in result
        ]
        # Get errors
        errors = [
            result
            for result in batch_result["results"].values()
            if result and "error" in result
        ]
        # Normalize the data structure to match frontend expectations
        normalized_opportunities = []
        for opp in opportunities:
            normalized_opp = {
                "type": "stock",
                "symbol": opp.get("symbol"),
                "trigger": "watchlist",
                "timestamp": datetime.now().isoformat(),
                "news_count": opp.get("news_count", 0),
                "price_data": {
                    "current_price": opp.get("current_price", 0),
                    "change": 0,
                    "volume": 0,
                    "change_percent": "0%",
                },
                "signal_data": {
                    "action": opp.get("action", "HOLD"),
                    "reasoning": opp.get("reasoning", "No reasoning provided"),
                    "confidence": opp.get("confidence", 0),
                    "signal_strength": opp.get("signal_strength", 0),
                },
                "trade_signal": {
                    "action": opp.get("action", "HOLD"),
                    "option_price": 0,
                    "strike_price": 0,
                    "position_size": 1,
                },
                "sentiment_data": {
                    "summary": "Watchlist analysis",
                    "confidence": opp.get("confidence", 0),
                    "sentiment_score": opp.get("sentiment_score", 0),
                },
            }
            normalized_opportunities.append(normalized_opp)
        trading_logger.api_logger.info(
            f"[DEBUG] Real-time watchlist_opportunities result: {len(normalized_opportunities)} opportunities, {len(errors)} errors"
        )
        return create_api_response(
            data={
                "opportunities": normalized_opportunities,
                "count": len(normalized_opportunities),
                "opportunities_found": len(normalized_opportunities),
                "total_analyzed": len(watchlist_symbols),
                "errors_count": len(errors),
                "errors": errors[:5],  # Limit error details
                "cached": False,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        trading_logger.error_logger.error(
            f"[ERROR] Error in watchlist_opportunities endpoint: {str(e)}"
        )
        log_exception("Watchlist opportunities endpoint", e)
        return create_api_response(error=str(e), status_code=500)
def get_system_metrics():
    """Get basic system metrics"""
    try:
        import psutil
        import platform
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        # Disk usage
        disk = psutil.disk_usage("/")
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        # System info
        system_info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "architecture": platform.machine(),
        }
        # Process info
        process = psutil.Process()
        process_memory_mb = process.memory_info().rss / (1024**2)
        process_cpu_percent = process.cpu_percent()
        return {
            "status": "ok",
            "cpu": {
                "system_percent": cpu_percent,
                "process_percent": process_cpu_percent,
            },
            "memory": {
                "system_percent": memory_percent,
                "system_used_gb": round(memory_used_gb, 2),
                "system_total_gb": round(memory_total_gb, 2),
                "process_mb": round(process_memory_mb, 2),
            },
            "disk": {
                "percent": disk_percent,
                "used_gb": round(disk_used_gb, 2),
                "total_gb": round(disk_total_gb, 2),
            },
            "system": system_info,
            "uptime": {
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            },
        }
    except Exception as e:
        log_error(f"Error getting system metrics: {str(e)}")
        return {"status": "error", "error": str(e)}
@app.route("/api/go_services/health")
def go_services_health():
    """Get health status of Go microservices - DISABLED"""
    return create_api_response(
        data={
            "go_services_enabled": False,
            "services": {},
            "overall_health": "disabled",
            "message": "Go services are not implemented in this version",
        }
    )
# system_status route moved to routes/system_routes.py
# logs route moved to routes/page_routes.py
# System status endpoint moved to system_routes.py blueprint
@app.route("/api/preload_stock_data", methods=["POST"])
def trigger_preload_stock_data():
    """Manually trigger preload_stock_data job"""
    try:
        print("[DEBUG] Manual trigger of preload_stock_data requested")
        preload_stock_data()
        return jsonify({
            "status": "success",
            "message": "Preload stock data job completed successfully",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        print(f"[ERROR] Failed to trigger preload_stock_data: {e}")
        return jsonify({
            "status": "error",
            "message": f"Failed to trigger preload_stock_data: {str(e)}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 500
@app.route("/api/historical_data/update", methods=["POST"])
def trigger_historical_data_update():
    """Manually trigger historical data update job"""
    try:
        from src.data.historical_data_updater import update_historical_data_job
        # Run the update job
        result = update_historical_data_job()
        if result["status"] == "success":
            return jsonify({
                "status": "success",
                "message": f"Historical data update completed: {result['updated_count']} symbols updated",
                "details": result,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Historical data update failed: {result['message']}",
                "details": result,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }), 500
    except Exception as e:
        log_error(f"Error triggering historical data update: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to trigger historical data update: {str(e)}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 500
@app.route("/api/news_services/status", methods=["GET"])
def get_news_services_status():
    """Get status of all news services"""
    try:
        # Test actual API functionality instead of just checking placeholder
        # values
        finnhub_working = True
        reddit_working = True
        yahoo_working = True
        alpha_vantage_working = True
        # Test Finnhub API
        try:
            test_news = data_fetcher.get_company_news("AAPL", days_back=1)
            finnhub_working = len(test_news) > 0
        except Exception:
            finnhub_working = False
        # Test Reddit API
        try:
            test_reddit = data_fetcher.get_reddit_news("AAPL", limit=1)
            reddit_working = len(test_reddit) > 0
        except Exception:
            reddit_working = False
        # Test Yahoo Finance API
        try:
            test_yahoo = data_fetcher.get_yahoo_finance_news("AAPL", limit=1)
            yahoo_working = len(test_yahoo) > 0
        except Exception:
            yahoo_working = False
        # Test Alpha Vantage API
        try:
            test_alpha = data_fetcher.get_alpha_vantage_news("AAPL", limit=1)
            alpha_vantage_working = len(test_alpha) > 0
        except Exception:
            alpha_vantage_working = False
        services_status = {
            "finnhub_news": {
                "name": "Finnhub News API",
                "enabled": True,
                "status": "working" if finnhub_working else "error",
                "description": "Company-specific financial news and earnings reports",
                "category": "financial",
            },
            "yahoo_news": {
                "name": "Yahoo Finance News",
                "enabled": Config.ENABLE_YAHOO_NEWS,
                "status": "working" if yahoo_working else "error",
                "description": "General market news and analysis from Yahoo Finance",
                "category": "financial",
                "cost": "Free",
            },
            "alpha_vantage_news": {
                "name": "Alpha Vantage News",
                "enabled": Config.ENABLE_ALPHA_VANTAGE_NEWS
                and bool(Config.ALPHA_VANTAGE_API_KEY),
                "status": "working" if alpha_vantage_working else "error",
                "description": "Real-time and historical market news with sentiment analysis",
                "category": "financial",
                "cost": "API Key Required",
            },
            "reddit_news": {
                "name": "Reddit Social Sentiment",
                "enabled": True,
                "status": "working" if reddit_working else "error",
                "description": "Social sentiment from r/stocks, r/investing, r/wallstreetbets",
                "category": "social",
            },
            "reddit_options_news": {
                "name": "Reddit Options Sentiment",
                "enabled": True,
                "status": "working" if reddit_working else "error",
                "description": "Options-specific discussions from r/options, r/thetagang",
                "category": "options",
            },
            "crypto_news": {
                "name": "Crypto News Sources",
                "enabled": True,
                "status": "working",
                "description": "Finnhub crypto news + Reddit crypto communities",
                "category": "crypto",
            },
            "news_api": {
                "name": "NewsAPI.org",
                "enabled": False,
                "status": "coming_soon",
                "description": "Global financial news aggregation (Future Enhancement)",
                "category": "financial",
                "cost": "API Key Required",
            },
        }
        return jsonify(
            {
                "services": services_status,
                "total_services": len(services_status),
                "active_services": len(
                    [s for s in services_status.values() if s["enabled"]]
                ),
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/news_services/toggle", methods=["POST"])
def toggle_news_service():
    """Toggle a news service on/of"""
    try:
        data = request.get_json()
        service_id = data.get("service_id")
        enabled = data.get("enabled", False)
        if not service_id:
            return create_api_response(error="Service ID is required", status_code=400)
        # For now, we'll just return success since the actual implementation
        # would require modifying the data fetcher configuration
        # In a production system, this would update a database or config file
        return create_api_response(
            data={"service_id": service_id, "enabled": enabled},
            message="News service {service_id} {'enabled' if enabled else 'disabled'}",
        )
    except Exception as e:
        log_exception("Toggle news service endpoint", e)
        return create_api_response(error=str(e), status_code=500)
@app.route("/api/news_services/test", methods=["POST"])
def test_news_service():
    """Test a specific news service"""
    try:
        data = request.get_json()
        if not data or "service_id" not in data:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Missing required parameter: service_id",
                    }
                ),
                400,
            )
        service_id = data["service_id"]
        if service_id == "finnhub_news":
            # Test Finnhub news
            news = data_fetcher.get_company_news("AAPL", days_back=1)
            return jsonify(
                {
                    "success": True,
                    "message": "Finnhub API working - fetched {len(news)} articles",
                    "articles_count": len(news),
                }
            )
        elif service_id == "yahoo_news":
            # Test Yahoo Finance news
            news = data_fetcher.get_yahoo_finance_news("AAPL", limit=5)
            return jsonify(
                {
                    "success": True,
                    "message": "Yahoo Finance API working - fetched {len(news)} articles",
                    "articles_count": len(news),
                }
            )
        elif service_id == "alpha_vantage_news":
            # Test Alpha Vantage news
            news = data_fetcher.get_alpha_vantage_news("AAPL", limit=5)
            return jsonify(
                {
                    "success": True,
                    "message": "Alpha Vantage API working - fetched {len(news)} articles",
                    "articles_count": len(news),
                }
            )
        elif service_id == "reddit_news":
            # Test Reddit news
            news = data_fetcher.get_reddit_news("AAPL", limit=1)
            return jsonify(
                {
                    "success": True,
                    "message": "Reddit API working - fetched {len(news)} posts",
                    # Changed from posts_count to articles_count
                    "articles_count": len(news),
                }
            )
        else:
            return (
                jsonify({"success": False, "message": "Unknown service: {service_id}"}),
                400,
            )
    except Exception as e:
        log_error("Error testing news service: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
@app.route("/api/news_services/config", methods=["GET"])
def get_news_services_config():
    """Get news services configuration status"""
    try:
        # Test actual API functionality
        finnhub_configured = True
        reddit_configured = True
        # Test Finnhub API
        try:
            test_news = data_fetcher.get_company_news("AAPL", days_back=1)
            finnhub_configured = len(test_news) > 0
        except Exception:
            finnhub_configured = False
        # Test Reddit API
        try:
            test_reddit = data_fetcher.get_reddit_news("AAPL", limit=1)
            reddit_configured = len(test_reddit) > 0
        except Exception:
            reddit_configured = False
        config_status = {
            "finnhub_api_key": {
                "configured": finnhub_configured,
                "description": "Required for company news and financial data",
            },
            "reddit_credentials": {
                "configured": reddit_configured,
                "description": "Required for social sentiment analysis",
            },
            "yahoo_finance": {
                "configured": True,  # Public API
                "description": "Public API - no key required",
            },
        }
        return jsonify(
            {"configurations": config_status, "timestamp": datetime.now().isoformat()}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/performance_status")
def performance_status():
    """Get system performance status"""
    try:
        # Get database stats if available
        db_stats = {"status": "unavailable"}
        try:
            from src.core.database import get_database_stats
            db_stats = get_database_stats()
        except Exception:
            logging.error("Error getting database stats: {str(e)}")
        # Get cache stats
        cache_stats = {"status": "unavailable"}
        try:
            cache_stats = get_cache_stats()
        except Exception:
            logging.error("Error getting cache stats: {str(e)}")
        # Get system metrics
        system_metrics = get_system_metrics()
        # Get application config
        config_info = {
            # Tier management removed - will be rebuilt from scratch
            "telegram_enabled": telegram_alerter.is_enabled(),
            "cache_enabled": (
                Config.ENABLE_CACHE if hasattr(Config, "ENABLE_CACHE") else False
            ),
            "debug_mode": app.debug,
            "version": "1.0.0",
        }
        return jsonify(
            {
                "status": "ok",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "system": system_metrics,
                "database": db_stats,
                "cache": cache_stats,
                "config": config_info,
            }
        )
    except Exception as e:
        logging.error("Error getting performance status: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500
@app.route("/api/enhanced_analysis", methods=["POST"])
@log_user_actions(trading_logger)
@log_timing(trading_logger)
def enhanced_analysis():
    """Enhanced stock analysis with multiple strategies and backtesting"""
    try:
        data = request.get_json()
        trading_logger.api_logger.info(
            f"[DEBUG] Incoming /api/enhanced_analysis request: {data}"
        )
        if not data or "symbol" not in data:
            trading_logger.api_logger.info(
                f"[DEBUG] /api/enhanced_analysis missing symbol: {data}"
            )
            return create_api_response(
                error="Missing required parameter: symbol", status_code=400
            )
        symbol = data["symbol"].strip().upper()
        if not symbol:
            trading_logger.api_logger.info(
                f"[DEBUG] /api/enhanced_analysis empty symbol: {data}"
            )
            return create_api_response(error="Symbol cannot be empty", status_code=400)
        # Check rate limits
        if not check_rate_limit("enhanced_analysis"):
            trading_logger.api_logger.info(
                f"[DEBUG] /api/enhanced_analysis rate limit hit: {data}"
            )
            return create_api_response(
                error="Rate limit exceeded. Please try again later.", status_code=429
            )
        def emit_progress(step, message):
            """Emit progress updates via WebSocket"""
            socketio.emit(
                "analysis_progress",
                {
                    "step": step,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                },
            )
        try:
            emit_progress(1, "Fetching market data...")
            price_data = data_fetcher.get_stock_price(symbol)
            if not price_data or "current_price" not in price_data:
                trading_logger.api_logger.info(
                    f"[DEBUG] /api/enhanced_analysis missing price data: {price_data}"
                )
                return create_api_response(
                    error=f"Could not fetch price data for {symbol}", status_code=400
                )
            emit_progress(2, "Gathering news data...")
            news_data = data_fetcher.get_company_news(symbol)
            if not news_data:
                trading_logger.api_logger.info(
                    f"[DEBUG] /api/enhanced_analysis missing news data: {news_data}"
                )
                return create_api_response(
                    error=f"Could not fetch news data for {symbol}", status_code=400
                )
            emit_progress(3, "Analyzing sentiment...")
            sentiment_data = sentiment_analyzer.analyze_news_sentiment(
                news_data, symbol=symbol
            )
            emit_progress(4, "Generating trading signals...")
            signal_data = sentiment_analyzer.get_trading_signal(sentiment_data)
            emit_progress(5, "Generating comprehensive recommendations...")
            recommendations = (
                enhanced_trading_strategy.get_comprehensive_recommendations(
                    symbol, price_data["current_price"], sentiment_data, signal_data
                )
            )
            emit_progress(6, "Finalizing analysis...")
            response_data = {
                "symbol": symbol,
                "price_data": price_data,
                "sentiment_analysis": sentiment_data,
                "news_count": len(news_data),
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat(),
            }
            cache_result(f"enhanced_{symbol}", response_data)
            response = {
                "status": "success",
                "data": response_data,
                "cache_status": "miss",
                "timestamp": datetime.now().isoformat(),
            }
            trading_logger.api_logger.info(
                f"[DEBUG] /api/enhanced_analysis response: {response}"
            )
            return jsonify(response)
        except Exception as e:
            trading_logger.api_logger.error(
                f"[DEBUG] /api/enhanced_analysis error: {str(e)}", exc_info=True
            )
            return create_api_response(error=str(e), status_code=500)
    except Exception as e:
        trading_logger.api_logger.error(
            f"[DEBUG] /api/enhanced_analysis error: {str(e)}", exc_info=True
        )
        return create_api_response(error=str(e), status_code=500)
@app.route("/api/comprehensive_analysis", methods=["POST"])
def comprehensive_analysis():
    """Enhanced analysis with both stock and options recommendations"""
    try:
        data = request.get_json()
        symbol = data.get("symbol", "").upper()
        ai_provider = data.get("ai_provider", "ollama")
        if not symbol:
            return create_api_response(error="Symbol is required", status_code=400)
        # Fetch stock data and news
        price_data = data_fetcher.get_stock_price(symbol)
        if "error" in price_data:
            return create_api_response(error=price_data["error"], status_code=400)
        # Validate price_data is a dictionary with required fields
        if not isinstance(price_data, dict) or "current_price" not in price_data:
            return create_api_response(
                error=f"Invalid price data received for {symbol}: type={type(price_data)}",
                status_code=500,
            )
        news_data = data_fetcher.get_company_news(symbol, days_back=7)
        # Analyze sentiment with fallback to price-based analysis
        sentiment_data = analyze_sentiment_with_fallback(
            news_data, price_data, symbol, ai_provider=ai_provider
        )
        signal_data = sentiment_analyzer.get_trading_signal(sentiment_data)
        # Generate comprehensive recommendations (both stocks and options)
        comprehensive_results = (
            enhanced_trading_strategy.get_comprehensive_recommendations(
                symbol, price_data["current_price"], sentiment_data, signal_data
            )
        )
        return create_api_response(
            data={
                "symbol": symbol,
                "price_data": price_data,
                "sentiment_data": sentiment_data,
                "signal_data": signal_data,
                "comprehensive_recommendations": comprehensive_results,
                "news_count": len(news_data),
                "ai_provider_used": ai_provider,
            }
        )
    except Exception as e:
        log_exception("Comprehensive analysis endpoint", e)
        return create_api_response(error=str(e), status_code=500)
def analyze_sentiment_with_fallback(news_data, price_data, symbol, ai_provider=None):
    """
    Analyze sentiment with fallback to price-based analysis when no news articles are available.
    Args:
        news_data: List of news articles
        price_data: Dictionary containing price information
        symbol: Stock symbol for context
        ai_provider: AI provider to use for news sentiment analysis
    Returns:
        Dict: Sentiment analysis result with news_sentiment field
    """
    try:
        # First try news-based sentiment analysis
        if news_data and len(news_data) > 0:
            print(f"🔍 Analyzing {symbol} using news sentiment...")
            if isinstance(ai_provider, str):
                sentiment_result = sentiment_analyzer.analyze_news_sentiment(
                    news_data, ai_provider=ai_provider, symbol=symbol
                )
            else:
                sentiment_result = sentiment_analyzer.analyze_news_sentiment(
                    news_data, symbol=symbol
                )
            # Add news_sentiment field to indicate news was used
            sentiment_result["news_sentiment"] = sentiment_result["sentiment_score"]
            sentiment_result["has_news"] = True
            return sentiment_result
        else:
            # Fallback to price-based sentiment analysis
            print(
                f"📊 No news articles for {symbol}, using price-based sentiment analysis..."
            )
            sentiment_result = sentiment_analyzer.analyze_price_based_sentiment(
                price_data, symbol
            )
            # Add news_sentiment field as 0 to indicate no news was used
            sentiment_result["news_sentiment"] = 0.0
            sentiment_result["has_news"] = False
            return sentiment_result
    except Exception as e:
        # If news sentiment fails, try price-based analysis
        if "No news articles provided for analysis" in str(
            e
        ) or "No valid news content found" in str(e):
            print(
                f"📊 News analysis failed for {symbol}, falling back to price-based analysis..."
            )
            try:
                sentiment_result = sentiment_analyzer.analyze_price_based_sentiment(
                    price_data, symbol
                )
                # Add news_sentiment field as 0 to indicate no news was used
                sentiment_result["news_sentiment"] = 0.0
                sentiment_result["has_news"] = False
                return sentiment_result
            except Exception as price_error:
                print(
                    f"❌ Price-based analysis also failed for {symbol}: {price_error}"
                )
                # Return neutral sentiment as last resort
                return {
                    "sentiment_score": 0.0,
                    "confidence": 0.3,
                    "summary": f"Analysis failed for {symbol}",
                    "reasoning": f"Both news and price analysis failed: {str(e)}",
                    "provider": "fallback",
                    "analysis_type": "error",
                    "news_sentiment": 0.0,
                    "has_news": False,
                }
        else:
            # Re-raise other types of errors
            raise e
def analyze_single_stock(symbol):
    """Analyze a single stock and return the results"""
    print(
        f"[DEBUG] analyze_single_stock called for {symbol} from API context"
    )  # ADDED DEBUG
    # Get stock price data
    price_data = data_fetcher.get_stock_price(symbol)
    print(
        f"🔍 DEBUG price_data for {symbol}: type={type(price_data)}, value={price_data}"
    )
    if "error" in price_data:
        return {
            "error": f"Failed to get price data for {symbol}: {price_data['error']}"
        }
    if not isinstance(price_data, dict) or "current_price" not in price_data:
        return {
            "error": f"Invalid price data received for {symbol}: type={type(price_data)}, keys={list(price_data.keys()) if isinstance(price_data, dict) else 'not dict'}"
        }
    # Get news data from different sources
    news_data = []
    # Get Finnhub news
    try:
        finnhub_news = data_fetcher.get_company_news(symbol)
        if not isinstance(finnhub_news, list):
            print(
                f"[WARN] finnhub_news is not a list: {type(finnhub_news)}; value={finnhub_news}"
            )
            finnhub_news = []
        print(f"✅ Got {len(finnhub_news)} Finnhub news articles for {symbol}")
        news_data.extend(finnhub_news)
    except Exception as e:
        print(f"[ERROR] Failed to get Finnhub news for {symbol}: {str(e)}")
        finnhub_news = []
    # Get Yahoo Finance news
    try:
        yahoo_news = data_fetcher.get_yahoo_finance_news(symbol)
        if not isinstance(yahoo_news, list):
            print(
                f"[WARN] yahoo_news is not a list: {type(yahoo_news)}; value={yahoo_news}"
            )
            yahoo_news = []
        print(f"✅ Got {len(yahoo_news)} Yahoo Finance news articles for {symbol}")
        news_data.extend(yahoo_news)
    except Exception as e:
        print(f"[ERROR] Failed to get Yahoo Finance news for {symbol}: {str(e)}")
        yahoo_news = []
    # Get Alpha Vantage news
    try:
        alpha_news = data_fetcher.get_alpha_vantage_news(symbol)
        if not isinstance(alpha_news, list):
            print(
                f"[WARN] alpha_news is not a list: {type(alpha_news)}; value={alpha_news}"
            )
            alpha_news = []
        print(f"✅ Got {len(alpha_news)} Alpha Vantage news articles for {symbol}")
        news_data.extend(alpha_news)
    except Exception as e:
        print(f"[ERROR] Failed to get Alpha Vantage news for {symbol}: {str(e)}")
        alpha_news = []
    # Get Reddit news
    try:
        reddit_news = data_fetcher.get_reddit_news(symbol)
        if not isinstance(reddit_news, list):
            print(
                f"[WARN] reddit_news is not a list: {type(reddit_news)}; value={reddit_news}"
            )
            reddit_news = []
        print(f"✅ Got {len(reddit_news)} Reddit posts for {symbol}")
        news_data.extend(reddit_news)
    except Exception as e:
        print(f"[ERROR] Failed to get Reddit news for {symbol}: {str(e)}")
        reddit_news = []
    print(
        f"[DEBUG] News source counts: finnhub={len(finnhub_news)}, yahoo={len(yahoo_news)}, alpha={len(alpha_news)}, reddit={len(reddit_news)}"
    )
    if not news_data:
        print(
            f"📊 No news data available for {symbol}, using price-based sentiment analysis..."
        )
    log_info("🔍 Using Ollama (local) for sentiment analysis...")
    sentiment_result = analyze_sentiment_with_fallback(news_data, price_data, symbol)
    print(
        f"🔍 DEBUG: sentiment_result type: {type(sentiment_result)}, value: {sentiment_result}"
    )
    if not isinstance(sentiment_result, dict):
        print(
            f"[ERROR] sentiment_result is not a dict: {type(sentiment_result)} - {sentiment_result}"
        )
        return {
            "error": f"Sentiment analysis returned invalid data type: {type(sentiment_result)}"
        }
    try:
        signal_data = sentiment_analyzer.get_trading_signal(sentiment_result)
        print(f"🔍 DEBUG: signal_data type: {type(signal_data)}, value: {signal_data}")
    except (TypeError, ValueError) as e:
        print(f"[ERROR] get_trading_signal failed for {symbol}: {str(e)}")
        return {"error": f"Trading signal generation failed: {str(e)}"}
    if not isinstance(signal_data, dict):
        print(f"[ERROR] signal_data is not a dict: {type(signal_data)} - {signal_data}")
        return {
            "error": f"Trading signal returned invalid data type: {type(signal_data)}"
        }
    trading_recommendation = trading_strategy.get_recommendation(
        symbol, price_data, sentiment_result, signal_data
    )
    # Add position recommendations and day trading notes to the trading recommendation
    if isinstance(trading_recommendation, dict):
        if "position_recommendations" not in trading_recommendation:
            trading_recommendation["position_recommendations"] = {
                "$1000": {
                    "contracts": 1,
                    "total_cost": price_data.get("current_price", 0) * 100,
                    "risk_percent": 5.0,
                    "risk_reward_ratio": 2.0,
                }
            }
        # Fix any template variables in position_recommendations
        if "position_recommendations" in trading_recommendation and isinstance(
            trading_recommendation["position_recommendations"], dict
        ):
            fixed_recommendations = {}
            for key, value in trading_recommendation[
                "position_recommendations"
            ].items():
                # Replace template variables in keys
                fixed_key = key
                if "${amount}" in key:
                    fixed_key = "$1000"
                fixed_recommendations[fixed_key] = value
            trading_recommendation["position_recommendations"] = fixed_recommendations
        if "day_trading_notes" not in trading_recommendation:
            trading_recommendation["day_trading_notes"] = [
                f"Current price: ${price_data.get('current_price', 0)}",
                f"Sentiment score: {sentiment_result.get('sentiment_score', 0)}",
                f"Confidence: {sentiment_result.get('confidence', 0)}",
                "Watch for market volatility",
            ]
        # Fix any template variables in day_trading_notes
        if "day_trading_notes" in trading_recommendation and isinstance(
            trading_recommendation["day_trading_notes"], list
        ):
            fixed_notes = []
            for note in trading_recommendation["day_trading_notes"]:
                # Replace common template variables
                note = note.replace(
                    "{strategy_type}",
                    trading_recommendation.get("strategy_type", "Standard"),
                )
                note = note.replace(
                    "{self._get_conviction_level(sentiment_score)}", "Moderate"
                )
                fixed_notes.append(note)
            trading_recommendation["day_trading_notes"] = fixed_notes
    print(
        f"🔍 DEBUG: trading_recommendation type: {type(trading_recommendation)}, value: {trading_recommendation}"
    )
    print(
        f"🔍 DEBUG: target_gain_percent = {trading_recommendation.get('target_gain_percent', 'NOT FOUND')}, stop_loss_percent = {trading_recommendation.get('stop_loss_percent', 'NOT FOUND')}"
    )
    if not isinstance(trading_recommendation, dict):
        print(
            f"[ERROR] trading_recommendation is not a dict: {type(trading_recommendation)} - {trading_recommendation}"
        )
        return {
            "error": f"Trading recommendation returned invalid data type: {type(trading_recommendation)}"
        }
    # Generate options recommendation using OptionsStrategy
    try:
        from src.trading.enhanced_trading_strategy import OptionsStrategy
        print(
            f"[DEBUG] Successfully imported OptionsStrategy for {symbol}"
        )  # ADDED DEBUG
        options_strategy = OptionsStrategy()
        print(
            f"[DEBUG] Successfully created OptionsStrategy instance for {symbol}"
        )  # ADDED DEBUG
        options_recommendation = options_strategy.get_recommendation(
            symbol, price_data, sentiment_result, signal_data
        )
        print(
            f"🔍 DEBUG: options_recommendation type: {type(options_recommendation)}, value: {options_recommendation}"
        )
    except Exception as e:
        print(
            f"[ERROR] Failed to generate options recommendation for {symbol}: {str(e)}"
        )
        traceback.print_exc()  # ADDED DEBUG
        options_recommendation = {
            "symbol": symbol,
            "action": "HOLD",
            "recommendation": "Options analysis failed",
            "reasoning": f"Error generating options recommendation: {str(e)}",
            "confidence": 0.0,
        }
    # Instead of nesting recommendations, merge the trading recommendation directly into the result
    # This will make it easier for the frontend to access the data
    result = {
        "symbol": symbol,
        "current_price": price_data.get("current_price", 0),
        "news_count": len(news_data),
        "news_sources": {
            "finnhub": len(finnhub_news),
            "yahoo_finance": len(yahoo_news),
            "alpha_vantage": len(alpha_news),
            "reddit": len(reddit_news),
        },
        "sentiment_score": sentiment_result.get("sentiment_score", 0),
        "confidence": sentiment_result.get("confidence", 0),
        "action": trading_recommendation.get("action", "HOLD"),
        "option_type": trading_recommendation.get("option_type", ""),
        "strike_price": trading_recommendation.get("strike_price", 0),
        "days_to_expiry": trading_recommendation.get("days_to_expiry", 0),
        "option_price": trading_recommendation.get("option_price", 0),
        "target_gain": trading_recommendation.get("target_gain_percent", ""),
        "stop_loss": trading_recommendation.get("stop_loss_percent", ""),
        "position_size": trading_recommendation.get("position_size", 0),
        "strategy_type": trading_recommendation.get("strategy_type", ""),
        "reasoning": trading_recommendation.get("reasoning", ""),
        "position_recommendations": trading_recommendation.get(
            "position_recommendations", {}
        ),
        "day_trading_notes": trading_recommendation.get("day_trading_notes", []),
        "timestamp": datetime.now().isoformat(),
    }
    print(f"🔍 DEBUG: Final result keys: {list(result.keys())}")
    print(
        f"🔍 DEBUG: options_recommendation in result: {'options_recommendation' in result}"
    )
    return result
def analyze_stock_batch(symbols):
    """Analyze multiple stocks in a batch"""
    results = []
    for symbol in symbols:
        try:
            result = analyze_single_stock(symbol)
            results.append(result)
        except Exception as e:
            log_error(f"Error analyzing stock {symbol}: {str(e)}")
            results.append({"symbol": symbol, "error": str(e), "status": "failed"})
    return results
def check_rate_limit(endpoint):
    """Check rate limit for a given endpoint"""
    # Implement rate limiting logic based on your requirements
    # For example, you can use a simple counter or a more sophisticated algorithm
    # to track and limit the number of requests per time unit
    return True
def create_app(port=5001):
    """
    Create and start the Flask application
    Args:
        port (int): Port number to run the server on (default: 5001)
    """
    print(f"[DEBUG] Entered create_app() with port={port}")
    try:
        from src.core.logger import log_info, log_system_event
        log_info(f"Starting Flask application on port {port}", "system")
        log_system_event(f"Flask application starting on port {port}", "INFO")
        # Start job scheduler in background thread
        def start_job_scheduler():
            try:
                from start_app import run_scheduled_jobs
                print("[DEBUG] Starting job scheduler in background...")
                run_scheduled_jobs()
            except Exception as e:
                print(f"[DEBUG] Job scheduler failed to start: {e}")
        scheduler_thread = threading.Thread(target=start_job_scheduler, daemon=True)
        scheduler_thread.start()
        print(f"[DEBUG] About to start socketio.run() on 0.0.0.0:{port}")
        sys.stdout.flush()
        # Start the SocketIO server
        socketio.run(
            app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True
        )
        print(
            "[DEBUG] socketio.run() has exited (should not happen unless server stops)"
        )
        sys.stdout.flush()
    except Exception as e:
        print(f"[DEBUG] Exception in create_app: {e}")
        from src.core.logger import log_exception
        log_exception(f"Failed to start Flask application on port {port}", e)
        sys.stdout.flush()
# Global cache for preloaded data
preloaded_data = None
preload_timestamp = None
# API tracking is now handled by the dedicated api_tracker module
# Function to preload data
def preload_stock_data():
    print("[DEBUG] Starting background preload_stock_data()")
    sys.stdout.flush()
    
    try:
        # Get the raw Alpha Vantage data directly
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TOP_GAINERS_LOSERS",
            "apikey": Config.ALPHA_VANTAGE_API_KEY,
        }
        
        try:
            import requests
            response = requests.get(url, params=params)
            if response.status_code == 200:
                alpha_data = response.json()
                print(f"[DEBUG] Got raw Alpha Vantage data")
                
                # Process top 3 gainers directly from Alpha Vantage
                gainers = []
                top_gainers = alpha_data.get("top_gainers", [])[:3]  # Take top 3
                for gainer in top_gainers:
                    ticker = gainer.get("ticker")
                    gainers.append({
                        "symbol": ticker,
                        "type": "GAINER",
                        "price": float(gainer.get("price", 0)),
                        "change_amount": 0,
                        "change_percent": float(str(gainer.get("change_percentage", 0)).replace('%', '')),
                        "volume": int(gainer.get("volume", 0)),
                        "timestamp": datetime.now(),
                        "analysis_data": gainer
                    })
                    print(f"[DEBUG] Added gainer: {ticker} - {gainer.get('change_percentage')}% at ${gainer.get('price')}")
                
                # Process top 3 losers directly from Alpha Vantage
                losers = []
                top_losers = alpha_data.get("top_losers", [])[:3]  # Take top 3
                for loser in top_losers:
                    ticker = loser.get("ticker")
                    losers.append({
                        "symbol": ticker,
                        "type": "LOSER",
                        "price": float(loser.get("price", 0)),
                        "change_amount": 0,
                        "change_percent": float(str(loser.get("change_percentage", 0)).replace('%', '')),
                        "volume": int(loser.get("volume", 0)),
                        "timestamp": datetime.now(),
                        "analysis_data": loser
                    })
                    print(f"[DEBUG] Added loser: {ticker} - {loser.get('change_percentage')}% at ${loser.get('price')}")
                
                print(f"[DEBUG] Processed {len(gainers)} gainers and {len(losers)} losers from Alpha Vantage data")
            else:
                print(f"[ERROR] Failed to get raw Alpha Vantage data: {response.status_code}")
                gainers = []
                losers = []
        except Exception as e:
            print(f"[ERROR] Exception getting raw Alpha Vantage data: {e}")
            gainers = []
            losers = []
        
        # Save to market_movers table using the current table structure
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Clear existing data
                    cur.execute("DELETE FROM market_movers")
                    # Insert gainers
                    for gainer in gainers:
                        cur.execute("""
                            INSERT INTO market_movers (symbol, type, price, change_amount, change_percent, volume, timestamp, analysis_data)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            gainer.get('symbol', ''),
                            'GAINER',
                            gainer.get('price', 0),
                            gainer.get('change_amount', 0),
                            gainer.get('change_percent', 0),
                            gainer.get('volume', 0),
                            datetime.now(),
                            json.dumps(gainer.get('analysis_data', {}))
                        ))
                    # Insert losers
                    for loser in losers:
                        cur.execute("""
                            INSERT INTO market_movers (symbol, type, price, change_amount, change_percent, volume, timestamp, analysis_data)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            loser.get('symbol', ''),
                            'LOSER',
                            loser.get('price', 0),
                            loser.get('change_amount', 0),
                            loser.get('change_percent', 0),
                            loser.get('volume', 0),
                            datetime.now(),
                            json.dumps(loser.get('analysis_data', {}))
                        ))
                    conn.commit()
                    print(f"[DEBUG] Successfully saved {len(gainers)} gainers and {len(losers)} losers to market_movers table")
        except Exception as e:
            print(f"[ERROR] Failed to save to market_movers table: {e}")
        
        print(f"[DEBUG] Processed {len(gainers)} gainers and {len(losers)} losers for market_movers table")
        print("[DEBUG] Finished background preload_stock_data()")
    except Exception as e:
        print(f"[ERROR] Exception in preload_stock_data: {str(e)}")
        sys.stdout.flush()
# Schedule the preload task
scheduler = BackgroundScheduler()
# Run at 9:35 AM on trading days for S&P 500
scheduler.add_job(
    preload_stock_data,
    "cron",
    day_of_week="mon-fri",
    hour=9,
    minute=35,
    timezone="America/New_York",
)
# Run at 9:40 AM on trading days for news-driven opportunities
from ..data.preload_news_opportunities import preload_news_opportunities
scheduler.add_job(
    preload_news_opportunities,
    "cron",
    day_of_week="mon-fri",
    hour=9,
    minute=40,
    timezone="America/New_York",
)
# Run at 9:45 AM on trading days for watchlist opportunities
from ..data.preload_watchlist_opportunities import preload_watchlist_opportunities
scheduler.add_job(
    preload_watchlist_opportunities,
    "cron",
    day_of_week="mon-fri",
    hour=9,
    minute=45,
    timezone="America/New_York",
)
# Scalping analysis is now handled by the database-configured job scheduler
scheduler.start()
# Preload data in a background thread on startup (do NOT block main thread)
def start_preload_in_background():
    preload_thread = threading.Thread(target=preload_stock_data, daemon=True)
    preload_thread.start()
    # Also preload news-driven opportunities
    preload_news_thread = threading.Thread(
        target=preload_news_opportunities, daemon=True
    )
    preload_news_thread.start()
    # Also preload watchlist opportunities
    preload_watchlist_thread = threading.Thread(
        target=preload_watchlist_opportunities, daemon=True
    )
    preload_watchlist_thread.start()
start_preload_in_background()
@app.route("/api/preloaded_data")
def get_preloaded_data():
    """Endpoint to get preloaded stock data directly from database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get the most recent timestamp
                cur.execute("""
                    SELECT timestamp FROM market_movers 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                row = cur.fetchone()
                if row:
                    timestamp = row["timestamp"]
                    # Get all market movers, ordered by type (gainers first) and change_percent (desc)
                    cur.execute("""
                        SELECT symbol, type, price, change_amount, change_percent, volume, analysis_data 
                        FROM market_movers
                        ORDER BY 
                            CASE WHEN type = 'GAINER' THEN 0 ELSE 1 END,
                            ABS(change_percent) DESC
                    """)
                    rows = cur.fetchall()
                    enhanced_analysis = []
                    for row in rows:
                        symbol = row["symbol"]
                        type_val = row["type"]
                        price = row["price"]
                        change_amount = row["change_amount"]
                        change_percent = row["change_percent"]
                        volume = row["volume"]
                        analysis_data = row["analysis_data"]
                        # Skip stocks with invalid prices (0.0 or None)
                        if not price or float(price) == 0.0:
                            continue
                        # Use the stored analysis_data directly, but ensure it has the required structure
                        if analysis_data and isinstance(analysis_data, dict):
                            # Ensure the analysis_data has the symbol
                            analysis_data["symbol"] = symbol
                            analysis_data["type"] = "Stock"
                            # Ensure price_data is properly structured
                            if "price_data" not in analysis_data:
                                analysis_data["price_data"] = {
                                    "current_price": float(price)
                                    if price is not None
                                    else 0.0,
                                    "change_amount": float(change_amount)
                                    if change_amount is not None
                                    else 0.0,
                                    "change_percent": float(change_percent)
                                    if change_percent is not None
                                    else 0.0,
                                    "volume": int(volume) if volume is not None else 0,
                                }
                            # Ensure sentiment_data exists
                            if "sentiment_data" not in analysis_data:
                                analysis_data["sentiment_data"] = {
                                    "sentiment_score": 0.0,
                                    "confidence": 0.5,
                                }
                            # Ensure signal_data exists
                            if "signal_data" not in analysis_data:
                                analysis_data["signal_data"] = {
                                    "action": "HOLD",
                                    "signal_strength": 0.0,
                                }
                            # Ensure news_count exists
                            if "news_count" not in analysis_data:
                                analysis_data["news_count"] = 0
                            enhanced_analysis.append(analysis_data)
                        else:
                            # Fallback to creating basic structure if analysis_data is missing
                            stock_data = {
                                "symbol": symbol,
                                "type": "Stock",
                                "price_data": {
                                    "current_price": float(price)
                                    if price is not None
                                    else 0.0,
                                    "change_amount": float(change_amount)
                                    if change_amount is not None
                                    else 0.0,
                                    "change_percent": float(change_percent)
                                    if change_percent is not None
                                    else 0.0,
                                    "volume": int(volume) if volume is not None else 0,
                                },
                                "sentiment_data": {
                                    "sentiment_score": 0.0,
                                    "confidence": 0.5,
                                },
                                "signal_data": {
                                    "action": "HOLD",
                                    "signal_strength": 0.0,
                                },
                                "news_count": 0,
                                "timestamp": timestamp.isoformat(),
                            }
                            enhanced_analysis.append(stock_data)
                    opportunities_found = len(
                        [s for s in enhanced_analysis if s.get("change_percent", 0) > 0]
                    )
                    response_data = {
                        "enhanced_analysis": enhanced_analysis,
                        "total_analyzed": len(enhanced_analysis),
                        "opportunities_found": opportunities_found,
                        "timestamp": timestamp.isoformat(),
                        "cache_status": "database_fresh",
                    }
                    return create_api_response(
                        data=response_data,
                        message=f"Successfully loaded {len(enhanced_analysis)} market movers from database",
                    )
                else:
                    return create_api_response(
                        data={
                            "enhanced_analysis": [],
                            "total_analyzed": 0,
                            "opportunities_found": 0,
                            "timestamp": datetime.now().isoformat(),
                            "fallback": True,
                        },
                        message="No market movers found in database",
                        success=False,
                        error="0",
                    )
    except Exception as e:
        print(f"[ERROR] Failed to load preloaded data from database: {e}")
        traceback.print_exc()
        return create_api_response(
            data={
                "enhanced_analysis": [],
                "total_analyzed": 0,
                "opportunities_found": 0,
                "timestamp": datetime.now().isoformat(),
                "fallback": True,
            },
            message=f"Error loading market movers from database: {str(e)}",
            success=False,
            error=str(e),
        )
@app.route("/api/refresh_market_movers", methods=["POST"])
def refresh_market_movers():
    """Trigger full pipeline to refresh market movers data"""
    try:
        print("[INFO] Refresh market movers request received")
        # Run the full pipeline to get fresh market movers
        # This now uses the market_movers table directly via preload_stock_data()
        preload_stock_data()
        # Check if we actually have data in the database
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM market_movers")
                count_result = cur.fetchone()
                count = count_result["count"] if count_result else 0
        if count > 0:
            print(
                f"[INFO] Market movers data refreshed successfully - {count} records in database"
            )
            return jsonify(
                {
                    "success": True,
                    "message": f"Market movers data refreshed successfully - {count} records updated",
                }
            )
        else:
            print("[ERROR] No market movers data found in database after refresh")
            return jsonify(
                {
                    "success": False,
                    "error": "No market movers data found in database after refresh",
                }
            )
    except Exception as e:
        print(f"[ERROR] Error refreshing market movers: {e}")
        traceback.print_exc()
        return jsonify(
            {"success": False, "error": f"Error refreshing market movers: {str(e)}"}
        )
def load_preloaded_data_from_db():
    global preloaded_data, preload_timestamp
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get the most recent timestamp
                cur.execute("""
                    SELECT timestamp FROM market_movers 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                row = cur.fetchone()
                if row:
                    preload_timestamp = row["timestamp"]
                    # Get all market movers
                    cur.execute("""
                        SELECT analysis_data FROM market_movers
                        ORDER BY 
                            CASE WHEN type = 'GAINER' THEN 0 ELSE 1 END,
                            change_percent DESC
                    """)
                    # Reconstruct the data in the expected format
                    enhanced_analysis = [row["analysis_data"] for row in cur.fetchall()]
                    preloaded_data = {
                        "enhanced_analysis": enhanced_analysis,
                        "total_analyzed": len(enhanced_analysis),
                        "opportunities_found": len(
                            [
                                s
                                for s in enhanced_analysis
                                if s.get("change_percent", 0) > 0
                            ]
                        ),
                        "timestamp": preload_timestamp.isoformat(),
                        "status": "success",
                    }
                    log_info(
                        f"Loaded {len(enhanced_analysis)} market movers from database into preloaded_data",
                        "system",
                    )
                    log_info(
                        f"preloaded_data keys: {list(preloaded_data.keys())}", "system"
                    )
                    log_info(
                        f"enhanced_analysis length: {len(enhanced_analysis)}", "system"
                    )
                else:
                    log_info("No market movers found in database", "system")
                    preloaded_data = None
    except Exception as e:
        log_exception("Failed to load preloaded data from database", e)
        preloaded_data = None
@app.route("/api/logs", methods=["GET"])
def get_logs():
    """
    Retrieve logs from the database with filtering and pagination
    Query params:
    - limit: max number of logs to return (default: 100)
    - level: filter by log level (e.g., ERROR, INFO, etc.)
    - category: filter by log category
    - search: text search in log message
    """
    try:
        # Get query parameters
        limit = min(int(request.args.get("limit", 100)), 1000)  # Max 1000 logs
        level = request.args.get("level")
        category = request.args.get("category")
        search = request.args.get("search")
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Base query
                query = """
                    SELECT 
                        id, 
                        timestamp, 
                        level, 
                        logger, 
                        module, 
                        function, 
                        line, 
                        message, 
                        exception,
                        traceback,
                        extra,
                        category,
                        session_id
                    FROM logs
                    WHERE 1=1
                """
                params = []
                # Add filters
                if level:
                    query += " AND level = %s"
                    params.append(level.upper())
                if category:
                    query += " AND category = %s"
                    params.append(category)
                if search:
                    query += " AND (message ILIKE %s OR exception::text ILIKE %s)"
                    search_term = f"%{search}%"
                    params.extend([search_term, search_term])
                # Order and limit
                query += " ORDER BY timestamp DESC LIMIT %s"
                params.append(limit)
                # Execute query
                cur.execute(query, params)
                logs = cur.fetchall()
                # Convert datetime to ISO format for JSON serialization
                for log in logs:
                    if "timestamp" in log and log["timestamp"] is not None:
                        log["timestamp"] = log["timestamp"].isoformat()
                # Return logs data
                return create_api_response(
                    {
                        "logs": logs,
                        "total": len(logs),
                        "filters": {
                            "level": level,
                            "category": category,
                            "limit": limit,
                        },
                    }
                )
    except Exception as e:
        log_exception("Logs endpoint", e)
        return create_api_response(error=str(e), status_code=500)
# At startup, load from database before running preload_stock_data
print("=== STARTUP: About to load preloaded data from database ===")
load_preloaded_data_from_db()
print("=== STARTUP: Finished loading preloaded data from database ===")
@app.route("/api/watchlist/config", methods=["GET", "POST"])
def watchlist_config():
    """Get or update watchlist configuration"""
    try:
        log_info(
            f"[WATCHLIST_CONFIG] Incoming {request.method} request from {request.remote_addr}"
        )
        if request.method == "GET":
            # Get current watchlist configuration (stocks and crypto)
            stocks = watchlist_manager.get_stocks()
            cryptos = watchlist_manager.get_cryptos()
            log_info(f"[WATCHLIST_CONFIG] Stocks: {stocks}")
            log_info(f"[WATCHLIST_CONFIG] Cryptos: {cryptos}")
            # Format data for frontend (stocks and crypto)
            stock_data = [{"symbol": symbol, "notes": ""} for symbol in stocks]
            crypto_data = [{"symbol": symbol, "notes": ""} for symbol in cryptos]
            response_data = {
                "stocks": stock_data,
                "crypto": crypto_data,
                "stock_limit": Config.BULK_ANALYSIS_WATCHLIST_LIMIT
                if hasattr(Config, "BULK_ANALYSIS_WATCHLIST_LIMIT")
                else 50,
                "news_days": Config.BULK_ANALYSIS_NEWS_DAYS
                if hasattr(Config, "BULK_ANALYSIS_NEWS_DAYS")
                else 2,
                "stats": {"stocks": stocks, "crypto": cryptos},
                "message": f"Watchlist contains {len(stocks)} stocks and {len(cryptos)} cryptos",
            }
            log_info(f"[WATCHLIST_CONFIG] Response: {response_data}")
            return create_api_response(response_data)
        elif request.method == "POST":
            # Update watchlist configuration (stocks and crypto)
            data = request.get_json()
            action = data.get("action")
            symbol = data.get("symbol", "").upper().strip()
            symbol_type = data.get("type", "stock")  # Default to stock
            if not action or not symbol:
                return create_api_response(
                    success=False,
                    error="Missing required fields: action, symbol",
                    status_code=400,
                )
            if symbol_type == "stock":
                if action == "add":
                    success = watchlist_manager.add_stock(symbol)
                    if success:
                        return create_api_response(
                            {
                                "message": f"Added {symbol} to stock watchlist",
                                "symbol": symbol,
                                "type": "stock",
                            }
                        )
                    else:
                        return create_api_response(
                            success=False,
                            error=f"Failed to add {symbol} to watchlist",
                            status_code=500,
                        )
                elif action == "remove":
                    success = watchlist_manager.remove_stock(symbol)
                    if success:
                        return create_api_response(
                            {
                                "message": f"Removed {symbol} from stock watchlist",
                                "symbol": symbol,
                                "type": "stock",
                            }
                        )
                    else:
                        return create_api_response(
                            success=False,
                            error=f"Failed to remove {symbol} from watchlist",
                            status_code=500,
                        )
                else:
                    return create_api_response(
                        success=False,
                        error="Invalid action. Must be 'add' or 'remove'",
                        status_code=400,
                    )
            elif symbol_type == "crypto":
                if action == "add":
                    success = watchlist_manager.add_crypto(symbol)
                    if success:
                        return create_api_response(
                            {
                                "message": f"Added {symbol} to crypto watchlist",
                                "symbol": symbol,
                                "type": "crypto",
                            }
                        )
                    else:
                        return create_api_response(
                            success=False,
                            error=f"Failed to add {symbol} to crypto watchlist",
                            status_code=500,
                        )
                elif action == "remove":
                    success = watchlist_manager.remove_crypto(symbol)
                    if success:
                        return create_api_response(
                            {
                                "message": f"Removed {symbol} from crypto watchlist",
                                "symbol": symbol,
                                "type": "crypto",
                            }
                        )
                    else:
                        return create_api_response(
                            success=False,
                            error=f"Failed to remove {symbol} from crypto watchlist",
                            status_code=500,
                        )
                else:
                    return create_api_response(
                        success=False,
                        error="Invalid action. Must be 'add' or 'remove'",
                        status_code=400,
                    )
            else:
                return create_api_response(
                    success=False,
                    error="Only stock or crypto symbols are supported",
                    status_code=400,
                )
    except Exception as e:
        log_exception("Error in watchlist config", e)
        return create_api_response(
            success=False,
            error="Failed to manage watchlist configuration",
            status_code=500,
        )
@app.route("/api/logs/export", methods=["GET"])
def export_logs():
    """
    Export logs as JSON or CSV file
    Query params:
    - format: 'json' or 'csv' (default: 'json')
    - limit: max number of logs to export (default: 1000)
    - level: filter by log level
    - category: filter by log category
    - type: filter by log type (alias for category)
    """
    try:
        import csv
        import io
        from datetime import datetime
        # Get query parameters
        export_format = request.args.get("format", "json").lower()
        limit = min(int(request.args.get("limit", 1000)), 10000)  # Max 10,000 logs
        level = request.args.get("level")
        category = request.args.get("category") or request.args.get(
            "type"
        )  # Support both 'category' and 'type'
        if export_format not in ["json", "csv"]:
            return create_api_response(
                success=False,
                error="Invalid format. Use 'json' or 'csv'",
                status_code=400,
            )
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Base query (same as get_logs)
                query = """
                    SELECT 
                        id, 
                        timestamp, 
                        level, 
                        logger, 
                        module, 
                        function, 
                        line, 
                        message, 
                        exception,
                        traceback,
                        extra,
                        category,
                        session_id
                    FROM logs
                    WHERE 1=1
                """
                params = []
                # Add filters
                if level:
                    query += " AND level = %s"
                    params.append(level.upper())
                if category:
                    query += " AND category = %s"
                    params.append(category)
                # Order and limit
                query += " ORDER BY timestamp DESC LIMIT %s"
                params.append(limit)
                # Execute query
                cur.execute(query, params)
                logs = cur.fetchall()
                # Convert datetime to ISO format for JSON serialization
                for log in logs:
                    if "timestamp" in log and log["timestamp"] is not None:
                        log["timestamp"] = log["timestamp"].isoformat()
                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"logs_export_{timestamp}"
                if export_format == "json":
                    # Export as JSON
                    response_data = {
                        "export_info": {
                            "format": "json",
                            "timestamp": datetime.now().isoformat(),
                            "total_logs": len(logs),
                            "filters": {
                                "level": level,
                                "category": category,
                                "limit": limit,
                            },
                        },
                        "logs": logs,
                    }
                    response = make_response(json.dumps(response_data, indent=2))
                    response.headers["Content-Type"] = "application/json"
                    response.headers["Content-Disposition"] = (
                        f'attachment; filename="{filename}.json"'
                    )
                    return response
                elif export_format == "csv":
                    # Export as CSV
                    output = io.StringIO()
                    writer = csv.writer(output)
                    # Write header
                    if logs:
                        headers = list(logs[0].keys())
                        writer.writerow(headers)
                        # Write data rows
                        for log in logs:
                            row = []
                            for header in headers:
                                value = log.get(header, "")
                                # Convert complex objects to string
                                if isinstance(value, (dict, list)):
                                    value = json.dumps(value)
                                row.append(str(value))
                            writer.writerow(row)
                    response = make_response(output.getvalue())
                    response.headers["Content-Type"] = "text/csv"
                    response.headers["Content-Disposition"] = (
                        f'attachment; filename="{filename}.csv"'
                    )
                    return response
    except Exception as e:
        log_exception("Log export endpoint", e)
        return create_api_response(error=str(e), status_code=500)
# At startup, load from database before running preload_stock_data
print("=== STARTUP: About to load preloaded data from database ===")
load_preloaded_data_from_db()
print("=== STARTUP: Finished loading preloaded data from database ===")
@app.route("/recommendations")
def recommendations_page():
    """Main recommendations dashboard page"""
    return render_template("recommendations.html")
recommendation_manager = RecommendationManager()
@app.route("/api/recommendations", methods=["GET"])
def api_recommendations():
    """Paginated, filterable recommendations API"""
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
        symbol = request.args.get("symbol", None)
        recommendation_type = request.args.get("type", None)
        action = request.args.get("action", None)
        outcome = request.args.get("outcome", None)
        offset = (page - 1) * page_size
        filters = []
        params = []
        if symbol:
            filters.append("symbol = %s")
            params.append(symbol.upper())
        if recommendation_type:
            filters.append("recommendation_type = %s")
            params.append(recommendation_type)
        if action:
            filters.append("action = %s")
            params.append(action.upper())
        if outcome:
            if outcome == "profitable":
                filters.append("profitable = TRUE")
            elif outcome == "unprofitable":
                filters.append("profitable = FALSE")
            elif outcome == "pending":
                filters.append("profitable IS NULL")
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        query = f"""
            SELECT id, symbol, recommendation_type, action, timestamp, final_confidence, current_stock_price, actual_outcome, profitable
            FROM recommendations
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
        """
        count_query = f"SELECT COUNT(*) FROM recommendations {where_clause}"
        params_count = list(params)
        params.extend([page_size, offset])
        with recommendation_manager._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                cur.execute(count_query, params_count)
                count_result = cur.fetchone()
                total_count = count_result["count"] if count_result else 0
        # Format results
        recommendations = [
            {
                "id": row["id"],
                "symbol": row["symbol"],
                "recommendation_type": row["recommendation_type"],
                "action": row["action"],
                "timestamp": row["timestamp"],
                "final_confidence": float(row["final_confidence"])
                if row["final_confidence"] is not None
                else None,
                "current_stock_price": float(row["current_stock_price"])
                if row["current_stock_price"] is not None
                else None,
                "actual_outcome": float(row["actual_outcome"])
                if row["actual_outcome"] is not None
                else None,
                "profitable": row["profitable"],
            }
            for row in rows
        ]
        has_more = (offset + len(recommendations)) < total_count
        return jsonify(
            {
                "recommendations": recommendations,
                "total_count": total_count,
                "has_more": has_more,
            }
        )
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Error in api_recommendations: {e}\nTraceback:\n{tb}")
        return jsonify({"error": str(e), "traceback": tb}), 500
@app.route("/api/test_db", methods=["GET"])
def test_db():
    """Test database connection"""
    try:
        with recommendation_manager._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM recommendations")
                count_result = cur.fetchone()
                count = count_result["count"] if count_result else 0
                return jsonify({"success": True, "count": count})
    except Exception as e:
        print(f"Database test error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
@app.route("/api/recommendations/stats", methods=["GET"])
def api_recommendations_stats():
    """Returns comprehensive recommendation statistics"""
    try:
        with recommendation_manager._get_connection() as conn:
            with conn.cursor() as cur:
                # Total recommendations
                cur.execute("SELECT COUNT(*) as count FROM recommendations")
                total_recommendations = cur.fetchone()["count"] or 0
                # Performance metrics
                cur.execute("""
                    SELECT COUNT(*) as total_evaluated, 
                           COUNT(CASE WHEN profitable = TRUE THEN 1 END) as wins,
                           AVG(actual_outcome) as avg_outcome
                    FROM recommendations
                    WHERE actual_outcome IS NOT NULL
                """)
                perf_row = cur.fetchone()
                total_evaluated = perf_row["total_evaluated"] or 0
                wins = perf_row["wins"] or 0
                avg_outcome = (
                    float(perf_row["avg_outcome"])
                    if perf_row["avg_outcome"] is not None
                    else 0.0
                )
                win_rate = (wins / total_evaluated) if total_evaluated > 0 else 0.0
                # Recommendation types
                cur.execute("""
                    SELECT recommendation_type, COUNT(*) as count
                    FROM recommendations
                    GROUP BY recommendation_type
                    ORDER BY count DESC
                """)
                recommendation_types = [
                    {
                        "recommendation_type": r["recommendation_type"],
                        "count": r["count"],
                    }
                    for r in cur.fetchall()
                ]
                # Actions
                cur.execute("""
                    SELECT action, COUNT(*) as count
                    FROM recommendations
                    GROUP BY action
                    ORDER BY count DESC
                """)
                actions = [
                    {"action": r["action"], "count": r["count"]} for r in cur.fetchall()
                ]
                # Top symbols
                cur.execute("""
                    SELECT symbol, COUNT(*) as count
                    FROM recommendations
                    GROUP BY symbol
                    ORDER BY count DESC
                    LIMIT 10
                """)
                top_symbols = [
                    {"symbol": r["symbol"], "count": r["count"]} for r in cur.fetchall()
                ]
                # Symbol performance
                cur.execute("""
                    SELECT symbol, 
                           COUNT(*) as total,
                           COUNT(CASE WHEN profitable = TRUE THEN 1 END) as wins,
                           AVG(actual_outcome) as avg_outcome
                    FROM recommendations
                    WHERE actual_outcome IS NOT NULL
                    GROUP BY symbol
                    HAVING COUNT(*) >= 5
                    ORDER BY AVG(actual_outcome) DESC
                    LIMIT 10
                """)
                symbol_performance = {}
                for r in cur.fetchall():
                    symbol_performance[r["symbol"]] = {
                        "total": r["total"],
                        "wins": r["wins"],
                        "win_rate": (r["wins"] / r["total"]) if r["total"] > 0 else 0.0,
                        "avg_outcome": float(r["avg_outcome"])
                        if r["avg_outcome"] is not None
                        else 0.0,
                    }
                # Recommendation performance by type
                cur.execute("""
                    SELECT recommendation_type, action,
                           COUNT(*) as count,
                           COUNT(CASE WHEN profitable = TRUE THEN 1 END) as wins,
                           AVG(actual_outcome) as avg_outcome
                    FROM recommendations
                    WHERE actual_outcome IS NOT NULL
                    GROUP BY recommendation_type, action
                    HAVING COUNT(*) >= 3
                    ORDER BY AVG(actual_outcome) DESC
                    LIMIT 10
                """)
                recommendation_performance = []
                for r in cur.fetchall():
                    recommendation_performance.append(
                        {
                            "recommendation_type": r["recommendation_type"],
                            "action": r["action"],
                            "count": r["count"],
                            "wins": r["wins"],
                            "win_rate": (r["wins"] / r["count"])
                            if r["count"] > 0
                            else 0.0,
                            "avg_outcome": float(r["avg_outcome"])
                            if r["avg_outcome"] is not None
                            else 0.0,
                        }
                    )
                # Last updated
                cur.execute("SELECT MAX(timestamp) as max FROM recommendations")
                last_updated_row = cur.fetchone()
                last_updated = last_updated_row["max"] if last_updated_row else None
        return jsonify(
            {
                "total_recommendations": total_recommendations,
                "performance": {
                    "total_evaluated": total_evaluated,
                    "wins": wins,
                    "win_rate": win_rate,
                    "avg_outcome": avg_outcome,
                },
                "recommendation_types": recommendation_types,
                "actions": actions,
                "top_symbols": top_symbols,
                "symbol_performance": symbol_performance,
                "recommendation_performance": recommendation_performance,
                "last_updated": last_updated.isoformat() if last_updated else None,
            }
        )
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Error in api_recommendations_stats: {e}\nTraceback:\n{tb}")
        return jsonify({"error": str(e), "traceback": tb}), 500
@app.route("/api/recommendations/metrics", methods=["GET"])
def api_recommendations_metrics():
    """Returns win rate, average return, top 5 symbols, top 3 types by avg return"""
    with recommendation_manager._get_connection() as conn:
        with conn.cursor() as cur:
            # Win rate and average return
            cur.execute("""
                SELECT COUNT(*) as total, 
                       COUNT(CASE WHEN profitable = TRUE THEN 1 END) as wins,
                       AVG(actual_outcome) as avg_return
                FROM recommendations
                WHERE actual_outcome IS NOT NULL
            """)
            row = cur.fetchone()
            total = row[0] or 0
            wins = row[1] or 0
            avg_return = float(row[2]) if row[2] is not None else 0.0
            win_rate = (wins / total) if total > 0 else 0.0
            # Top 5 symbols by frequency
            cur.execute("""
                SELECT symbol, COUNT(*) as freq
                FROM recommendations
                GROUP BY symbol
                ORDER BY freq DESC
                LIMIT 5
            """)
            top_symbols = [{"symbol": r[0], "count": r[1]} for r in cur.fetchall()]
            # Top 3 recommendation types by avg return
            cur.execute("""
                SELECT recommendation_type, AVG(actual_outcome) as avg_ret
                FROM recommendations
                WHERE actual_outcome IS NOT NULL
                GROUP BY recommendation_type
                ORDER BY avg_ret DESC
                LIMIT 3
            """)
            top_types = [
                {
                    "recommendation_type": r[0],
                    "avg_return": float(r[1]) if r[1] is not None else 0.0,
                }
                for r in cur.fetchall()
            ]
    return jsonify(
        {
            "win_rate": win_rate,
            "average_return": avg_return,
            "top_symbols": top_symbols,
            "top_types": top_types,
        }
    )
# Ensure the job_schedules table exists at startup
ensure_job_schedules_table()
@app.route("/api/job_schedules", methods=["GET"])
def get_job_schedules():
    """Return all job schedules."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, job_name, run_time, enabled, last_run, created_at FROM job_schedules ORDER BY job_name"
                )
                rows = cur.fetchall()
                schedules = [
                    {
                        "id": row["id"],
                        "job_name": row["job_name"],
                        "run_time": str(row["run_time"]),
                        "enabled": row["enabled"],
                        "last_run": row["last_run"].isoformat()
                        if row["last_run"]
                        else None,
                        "created_at": row["created_at"].isoformat()
                        if row["created_at"]
                        else None,
                    }
                    for row in rows
                ]
        return jsonify({"schedules": schedules})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/job_schedules", methods=["POST"])
def set_job_schedule():
    """Add or update a job schedule."""
    try:
        data = request.get_json()
        job_name = data["job_name"]
        run_time = data["run_time"]
        enabled = data.get("enabled", True)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Upsert by job_name
                cur.execute(
                    """
                    INSERT INTO job_schedules (job_name, run_time, enabled)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (job_name) DO UPDATE SET run_time = EXCLUDED.run_time, enabled = EXCLUDED.enabled
                """,
                    (job_name, run_time, enabled),
                )
                conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/job_schedules/<int:schedule_id>/enable", methods=["POST"])
def enable_job_schedule(schedule_id):
    """Enable or disable a job schedule."""
    try:
        data = request.get_json()
        enabled = data["enabled"]
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE job_schedules SET enabled = %s WHERE id = %s",
                    (enabled, schedule_id),
                )
                conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/job_schedules/<int:schedule_id>", methods=["DELETE"])
def delete_job_schedule(schedule_id):
    """Delete a job schedule."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get job name for confirmation
                cur.execute(
                    "SELECT job_name FROM job_schedules WHERE id = %s", (schedule_id,)
                )
                job = cur.fetchone()
                if not job:
                    return jsonify({"error": "Job schedule not found"}), 404
                # Delete the job schedule
                cur.execute("DELETE FROM job_schedules WHERE id = %s", (schedule_id,))
                conn.commit()
        return jsonify(
            {
                "success": True,
                "message": f'Job schedule "{job[0]}" deleted successfully',
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# Removed save_preloaded_data_to_db function - now using market_movers table directly
@app.route("/reporting")
def reporting_page():
    """Reporting and analytics page"""
    # Set default dates (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    return render_template(
        "reporting.html",
        default_start_date=start_date.strftime("%Y-%m-%d"),
        default_end_date=end_date.strftime("%Y-%m-%d"),
    )
@app.route("/api/reporting/generate", methods=["POST"])
def generate_report():
    """Generate comprehensive trading report"""
    try:
        data = request.get_json()
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        report_type = data.get("report_type", "comprehensive")
        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        # Generate real report data from database
        report_data = generate_real_report_data(start_dt, end_dt, report_type)
        return create_api_response(data=report_data)
    except Exception as e:
        log_exception("Generate report", e)
        return create_api_response(error=str(e), status_code=500)
def generate_real_report_data(start_date, end_date, report_type):
    """Generate real report data from database with mock data clearly marked"""
    import random
    from datetime import timedelta
    # Generate date range
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    # REAL DATA: Get recommendations statistics
    recommendations_data = get_real_recommendations_data(start_date, end_date)
    # REAL DATA: Get scalping signals statistics
    scalping_data = get_real_scalping_data(start_date, end_date)
    # REAL DATA: Get market movers data
    market_movers_data = get_real_market_movers_data(start_date, end_date)
    # REAL DATA: Get backtest results
    backtest_data = get_real_backtest_data(start_date, end_date)
    # REAL DATA: Get system metrics
    system_data = get_real_system_metrics(start_date, end_date)
    # MOCK DATA: Portfolio performance (no real portfolio tracking yet)
    portfolio_values = [10000]
    for i in range(1, len(date_range)):
        daily_return = random.uniform(-0.03, 0.05)
        portfolio_values.append(portfolio_values[-1] * (1 + daily_return))
    total_return = (portfolio_values[-1] - portfolio_values[0]) / portfolio_values[0]
    return {
        "performance": {
            "total_return": total_return,
            "win_rate": recommendations_data.get("win_rate", 0.0),
            "sharpe_ratio": backtest_data.get("avg_sharpe", 1.2),
            "max_drawdown": backtest_data.get("avg_drawdown", -0.08),
            "portfolio_data": {
                "labels": date_range,
                "values": portfolio_values,
                "note": "🔴 MOCK DATA - No real portfolio tracking implemented",
            },
            "asset_allocation": {
                "labels": ["Stocks", "Options", "Crypto", "Cash"],
                "values": [45, 35, 15, 5],
                "note": "🔴 MOCK DATA - No real asset allocation tracking",
            },
        },
        "trading_activity": {
            "total_trades": recommendations_data.get("total_recommendations", 0),
            "avg_holding_period": recommendations_data.get("avg_holding_period", 3.5),
            "opportunity_conversion": recommendations_data.get(
                "opportunity_conversion", 0.4
            ),
            "avg_trade_size": recommendations_data.get("avg_trade_size", 1000),
            "daily_volume": {
                "labels": date_range[-10:],
                "values": recommendations_data.get(
                    "daily_volumes", [random.randint(5, 20) for _ in range(10)]
                ),
                "note": "🔴 MOCK DATA - Daily volumes not tracked",
            },
            "time_analysis": {
                "labels": ["9AM", "10AM", "11AM", "12PM", "1PM", "2PM", "3PM", "4PM"],
                "values": [random.randint(5, 25) for _ in range(8)],
                "note": "🔴 MOCK DATA - Time-based analysis not implemented",
            },
            "top_symbols": recommendations_data.get("top_symbols", []),
            "strategy_performance": {
                "labels": ["News-Driven", "Watchlist", "Scalping", "Technical"],
                "values": [0.12, 0.08, 0.18, 0.05],
                "note": "🔴 MOCK DATA - Strategy performance not tracked",
            },
        },
        "risk_management": {
            "value_at_risk": random.uniform(500, 1500),
            "volatility": random.uniform(0.15, 0.35),
            "beta": random.uniform(0.8, 1.2),
            "correlation": random.uniform(0.6, 0.9),
            "drawdown_data": {
                "labels": date_range,
                "values": [random.uniform(-0.1, 0.02) for _ in date_range],
                "note": "🔴 MOCK DATA - Real drawdown calculation not implemented",
            },
            "risk_return_data": {
                "points": [
                    {"x": random.uniform(0.1, 0.4), "y": random.uniform(0.05, 0.25)}
                    for _ in range(20)
                ],
                "note": "🔴 MOCK DATA - Risk-return analysis not implemented",
            },
        },
        "news_impact": {
            "success_rate": recommendations_data.get("news_success_rate", 0.7),
            "sentiment_accuracy": recommendations_data.get("sentiment_accuracy", 0.75),
            "avg_reaction_time": random.uniform(2, 8),
            "total_articles": recommendations_data.get("total_articles", 1500),
            "source_effectiveness": {
                "labels": ["Yahoo Finance", "Alpha Vantage", "NewsAPI", "Reddit"],
                "values": [0.75, 0.68, 0.72, 0.65],
                "note": "🔴 MOCK DATA - Source effectiveness not tracked",
            },
            "sentiment_performance": {
                "labels": date_range[-7:],
                "sentiment": [random.uniform(-0.5, 0.5) for _ in range(7)],
                "performance": [random.uniform(-0.02, 0.03) for _ in range(7)],
                "note": "🔴 MOCK DATA - Sentiment vs performance correlation not calculated",
            },
        },
        "system_metrics": {
            "uptime": system_data.get("uptime", 0.98),
            "data_freshness": system_data.get("data_freshness", 5),
            "api_success_rate": system_data.get("api_success_rate", 0.95),
            "preload_success_rate": system_data.get("preload_success_rate", 0.85),
            "api_response_times": {
                "labels": date_range[-7:],
                "values": system_data.get(
                    "api_response_times", [random.uniform(100, 500) for _ in range(7)]
                ),
                "note": "🔴 MOCK DATA - API response times not tracked",
            },
            "provider_reliability": {
                "labels": ["Alpha Vantage", "Yahoo Finance", "NewsAPI"],
                "values": [0.92, 0.95, 0.88, 0.90],
                "note": "🔴 MOCK DATA - Provider reliability not tracked",
            },
        },
        "comparative": {
            "benchmark_data": {
                "labels": date_range,
                "portfolio": portfolio_values,
                "benchmark": [10000 * (1 + i * 0.0005) for i in range(len(date_range))],
                "note": "🔴 MOCK DATA - Benchmark comparison not implemented",
            },
            "strategy_comparison": {
                "labels": ["News-Driven", "Watchlist", "Scalping", "Technical"],
                "returns": [0.12, 0.08, 0.18, 0.05],
                "note": "🔴 MOCK DATA - Strategy comparison not implemented",
            },
            "metrics_comparison": [
                {
                    "name": "Total Return",
                    "portfolio": total_return,
                    "benchmark": 0.08,
                    "difference": total_return - 0.08,
                },
                {
                    "name": "Volatility",
                    "portfolio": random.uniform(0.15, 0.35),
                    "benchmark": 0.18,
                    "difference": random.uniform(-0.1, 0.1),
                },
                {
                    "name": "Sharpe Ratio",
                    "portfolio": backtest_data.get("avg_sharpe", 1.2),
                    "benchmark": 0.9,
                    "difference": backtest_data.get("avg_sharpe", 1.2) - 0.9,
                },
                {
                    "name": "Max Drawdown",
                    "portfolio": backtest_data.get("avg_drawdown", -0.08),
                    "benchmark": -0.12,
                    "difference": backtest_data.get("avg_drawdown", -0.08) - (-0.12),
                },
            ],
        },
    }
def get_real_recommendations_data(start_date, end_date):
    """Get real recommendations data from database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get total recommendations in date range
                cur.execute(
                    """
                    SELECT COUNT(*) as total,
                           COUNT(CASE WHEN actual_outcome IS NOT NULL THEN 1 END) as evaluated,
                           COUNT(CASE WHEN profitable = TRUE THEN 1 END) as profitable,
                           AVG(CASE WHEN actual_outcome IS NOT NULL THEN actual_outcome ELSE NULL END) as avg_outcome
                    FROM recommendations
                    WHERE timestamp BETWEEN %s AND %s
                """,
                    (start_date, end_date),
                )
                result = cur.fetchone()
                if not result:
                    return {"total_recommendations": 0, "win_rate": 0.0}
                total = result["total"] or 0
                evaluated = result["evaluated"] or 0
                profitable = result["profitable"] or 0
                avg_outcome = result["avg_outcome"] or 0.0
                win_rate = (profitable / evaluated * 100) if evaluated > 0 else 0.0
                # Get top symbols by recommendation count
                cur.execute(
                    """
                    SELECT symbol, COUNT(*) as count,
                           COUNT(CASE WHEN profitable = TRUE THEN 1 END) as wins
                    FROM recommendations
                    WHERE timestamp BETWEEN %s AND %s
                    GROUP BY symbol
                    ORDER BY count DESC
                    LIMIT 5
                """,
                    (start_date, end_date),
                )
                top_symbols = []
                for row in cur.fetchall():
                    symbol = row["symbol"]
                    count = row["count"]
                    wins = row["wins"]
                    win_rate_symbol = (wins / count * 100) if count > 0 else 0.0
                    top_symbols.append(
                        {
                            "symbol": symbol,
                            "trades": count,
                            "win_rate": win_rate_symbol,
                            "return_pct": avg_outcome
                            * 100,  # Using overall average as proxy
                        }
                    )
                return {
                    "total_recommendations": total,
                    "evaluated_recommendations": evaluated,
                    "profitable_recommendations": profitable,
                    "win_rate": win_rate,
                    "avg_outcome": avg_outcome,
                    "top_symbols": top_symbols,
                    "avg_holding_period": 3.5,  # Mock - not tracked
                    "opportunity_conversion": 0.4,  # Mock - not tracked
                    "avg_trade_size": 1000,  # Mock - not tracked
                    "news_success_rate": 0.7,  # Mock - not tracked
                    "sentiment_accuracy": 0.75,  # Mock - not tracked
                    "total_articles": 1500,  # Mock - not tracked
                }
    except Exception as e:
        log_error(f"Error getting recommendations data: {e}")
        return {"total_recommendations": 0, "win_rate": 0.0}
def get_real_scalping_data(start_date, end_date):
    """Get real scalping signals data from database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get scalping signals in date range
                cur.execute(
                    """
                    SELECT COUNT(*) as total,
                           COUNT(CASE WHEN sentiment_class = 'Bullish' THEN 1 END) as bullish,
                           COUNT(CASE WHEN sentiment_class = 'Bearish' THEN 1 END) as bearish,
                           AVG(sentiment_score) as avg_sentiment
                    FROM scalping_signals
                    WHERE date BETWEEN %s AND %s
                """,
                    (start_date, end_date),
                )
                result = cur.fetchone()
                if not result:
                    return {"total_signals": 0}
                return {
                    "total_signals": result["total"] or 0,
                    "bullish_signals": result["bullish"] or 0,
                    "bearish_signals": result["bearish"] or 0,
                    "avg_sentiment": result["avg_sentiment"] or 0.0,
                }
    except Exception as e:
        log_error(f"Error getting scalping data: {e}")
        return {"total_signals": 0}
def get_real_market_movers_data(start_date, end_date):
    """Get real market movers data from database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get market movers in date range
                cur.execute(
                    """
                    SELECT COUNT(*) as total,
                           COUNT(CASE WHEN type = 'GAINER' THEN 1 END) as gainers,
                           COUNT(CASE WHEN type = 'LOSER' THEN 1 END) as losers,
                           AVG(change_percent) as avg_change
                    FROM market_movers
                    WHERE timestamp BETWEEN %s AND %s
                """,
                    (start_date, end_date),
                )
                result = cur.fetchone()
                if not result:
                    return {"total_movers": 0}
                return {
                    "total_movers": result["total"] or 0,
                    "gainers": result["gainers"] or 0,
                    "losers": result["losers"] or 0,
                    "avg_change": result["avg_change"] or 0.0,
                }
    except Exception as e:
        log_error(f"Error getting market movers data: {e}")
        return {"total_movers": 0}
def get_real_backtest_data(start_date, end_date):
    """Get real backtest results data from database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get backtest results in date range
                cur.execute(
                    """
                    SELECT COUNT(*) as total,
                           AVG(total_return) as avg_return,
                           AVG(win_rate) as avg_win_rate,
                           AVG(total_trades) as avg_trades
                    FROM backtest_results
                    WHERE timestamp BETWEEN %s AND %s
                """,
                    (start_date, end_date),
                )
                result = cur.fetchone()
                if not result:
                    return {"total_backtests": 0}
                return {
                    "total_backtests": result["total"] or 0,
                    "avg_return": result["avg_return"] or 0.0,
                    "avg_win_rate": result["avg_win_rate"] or 0.0,
                    "avg_trades": result["avg_trades"] or 0,
                    "avg_sharpe": 1.2,  # Mock - not calculated
                    "avg_drawdown": -0.08,  # Mock - not calculated
                }
    except Exception as e:
        log_error(f"Error getting backtest data: {e}")
        return {"total_backtests": 0}
def get_real_system_metrics(start_date, end_date):
    """Get real system metrics from database"""
    import random
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get cache statistics
                cur.execute(
                    """
                    SELECT COUNT(*) as total_cache_entries
                    FROM cache
                    WHERE created_at BETWEEN %s AND %s
                """,
                    (start_date, end_date),
                )
                cache_result = cur.fetchone()
                cache_entries = (
                    cache_result["total_cache_entries"] if cache_result else 0
                )
                # Get API cache statistics
                cur.execute(
                    """
                    SELECT COUNT(*) as total_api_cache_entries
                    FROM api_cache
                    WHERE created_at BETWEEN %s AND %s
                """,
                    (start_date, end_date),
                )
                api_cache_result = cur.fetchone()
                api_cache_entries = (
                    api_cache_result["total_api_cache_entries"]
                    if api_cache_result
                    else 0
                )
                return {
                    "uptime": 0.98,  # Mock - not tracked
                    "data_freshness": 5,  # Mock - not tracked
                    "api_success_rate": 0.95,  # Mock - not tracked
                    "preload_success_rate": 0.85,  # Mock - not tracked
                    "cache_entries": cache_entries,
                    "api_cache_entries": api_cache_entries,
                    "api_response_times": [
                        random.uniform(100, 500) for _ in range(7)
                    ],  # Mock - not tracked
                }
    except Exception as e:
        log_error(f"Error getting system metrics: {e}")
        return {"uptime": 0.98, "data_freshness": 5}
if __name__ == "__main__":
    create_app()
