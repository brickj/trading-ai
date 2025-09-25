"""Portfolio and simulated trading endpoints."""
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from ..helpers import create_api_response
from ..utils.page_logger import page_logger
from ..dependencies import data_fetcher, trading_strategy, sentiment_analyzer
from ..services.analysis_utils import analyze_sentiment_with_fallback


portfolio_bp = Blueprint("portfolio", __name__)

log_exception = page_logger.exception


@portfolio_bp.route("/api/execute_trade", methods=["POST"])
def execute_trade():
    """Execute a simulated trade based on current analysis."""
    try:
        data = request.get_json() or {}
        symbol = data.get("symbol", "").upper()
        if not symbol:
            return create_api_response(error="Symbol is required", status_code=400)

        price_data = data_fetcher.get_stock_price(symbol)
        if not isinstance(price_data, dict) or "current_price" not in price_data:
            return create_api_response(
                error=f"Invalid price data received for {symbol}: type={type(price_data)}",
                status_code=500,
            )

        news_data = data_fetcher.get_company_news(symbol, days_back=7)
        sentiment_data = analyze_sentiment_with_fallback(news_data, price_data, symbol)
        signal_data = sentiment_analyzer.get_trading_signal(sentiment_data)

        trade_signal = trading_strategy.generate_trade_signal(
            symbol, price_data["current_price"], sentiment_data, signal_data
        )
        execution_result = trading_strategy.execute_trade(trade_signal)
        portfolio_summary = trading_strategy.get_portfolio_summary()

        return jsonify(
            {
                "trade_signal": trade_signal,
                "execution_result": execution_result,
                "portfolio_summary": portfolio_summary,
                "simulation_notice": {
                    "message": "🚨 IMPORTANT: This is a SIMULATED trade for educational purposes only.",
                    "details": [
                        "❌ No real broker API is connected",
                        "❌ No actual money is being traded",
                        "❌ This is paper trading simulation only",
                        "⚠️ To enable real trading, integrate with:",
                        "   • Robinhood API",
                        "   • Interactive Brokers API",
                        "   • TD Ameritrade API",
                        "   • E*TRADE API",
                        "   • Schwab API",
                        "   • Or other broker APIs",
                    ],
                    "next_steps": "Contact the developer to add real trade execution API integration for live trading.",
                    "disclaimer": "Trading options involves substantial risk of loss and is not suitable for all investors.",
                },
            }
        )
    except Exception as exc:  # pragma: no cover - defensive fallback
        return (
            jsonify(
                {
                    "error": str(exc),
                    "simulation_notice": {
                        "message": "🚨 This would have been a simulated trade - no real trading API is connected.",
                        "details": [
                            "Real trade execution API integration needed for live trading"
                        ],
                    },
                }
            ),
            500,
        )


@portfolio_bp.route("/api/portfolio")
def portfolio():
    """Return mock portfolio data for demo purposes."""
    try:
        portfolio_summary = {
            "current_capital": 125000,
            "initial_capital": 100000,
            "open_positions": 8,
            "positions_value": 85000,
            "total_trades": 45,
            "total_value": 125000,
            "unrealized_pnl": 25000,
            "note": "🔴 MOCK DATA - No real portfolio tracking implemented",
        }

        recent_trades = [
            {
                "symbol": "AAPL",
                "action": "BUY",
                "quantity": 100,
                "price": 175.50,
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "pnl": 250.00,
                "status": "closed",
            },
            {
                "symbol": "TSLA",
                "action": "SELL",
                "quantity": 50,
                "price": 245.75,
                "timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
                "pnl": -125.00,
                "status": "closed",
            },
            {
                "symbol": "NVDA",
                "action": "BUY",
                "quantity": 75,
                "price": 890.25,
                "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
                "pnl": 1875.00,
                "status": "closed",
            },
            {
                "symbol": "META",
                "action": "BUY",
                "quantity": 120,
                "price": 485.30,
                "timestamp": (datetime.now() - timedelta(hours=8)).isoformat(),
                "pnl": 456.00,
                "status": "closed",
            },
        ]

        open_positions = [
            {
                "symbol": "MSFT",
                "quantity": 60,
                "entry_price": 422.15,
                "current_price": 430.25,
                "unrealized_pnl": 486.00,
                "entry_date": (datetime.now() - timedelta(days=5)).date().isoformat(),
            },
            {
                "symbol": "AMD",
                "quantity": 80,
                "entry_price": 162.75,
                "current_price": 167.80,
                "unrealized_pnl": 404.00,
                "entry_date": (datetime.now() - timedelta(days=3)).date().isoformat(),
            },
        ]

        return create_api_response(
            data={
                "summary": portfolio_summary,
                "recent_trades": recent_trades,
                "open_positions": open_positions,
                "message": "Portfolio data is simulated. Connect to a brokerage API for live trading.",
            }
        )
    except Exception as exc:
        log_exception("Portfolio endpoint", exc)
        return create_api_response(error=str(exc), status_code=500)


__all__ = ["portfolio_bp"]
