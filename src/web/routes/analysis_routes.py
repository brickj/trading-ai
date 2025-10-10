"""
Analysis routes for stock and crypto analysis endpoints
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import time

# Import helper functions
from ..helpers import (
    create_api_response,
    get_request_params,
    validate_symbol,
    execute_db_query,
    get_preloaded_opportunities,
)
from ..utils import api_error_handler
from ..utils.decorators import rate_limit

# Import core modules
from ...core.logger import trading_logger, log_info, log_error, log_exception, log_timing, log_user_actions

# Import services
from ..services import analysis_service, system_service
from ...core.redis_cache import redis_cache

# Create blueprint
analysis_bp = Blueprint('analysis', __name__)


@analysis_bp.route("/api/analyze_stock", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)  # 10 requests per minute
@api_error_handler("analyze_stock")
@log_user_actions(trading_logger)
@log_timing(trading_logger)
def analyze_stock():
    """Analyze a single stock"""
    data = request.get_json()
    trading_logger.api_logger.info(
        f"[DEBUG] Incoming /api/analyze_stock request: {data}"
    )
    if not data or "symbol" not in data:
        trading_logger.api_logger.info(
            f"[DEBUG] /api/analyze_stock missing symbol: {data}"
        )
        return create_api_response(
            error="Missing required parameter: symbol",
            status_code=400
        )

    symbol = data["symbol"].strip().upper() if data["symbol"] else ""
    if not symbol:
        trading_logger.api_logger.info(
            f"[DEBUG] /api/analyze_stock empty symbol: {data}"
        )
        return create_api_response(
            error="Symbol cannot be empty",
            status_code=400
        )

    # Use the analysis service
    result = analysis_service.analyze_single_stock(symbol, use_cache=True)

    if "error" in result:
        # Check if it's a data fetching error (invalid symbol) vs server error
        error_msg = result["error"].lower()
        if any(keyword in error_msg for keyword in ["no data found", "delisted", "invalid", "not found", "404", "may be delisted"]):
            return create_api_response(
                error=f"Invalid symbol '{symbol}': {result['error']}",
                status_code=400
            )
        else:
            return create_api_response(
                error=result["error"],
                status_code=500
            )

    return create_api_response(
        data=result,
        message="Stock analysis completed successfully"
    )


@analysis_bp.route("/api/analyze_bulk", methods=["POST"])
@api_error_handler("analyze_bulk")
def analyze_bulk():
    """Analyze multiple stocks with rate limiting and batching"""
    data = request.get_json()
    if not data or "symbols" not in data:
        return create_api_response(
            error="Missing required parameter: symbols",
            status_code=400
        )

    symbols = data["symbols"]
    if not isinstance(symbols, list) or len(symbols) == 0:
        return create_api_response(
            error="Symbols must be a non-empty list",
            status_code=400
        )

    # Limit batch size
    if len(symbols) > 10:
        return create_api_response(
            error="Maximum 10 symbols allowed per batch",
            status_code=400
        )

    # Clean and validate symbols
    clean_symbols = []
    for symbol in symbols:
        symbol = symbol.strip().upper()
        if symbol:
            clean_symbols.append(symbol)

    # Use the analysis service for bulk processing
    result = analysis_service.analyze_bulk_stocks(clean_symbols, max_concurrent=5)

    return create_api_response(data=result)


@analysis_bp.route("/api/stock/<symbol>/analysis")
@api_error_handler("analyze_stock_by_symbol")
def analyze_stock_by_symbol(symbol):
    """Get stock analysis by symbol"""
    if not symbol:
        return create_api_response(
            error="Symbol parameter is required",
            status_code=400
        )

    symbol = symbol.strip().upper()

    # Use the analysis service
    result = analysis_service.analyze_single_stock(symbol, use_cache=True)

    return create_api_response(data=result)


@analysis_bp.route("/api/sp500_analysis")
@api_error_handler("sp500_analysis")
def sp500_analysis():
    """API endpoint for S&P 500 winners and losers analysis"""
    try:
        # Get query parameters
        limit = request.args.get("limit", type=int)
        refresh = request.args.get("refresh", default=0, type=int) == 1
        
        # Use the analysis service for SP500 analysis
        result = analysis_service.get_sp500_analysis(limit=limit, refresh=refresh)
        
        return create_api_response(data=result)

    except Exception as e:
        trading_logger.error_logger.error(
            f"[ERROR] Error in sp500_analysis endpoint: {str(e)}"
        )
        return create_api_response(
            error=f"Failed to analyze S&P 500: {str(e)}", status_code=500
        )


@analysis_bp.route("/api/crypto_analysis")
@api_error_handler("crypto_analysis")
def crypto_analysis():
    """Analyze cryptocurrencies for trading opportunities with fast preload"""
    # Get query parameters
    refresh_requested = request.args.get('refresh', '0') == '1'

    # Use the analysis service for crypto analysis
    result = analysis_service.get_crypto_analysis(refresh=refresh_requested)

    return create_api_response(data=result)


@analysis_bp.route("/api/enhanced_analysis", methods=["POST"])
@rate_limit(max_requests=5, window_seconds=60)  # 5 requests per minute (more resource intensive)
@api_error_handler("enhanced_analysis")
@log_user_actions(trading_logger)
@log_timing(trading_logger)
def enhanced_analysis():
    """Enhanced stock analysis with multiple strategies and backtesting"""
    data = request.get_json()
    if not data or "symbol" not in data:
        return create_api_response(
            error="Missing required parameter: symbol",
            status_code=400
        )

    symbol = data["symbol"].strip().upper()
    if not symbol:
        return create_api_response(
            error="Symbol cannot be empty",
            status_code=400
        )

    # Services now available via system_service
    enhanced_strategy = system_service.get_enhanced_trading_strategy()
    data_fetcher = system_service.get_data_fetcher()
    sentiment_analyzer = system_service.get_sentiment_analyzer()

    price_data = data_fetcher.get_stock_price(symbol)
    if not price_data or "current_price" not in price_data:
        return create_api_response(
            error=f"Could not fetch price data for {symbol}. Possible reasons: API key issue, rate limiting, or network connectivity problem.",
            status_code=400
        )

    news_data = data_fetcher.get_company_news(symbol, days_back=2)
    if len(news_data) > 3:
        news_data = news_data[:3]

    if len(news_data) < 2:
        sentiment_data = {
            "sentiment_score": 0.1,
            "confidence": 0.6,
            "summary": "Enhanced analysis with limited news data",
        }
    else:
        sentiment_data = sentiment_analyzer.analyze_news_sentiment(news_data, ai_provider="ollama", symbol=symbol)
    signal_data = sentiment_analyzer.get_trading_signal(sentiment_data)

    recommendations = enhanced_strategy.get_comprehensive_recommendations(
        symbol, price_data["current_price"], sentiment_data, signal_data
    )

    if recommendations and "all_recommendations" in recommendations:
        for rec in recommendations["all_recommendations"]:
            if "historical_stats" in rec:
                if rec["historical_stats"].get("total_trades", 0) < 10:
                    print(f"⚠️ Enhanced Analysis: {symbol} has insufficient historical data for proper backtesting")

    response_data = {
        "symbol": symbol,
        "price_data": price_data,
        "sentiment_data": sentiment_data,
        "signal_data": signal_data,
        "news_count": len(news_data),
        "enhanced_analysis": {
            "symbol": symbol,
            "price_data": price_data,
            "sentiment_data": sentiment_data,
            "signal_data": signal_data,
            "recommendations": recommendations,
            "news_data": {"article_count": len(news_data)},
            "analysis_type": "enhanced",
        },
        "timestamp": datetime.now().isoformat(),
    }

    return create_api_response(
        data=response_data,
        message="Enhanced analysis with multiple strategies completed successfully",
    )


@analysis_bp.route("/api/comprehensive_analysis", methods=["POST"])
@rate_limit(max_requests=3, window_seconds=60)  # 3 requests per minute (most resource intensive)
@api_error_handler("comprehensive_analysis")
def comprehensive_analysis():
    """Enhanced analysis with both stock and options recommendations with Redis caching"""
    data = request.get_json()
    symbol = data.get("symbol", "").upper()
    ai_provider = data.get("ai_provider", "ollama")

    if not symbol:
        return create_api_response(error="Symbol is required", status_code=400)
    
    # Check Redis cache first
    cache_key = f"comprehensive_analysis_{symbol}_{ai_provider}"
    if redis_cache.health_check():
        cached_result = redis_cache.get(cache_key)
        if cached_result:
            return create_api_response(data=cached_result)

    # Services now available via system_service
    trading_strategy = system_service.get_trading_strategy()
    data_fetcher = system_service.get_data_fetcher()
    sentiment_analyzer = system_service.get_sentiment_analyzer()

    price_data = data_fetcher.get_stock_price(symbol)
    if not price_data or "current_price" not in price_data:
        return create_api_response(
            error=f"Could not fetch price data for {symbol}. Possible reasons: API key issue, rate limiting, or network connectivity problem.",
            status_code=400
        )

    news_data = data_fetcher.get_company_news(symbol, days_back=3)
    if len(news_data) > 5:
        news_data = news_data[:5]

    sentiment_data = sentiment_analyzer.analyze_news_sentiment(news_data, ai_provider="ollama", symbol=symbol)
    signal_data = sentiment_analyzer.get_trading_signal(sentiment_data)

    recommendation = trading_strategy.get_recommendation(
        symbol, price_data, sentiment_data, signal_data
    )

    result_data = {
        "symbol": symbol,
        "comprehensive_analysis": {
            "symbol": symbol,
            "price_data": price_data,
            "sentiment_data": sentiment_data,
            "signal_data": signal_data,
            "recommendation": recommendation,
            "news_data": {"article_count": len(news_data)},
            "analysis_type": "standard"
        },
        "ai_provider_used": ai_provider,
        "timestamp": datetime.now().isoformat()
    }
    
    # Cache result in Redis
    if redis_cache.health_check():
        redis_cache.set(cache_key, result_data, ttl=1800)  # 30 minutes
    
    return create_api_response(data=result_data)


# analyze_single_stock function moved to services/analysis_service.py
