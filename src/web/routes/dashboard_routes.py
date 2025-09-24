"""Dashboard and market overview routes."""
from datetime import datetime
import traceback

from flask import Blueprint, jsonify

from ..helpers import create_api_response
from ..utils.page_logger import page_logger
from ..dependencies import recommendation_manager
from ..services import system_service


dashboard_bp = Blueprint("dashboard", __name__)

log_info = page_logger.info
log_error = page_logger.error
log_exception = page_logger.exception
trading_logger = page_logger.logger

# Cached dashboard preload data populated on startup
preloaded_data = None
preload_timestamp = None


def get_system_metrics():
    """Gather basic system metrics for dashboard cards."""
    try:
        import psutil
        import platform

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        process = psutil.Process()

        return {
            "status": "ok",
            "cpu": {
                "system_percent": cpu_percent,
                "process_percent": process.cpu_percent(),
            },
            "memory": {
                "system_percent": memory.percent,
                "system_used_gb": round(memory.used / (1024**3), 2),
                "system_total_gb": round(memory.total / (1024**3), 2),
                "process_mb": round(process.memory_info().rss / (1024**2), 2),
            },
            "disk": {
                "system_percent": disk.percent,
                "system_used_gb": round(disk.used / (1024**3), 2),
                "system_total_gb": round(disk.total / (1024**3), 2),
            },
            "system": {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": platform.python_version(),
                "architecture": platform.machine(),
            },
        }
    except Exception as exc:  # pragma: no cover - defensive logging
        log_exception("Failed to compute system metrics", exc)
        return {
            "status": "error",
            "error": str(exc),
            "timestamp": datetime.now().isoformat(),
        }


@dashboard_bp.route("/api/dashboard/data")
def get_dashboard_data():
    """Get dashboard data for homepage with real data."""
    try:
        system_metrics = get_system_metrics()

        # Recent analyses from recommendations table
        recent_analyses = []
        try:
            with recommendation_manager._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT DISTINCT symbol, recommendation_type, timestamp,
                               final_confidence, action
                        FROM recommendations
                        ORDER BY timestamp DESC
                        LIMIT 3
                        """
                    )
                    for row in cur.fetchall():
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
        except Exception as exc:  # pragma: no cover - fallback logging
            log_exception("Error fetching recent analyses", exc)
            recent_analyses = []

        # Market overview stats
        market_overview = {}
        try:
            with recommendation_manager._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(DISTINCT symbol) FROM recommendations")
                    total_result = cur.fetchone()
                    total_stocks = total_result["count"] if total_result else 0

                    cur.execute(
                        """
                        SELECT COUNT(*) FROM recommendations
                        WHERE timestamp >= NOW() - INTERVAL '24 hours'
                        """
                    )
                    recent_result = cur.fetchone()
                    recent_count = recent_result["count"] if recent_result else 0

                    cur.execute(
                        """
                        SELECT
                            COUNT(*) as total,
                            COUNT(CASE WHEN profitable = TRUE THEN 1 END) as profitable_count
                        FROM recommendations
                        WHERE profitable IS NOT NULL
                        """
                    )
                    success_result = cur.fetchone()
                    if success_result and success_result["total"] > 0:
                        success_rate = (
                            success_result["profitable_count"]
                            / success_result["total"]
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
        except Exception as exc:
            log_exception("Error fetching market overview", exc)
            market_overview = {
                "total_stocks": len(recent_analyses),
                "active_analyses": len(recent_analyses),
                "success_rate": "N/A",
                "last_updated": datetime.now().isoformat(),
            }

        last_analysis = recent_analyses[0] if recent_analyses else None

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
    except Exception as exc:
        log_exception("Dashboard data endpoint", exc)
        return create_api_response(error=str(exc), status_code=500)


@dashboard_bp.route("/api/market_movers")
def get_market_movers():
    """Return cached market movers from the database."""
    try:
        with system_service.get_database_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM market_movers")
                count_result = cur.fetchone()
                if isinstance(count_result, dict):
                    count = count_result.get("count", 0)
                elif isinstance(count_result, (tuple, list)):
                    count = count_result[0] if count_result else 0
                else:
                    try:
                        count = count_result["count"]  # type: ignore[index]
                    except Exception:  # pragma: no cover - fallback
                        count = count_result[0] if hasattr(count_result, "__getitem__") else 0

                if count == 0:
                    return create_api_response(
                        data={
                            "gainers": [],
                            "losers": [],
                            "total_gainers": 0,
                            "total_losers": 0,
                            "timestamp": datetime.now().isoformat(),
                            "source": "market_movers_table",
                            "message": "No market movers data available",
                        }
                    )

                cur.execute(
                    """
                    SELECT symbol, type, change_percent, price, volume, timestamp
                    FROM market_movers
                    ORDER BY timestamp DESC
                    """
                )
                rows = cur.fetchall()

        gainers = []
        losers = []
        for row in rows:
            stock_data = {
                "symbol": row["symbol"],
                "type": row["type"].lower() if row["type"] else "unknown",
                "change_percent": row["change_percent"],
                "price": row["price"],
                "volume": row["volume"],
                "timestamp": row["timestamp"].isoformat()
                if row["timestamp"]
                else None,
            }
            if row["type"] == "GAINER":
                gainers.append(stock_data)
            elif row["type"] == "LOSER":
                losers.append(stock_data)

        gainers.sort(key=lambda item: item["change_percent"], reverse=True)
        losers.sort(key=lambda item: item["change_percent"])

        response_data = {
            "gainers": gainers[:3],
            "losers": losers[:3],
            "total_gainers": len(gainers),
            "total_losers": len(losers),
            "timestamp": datetime.now().isoformat(),
            "source": "market_movers_table",
        }
        return create_api_response(data=response_data)
    except Exception as exc:
        trading_logger.error_logger.error(f"Error in market_movers endpoint: {exc}")
        trading_logger.error_logger.error(traceback.format_exc())
        return create_api_response(error=str(exc), status_code=500)


@dashboard_bp.route("/api/refresh_market_movers", methods=["POST"])
def refresh_market_movers():
    """Trigger the preload job to refresh market movers."""
    try:
        result = system_service.preload_stock_data()
        with system_service.get_database_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM market_movers")
                count_result = cur.fetchone()
                count = count_result["count"] if count_result else 0
        if count > 0:
            return jsonify(
                {
                    "success": True,
                    "message": f"Market movers data refreshed successfully - {count} records updated",
                }
            )
        return jsonify(
            {
                "success": False,
                "error": "No market movers data found in database after refresh",
            }
        )
    except Exception as exc:
        traceback.print_exc()
        return jsonify(
            {"success": False, "error": f"Error refreshing market movers: {str(exc)}"}
        )


def load_preloaded_data_from_db():
    """Populate in-memory cache with latest market mover data."""
    global preloaded_data, preload_timestamp
    try:
        with system_service.get_database_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT timestamp FROM market_movers
                    ORDER BY timestamp DESC
                    LIMIT 1
                    """
                )
                row = cur.fetchone()
                if not row:
                    preloaded_data = None
                    return

                preload_timestamp = row["timestamp"]
                cur.execute(
                    """
                    SELECT analysis_data FROM market_movers
                    ORDER BY
                        CASE WHEN type = 'GAINER' THEN 0 ELSE 1 END,
                        change_percent DESC
                    """
                )
                enhanced_analysis = [r["analysis_data"] for r in cur.fetchall()]
                preloaded_data = {
                    "enhanced_analysis": enhanced_analysis,
                    "total_analyzed": len(enhanced_analysis),
                    "opportunities_found": len(
                        [item for item in enhanced_analysis if item.get("change_percent", 0) > 0]
                    ),
                    "timestamp": preload_timestamp.isoformat()
                    if preload_timestamp
                    else datetime.now().isoformat(),
                    "status": "success",
                }
                log_info(
                    f"Loaded {len(enhanced_analysis)} market movers from database into preloaded_data",
                    "system",
                )
    except Exception as exc:
        log_exception("Failed to load preloaded data from database", exc)
        preloaded_data = None


@dashboard_bp.route("/api/preloaded_data")
def get_preloaded_data():
    """Expose cached market mover data."""
    global preloaded_data
    try:
        if not preloaded_data:
            load_preloaded_data_from_db()
        if preloaded_data:
            return create_api_response(
                data=preloaded_data,
                message=
                f"Successfully loaded {len(preloaded_data.get('enhanced_analysis', []))} market movers from database",
            )
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
    except Exception as exc:
        log_exception("Failed to load preloaded data", exc)
        return create_api_response(
            data={
                "enhanced_analysis": [],
                "total_analyzed": 0,
                "opportunities_found": 0,
                "timestamp": datetime.now().isoformat(),
                "fallback": True,
            },
            message=f"Error loading market movers from database: {str(exc)}",
            success=False,
            error=str(exc),
        )


# Preload market data cache at import time for faster dashboard loads
load_preloaded_data_from_db()

__all__ = [
    "dashboard_bp",
    "get_system_metrics",
    "load_preloaded_data_from_db",
]
