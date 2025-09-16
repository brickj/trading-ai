"""Application factory and Socket.IO setup for Trading AI UI."""
from datetime import timedelta

from flask import Flask
from flask_cors import CORS

from .extensions import socketio
from .routes import register_routes
from .utils.page_logger import page_logger
from src.core.config import Config


log_info = page_logger.info
log_error = page_logger.error
log_exception = page_logger.exception
trading_logger = page_logger.logger


def create_flask_app() -> Flask:
    """Create and configure the Flask application instance."""
    app = Flask(__name__)
    register_routes(app)

    CORS(
        app,
        origins="*",
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    app.debug = True
    app.config.update(
        DEBUG=True,
        ENV="development",
        SECRET_KEY="trading_ai_secret_key_change_in_production",
        SEND_FILE_MAX_AGE_DEFAULT=31536000,
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=10),
    )

    socketio.init_app(
        app,
        cors_allowed_origins="*",
        ping_timeout=getattr(Config, "ENHANCED_ANALYSIS_TIMEOUT", 60),
        ping_interval=25,
    )

    return app


app = create_flask_app()


def create_app(host: str = "0.0.0.0", port: int = 5001) -> Flask:
    """Entry point used by start_app.py to launch the server."""
    log_info(f"Starting Trading AI UI on {host}:{port}", "system")
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
    return app


if __name__ == "__main__":
    create_app()
