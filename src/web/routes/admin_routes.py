"""Administrative routes for configuration and maintenance tasks."""
from datetime import datetime

from flask import Blueprint, jsonify, request

from ..helpers import create_api_response
from ..utils.page_logger import page_logger
from ..dependencies import watchlist_manager
from ..services import system_service
from ...core.config import Config


admin_bp = Blueprint("admin", __name__)

log_info = page_logger.info
log_error = page_logger.error
log_exception = page_logger.exception

# Job schedules table initialization moved to system service


@admin_bp.route("/api/go_services/health")
def go_services_health():
    """Placeholder health endpoint for Go services."""
    return create_api_response(
        data={
            "go_services_enabled": False,
            "services": {},
            "overall_health": "disabled",
            "message": "Go services are not implemented in this version",
        }
    )


@admin_bp.route("/api/preload_stock_data", methods=["POST"])
def trigger_preload_stock_data():
    """Manually trigger the stock data preload job."""
    try:
        result = system_service.preload_stock_data()
        return jsonify(
            {
                "status": "success",
                "message": "Preload stock data job completed successfully",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    except Exception as exc:
        return jsonify(
            {
                "status": "error",
                "message": f"Failed to trigger preload_stock_data: {str(exc)}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        ), 500


@admin_bp.route("/api/historical_data/update", methods=["POST"])
def trigger_historical_data_update():
    """Manually trigger historical data update job."""
    try:
        from src.data.historical_data_updater import update_historical_data_job

        result = update_historical_data_job()
        if result.get("status") == "success":
            return jsonify(
                {
                    "status": "success",
                    "message": (
                        "Historical data update completed: "
                        f"{result['updated_count']} symbols updated"
                    ),
                    "details": result,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
        return jsonify(
            {
                "status": "error",
                "message": f"Historical data update failed: {result.get('message')}",
                "details": result,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        ), 500
    except Exception as exc:
        log_error(f"Error triggering historical data update: {str(exc)}")
        return jsonify(
            {
                "status": "error",
                "message": f"Failed to trigger historical data update: {str(exc)}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        ), 500


@admin_bp.route("/api/watchlist/config", methods=["GET", "POST"])
def watchlist_config():
    """Get or update watchlist configuration."""
    try:
        log_info(
            f"[WATCHLIST_CONFIG] Incoming {request.method} request from {request.remote_addr}"
        )
        if request.method == "GET":
            stocks = watchlist_manager.get_stocks()
            cryptos = watchlist_manager.get_cryptos()
            response_data = {
                "stocks": [{"symbol": symbol, "notes": ""} for symbol in stocks],
                "crypto": [{"symbol": symbol, "notes": ""} for symbol in cryptos],
                "stock_limit": getattr(Config, "BULK_ANALYSIS_WATCHLIST_LIMIT", 50),
                "news_days": getattr(Config, "BULK_ANALYSIS_NEWS_DAYS", 2),
                "stats": {"stocks": stocks, "crypto": cryptos},
                "message": f"Watchlist contains {len(stocks)} stocks and {len(cryptos)} cryptos",
            }
            return create_api_response(response_data)

        data = request.get_json() or {}
        action = data.get("action")
        symbol = data.get("symbol", "").upper().strip()
        symbol_type = data.get("type", "stock")

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
                return create_api_response(
                    success=False,
                    error=f"Failed to add {symbol} to stock watchlist",
                    status_code=400,
                )
            if action == "remove":
                success = watchlist_manager.remove_stock(symbol)
                if success:
                    return create_api_response(
                        {
                            "message": f"Removed {symbol} from stock watchlist",
                            "symbol": symbol,
                            "type": "stock",
                        }
                    )
                return create_api_response(
                    success=False,
                    error=f"Failed to remove {symbol} from stock watchlist",
                    status_code=400,
                )

        if symbol_type == "crypto":
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
                return create_api_response(
                    success=False,
                    error=f"Failed to add {symbol} to crypto watchlist",
                    status_code=400,
                )
            if action == "remove":
                success = watchlist_manager.remove_crypto(symbol)
                if success:
                    return create_api_response(
                        {
                            "message": f"Removed {symbol} from crypto watchlist",
                            "symbol": symbol,
                            "type": "crypto",
                        }
                    )
                return create_api_response(
                    success=False,
                    error=f"Failed to remove {symbol} from crypto watchlist",
                    status_code=400,
                )

        return create_api_response(
            success=False,
            error="Invalid action or watchlist type",
            status_code=400,
        )
    except Exception as exc:
        log_exception("watchlist_config", exc)
        return create_api_response(
            success=False,
            error="Failed to manage watchlist configuration",
            status_code=500,
        )


@admin_bp.route("/api/job_schedules", methods=["GET"])
def get_job_schedules():
    """Return all job schedules."""
    try:
        with system_service.get_database_connection() as conn:
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
        return create_api_response(data={"schedules": schedules})
    except Exception as exc:
        log_exception("get_job_schedules", exc)
        return create_api_response(error=str(exc), status_code=500)


@admin_bp.route("/api/job_schedules", methods=["POST"])
def create_job_schedule():
    """Create a new job schedule entry."""
    try:
        data = request.get_json() or {}
        job_name = data.get("job_name")
        run_time = data.get("run_time")
        if not job_name or not run_time:
            return create_api_response(
                success=False,
                error="job_name and run_time are required",
                status_code=400,
            )
        with system_service.get_database_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO job_schedules (job_name, run_time, enabled)
                    VALUES (%s, %s, TRUE)
                    RETURNING id
                    """,
                    (job_name, run_time),
                )
                new_id = cur.fetchone()["id"]
        return create_api_response(data={"id": new_id, "job_name": job_name, "run_time": run_time})
    except Exception as exc:
        log_exception("create_job_schedule", exc)
        return create_api_response(error=str(exc), status_code=500)


@admin_bp.route("/api/job_schedules/<int:schedule_id>/enable", methods=["POST"])
def enable_job_schedule(schedule_id):
    """Enable or disable a job schedule."""
    try:
        data = request.get_json() or {}
        enabled = bool(data.get("enabled", True))
        with system_service.get_database_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE job_schedules SET enabled = %s WHERE id = %s",
                    (enabled, schedule_id),
                )
        return create_api_response(
            data={"schedule_id": schedule_id, "enabled": enabled},
            message="Job schedule updated",
        )
    except Exception as exc:
        log_exception("enable_job_schedule", exc)
        return create_api_response(error=str(exc), status_code=500)


@admin_bp.route("/api/job_schedules/<int:schedule_id>", methods=["DELETE"])
def delete_job_schedule(schedule_id):
    """Delete a job schedule entry."""
    try:
        with system_service.get_database_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM job_schedules WHERE id = %s", (schedule_id,))
        return create_api_response(
            data={"schedule_id": schedule_id},
            message="Job schedule deleted",
        )
    except Exception as exc:
        log_exception("delete_job_schedule", exc)
        return create_api_response(error=str(exc), status_code=500)


__all__ = ["admin_bp"]
