#!/usr/bin/env python3
"""
Trading AI Flask Web Application
Enhanced with comprehensive logging and monitoring
"""
import logging
from flask import Flask, render_template, request, jsonify, send_file, redirect, flash
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from datetime import datetime, timedelta
from src.data.data_fetcher import DataFetcher
from src.core.sentiment_analyzer import SentimentAnalyzer
from src.trading.trading_strategy import TradingStrategy
from src.data.news_monitor import NewsMonitor
from src.core.go_service_client import GoServiceClient
from src.core.config import Config
from src.core.telegram_alerts import telegram_alerter
from src.core.cache import get_cached_result, cache_result, get_cache_stats, clear_cache
from src.core.batch_processor import (
    batch_processor,
    create_crypto_analysis_tasks,
    create_watchlist_tasks,
)
import requests
import time
from src.trading.enhanced_trading_strategy import EnhancedTradingStrategy
import sys
import psutil
import platform
from src.core.logger import (
    trading_logger,
    log_info,
    log_warning,
    log_error,
    log_debug,
    log_api_call,
    log_performance,
    log_system_event,
    log_timeout,
    log_exception,
    log_timing,
    log_user_actions,
)
from src.core.recommendation_manager import get_recommendation_manager
from src.core.database import get_db_connection
import traceback
from src.core.watchlist_manager import watchlist_manager
from src.core.tier_manager import tier_manager
from apscheduler.schedulers.background import BackgroundScheduler
import psycopg2
from psycopg2.extras import Json, RealDictCursor
import threading
from src.core.database import get_db_connection

app = Flask(__name__)
# Enable CORS for all routes
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# FORCE PRODUCTION MODE - SET DEBUG OFF ONCE AND ONLY ONCE
app.debug = False
app.config["DEBUG"] = False
app.config["ENV"] = "production"
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
# Initialize components
data_fetcher = DataFetcher()
sentiment_analyzer = SentimentAnalyzer()
trading_strategy = TradingStrategy()
news_monitor = NewsMonitor()
go_client = GoServiceClient()
# Initialize enhanced trading strategy
enhanced_trading_strategy = EnhancedTradingStrategy()
# PostgreSQL cache is now handled by the cache module
# No more in-memory ANALYSIS_CACHE dictionary needed
# Add this function at the beginning of the file, after the imports but
# before the routes


def create_api_response(data=None, success=True, message="", error_code=None, error=None, status_code=200):
    """Create standardized API response"""
    response = {
        "success": success,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }
    if data is not None:
        response["data"] = data
    if error_code:
        response["error_code"] = error_code
    if error:
        response["error"] = error
        response["success"] = False
    return jsonify(response), status_code


@app.route("/")
def index():
    """Main dashboard page"""
    return render_template("index.html", historical_lookback_days=Config.HISTORICAL_LOOKBACK_DAYS)


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
                "updated_at": tier_info["updated_at"]
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
                error=f"Invalid tier: {tier}. Must be 'free' or 'paid'", 
                status_code=400
            )
        
        tier_info = tier_manager.upgrade_tier(user_id, tier)
        
        return create_api_response(
            data=tier_info,
            message=f"Successfully switched to {tier} tier"
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
            return create_api_response(error="Feature parameter is required", status_code=400)
        
        has_access = tier_manager.check_feature_access(user_id, feature)
        
        return create_api_response(
            data={
                "feature": feature,
                "has_access": has_access,
                "user_id": user_id
            }
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


@app.route("/api/analyze_stock", methods=["POST"])
@log_user_actions(trading_logger)
@log_timing(trading_logger)
def analyze_stock():
    """Analyze a single stock"""
    try:
        data = request.get_json()
        trading_logger.api_logger.info(f"[DEBUG] Incoming /api/analyze_stock request: {data}")
        if not data or "symbol" not in data:
            trading_logger.api_logger.info(f"[DEBUG] /api/analyze_stock missing symbol: {data}")
            return (
                jsonify({"status": "error", "error": "Missing required parameter: symbol"}),
                400,
            )
        symbol = data["symbol"].strip().upper() if data["symbol"] else ""
        if not symbol:
            trading_logger.api_logger.info(f"[DEBUG] /api/analyze_stock empty symbol: {data}")
            return jsonify({"status": "error", "error": "Symbol cannot be empty"}), 400
        # Check rate limits
        if not check_rate_limit("analyze_stock"):
            trading_logger.api_logger.info(f"[DEBUG] /api/analyze_stock rate limit hit: {data}")
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Rate limit exceeded. Please try again later.",
                    }
                ),
                429,
            )
        # Get cached result if available
        cache_key = f"stock_analysis_{symbol}"
        cached_result = get_cached_result(cache_key)
        if cached_result:
            trading_logger.api_logger.info(f"[DEBUG] /api/analyze_stock cache hit for {symbol}")
            response = {
                    "status": "success",
                    "data": cached_result,
                    "cache_status": "hit",
                    "timestamp": datetime.now().isoformat(),
                }
            trading_logger.api_logger.info(f"[DEBUG] /api/analyze_stock response: {response}")
            return jsonify(response)
        # Perform analysis
        start_time = time.time()
        result = analyze_single_stock(symbol)
        print(f"[DEBUG] analyze_single_stock result: {result}")  # ADDED DEBUG
        print(f"[DEBUG] analyze_single_stock result keys: {list(result.keys()) if isinstance(result, dict) else 'not dict'}")  # ADDED DEBUG
        print(f"[DEBUG] Has options_recommendation: {'options_recommendation' in result if isinstance(result, dict) else False}")  # ADDED DEBUG
        execution_time = time.time() - start_time
        # Cache the result
        cache_result(cache_key, result)
        # Add performance metrics
        if isinstance(result, dict):
            result["performance_metrics"] = {
                "execution_time_seconds": execution_time,
                "cache_status": "miss",
                "timestamp": datetime.now().isoformat(),
            }
        response = {
                "status": "success",
                "data": result,
                "cache_status": "miss",
                "timestamp": datetime.now().isoformat(),
            }
        print(f"[DEBUG] /api/analyze_stock response: {response}")  # ADDED DEBUG
        trading_logger.api_logger.info(f"[DEBUG] /api/analyze_stock response: {response}")
        return jsonify(response)
    except Exception as e:
        trading_logger.api_logger.error(f"[DEBUG] /api/analyze_stock error: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/analyze_bulk", methods=["POST"])
def analyze_bulk():
    """Analyze multiple stocks with rate limiting and batching"""
    try:
        data = request.get_json()
        if not data or "symbols" not in data:
            return (
                jsonify({"status": "error", "error": "Missing required parameter: symbols"}),
                400,
            )
        symbols = [s.upper() for s in data["symbols"]]
        # Enforce bulk analysis limits
        if len(symbols) > Config.MAX_BATCH_SIZE:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": (
                            f"Batch size exceeds maximum limit of "
                            f"{Config.MAX_BATCH_SIZE} symbols"
                        ),
                    }
                ),
                400,
            )
        # Check rate limits
        if not check_rate_limit("analyze_bulk"):
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Rate limit exceeded. Please try again later.",
                    }
                ),
                429,
            )
        # Process in batches
        results = []
        start_time = time.time()
        for i in range(0, len(symbols), Config.MAX_CONCURRENT_REQUESTS):
            batch = symbols[i : i + Config.MAX_CONCURRENT_REQUESTS]
            batch_results = analyze_stock_batch(batch)
            results.extend(batch_results)
        execution_time = time.time() - start_time
        # Add performance metrics
        response = {
            "status": "success",
            "data": {
                "results": results,
                "performance_metrics": {
                    "execution_time_seconds": execution_time,
                    "batch_size": len(symbols),
                    "batches_processed": (len(symbols) + Config.MAX_CONCURRENT_REQUESTS - 1)
                    // Config.MAX_CONCURRENT_REQUESTS,
                    "timestamp": datetime.now().isoformat(),
                },
            },
            "timestamp": datetime.now().isoformat(),
        }
        return jsonify(response)
    except Exception as e:
        log_error(f"Error in bulk analysis: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


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
            return create_api_response(error=f"Invalid price data received for {symbol}: type={type(price_data)}", status_code=500)
        
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


@app.route("/api/sp500_analysis")
def sp500_analysis():
    """API endpoint for S&P 500 winners and losers analysis"""
    trading_logger.api_logger.info("[DEBUG] Entered sp500_analysis endpoint")
    try:
        # Get limit parameter for testing purposes
        limit = request.args.get('limit', type=int)
        refresh = request.args.get('refresh', default=0, type=int)
        trading_logger.api_logger.info(f"[DEBUG] sp500_analysis request params: limit={limit}, refresh={refresh}")
        
        if limit and limit > 0:
            trading_logger.api_logger.info(f"[DEBUG] TEST MODE: Limiting analysis to {limit} stocks")
        
        cache_key = "sp500_analysis"
        # Only clear cache if refresh=1 is passed
        if refresh:
            trading_logger.api_logger.info("[DEBUG] Manual refresh requested, clearing cache...")
            try:
                clear_cache()
            except Exception as e:
                trading_logger.error_logger.error(f"[ERROR] Cache clear failed: {e}")
        
        # Check cache first
        cached_result = get_cached_result(cache_key)
        if cached_result and not refresh:
            # Ensure cached_result is a dictionary, not a string
            if isinstance(cached_result, dict):
                # Modify cached result to indicate it came from cache
                cached_result["cached"] = True
                cached_result["cache_timestamp"] = datetime.now().isoformat()
                trading_logger.api_logger.info("[DEBUG] Returning cached sp500_analysis result")
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
                trading_logger.error_logger.error(f"[ERROR] Invalid winners_losers data type: {type(cached_result)}")
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
        limit_per_category = 3  # Reduced from 5 to 3 (keeping 3 winners + 3 losers = 6 total)
        try:
            trading_logger.api_logger.info("[DEBUG] Fetching top gainers/losers from Alpha Vantage API")
            winners_losers = data_fetcher.get_top_gainers_losers(limit=limit_per_category)
            trading_logger.api_logger.info(f"[DEBUG] top_gainers_losers type: {type(winners_losers)}, value: {winners_losers}")
        except Exception as e:
            trading_logger.error_logger.error(f"[ERROR] Error getting top gainers/losers: {e}")
            # Fallback to default symbols if API fails
            winners_losers = {
                "gainers": ["AAPL", "MSFT", "GOOGL"],
                "losers": ["META", "NVDA", "JPM"],
                "timestamp": datetime.now().isoformat(),
                "source": "fallback"
            }
            trading_logger.api_logger.info("[DEBUG] Using fallback symbols for gainers/losers")
        
        # Ensure winners_losers is a dictionary
        if not isinstance(winners_losers, dict):
            trading_logger.error_logger.error(f"[ERROR] Invalid top_gainers_losers data type: {type(winners_losers)}")
            # Fallback to default symbols
            winners_losers = {
                "gainers": ["AAPL", "MSFT", "GOOGL"],
                "losers": ["META", "NVDA", "JPM"],
                "timestamp": datetime.now().isoformat(),
                "source": "fallback"
            }
            trading_logger.api_logger.info("[DEBUG] Using fallback symbols due to invalid data type")
            
        if not winners_losers.get("gainers") and not winners_losers.get("losers"):
            trading_logger.error_logger.error("[ERROR] No gainers/losers data returned")
            winners_losers = {
                "gainers": ["AAPL", "MSFT", "GOOGL"],
                "losers": ["META", "NVDA", "JPM"],
                "timestamp": datetime.now().isoformat(),
                "source": "fallback"
            }
            trading_logger.api_logger.info("[DEBUG] Using fallback symbols due to empty gainers/losers lists")
            
        # Combine gainers and losers for analysis
        symbols_to_analyze = []
        symbols_to_analyze.extend(winners_losers.get("gainers", []))
        symbols_to_analyze.extend(winners_losers.get("losers", []))
        
        # Apply limit if specified (for testing)
        if limit and limit > 0:
            symbols_to_analyze = symbols_to_analyze[:limit]
            trading_logger.api_logger.info(f"[DEBUG] TEST MODE: Limited to {len(symbols_to_analyze)} symbols: {symbols_to_analyze}")
        
        trading_logger.api_logger.info(
            f"[DEBUG] Running optimized analysis for {len(symbols_to_analyze)} symbols: "
            f"{symbols_to_analyze}"
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
                        result is not None and "error" not in result if result else False
                    ),
                    "cached": False,
                },
            )

        # Run optimized analysis for each symbol
        enhanced_results = []
        errors = []
        start_time = time.time()
        
        for i, symbol in enumerate(symbols_to_analyze):
            try:
                print(f"🔍 Analyzing {symbol} ({i+1}/{len(symbols_to_analyze)})...")
                
                # OPTIMIZATION 1: Get price data first (fast)
                price_data = data_fetcher.get_stock_price(symbol)
                if "error" in price_data:
                    raise Exception(f"Error getting price data: {price_data['error']}")
                
                # Validate price_data is a dictionary with required fields
                if not isinstance(price_data, dict) or "current_price" not in price_data:
                    raise Exception(f"Invalid price data received for {symbol}: type={type(price_data)}")
                
                # OPTIMIZATION 2: Get news data with shorter timeframe (3 days instead of 7)
                news_data = data_fetcher.get_company_news(symbol, days_back=3)
                
                # OPTIMIZATION 3: Skip AI sentiment analysis if no news (use price-based only)
                if not news_data or len(news_data) == 0:
                    print(f"📊 No news articles for {symbol}, using price-based sentiment analysis only")
                    # Use price-based sentiment analysis (much faster)
                    sentiment_data = {
                        "sentiment_score": 0.0,
                        "sentiment_label": "neutral",
                        "confidence": 0.5,
                        "analysis_method": "price_based",
                        "news_count": 0
                    }
                else:
                    print(f"🔍 Analyzing {symbol} using news sentiment...")
                    # Only use AI sentiment if we have news (but with timeout)
                    try:
                        sentiment_data = analyze_sentiment_with_fallback(news_data, price_data, symbol)
                    except Exception as e:
                        print(f"⚠️ AI sentiment failed for {symbol}, using price-based: {e}")
                        sentiment_data = {
                            "sentiment_score": 0.0,
                            "sentiment_label": "neutral",
                            "confidence": 0.5,
                            "analysis_method": "price_based_fallback",
                            "news_count": len(news_data)
                        }
                
                # OPTIMIZATION 4: Use faster signal generation
                signal_data = sentiment_analyzer.get_trading_signal(sentiment_data)
                
                # OPTIMIZATION 5: Skip historical data testing for speed (not needed for basic analysis)
                # Historical data testing is very slow and not essential for S&P 500 overview
                historical_data = []
                
                # Generate comprehensive recommendations with position sizes and trading notes
                comprehensive_result = enhanced_trading_strategy.get_comprehensive_recommendations(
                    symbol, price_data["current_price"], sentiment_data, signal_data
                )
                
                print(f"✅ Generated comprehensive recommendations for {symbol}")
                
                # Determine if this is a winner or loser based on the symbol
                symbol_type = "winner" if symbol in winners_losers.get("gainers", []) else "loser"
                
                # Create the enhanced analysis result with comprehensive analysis
                result = {
                    "symbol": symbol,
                    "type": symbol_type,
                    "price_data": price_data,
                    "sentiment_data": sentiment_data,
                    "signal_data": signal_data,
                    "news_count": len(news_data) if news_data else 0,
                    "comprehensive_analysis": comprehensive_result,
                    "timestamp": datetime.now().isoformat()
                }
                
                enhanced_results.append(result)
                
                # Call progress callback
                progress_callback(
                    symbol, i + 1, len(symbols_to_analyze), result
                )
                
            except Exception as e:
                trading_logger.error_logger.error(f"[ERROR] Error analyzing {symbol}: {e}")
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
                "success_rate": f"{round(len(enhanced_results) / len(symbols_to_analyze) * 100, 1)}%" if len(symbols_to_analyze) > 0 else "0%"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Cache the results for future use
        cache_result(cache_key, response_data)  # Cache for 5 minutes
        
        trading_logger.api_logger.info(f"[DEBUG] Returning sp500_analysis result with {len(enhanced_results)} stocks")
        return create_api_response(data=response_data)
        
    except Exception as e:
        trading_logger.error_logger.error(f"[ERROR] Error in sp500_analysis endpoint: {str(e)}")
        return create_api_response(error=f"Failed to analyze S&P 500: {str(e)}", status_code=500)


@app.route("/api/crypto_analysis")
def crypto_analysis():
    """Analyze cryptocurrencies for trading opportunities"""
    try:
        # Check cache first
        cache_key = "crypto_analysis_v1"
        cached_result = get_cached_result(cache_key)
        if cached_result:
            # Ensure cached_result is a dictionary, not a string
            if isinstance(cached_result, dict):
                print("📊 Returning cached crypto analysis results")
                socketio.emit(
                    "crypto_progress",
                    {
                        "current": 100,
                        "total": 100,
                        "symbol": "COMPLETED",
                        "status": "completed",
                        "cached": True,
                    },
                )
                return create_api_response(data=cached_result)
            else:
                # If cached result is not a dict (e.g., string), clear cache and proceed
                print(f"⚠️ Invalid cached crypto result type: {type(cached_result)}, clearing cache")
                cached_result = None

        print("🚀 Starting fresh crypto analysis with smart batching...")

        # Get crypto symbols from database instead of config
        crypto_symbols = watchlist_manager.get_cryptos()
        watchlist_manager.get_stocks()

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

        # Use smart batching for concurrent processing
        limited_cryptos = crypto_symbols[: Config.BULK_ANALYSIS_CRYPTO_LIMIT]

        # Create batch tasks (with shared crypto news for efficiency)
        tasks = create_crypto_analysis_tasks(limited_cryptos, Config.BULK_ANALYSIS_NEWS_DAYS)
        print(f"🚀 Processing {len(tasks)} cryptocurrencies concurrently")

        # Progress callback for WebSocket updates

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
                        result is not None and "error" not in result if result else False
                    ),
                    "cached": False,
                },
            )

        # Process batch with real-time progress
        batch_result = batch_processor.process_batch_sync(tasks, progress_callback)

        # Convert batch results to expected format
        opportunities = []
        errors = []
        for symbol, result in batch_result["results"].items():
            if result and "error" not in result:
                opportunities.append(result)
                print(f"✅ Found opportunity: {symbol} - {result.get('action', 'UNKNOWN')}")
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
                    print(f"❌ Error analyzing {symbol}: {result.get('error', 'unknown error')}")
            else:
                print(f"⚪ {symbol} - No strong signal found")

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
                "opportunity_rate": (f"{(len(opportunities) / len(limited_cryptos) * 100):.1f}%"),
            },
            "note": (
                f"Analyzed {len(limited_cryptos)} of {len(crypto_symbols)} total "
                "cryptocurrencies with smart batching"
            ),
        }

        # Cache the result
        cache_result(cache_key, result_data)

        # Emit completion
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
            return create_api_response(error=f"Invalid price data received for {symbol}: type={type(price_data)}", status_code=500)
            
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
                        "details": ["Real trade execution API integration needed for live trading"],
                    },
                }
            ),
            500,
        )


@app.route("/api/backtest", methods=["POST"])
def backtest():
    """Run backtest for a symbol"""
    try:
        data = request.get_json()
        symbol = data.get("symbol", "").upper()
        days_back = data.get("days_back", 30)
        backtest_results = trading_strategy.backtest_strategy(symbol, days_back)
        return create_api_response(data=backtest_results)
    except Exception as e:
        log_exception("Backtest endpoint", e)
        return create_api_response(error=str(e), status_code=500)


@app.route("/api/portfolio")
def portfolio():
    """Get current portfolio status"""
    try:
        portfolio_summary = trading_strategy.get_portfolio_summary()
        recent_trades = trading_strategy.trade_history[-10:]  # Last 10 trades
        # Convert datetime objects to strings for JSON serialization
        for trade in recent_trades:
            if "timestamp" in trade:
                trade["timestamp"] = trade["timestamp"].isoformat()
        return create_api_response(
            data={
                "portfolio_summary": portfolio_summary,
                "recent_trades": recent_trades,
                "open_positions": trading_strategy.positions,
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
                            "Failed to send welcome message. " "Check the chat ID and try again."
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
            return create_api_response(error="Telegram alerts are disabled", status_code=400)
        data = request.get_json()
        message = data.get("message", "")
        if not message:
            return create_api_response(error="Message content is required", status_code=400)
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
        return create_api_response(error="Error sending raw message: {str(e)}", status_code=500)


@app.route("/stocks")
def stocks_page():
    """S&P 500 stocks analysis page"""
    try:
        trading_logger.api_logger.info("[DEBUG] Entering stocks_page route handler")
        
        # Check if preloaded data is available (warm the cache)
        try:
            if not preloaded_data:
                trading_logger.api_logger.warning("[DEBUG] No preloaded data available for stocks page")
        except Exception as e:
            trading_logger.error_logger.error(f"[DEBUG] Error checking preloaded_data: {str(e)}")
        
        trading_logger.api_logger.info("[DEBUG] Rendering stocks.html template")
        return render_template("stocks.html", historical_lookback_days=Config.HISTORICAL_LOOKBACK_DAYS)
    except Exception as e:
        trading_logger.error_logger.error(f"[CRITICAL] Error rendering stocks page: {str(e)}")
        # Return a simple error page instead of crashing
        return f"<html><body><h1>Error loading stocks page</h1><p>Please try again later. Error: {str(e)}</p></body></html>", 500


@app.route("/crypto")
def crypto_page():
    """Crypto analysis page"""
    return render_template("crypto.html", historical_lookback_days=Config.HISTORICAL_LOOKBACK_DAYS)


@app.route("/portfolio_page")
def portfolio_page():
    """Portfolio management page"""
    return render_template(
        "portfolio.html", historical_lookback_days=Config.HISTORICAL_LOOKBACK_DAYS
    )


@app.route("/backtest_page")
def backtest_page():
    """Backtesting page"""
    return render_template(
        "backtest.html", historical_lookback_days=Config.HISTORICAL_LOOKBACK_DAYS
    )


@app.route("/api/news_opportunities")
def news_opportunities():
    """Get news-driven trading opportunities"""
    try:
        opportunities = news_monitor.analyze_news_driven_opportunities()
        return create_api_response(
            data={"opportunities": opportunities, "count": len(opportunities)}
        )
    except Exception as e:
        log_exception("News opportunities endpoint", e)
        return create_api_response(error=str(e), status_code=500)


@app.route("/api/watchlist_opportunities")
def watchlist_opportunities():
    """Get trading opportunities for watchlist stocks with smart batching and real-time progress"""
    try:
        # Check cache first
        cache_key = f"watchlist_opportunities_{int(datetime.now().timestamp())}"
        cached_result = get_cached_result(cache_key)
        if cached_result:
            # Ensure cached_result is a dictionary, not a string
            if isinstance(cached_result, dict):
                # Modify cached result to indicate it came from cache
                cached_result["cached"] = True
                cached_result["cache_timestamp"] = datetime.now().isoformat()
                # Still emit cached progress for UI consistency
                socketio.emit(
                    "watchlist_progress",
                    {
                        "current": cached_result.get("total_analyzed", 0),
                        "total": cached_result.get("total_analyzed", 0),
                        "symbol": "CACHED",
                        "status": "completed",
                        "cached": True,
                    },
                )
                return create_api_response(data=cached_result)
            else:
                # If cached result is not a dict (e.g., string), clear cache and proceed
                print(f"⚠️ Invalid winners_losers data type: {type(cached_result)}")
                cached_result = None
        
        if cached_result:
            # Still emit cached progress for UI consistency
            socketio.emit(
                "watchlist_progress",
                {
                    "current": cached_result.get("total_analyzed", 0),
                    "total": cached_result.get("total_analyzed", 0),
                    "symbol": "CACHED",
                    "status": "completed",
                    "cached": True,
                },
            )
            return create_api_response(data=cached_result)
        
        # Get watchlist stocks from database (no fallback to config)
        watchlist_stocks = watchlist_manager.get_stocks()
        if not watchlist_stocks:
            # No stocks in watchlist - return helpful message
            return create_api_response(
                data={
                    "opportunities": [],
                    "errors": [],
                    "timestamp": datetime.now().isoformat(),
                    "total_analyzed": 0,
                    "opportunities_found": 0,
                    "errors_count": 0,
                    "batch_stats": {
                        "total_tasks": 0,
                        "successful": 0,
                        "failed": 0,
                        "time_taken": 0,
                        "avg_time_per_task": 0,
                    },
                    "note": "No stocks in watchlist. Go to System Status page to add stocks for analysis.",
                    "message": "Please add stocks to your watchlist using the System Status page to get trading opportunities.",
                }
            )

        log_info(f"🚀 Starting fresh watchlist opportunities analysis with smart batching...")
        log_info(f"🚀 Processing {len(watchlist_stocks)} watchlist stocks concurrently")

        # Create tasks for batch processing
        tasks = create_watchlist_tasks(watchlist_stocks, Config.BULK_ANALYSIS_NEWS_DAYS)
        print(f"🚀 Processing {len(tasks)} watchlist stocks concurrently")

        # Progress callback for WebSocket updates

        def progress_callback(symbol, completed, total, result):
            socketio.emit(
                "watchlist_progress",
                {
                    "current": completed,
                    "total": total,
                    "symbol": symbol,
                    "status": "completed" if completed == total else "processing",
                    "has_error": "error" in result if result else False,
                    "is_opportunity": (
                        result is not None and "error" not in result if result else False
                    ),
                    "cached": False,
                },
            )

        # Process batch with real-time progress
        batch_result = batch_processor.process_batch_sync(tasks, progress_callback)

        # Convert batch results to expected format (only opportunities)
        opportunities = []
        errors = []
        for symbol, result in batch_result["results"].items():
            if result and "error" not in result:
                # Transform the result to match frontend expectations
                opportunity = {
                    "symbol": result.get("symbol", symbol),
                    "type": "stock",  # Watchlist stocks are always stocks
                    "trigger": "watchlist_scan",
                    "news_count": result.get("news_count", 0),
                    "price_data": {
                        "current_price": result.get("current_price", 0),
                        # Fallback
                        "previous_close": result.get("current_price", 0),
                        "change": 0,  # Not available in batch results
                        "change_percent": 0,  # Not available in batch results
                    },
                    "sentiment_data": {
                        "sentiment_score": result.get("sentiment_score", 0),
                        "confidence": result.get("confidence", 0),
                        "sentiment_label": (
                            "Positive"
                            if result.get("sentiment_score", 0) > 0
                            else ("Negative" if result.get("sentiment_score", 0) < 0 else "Neutral")
                        ),
                    },
                    "signal_data": {
                        "action": result.get("action", "HOLD"),
                        "signal_strength": result.get("signal_strength", "LOW"),
                        "reasoning": f"Based on sentiment analysis of {result.get('news_count', 0)} recent news articles",
                    },
                    "trade_signal": {
                        # Use current price as strike
                        "strike_price": result.get("current_price", 0),
                        "option_price": 0.01,  # Default option price
                        "position_size": 1,  # Default position size
                        "expiration": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),  # 30 days from now
                    },
                    "opportunity_type": result.get("opportunity_type", "Unknown"),
                    "timestamp": datetime.now().isoformat(),
                }
                opportunities.append(opportunity)
                print(f"✅ Found opportunity: {symbol} - {result.get('action', 'UNKNOWN')}")
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
                    print(f"❌ Error analyzing {symbol}: {result.get('error', 'unknown error')}")
            else:
                print(f"⚪ {symbol} - No strong signal found")

        result_data = {
            "opportunities": opportunities,
            "errors": errors,
            "timestamp": datetime.now().isoformat(),
            "total_analyzed": len(watchlist_stocks),
            "opportunities_found": len(opportunities),
            "errors_count": len(errors),
            "cached": False,
            "batch_stats": batch_result["stats"],
            "performance": {
                "time_taken": batch_result["stats"]["time_taken"],
                "avg_time_per_stock": batch_result["stats"]["avg_time_per_task"],
                "success_rate": f"{(batch_result['stats']['successful'] / batch_result['stats']['total_tasks'] * 100):.1f}%",
                "opportunity_rate": f"{(len(opportunities) / len(watchlist_stocks) * 100):.1f}%",
            },
            "note": f"Analyzed {len(watchlist_stocks)} of {len(Config.WATCHLIST_STOCKS)} total watchlist stocks with smart batching",
        }

        # Cache the result
        cache_result(cache_key, result_data)

        # Emit completion
        socketio.emit(
            "watchlist_progress",
            {
                "current": len(watchlist_stocks),
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
    except Exception as e:
        # Emit error
        socketio.emit("watchlist_progress", {"status": "error", "error": str(e)})
        traceback.print_exc()
        log_error(f"watchlist_opportunities error: {e}\n" + traceback.format_exc())
        return create_api_response(error=str(e), status_code=500)


@app.route("/api/all_opportunities")
def all_opportunities():
    """Get all trading opportunities (news-driven + watchlist)"""
    try:
        all_opps = news_monitor.get_all_opportunities()
        return create_api_response(data=all_opps)
    except Exception as e:
        log_exception("All opportunities endpoint", e)
        return create_api_response(error=str(e), status_code=500)


@app.route("/opportunities")
def opportunities_page():
    """Trading opportunities page"""
    return render_template(
        "opportunities.html", historical_lookback_days=Config.HISTORICAL_LOOKBACK_DAYS
    )


@app.route("/api/go_services/health")
def go_services_health():
    """Get health status of Go microservices - DISABLED"""
    return create_api_response(
        data={
            "go_services_enabled": False,
            "services": {},
            "overall_health": "disabled",
            "message": "Go services are not implemented in this version"
        }
    )


@app.route("/system_status")
def system_status_page():
    """System status and Go services monitoring page"""
    return render_template(
        "system_status.html", historical_lookback_days=Config.HISTORICAL_LOOKBACK_DAYS
    )


@app.route("/api/system_status")
def system_status():
    """System status information with comprehensive error handling"""
    try:
        # Get basic system metrics with error handling
        system_metrics = {}
        try:
            system_metrics = get_system_metrics()
        except Exception as e:
            log_error(f"Error getting system metrics: {str(e)}")
            system_metrics = {"status": "error", "error": str(e)}
        
        # Get database stats with error handling
        db_stats = {"status": "unavailable"}
        try:
            from src.core.database import get_database_stats
            db_stats = get_database_stats()
        except Exception as e:
            log_error(f"Error getting database stats: {str(e)}")
            db_stats = {"status": "error", "error": str(e)}
        
        # Get cache stats with error handling
        cache_stats = {"status": "unavailable"}
        try:
            cache_stats = get_cache_stats()
        except Exception as e:
            log_error(f"Error getting cache stats: {str(e)}")
            cache_stats = {"status": "error", "error": str(e)}
        
        # Get application config
        config_info = {
            # Tier management removed - will be rebuilt from scratch
            "telegram_enabled": telegram_alerter.is_enabled(),
            "cache_enabled": (Config.ENABLE_CACHE if hasattr(Config, "ENABLE_CACHE") else False),
            "debug_mode": app.debug,
            "version": "1.0.0",
        }
        
        # Try to get telegram status safely
        try:
            config_info["telegram_enabled"] = telegram_alerter.is_enabled()
        except Exception as e:
            log_error(f"Error getting telegram status: {str(e)}")
        
        return jsonify({
            "status": "ok",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "system": system_metrics,
            "database": db_stats,
            "cache": cache_stats,
            "config": config_info,
        })
    except Exception as e:
        log_error(f"Critical error in system_status: {str(e)}")
        return jsonify({
            "status": "error", 
            "error": "System status unavailable",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 500


@app.route("/recommendations_test")
def recommendations_test_page():
    """Simple recommendations testing page"""
    return render_template(
        "recommendations_test.html",
        historical_lookback_days=Config.HISTORICAL_LOOKBACK_DAYS,
    )


@app.route("/api/test", methods=["POST"])
def consolidated_test():
    """Consolidated test endpoint for various services"""
    try:
        data = request.get_json()
        test_type = data.get("type", "all")
        results = {"tests": {}}
        # Test sentiment analysis
        if test_type in ["all", "sentiment"]:
            try:
                # Create test news articles in the correct format
                test_articles = [
                    {
                        "headline": "Test Company Reports Strong Earnings",
                        "summary": "This is a test message for sentiment analysis showing positive financial news"
                    }
                ]
                sentiment = sentiment_analyzer.analyze_news_sentiment(test_articles, symbol="TEST")
                results["tests"]["sentiment"] = {
                    "status": "success",
                    "result": sentiment,
                }
            except Exception as e:
                results["tests"]["sentiment"] = {"status": "error", "error": str(e)}
        # Test news services
        if test_type in ["all", "news"]:
            try:
                test_symbol = "AAPL"
                news = data_fetcher.get_company_news(test_symbol)
                results["tests"]["news"] = {"status": "success", "count": len(news)}
            except Exception as e:
                results["tests"]["news"] = {"status": "error", "error": str(e)}
        # Test Telegram
        if test_type in ["all", "telegram"]:
            try:
                telegram_alerter.send_message("Test message from Trading AI")
                results["tests"]["telegram"] = {"status": "success"}
            except Exception as e:
                results["tests"]["telegram"] = {"status": "error", "error": str(e)}
        return create_api_response(data=results)
    except Exception as e:
        log_exception("Consolidated test endpoint", e)
        return create_api_response(error=str(e), status_code=500)


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
                "enabled": Config.ENABLE_ALPHA_VANTAGE_NEWS and bool(Config.ALPHA_VANTAGE_API_KEY),
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
                "active_services": len([s for s in services_status.values() if s["enabled"]]),
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
        return jsonify({"configurations": config_status, "timestamp": datetime.now().isoformat()})
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
            "cache_enabled": (Config.ENABLE_CACHE if hasattr(Config, "ENABLE_CACHE") else False),
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
        trading_logger.api_logger.info(f"[DEBUG] Incoming /api/enhanced_analysis request: {data}")
        if not data or "symbol" not in data:
            trading_logger.api_logger.info(f"[DEBUG] /api/enhanced_analysis missing symbol: {data}")
            return create_api_response(error="Missing required parameter: symbol", status_code=400)
        symbol = data["symbol"].strip().upper()
        if not symbol:
            trading_logger.api_logger.info(f"[DEBUG] /api/enhanced_analysis empty symbol: {data}")
            return create_api_response(error="Symbol cannot be empty", status_code=400)
        # Check rate limits
        if not check_rate_limit("enhanced_analysis"):
            trading_logger.api_logger.info(f"[DEBUG] /api/enhanced_analysis rate limit hit: {data}")
            return create_api_response(
                error="Rate limit exceeded. Please try again later.",
                status_code=429
            )
        def emit_progress(step, message):
            """Emit progress updates via WebSocket"""
            socketio.emit('analysis_progress', {
                'step': step,
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
        try:
            emit_progress(1, "Fetching market data...")
            price_data = data_fetcher.get_stock_price(symbol)
            if not price_data or 'current_price' not in price_data:
                trading_logger.api_logger.info(f"[DEBUG] /api/enhanced_analysis missing price data: {price_data}")
                return create_api_response(error=f"Could not fetch price data for {symbol}", status_code=400)
            emit_progress(2, "Gathering news data...")
            news_data = data_fetcher.get_company_news(symbol)
            if not news_data:
                trading_logger.api_logger.info(f"[DEBUG] /api/enhanced_analysis missing news data: {news_data}")
                return create_api_response(error=f"Could not fetch news data for {symbol}", status_code=400)
            emit_progress(3, "Analyzing sentiment...")
            sentiment_data = sentiment_analyzer.analyze_news_sentiment(news_data, symbol=symbol)
            emit_progress(4, "Generating trading signals...")
            signal_data = sentiment_analyzer.get_trading_signal(sentiment_data)
            emit_progress(5, "Generating comprehensive recommendations...")
            recommendations = enhanced_trading_strategy.get_comprehensive_recommendations(
                symbol,
                price_data['current_price'],
                sentiment_data,
                signal_data
            )
            emit_progress(6, "Finalizing analysis...")
            response_data = {
                'symbol': symbol,
                'price_data': price_data,
                'sentiment_analysis': sentiment_data,
                'news_count': len(news_data),
                'recommendations': recommendations,
                'timestamp': datetime.now().isoformat()
            }
            cache_result(f"enhanced_{symbol}", response_data)
            response = {
                'status': 'success',
                'data': response_data,
                'cache_status': 'miss',
                'timestamp': datetime.now().isoformat()
            }
            trading_logger.api_logger.info(f"[DEBUG] /api/enhanced_analysis response: {response}")
            return jsonify(response)
        except Exception as e:
            trading_logger.api_logger.error(f"[DEBUG] /api/enhanced_analysis error: {str(e)}", exc_info=True)
            return create_api_response(error=str(e), status_code=500)
    except Exception as e:
        trading_logger.api_logger.error(f"[DEBUG] /api/enhanced_analysis error: {str(e)}", exc_info=True)
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
            return create_api_response(error=f"Invalid price data received for {symbol}: type={type(price_data)}", status_code=500)
            
        news_data = data_fetcher.get_company_news(symbol, days_back=7)
        # Analyze sentiment with fallback to price-based analysis
        sentiment_data = analyze_sentiment_with_fallback(
            news_data, price_data, symbol, ai_provider=ai_provider
        )
        signal_data = sentiment_analyzer.get_trading_signal(sentiment_data)
        # Generate comprehensive recommendations (both stocks and options)
        comprehensive_results = enhanced_trading_strategy.get_comprehensive_recommendations(
            symbol, price_data["current_price"], sentiment_data, signal_data
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
                sentiment_result = sentiment_analyzer.analyze_news_sentiment(news_data, ai_provider=ai_provider, symbol=symbol)
            else:
                sentiment_result = sentiment_analyzer.analyze_news_sentiment(news_data, symbol=symbol)
            # Add news_sentiment field to indicate news was used
            sentiment_result["news_sentiment"] = sentiment_result["sentiment_score"]
            sentiment_result["has_news"] = True
            return sentiment_result
        else:
            # Fallback to price-based sentiment analysis
            print(f"📊 No news articles for {symbol}, using price-based sentiment analysis...")
            sentiment_result = sentiment_analyzer.analyze_price_based_sentiment(price_data, symbol)
            # Add news_sentiment field as 0 to indicate no news was used
            sentiment_result["news_sentiment"] = 0.0
            sentiment_result["has_news"] = False
            return sentiment_result
    except Exception as e:
        # If news sentiment fails, try price-based analysis
        if "No news articles provided for analysis" in str(e) or "No valid news content found" in str(e):
            print(f"📊 News analysis failed for {symbol}, falling back to price-based analysis...")
            try:
                sentiment_result = sentiment_analyzer.analyze_price_based_sentiment(price_data, symbol)
                # Add news_sentiment field as 0 to indicate no news was used
                sentiment_result["news_sentiment"] = 0.0
                sentiment_result["has_news"] = False
                return sentiment_result
            except Exception as price_error:
                print(f"❌ Price-based analysis also failed for {symbol}: {price_error}")
                # Return neutral sentiment as last resort
                return {
                    "sentiment_score": 0.0,
                    "confidence": 0.3,
                    "summary": f"Analysis failed for {symbol}",
                    "reasoning": f"Both news and price analysis failed: {str(e)}",
                    "provider": "fallback",
                    "analysis_type": "error",
                    "news_sentiment": 0.0,
                    "has_news": False
                }
        else:
            # Re-raise other types of errors
            raise e


def analyze_single_stock(symbol):
    """Analyze a single stock and return the results"""
    print(f"[DEBUG] analyze_single_stock called for {symbol} from API context")  # ADDED DEBUG
    # Get stock price data
    price_data = data_fetcher.get_stock_price(symbol)
    print(f"🔍 DEBUG price_data for {symbol}: type={type(price_data)}, value={price_data}")
    if "error" in price_data:
        return {"error": f"Failed to get price data for {symbol}: {price_data['error']}"}
    if not isinstance(price_data, dict) or "current_price" not in price_data:
        return {"error": f"Invalid price data received for {symbol}: type={type(price_data)}, keys={list(price_data.keys()) if isinstance(price_data, dict) else 'not dict'}"}
    # Get news data from different sources
    news_data = []
    # Get Finnhub news
    try:
        finnhub_news = data_fetcher.get_company_news(symbol)
        if not isinstance(finnhub_news, list):
            print(f"[WARN] finnhub_news is not a list: {type(finnhub_news)}; value={finnhub_news}")
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
            print(f"[WARN] yahoo_news is not a list: {type(yahoo_news)}; value={yahoo_news}")
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
            print(f"[WARN] alpha_news is not a list: {type(alpha_news)}; value={alpha_news}")
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
            print(f"[WARN] reddit_news is not a list: {type(reddit_news)}; value={reddit_news}")
            reddit_news = []
        print(f"✅ Got {len(reddit_news)} Reddit posts for {symbol}")
        news_data.extend(reddit_news)
    except Exception as e:
        print(f"[ERROR] Failed to get Reddit news for {symbol}: {str(e)}")
        reddit_news = []
    print(f"[DEBUG] News source counts: finnhub={len(finnhub_news)}, yahoo={len(yahoo_news)}, alpha={len(alpha_news)}, reddit={len(reddit_news)}")
    if not news_data:
        print(f"📊 No news data available for {symbol}, using price-based sentiment analysis...")
    log_info("🔍 Using Ollama (local) for sentiment analysis...")
    sentiment_result = analyze_sentiment_with_fallback(news_data, price_data, symbol)
    print(f"🔍 DEBUG: sentiment_result type: {type(sentiment_result)}, value: {sentiment_result}")
    if not isinstance(sentiment_result, dict):
        print(f"[ERROR] sentiment_result is not a dict: {type(sentiment_result)} - {sentiment_result}")
        return {"error": f"Sentiment analysis returned invalid data type: {type(sentiment_result)}"}
    try:
        signal_data = sentiment_analyzer.get_trading_signal(sentiment_result)
        print(f"🔍 DEBUG: signal_data type: {type(signal_data)}, value: {signal_data}")
    except (TypeError, ValueError) as e:
        print(f"[ERROR] get_trading_signal failed for {symbol}: {str(e)}")
        return {"error": f"Trading signal generation failed: {str(e)}"}
    if not isinstance(signal_data, dict):
        print(f"[ERROR] signal_data is not a dict: {type(signal_data)} - {signal_data}")
        return {"error": f"Trading signal returned invalid data type: {type(signal_data)}"}
    trading_recommendation = trading_strategy.get_recommendation(
        symbol, price_data, sentiment_result, signal_data
    )
    print(f"🔍 DEBUG: trading_recommendation type: {type(trading_recommendation)}, value: {trading_recommendation}")
    if not isinstance(trading_recommendation, dict):
        print(f"[ERROR] trading_recommendation is not a dict: {type(trading_recommendation)} - {trading_recommendation}")
        return {"error": f"Trading recommendation returned invalid data type: {type(trading_recommendation)}"}
    
    # Generate options recommendation using OptionsStrategy
    try:
        from src.trading.enhanced_trading_strategy import OptionsStrategy
        print(f"[DEBUG] Successfully imported OptionsStrategy for {symbol}")  # ADDED DEBUG
        options_strategy = OptionsStrategy()
        print(f"[DEBUG] Successfully created OptionsStrategy instance for {symbol}")  # ADDED DEBUG
        options_recommendation = options_strategy.get_recommendation(
            symbol, price_data, sentiment_result, signal_data
        )
        print(f"🔍 DEBUG: options_recommendation type: {type(options_recommendation)}, value: {options_recommendation}")
    except Exception as e:
        print(f"[ERROR] Failed to generate options recommendation for {symbol}: {str(e)}")
        import traceback
        traceback.print_exc()  # ADDED DEBUG
        options_recommendation = {
            "symbol": symbol,
            "action": "HOLD",
            "recommendation": "Options analysis failed",
            "reasoning": f"Error generating options recommendation: {str(e)}",
            "confidence": 0.0
        }
    
    result = {
        "symbol": symbol,
        "price_data": price_data,
        "sentiment_analysis": sentiment_result,
        "news_count": len(news_data),
        "news_sources": {
            "finnhub": len(finnhub_news),
            "yahoo_finance": len(yahoo_news),
            "alpha_vantage": len(alpha_news),
            "reddit": len(reddit_news),
        },
        "trading_recommendation": trading_recommendation,
        "options_recommendation": options_recommendation,
        "timestamp": datetime.now().isoformat(),
    }
    print(f"🔍 DEBUG: Final result keys: {list(result.keys())}")
    print(f"🔍 DEBUG: options_recommendation in result: {'options_recommendation' in result}")
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


def create_app():
    """Create and start the Flask application"""
    import sys
    print('[DEBUG] Entered create_app()')
    try:
        from src.core.logger import log_info, log_system_event
        log_info("Starting Flask application via create_app", "system")
        log_system_event("Flask application starting", "INFO")
        print('[DEBUG] About to start socketio.run() on 0.0.0.0:5001')
        sys.stdout.flush()
        # Start the SocketIO server
        socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)
        print('[DEBUG] socketio.run() has exited (should not happen unless server stops)')
        sys.stdout.flush()
    except Exception as e:
        print(f'[DEBUG] Exception in create_app: {e}')
        from src.core.logger import log_exception
        log_exception("Failed to start Flask application", e)
        sys.stdout.flush()

# Global cache for preloaded data
preloaded_data = None
preload_timestamp = None

# Function to preload data
def preload_stock_data():
    import sys
    from requests.exceptions import HTTPError, RequestException
    print('[DEBUG] Starting background preload_stock_data()')
    sys.stdout.flush()
    
    # Track rate limiting status for each data source
    rate_limited_sources = set()
    
    try:
        # Use internal function call instead of HTTP request to avoid circular dependency
        from src.data.data_fetcher import DataFetcher
        from src.core.config import Config
        
        # Initialize components if not already done
        if 'data_fetcher' not in globals():
            global data_fetcher
            data_fetcher = DataFetcher()
        
        # Get S&P 500 analysis directly
        print('[DEBUG] Fetching S&P 500 analysis for preloading...')
        start_time = time.time()
        
        # Get top 3 gainers and losers from Alpha Vantage
        market_movers = data_fetcher.get_top_gainers_losers(limit=3)
        test_symbols = market_movers.get('gainers', []) + market_movers.get('losers', [])
        print(f'[DEBUG] Found market movers: {market_movers}')
        
        # Fallback to test symbols if no market movers found
        if not test_symbols:
            test_symbols = ['AAPL', 'MSFT', 'GOOGL']
            print('[DEBUG] Using fallback test symbols')
        
        # Analyze each stock using a simplified analysis
        enhanced_analysis = []
        
        for i, symbol in enumerate(test_symbols):
            stock_info = {
                'symbol': symbol,
                'price': 0,
                'change': 0,
                'change_percent': 0,
                'timestamp': datetime.now().isoformat(),
                'sources_used': [],
                'sources_skipped': []
            }
            
            try:
                print(f'🔍 Analyzing {symbol} ({i+1}/{len(test_symbols)})...')
                
                # Get basic stock data
                try:
                    stock_data = data_fetcher.get_market_data(symbol)
                    if stock_data and 'price' in stock_data:
                        stock_info.update({
                            'price': stock_data.get('price', 0),
                            'change': stock_data.get('change', 0),
                            'change_percent': stock_data.get('change_percent', 0)
                        })
                        stock_info['sources_used'].append('market_data')
                        print(f'✅ Got market data for {symbol}')
                    else:
                        stock_info['sources_skipped'].append('market_data')
                        print(f'⚠️ No market data available for {symbol}')
                except Exception as e:
                    stock_info['sources_skipped'].append('market_data')
                    print(f'⚠️ Error getting market data for {symbol}: {str(e)}')
                
                # Always try to get news, even if some sources are rate limited
                try:
                    # Get news data with error handling
                    news = data_fetcher.get_company_news(symbol)
                    if news and isinstance(news, list):
                        # Filter out any None or invalid news items
                        valid_news = [n for n in news if n and isinstance(n, dict)]
                        if valid_news:
                            stock_info['news'] = valid_news[:3]  # Limit to 3 news items
                            stock_info['sources_used'].append('news')
                            print(f'✅ Added {len(valid_news[:3])} news items for {symbol} from {len(set(n.get("source", "") for n in valid_news))} sources')
                        else:
                            stock_info['sources_skipped'].append('news')
                            print(f'⚠️ No valid news items found for {symbol}')
                    else:
                        stock_info['sources_skipped'].append('news')
                        print(f'⚠️ No news data available for {symbol}')
                except Exception as news_err:
                    stock_info['sources_skipped'].append('news')
                    print(f'⚠️ Error getting news for {symbol}: {str(news_err)}')
                
                enhanced_analysis.append(stock_info)
                
            except Exception as e:
                print(f'[ERROR] Failed to process {symbol}: {str(e)}')
                # Add basic info even if there was an error
                enhanced_analysis.append(stock_info)
        
        # Prepare the final data structure
        status_msg = 'Analysis complete'
        
        # Check which sources were used and which were skipped
        all_sources_used = set()
        all_sources_skipped = set()
        for analysis in enhanced_analysis:
            all_sources_used.update(analysis.get('sources_used', []))
            all_sources_skipped.update(analysis.get('sources_skipped', []))
        
        if all_sources_skipped:
            status_msg += f' (Some sources unavailable: {sorted(all_sources_skipped)})'
        
        preloaded_data = {
            'enhanced_analysis': enhanced_analysis,
            'total_analyzed': len(enhanced_analysis),
            'opportunities_found': len([s for s in enhanced_analysis if s.get('change_percent', 0) > 0]),
            'timestamp': datetime.now().isoformat(),
            'cache_duration': time.time() - start_time,
            'status': 'success',
            'sources_used': sorted(all_sources_used),
            'sources_skipped': sorted(all_sources_skipped),
            'message': status_msg,
            'version': '1.0',
            'data_sources': sorted(all_sources_used),
            'cache_timestamp': int(time.time())
        }
        preload_timestamp = datetime.now()
        
        # Save to database
        save_preloaded_data_to_db(preloaded_data)
        
        # Clean up old entries, keeping only the most recent 6 entries (3 winners + 3 losers)
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get the IDs of all entries
                    cur.execute("""
                        SELECT id FROM preloaded_data 
                        ORDER BY timestamp DESC
                    """)
                    all_ids = [row[0] for row in cur.fetchall()]
                    
                    # If we have more than 6 entries, delete the oldest ones
                    if len(all_ids) > 6:
                        # Keep only the 6 most recent entries
                        ids_to_keep = all_ids[:6]
                        # Delete all other entries
                        cur.execute("""
                            DELETE FROM preloaded_data 
                            WHERE id != ALL(%s)
                        """, (ids_to_keep,))
                        conn.commit()
                        print(f'[DEBUG] Cleaned up {len(all_ids) - 6} old entries from preloaded_data table')
        except Exception as e:
            print(f'[WARNING] Error cleaning up old entries: {e}')
        
        print(f'[DEBUG] Successfully preloaded {len(enhanced_analysis)} stock analyses in {time.time() - start_time:.2f} seconds')
        
    except Exception as e:
        print(f'[ERROR] Exception in preload_stock_data: {str(e)}')
        sys.stdout.flush()
    print('[DEBUG] Finished background preload_stock_data()')
    sys.stdout.flush()

# Schedule the preload task
scheduler = BackgroundScheduler()
# Run at 9:35 AM on trading days
scheduler.add_job(preload_stock_data, 'cron', day_of_week='mon-fri', hour=9, minute=35, timezone='America/New_York')
scheduler.start()

# Preload data in a background thread on startup (do NOT block main thread)
def start_preload_in_background():
    preload_thread = threading.Thread(target=preload_stock_data, daemon=True)
    preload_thread.start()

start_preload_in_background()

@app.route("/api/preloaded_data")
def get_preloaded_data():
    """Endpoint to get preloaded stock data directly from database"""
    return load_preloaded_data_from_db()

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
                    timestamp = row[0]
                    
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
                        symbol, type, price, change_amount, change_percent, volume, analysis_data = row
                        # Make sure the analysis_data has the correct price and change values
                        if analysis_data and isinstance(analysis_data, dict):
                            analysis_data['price'] = price
                            analysis_data['change'] = change_amount
                            analysis_data['change_percent'] = change_percent
                            analysis_data['volume'] = volume
                            enhanced_analysis.append(analysis_data)
                    
                    opportunities_found = len([s for s in enhanced_analysis if s.get('change_percent', 0) > 0])
                    
                    response_data = {
                        'enhanced_analysis': enhanced_analysis,
                        'total_analyzed': len(enhanced_analysis),
                        'opportunities_found': opportunities_found,
                        'timestamp': timestamp.isoformat(),
                        'cache_status': 'database_fresh'
                    }
                    
                    return create_api_response(
                        data=response_data,
                        message=f"Successfully loaded {len(enhanced_analysis)} market movers from database"
                    )
                else:
                    return create_api_response(
                        data={
                            'enhanced_analysis': [],
                            'total_analyzed': 0,
                            'opportunities_found': 0,
                            'timestamp': datetime.now().isoformat(),
                            'fallback': True
                        },
                        message="No market movers found in database",
                        success=False
                    )
                    
    except Exception as e:
        print(f'[ERROR] Failed to load market movers from database: {str(e)}')
        return create_api_response(
            data={
                'enhanced_analysis': [],
                'total_analyzed': 0,
                'opportunities_found': 0,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'fallback': True
            },
            message="Error loading market movers from database",
            success=False,
            error=str(e)
        )

@app.route("/api/frontend_logs", methods=["POST"])
def frontend_logs():
    """Endpoint to receive frontend logs"""
    try:
        data = request.get_json()
        if not data:
            return create_api_response(error="No log data provided", status_code=400)
        
        # Extract log information
        level = data.get('level', 'INFO')
        message = data.get('message', '')
        timestamp = data.get('timestamp', datetime.now().isoformat())
        session_id = data.get('sessionId', 'unknown')
        
        # Log the frontend message
        log_message = f"[FRONTEND] [{session_id}] {message}"
        
        if level == 'ERROR':
            log_error(log_message, "frontend")
        elif level == 'WARN':
            log_warning(log_message, "frontend")
        elif level == 'DEBUG':
            log_debug(log_message, "frontend")
        else:
            log_info(log_message, "frontend")
        
        return create_api_response(message="Log received successfully")
        
    except Exception as e:
        log_exception("Frontend logs endpoint", e)
        return create_api_response(error=str(e), status_code=500)

def save_preloaded_data_to_db(data_to_save=None):
    global preloaded_data
    try:
        # Use provided data or fall back to global preloaded_data
        data = data_to_save if data_to_save is not None else preloaded_data
        if not data or 'enhanced_analysis' not in data:
            print('[WARNING] No valid data provided to save_preloaded_data_to_db')
            return False
            
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # First clear existing entries
                cur.execute("TRUNCATE TABLE market_movers")
                
                # Insert new entries
                for stock in data['enhanced_analysis']:
                    # Ensure we have valid market data
                    if not stock.get('price') or stock.get('price') == 0:
                        # Try to fetch market data if not already present
                        try:
                            data_fetcher = DataFetcher()
                            market_data = data_fetcher.get_market_data(stock.get('symbol'))
                            if market_data and 'price' in market_data:
                                stock.update({
                                    'price': market_data.get('price', 0),
                                    'change': market_data.get('change', 0),
                                    'change_percent': market_data.get('change_percent', 0),
                                    'volume': market_data.get('volume', 0)
                                })
                                print(f"✅ Updated market data for {stock.get('symbol')}: price={stock.get('price')}, change={stock.get('change_percent')}%")
                        except Exception as e:
                            print(f"⚠️ Failed to fetch market data for {stock.get('symbol')}: {e}")
                    
                    stock_type = 'GAINER' if stock.get('change_percent', 0) > 0 else 'LOSER'
                    cur.execute("""
                        INSERT INTO market_movers 
                        (symbol, type, price, change_amount, change_percent, 
                         volume, timestamp, analysis_data)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        stock.get('symbol'),
                        stock_type,
                        stock.get('price', 0),
                        stock.get('change', 0),
                        stock.get('change_percent', 0),
                        stock.get('volume', 0),
                        datetime.now(),
                        Json(stock)  # Store full analysis as JSONB for flexibility
                    ))
                conn.commit()
        print(f'[DEBUG] Saved {len(data["enhanced_analysis"])} market movers to database')
        return True
    except Exception as e:
        print(f'[ERROR] Failed to save market movers to database: {e}')
        return False

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
                    preload_timestamp = row[0]
                    
                    # Get all market movers
                    cur.execute("""
                        SELECT analysis_data FROM market_movers
                        ORDER BY 
                            CASE WHEN type = 'GAINER' THEN 0 ELSE 1 END,
                            change_percent DESC
                    """)
                    
                    # Reconstruct the data in the expected format
                    enhanced_analysis = [row[0] for row in cur.fetchall()]
                    preloaded_data = {
                        'enhanced_analysis': enhanced_analysis,
                        'total_analyzed': len(enhanced_analysis),
                        'opportunities_found': len([s for s in enhanced_analysis if s.get('change_percent', 0) > 0]),
                        'timestamp': preload_timestamp.isoformat(),
                        'status': 'success'
                    }
                    print(f'[DEBUG] Loaded {len(enhanced_analysis)} market movers from database')
                else:
                    print('[DEBUG] No market movers found in database')
    except Exception as e:
        print(f'[ERROR] Failed to load preloaded data from database: {e}')

# At startup, load from database before running preload_stock_data
load_preloaded_data_from_db()

if __name__ == "__main__":
    create_app()

