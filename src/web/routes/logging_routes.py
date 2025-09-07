from flask import Blueprint, request
from datetime import datetime

from ..helpers import create_api_response, handle_api_error
from ..utils.page_logger import page_logger

logging_bp = Blueprint("logging", __name__)

# Access the underlying trading logger and exception helper
trading_logger = page_logger.logger
log_exception = page_logger.exception


@logging_bp.route("/api/log_client_error", methods=["POST"])
def log_client_error():
    """Log client-side JavaScript errors from the frontend."""
    try:
        data = request.get_json(force=True)
        page = data.get("page", "unknown")
        error = data.get("error", "No error message")
        stack = data.get("stack", "No stack trace")
        timestamp = data.get("timestamp", datetime.now().isoformat())
        log_message = (
            f"[CLIENT ERROR] Page: {page} | Error: {error} | "
            f"Stack: {stack} | Timestamp: {timestamp}"
        )
        trading_logger.error_logger.error(log_message)
        log_exception(f"Client error on {page}", error)
        return create_api_response(message="Error logged successfully")
    except Exception as e:  # pragma: no cover - safeguard
        return handle_api_error(e, "log_client_error endpoint")


@logging_bp.route("/api/frontend_logs", methods=["POST"])
def frontend_logs():
    """Alternative endpoint for frontend logging (compatibility)."""
    return log_client_error()
