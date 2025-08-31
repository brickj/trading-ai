"""
Telegram routes for Telegram bot integration
"""

from flask import Blueprint, request, jsonify
from datetime import datetime

# Import helper functions
from ..helpers import (
    create_api_response, 
    handle_api_error, 
    api_error_handler
)

# Import core modules
from ...core.logger import trading_logger, log_exception
from ...core.telegram_alerts import telegram_alerter

# Create blueprint
telegram_bp = Blueprint('telegram', __name__)


@telegram_bp.route("/api/telegram/test")
def test_telegram():
    """Test Telegram bot connectivity"""
    try:
        # Test telegram connection
        connection_result = telegram_alerter.test_connection()
        
        # Construct response with working field at top level as expected by test
        response_data = {
            "status": "success",
            "message": "Telegram connection successful" if connection_result.get("working") else "Telegram connection failed",
            "timestamp": datetime.now().isoformat(),
            "working": connection_result.get("working", False),  # Working field at top level
            "data": {
                "bot_name": connection_result.get("bot_name", "Unknown"),
                "username": connection_result.get("username", "Unknown"),
                "chat_count": connection_result.get("chat_count", 0),
                "chat_ids": connection_result.get("chat_ids", []),
                "working": connection_result.get("working", False)
            }
        }
        
        return jsonify(response_data), 200
    except Exception as e:
        return handle_api_error(e, "test_telegram endpoint")


@telegram_bp.route("/api/telegram/toggle", methods=["POST"])
def toggle_telegram_alerts():
    """Toggle Telegram alerts on/off"""
    try:
        data = request.get_json()
        if not data:
            return create_api_response(
                error="Request body is required",
                status_code=400
            )

        enabled = data.get("enabled", True)
        
        # Toggle telegram alerts
        telegram_alerter.set_enabled(enabled)
        
        return create_api_response(
            data={
                "enabled": enabled,
                "message": f"Telegram alerts {'enabled' if enabled else 'disabled'}",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        return handle_api_error(e, "toggle_telegram_alerts endpoint")


@telegram_bp.route("/api/telegram/send_test", methods=["POST"])
def send_test_telegram():
    """Send a test Telegram message"""
    try:
        data = request.get_json()
        message = data.get("message", "Test message from Trading AI") if data else "Test message from Trading AI"
        
        # Send test message
        success = telegram_alerter.send_message(message)
        
        return create_api_response(
            data={
                "sent": success,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        return handle_api_error(e, "send_test_telegram endpoint")


@telegram_bp.route("/api/telegram/chat_ids", methods=["GET"])
def get_telegram_chat_ids():
    """Get current Telegram chat IDs"""
    try:
        chat_ids = telegram_alerter.get_chat_ids()
        
        return create_api_response(
            data={
                "chat_ids": chat_ids,
                "count": len(chat_ids),
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        return handle_api_error(e, "get_telegram_chat_ids endpoint")


@telegram_bp.route("/api/telegram/add_chat_id", methods=["POST"])
def add_telegram_chat_id():
    """Add a new Telegram chat ID"""
    try:
        data = request.get_json()
        if not data or "chat_id" not in data:
            return create_api_response(
                error="Chat ID is required",
                status_code=400
            )

        chat_id = data["chat_id"]
        
        # Add chat ID
        success = telegram_alerter.add_chat_id(chat_id)
        
        if success:
            return create_api_response(
                data={
                    "chat_id": chat_id,
                    "added": True,
                    "message": f"Chat ID {chat_id} added successfully"
                }
            )
        else:
            return create_api_response(
                error=f"Failed to add chat ID {chat_id}",
                status_code=400
            )
    except Exception as e:
        return handle_api_error(e, "add_telegram_chat_id endpoint")


@telegram_bp.route("/api/telegram/remove_chat_id", methods=["POST"])
def remove_telegram_chat_id():
    """Remove a Telegram chat ID"""
    try:
        data = request.get_json()
        if not data or "chat_id" not in data:
            return create_api_response(
                error="Chat ID is required",
                status_code=400
            )

        chat_id = data["chat_id"]
        
        # Remove chat ID
        success = telegram_alerter.remove_chat_id(chat_id)
        
        if success:
            return create_api_response(
                data={
                    "chat_id": chat_id,
                    "removed": True,
                    "message": f"Chat ID {chat_id} removed successfully"
                }
            )
        else:
            return create_api_response(
                error=f"Failed to remove chat ID {chat_id}",
                status_code=400
            )
    except Exception as e:
        return handle_api_error(e, "remove_telegram_chat_id endpoint")


@telegram_bp.route("/api/telegram/send_raw_message", methods=["POST"])
def send_raw_telegram_message():
    """Send a custom raw message via Telegram to all recipients"""
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return create_api_response(
                error="Message is required",
                status_code=400
            )

        message = data["message"]
        
        # Send raw message
        success = telegram_alerter.send_message(message)
        
        return create_api_response(
            data={
                "message": message,
                "sent": success,
                "timestamp": datetime.now().isoformat(),
                "recipients": len(telegram_alerter.get_chat_ids())
            }
        )
    except Exception as e:
        return handle_api_error(e, "send_raw_telegram_message endpoint")
