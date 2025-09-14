"""
Backtest routes for backtesting functionality
"""

from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timedelta
import json

# Import helper functions
from ..helpers import (
    create_api_response,
    get_request_params,
    validate_symbol,
    execute_db_query,
)
from ..utils import api_error_handler

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
@api_error_handler("backtest")
def backtest():
    """Run backtest for a symbol, with DB persistence and prepopulation."""
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


@backtest_bp.route("/api/backtest/historical", methods=["POST"])
@api_error_handler("backtest_historical")
def backtest_historical_recommendations():
    """Run backtest based on historical recommendations from the database."""
    data = request.get_json()
    if not data:
        return create_api_response(
            error="Request body is required",
            status_code=400
        )

    symbol = data.get("symbol", "").strip().upper()
    days_back = int(data.get("days_back", 30))
    initial_capital = float(data.get("initial_capital", 10000))

    recommendations_data = backtest_service.get_backtest_recommendations(symbol, days_back)
    recommendations = recommendations_data.get("recommendations", [])

    if not recommendations:
        return create_api_response(
            data={
                "symbol": symbol,
                "trades": [],
                "total_return": 0,
                "message": "No historical recommendations found",
            }
        )

    backtest_results = backtest_service.process_historical_recommendations(recommendations)

    return create_api_response(data=backtest_results)


@backtest_bp.route("/api/backtest/recommendations", methods=["GET"])
@api_error_handler("get_backtest_recommendations")
def get_backtest_recommendations():
    """Get historical recommendations for backtesting analysis."""
    symbol = request.args.get("symbol", "").strip().upper()
    days_back = int(request.args.get("days_back", 30))
    strategy_type = request.args.get("strategy_type", "").strip().lower()

    result = backtest_service.get_backtest_recommendations(symbol, days_back, strategy_type)

    return create_api_response(data=result)


@backtest_bp.route("/api/backtest/stats", methods=["GET"])
@api_error_handler("get_backtest_statistics")
def get_backtest_statistics():
    """Get comprehensive backtesting statistics from historical recommendations."""
    symbol = request.args.get("symbol", "").strip().upper()
    days_back = int(request.args.get("days_back", 30))

    result = backtest_service.get_backtest_statistics(symbol, days_back)

    return create_api_response(data=result)


# Helper functions moved to services/backtest_service.py
