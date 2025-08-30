"""
Page routes for HTML template rendering
"""

from flask import Blueprint, render_template, request
from datetime import datetime

# Import helper functions
from ..helpers import create_api_response, handle_api_error

# Create blueprint
page_bp = Blueprint('pages', __name__)


@page_bp.route("/")
def index():
    """Main dashboard page"""
    try:
        from ...core.config import Config
        return render_template(
            "index.html",
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            page_title="Trading AI Dashboard",
            historical_lookback_days=Config.HISTORICAL_LOOKBACK_DAYS
        )
    except Exception as e:
        return f"Error loading dashboard: {str(e)}", 500


@page_bp.route("/stocks")
def stocks_page():
    """S&P 500 stocks analysis page"""
    try:
        return render_template(
            "stocks.html",
            page_title="Stock Analysis",
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    except Exception as e:
        return f"Error loading stocks page: {str(e)}", 500


@page_bp.route("/crypto")
def crypto_page():
    """Crypto analysis page"""
    try:
        return render_template("crypto.html")
    except Exception as e:
        return f"Error loading crypto page: {str(e)}", 500


@page_bp.route("/portfolio")
def portfolio_page():
    """Portfolio management page"""
    try:
        return render_template("portfolio.html")
    except Exception as e:
        return f"Error loading portfolio page: {str(e)}", 500

@page_bp.route("/portfolio_page")
def portfolio_page_alt():
    """Portfolio management page (alternative route for compatibility)"""
    try:
        return render_template("portfolio.html")
    except Exception as e:
        return f"Error loading portfolio page: {str(e)}", 500


@page_bp.route("/foreign_markets_overview")
def foreign_markets_overview_page():
    """Foreign markets overview page"""
    try:
        return render_template("foreign_markets_overview.html")
    except Exception as e:
        return f"Error loading foreign markets page: {str(e)}", 500





@page_bp.route("/opportunities")
def opportunities_page():
    """Trading opportunities page"""
    try:
        return render_template(
            "opportunities.html",
            page_title="Trading Opportunities",
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    except Exception as e:
        return f"Error loading opportunities page: {str(e)}", 500


@page_bp.route("/weekly_plan")
def weekly_plan_page():
    """Weekly Market Plan page"""
    try:
        return render_template("weekly_plan.html")
    except Exception as e:
        return f"Error loading weekly plan page: {str(e)}", 500


@page_bp.route("/logs")
def logs_page():
    """Logs viewing page"""
    try:
        return render_template("logs.html")
    except Exception as e:
        return f"Error loading logs page: {str(e)}", 500


@page_bp.route("/recommendations")
def recommendations_page():
    """Main recommendations dashboard page"""
    try:
        return render_template("recommendations.html")
    except Exception as e:
        return f"Error loading recommendations page: {str(e)}", 500


@page_bp.route("/reporting")
def reporting_page():
    """Reporting and analytics page"""
    try:
        return render_template("reporting.html")
    except Exception as e:
        return f"Error loading reporting page: {str(e)}", 500
