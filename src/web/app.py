"""Application factory and Socket.IO setup for Trading AI UI."""
from __future__ import annotations

from flask import Flask

from src.core.config import Config

from .extensions import init_extensions, socketio
from .routes import register_routes
from .utils.page_logger import page_logger


def create_flask_app(config_object: type[Config] = Config) -> Flask:
    """Create and configure the Flask application instance."""

    app = Flask(__name__)
    app.config.from_object(config_object)
    register_routes(app)
    init_extensions(app)
    return app


app = create_flask_app()


def create_app(host: str | None = None, port: int | None = None) -> Flask:
    """Entry point used by start_app.py to launch the server."""

    host = host or app.config.get("HOST", "0.0.0.0")
    port = port or app.config.get("PORT", 5001)
    page_logger.info(
        f"Starting Trading AI UI on {host}:{port} (debug={app.debug})",
        "system",
    )
    
    # Start the job scheduler in a background thread
    import threading
    def start_scheduler():
        try:
            from start_app import run_scheduled_jobs
            page_logger.info("Starting job scheduler...", "system")
            run_scheduled_jobs()
            page_logger.info("Job scheduler started successfully", "system")
        except Exception as e:
            page_logger.error(f"Failed to start job scheduler: {e}", "system")
    
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    
    socketio.run(
        app,
        host=host,
        port=port,
        debug=app.debug,
        allow_unsafe_werkzeug=True,
    )
    return app


if __name__ == "__main__":
    create_app()
