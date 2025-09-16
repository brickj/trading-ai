"""Application extensions for the Trading AI web app."""
from flask_socketio import SocketIO

# Socket.IO instance shared across blueprints
socketio = SocketIO(cors_allowed_origins="*")

__all__ = ["socketio"]
