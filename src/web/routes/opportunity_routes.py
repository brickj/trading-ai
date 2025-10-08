"""Trading opportunity routes for news and watchlist analysis."""
from datetime import datetime
import traceback

from flask import Blueprint, request

from ..helpers import create_api_response
from ..utils.page_logger import page_logger
from ..dependencies import watchlist_manager
from ..extensions import socketio
from ..services import system_service
from src.core.logger import log_exception
from src.core.batch_processor import batch_processor_instance, create_watchlist_tasks
from src.core.redis_cache import redis_cache


opportunities_bp = Blueprint("opportunities", __name__)

trading_logger = page_logger.logger
log_error = page_logger.error
log_info = page_logger.info
log_exc = page_logger.exception

news_monitor = system_service.get_news_monitor()


@opportunities_bp.route("/api/news_opportunities")
def news_opportunities():
    """Get news-driven trading opportunities from preloaded data (fast) with Redis caching."""
    cache_key = "news_opportunities"
    
    # Try Redis cache first (faster)
    if redis_cache.health_check():
        cached_data = redis_cache.get(cache_key)
        if cached_data:
            return create_api_response(data=cached_data)
    
    trading_logger.api_logger.info(
        "[DEBUG] Entered news_opportunities endpoint (preloaded mode)"
    )
    try:
        ip = request.remote_addr or "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")
        trading_logger.api_logger.info(
            f"[DEBUG] news_opportunities request | IP: {ip} | UA: {user_agent}"
        )

        refresh = request.args.get("refresh", default=0, type=int)
        if not refresh:
            try:
                from src.data.preload_news_opportunities import (
                    get_latest_preloaded_news_opportunities,
                )

                preloaded = get_latest_preloaded_news_opportunities()
                if preloaded and preloaded.get("opportunities") is not None and not preloaded.get("error"):
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
                trading_logger.api_logger.warning(
                    f"[DEBUG] No preloaded news opportunities found in DB! Error: {preloaded.get('error', 'None')}"
                )
            except Exception as db_error:
                trading_logger.api_logger.warning(
                    f"[DEBUG] Database unavailable for preloaded data, falling back to live analysis: {str(db_error)}"
                )

        trading_logger.api_logger.info(
            "[DEBUG] Running fresh news opportunities analysis and updating cache..."
        )
        if refresh:
            try:
                from src.data.preload_news_opportunities import preload_news_opportunities

                preload_news_opportunities()
                from src.data.preload_news_opportunities import (
                    get_latest_preloaded_news_opportunities,
                )

                preloaded = get_latest_preloaded_news_opportunities()
                if preloaded and preloaded.get("opportunities") is not None and not preloaded.get("error"):
                    return create_api_response(
                        data={
                            "opportunities": preloaded["opportunities"],
                            "count": len(preloaded["opportunities"]),
                            "cached": True,
                            "refreshed": True,
                            "cache_timestamp": preloaded["timestamp"],
                        }
                    )
                trading_logger.api_logger.warning(
                    f"[DEBUG] Failed to refresh preloaded data, falling back to live analysis. Error: {preloaded.get('error', 'Unknown')}"
                )
            except Exception as db_error:
                trading_logger.api_logger.warning(
                    f"[DEBUG] Database unavailable for refresh, falling back to live analysis: {str(db_error)}"
                )

        trading_logger.api_logger.info(
            "[DEBUG] Running fallback real-time news opportunities analysis (slow)"
        )
        trending_symbols = news_monitor.scan_trending_news()
        opportunities = news_monitor.analyze_news_driven_opportunities(trending_symbols)
        
        result_data = {
            "opportunities": opportunities,
            "count": len(opportunities),
            "cached": False,
            "cache_timestamp": datetime.now().isoformat(),
        }
        
        # Cache in Redis for future requests
        if redis_cache.health_check():
            redis_cache.set(cache_key, result_data, ttl=1800)  # 30 minutes
        
        return create_api_response(data=result_data)
    except Exception as exc:
        trading_logger.error_logger.error(
            f"[ERROR] Error in news_opportunities endpoint: {str(exc)}"
        )
        log_exception("News opportunities endpoint", exc)
        return create_api_response(error=str(exc), status_code=500)


@opportunities_bp.route("/api/watchlist_opportunities")
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

        refresh = request.args.get("refresh", default=0, type=int)
        if not refresh:
            try:
                from src.data.preload_watchlist_opportunities import (
                    get_latest_preloaded_watchlist_opportunities,
                )

                preloaded = get_latest_preloaded_watchlist_opportunities()
                if preloaded and preloaded.get("opportunities") is not None and not preloaded.get("error"):
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
                trading_logger.api_logger.warning(
                    f"[DEBUG] No preloaded watchlist opportunities found in DB! Error: {preloaded.get('error', 'None')}"
                )
            except Exception as db_error:
                trading_logger.api_logger.warning(
                    f"[DEBUG] Database unavailable for preloaded watchlist data, falling back to live analysis: {str(db_error)}"
                )

        if refresh:
            try:
                from src.data.preload_watchlist_opportunities import (
                    preload_watchlist_opportunities,
                )

                preload_watchlist_opportunities()
                from src.data.preload_watchlist_opportunities import (
                    get_latest_preloaded_watchlist_opportunities,
                )

                preloaded = get_latest_preloaded_watchlist_opportunities()
                if preloaded and preloaded.get("opportunities") is not None and not preloaded.get("error"):
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
                trading_logger.api_logger.warning(
                    f"[DEBUG] Failed to refresh preloaded watchlist data, falling back to live analysis. Error: {preloaded.get('error', 'Unknown')}"
                )
            except Exception as db_error:
                trading_logger.api_logger.warning(
                    f"[DEBUG] Database unavailable for watchlist refresh, falling back to live analysis: {str(db_error)}"
                )

        trading_logger.api_logger.info(
            "[DEBUG] Running fallback real-time watchlist opportunities analysis (slow)"
        )
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

        tasks = create_watchlist_tasks(watchlist_symbols)

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

        trading_logger.api_logger.info(
            "[DEBUG] Starting real-time batch analysis for watchlist opportunities..."
        )
        batch_result = batch_processor_instance.process_batch_sync(
            tasks, progress_callback
        )

        opportunities = [
            result
            for result in batch_result["results"].values()
            if result and "error" not in result
        ]
        errors = [
            result
            for result in batch_result["results"].values()
            if result and "error" in result
        ]

        normalized_opportunities = []
        for opportunity in opportunities:
            normalized_opportunities.append(
                {
                    "type": "stock",
                    "symbol": opportunity.get("symbol"),
                    "trigger": "watchlist",
                    "timestamp": datetime.now().isoformat(),
                    "news_count": opportunity.get("news_count", 0),
                    "price_data": {
                        "current_price": opportunity.get("current_price", 0),
                        "change": 0,
                        "volume": 0,
                        "change_percent": "0%",
                    },
                    "signal_data": {
                        "action": opportunity.get("action", "HOLD"),
                        "reasoning": opportunity.get(
                            "reasoning", "No reasoning provided"
                        ),
                        "confidence": opportunity.get("confidence", 0),
                        "signal_strength": opportunity.get("signal_strength", 0),
                    },
                    "trade_signal": {
                        "action": opportunity.get("action", "HOLD"),
                        "option_price": 0,
                        "strike_price": 0,
                        "position_size": 1,
                    },
                    "sentiment_data": {
                        "summary": "Watchlist analysis",
                        "confidence": opportunity.get("confidence", 0),
                        "sentiment_score": opportunity.get("sentiment_score", 0),
                    },
                }
            )

        return create_api_response(
            data={
                "opportunities": normalized_opportunities,
                "count": len(normalized_opportunities),
                "opportunities_found": len(normalized_opportunities),
                "total_analyzed": len(watchlist_symbols),
                "errors_count": len(errors),
                "errors": errors[:5],
                "cached": False,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as exc:
        trading_logger.error_logger.error(
            f"[ERROR] Error in watchlist_opportunities endpoint: {str(exc)}"
        )
        log_exception("Watchlist opportunities endpoint", exc)
        return create_api_response(error=str(exc), status_code=500)


__all__ = ["opportunities_bp"]
