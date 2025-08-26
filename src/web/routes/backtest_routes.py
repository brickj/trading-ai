"""
Backtest routes for backtesting functionality
"""

from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timedelta
import json

# Import helper functions
from ..helpers import (
    create_api_response, 
    handle_api_error, 
    get_request_params, 
    validate_symbol, 
    execute_db_query, 
    api_error_handler
)

# Import core modules
from ...core.logger import trading_logger, log_exception

# Import services
from ..services import backtest_service

# Create blueprint
backtest_bp = Blueprint('backtest', __name__)


@backtest_bp.route("/backtest")
def backtest_page():
    """Backtesting page"""
    return render_template("backtest.html")


@backtest_bp.route("/api/backtest", methods=["POST"])
def backtest():
    """Run backtest for a symbol, with DB persistence and prepopulation."""
    try:
        data = request.get_json()
        if not data:
            return create_api_response(
                error="Request body is required",
                status_code=400
            )

        symbol = data.get("symbol", "").strip().upper()
        if not symbol:
            return create_api_response(
                error="Symbol is required",
                status_code=400
            )

        # Get backtest parameters
        days_back = int(data.get("days_back", 30))
        initial_capital = float(data.get("initial_capital", 10000))

        # Use the backtest service
        result = backtest_service.run_backtest(symbol, days_back, initial_capital)
        
        if "error" in result:
            return create_api_response(
                error=result["error"],
                status_code=500
            )

        return create_api_response(data=result)

    except Exception as e:
        return handle_api_error(e, "backtest endpoint")


@backtest_bp.route("/api/backtest/historical", methods=["POST"])
def backtest_historical_recommendations():
    """Run backtest based on historical recommendations from the database."""
    try:
        data = request.get_json()
        if not data:
            return create_api_response(
                error="Request body is required",
                status_code=400
            )

        symbol = data.get("symbol", "").strip().upper()
        days_back = int(data.get("days_back", 30))
        initial_capital = float(data.get("initial_capital", 10000))

        # Get historical recommendations using the service
        recommendations_data = backtest_service.get_backtest_recommendations(symbol, days_back)
        recommendations = recommendations_data.get("recommendations", [])
        
        if not recommendations:
            return create_api_response(
                data={
                    "symbol": symbol,
                    "trades": [],
                    "total_return": 0,
                    "message": "No historical recommendations found"
                }
            )

        # Process recommendations into backtest results using the service
        backtest_results = backtest_service.process_historical_recommendations(recommendations)

        return create_api_response(data=backtest_results)

    except Exception as e:
        return handle_api_error(e, "backtest_historical endpoint")


@backtest_bp.route("/api/backtest/recommendations", methods=["GET"])
def get_backtest_recommendations():
    """Get historical recommendations for backtesting analysis."""
    try:
        symbol = request.args.get("symbol", "").strip().upper()
        days_back = int(request.args.get("days_back", 30))
        strategy_type = request.args.get("strategy_type", "").strip().lower()

        # Use the backtest service
        result = backtest_service.get_backtest_recommendations(symbol, days_back, strategy_type)
        
        return create_api_response(data=result)

    except Exception as e:
        return handle_api_error(e, "get_backtest_recommendations endpoint")


@backtest_bp.route("/api/backtest/stats", methods=["GET"])
def get_backtest_statistics():
    """Get comprehensive backtesting statistics from historical recommendations."""
    try:
        symbol = request.args.get("symbol", "").strip().upper()
        days_back = int(request.args.get("days_back", 30))

        # Use the backtest service
        result = backtest_service.get_backtest_statistics(symbol, days_back)
        
        return create_api_response(data=result)

    except Exception as e:
        return handle_api_error(e, "get_backtest_statistics endpoint")


# Helper functions moved to services/backtest_service.py
