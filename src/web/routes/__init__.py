"""
Routes module for the Trading AI Flask application
"""

from flask import Blueprint

def register_routes(app):
    """Register all route blueprints with the Flask app"""
    from .analysis_routes import analysis_bp
    from .dashboard_routes import dashboard_bp
    from .market_routes import market_bp
    from .admin_routes import admin_bp
    from .report_routes import report_bp
    from .opportunity_routes import opportunities_bp
    from .recommendation_routes import recommendation_bp
    from .portfolio_routes import portfolio_bp
    from .backtest_routes import backtest_bp
    from .system_routes import system_bp
    from .page_routes import page_bp
    from .telegram_routes import telegram_bp
    from .logging_routes import logging_bp
    
    # Register blueprints
    app.register_blueprint(analysis_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(market_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(opportunities_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(backtest_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(page_bp)
    app.register_blueprint(telegram_bp)
    app.register_blueprint(logging_bp)
    
    # Register scalping signals blueprint
    try:
        from ..scalping_signals import scalping_signals_bp
        app.register_blueprint(scalping_signals_bp)
    except ImportError:
        # Scalping signals module not available
        pass
