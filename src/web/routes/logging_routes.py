from flask import Blueprint, request
from datetime import datetime
import json

from ..helpers import create_api_response
from ..utils import handle_api_error
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
    """Handle frontend logging with proper data structure."""
    try:
        data = request.get_json(force=True)
        
        # Handle different data formats
        if 'level' in data and 'message' in data:
            # New format from FrontendLogger
            level = data.get("level", "INFO")
            message = data.get("message", "No message")
            category = data.get("category", "frontend")
            timestamp = data.get("timestamp", datetime.now().isoformat())
            session_id = data.get("sessionId", "unknown")
            url = data.get("url", "unknown")
            
            log_message = f"[FRONTEND {level}] [{category}] {message} | Session: {session_id} | URL: {url} | Time: {timestamp}"
            trading_logger.error_logger.info(log_message)
            
        elif 'page' in data and 'error' in data:
            # Legacy format - redirect to client error handler
            return log_client_error()
        else:
            # Fallback for unknown format
            log_message = f"[FRONTEND LOG] {json.dumps(data)}"
            trading_logger.error_logger.info(log_message)
            
        return create_api_response(message="Frontend log received successfully")
    except Exception as e:
        return handle_api_error(e, "frontend_logs endpoint")
