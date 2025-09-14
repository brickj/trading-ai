"""
Routes module for the Trading AI Flask application
"""

from flask import Blueprint

def register_routes(app):
    """Register all route blueprints with the Flask app"""
    from .analysis_routes import analysis_bp
    from .backtest_routes import backtest_bp
    from .system_routes import system_bp
    from .page_routes import page_bp
    from .telegram_routes import telegram_bp
    from .logging_routes import logging_bp
    
    # Register blueprints
    app.register_blueprint(analysis_bp)
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
