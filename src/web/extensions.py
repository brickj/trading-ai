"""Application extensions for the Trading AI web app."""

from __future__ import annotations

from typing import Any, Dict, Sequence

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

# Shared extension instances
socketio = SocketIO()
cors = CORS()


def _as_sequence(value: Any) -> Sequence[str]:
    """Normalize configuration values that can be expressed as CSV strings."""

    if isinstance(value, str):
        return tuple(part.strip() for part in value.split(",") if part.strip())
    if isinstance(value, (list, tuple, set, frozenset)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    if value is None:
        return tuple()
    return (str(value).strip(),)


def _build_cors_resources(app: Flask) -> Dict[str, Dict[str, Any]]:
    """Create the CORS resources map using the application configuration."""

    resources = app.config.get("CORS_RESOURCES")
    origins = app.config.get("CORS_ORIGINS", "*")
    
    # For public recommendation app, wildcard CORS is acceptable
    # To restrict CORS, set CORS_ORIGINS in config to specific domains:
    # CORS_ORIGINS = "https://yourdomain.com,https://staging.yourdomain.com"
    
    if resources:
        return resources
    return {r"/*": {"origins": origins}}


def init_extensions(app: Flask) -> None:
    """Initialize Flask extensions bound to the application instance."""

    origins = app.config.get("CORS_ORIGINS", "*")
    methods = _as_sequence(
        app.config.get("CORS_METHODS", ("GET", "POST", "PUT", "DELETE", "OPTIONS"))
    ) or ("GET", "POST", "PUT", "DELETE", "OPTIONS")
    allow_headers = _as_sequence(
        app.config.get("CORS_ALLOW_HEADERS", ("Content-Type", "Authorization"))
    ) or ("Content-Type", "Authorization")

    cors.init_app(
        app,
        resources=_build_cors_resources(app),
        origins=origins,
        methods=methods,
        allow_headers=allow_headers,
        supports_credentials=app.config.get("CORS_SUPPORTS_CREDENTIALS", False),
    )

    socketio.init_app(
        app,
        cors_allowed_origins=app.config.get(
            "SOCKETIO_CORS_ALLOWED_ORIGINS", origins
        ),
        ping_timeout=app.config.get("SOCKETIO_PING_TIMEOUT", 60),
        ping_interval=app.config.get("SOCKETIO_PING_INTERVAL", 25),
    )


__all__ = ["socketio", "cors", "init_extensions"]
