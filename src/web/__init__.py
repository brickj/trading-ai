"""
Web application components.
This package contains:
- Flask application setup
- Web routes and views
- Template management
- Static assets
"""

from .app import app, socketio, create_app

__all__ = ["app", "socketio", "create_app"]
