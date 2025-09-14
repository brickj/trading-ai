#!/usr/bin/env python3
"""Trading AI Flask Web Application."""

from datetime import datetime, timedelta
import threading
import logging
import psutil

from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO
from apscheduler.schedulers.background import BackgroundScheduler

from src.core.config import Config
from src.core.recommendation_manager import RecommendationManager
from src.core.database import get_db_connection
from src.data.data_fetcher import DataFetcher
from src.data.preload_stock_data import preload_stock_data
from src.data.preload_news_opportunities import preload_news_opportunities
from src.data.preload_watchlist_opportunities import (
    preload_watchlist_opportunities,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def log_exception(operation, exception):
    """Log an exception with context."""
    logger.exception(f"{operation}: {exception}")


def create_api_response(data=None, success=True, error=None, status_code=200):
    """Return a standardized JSON API response."""
    return (
        jsonify({"success": success, "data": data, "error": error}),
        status_code,
    )

app = Flask(__name__, template_folder="templates")
CORS(
    app,
    origins="*",
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)
app.config.update(
    DEBUG=True,
    ENV="development",
    SECRET_KEY="trading_ai_secret_key_change_in_production",
    SEND_FILE_MAX_AGE_DEFAULT=31536000,
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=10),
)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    ping_timeout=Config.ENHANCED_ANALYSIS_TIMEOUT,
    ping_interval=25,
)

# Globals used by tests
data_fetcher = DataFetcher()

# Background scheduler configuration
scheduler = BackgroundScheduler()
scheduler.add_job(
    preload_stock_data,
    "cron",
    day_of_week="mon-fri",
    hour=9,
    minute=35,
    timezone="America/New_York",
    id="preload_stock_data",
)
scheduler.add_job(
    preload_news_opportunities,
    "cron",
    day_of_week="mon-fri",
    hour=9,
    minute=40,
    timezone="America/New_York",
    id="preload_news_opportunities",
)
scheduler.add_job(
    preload_watchlist_opportunities,
    "cron",
    day_of_week="mon-fri",
    hour=9,
    minute=45,
    timezone="America/New_York",
    id="preload_watchlist_opportunities",
)
scheduler.start()


def start_preload():
    threading.Thread(target=preload_stock_data, daemon=True).start()
    threading.Thread(target=preload_news_opportunities, daemon=True).start()
    threading.Thread(target=preload_watchlist_opportunities, daemon=True).start()


start_preload()

recommendation_manager = RecommendationManager()


def get_system_metrics():
    """Return basic system metrics."""
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "timestamp": datetime.now().isoformat(),
    }


@app.route("/api/dashboard/data")
def get_dashboard_data():
    """Get dashboard data for homepage with real data."""
    try:
        system_metrics = get_system_metrics()

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

        market_overview = {}
        try:
            with recommendation_manager._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(DISTINCT symbol) FROM recommendations")
                    total = cur.fetchone()
                    total_stocks = total["count"] if total else 0

                    cur.execute(
                        """
                        SELECT COUNT(*) FROM recommendations
                        WHERE timestamp >= NOW() - INTERVAL '24 hours'
                        """
                    )
                    recent_res = cur.fetchone()
                    recent_count = recent_res["count"] if recent_res else 0

                    cur.execute(
                        """
                        SELECT COUNT(*) as total,
                               COUNT(CASE WHEN profitable = TRUE THEN 1 END) as profitable_count
                        FROM recommendations
                        WHERE profitable IS NOT NULL
                        """
                    )
                    success_res = cur.fetchone()
                    if success_res and success_res["total"] > 0:
                        success_rate = (
                            success_res["profitable_count"] / success_res["total"]
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
    except Exception as e:
        log_exception("Dashboard data endpoint", e)
        return create_api_response(error=str(e), status_code=500)


@app.route("/api/preloaded_data")
def get_preloaded_data():
    """Return preloaded market movers from database."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT symbol, type, price, change_amount, change_percent, volume, analysis_data, timestamp
                    FROM market_movers
                    ORDER BY CASE WHEN type = 'GAINER' THEN 0 ELSE 1 END,
                             ABS(change_percent) DESC
                    """
                )
                rows = cur.fetchall()
                timestamp = datetime.now().isoformat()
                if rows:
                    timestamp = rows[0]["timestamp"].isoformat()

                analysis = []
                for row in rows:
                    price = row["price"]
                    if not price or float(price) == 0.0:
                        continue
                    data = row["analysis_data"] if isinstance(row["analysis_data"], dict) else {}
                    data.setdefault("symbol", row["symbol"])
                    data.setdefault("type", "Stock")
                    data.setdefault(
                        "price_data",
                        {
                            "current_price": float(price),
                            "change_amount": float(row.get("change_amount") or 0),
                            "change_percent": float(row.get("change_percent") or 0),
                            "volume": int(row.get("volume") or 0),
                        },
                    )
                    data.setdefault("sentiment_data", {"sentiment_score": 0.0, "confidence": 0.5})
                    data.setdefault("signal_data", {"action": "HOLD", "signal_strength": 0.0})
                    data.setdefault("news_count", 0)
                    analysis.append(data)

                response_data = {
                    "comprehensive_analysis": analysis,
                    "total_analyzed": len(analysis),
                    "opportunities_found": len([s for s in analysis if s.get("change_percent", 0) > 0]),
                    "timestamp": timestamp,
                    "cache_status": "database_fresh",
                }
                return create_api_response(data=response_data)
    except Exception as e:
        log_exception("get_preloaded_data", e)
        return create_api_response(
            data={
                "comprehensive_analysis": [],
                "total_analyzed": 0,
                "opportunities_found": 0,
                "timestamp": datetime.now().isoformat(),
                "fallback": True,
            },
            error=str(e),
            success=False,
        )


@app.route("/scalping_signals")
def scalping_signals():
    """Render the scalping signals page."""
    return render_template("scalping_signals.html")


def create_app(port: int = 5001):
    """Start the SocketIO server."""
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    create_app()
