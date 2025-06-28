import logging
import logging.handlers
import sys
from datetime import datetime
from functools import wraps
import time
from pathlib import Path
import json
import hashlib


class TradingLogger:
    """
    Comprehensive logging system for the Trading AI application.
    Captures API calls, errors, timeouts, performance metrics, and user actions.
    """

    def __init__(self, log_dir="logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.setup_loggers()

    def setup_loggers(self):
        """Set up different loggers for different types of events"""
        # Main application logger
        self.app_logger = self._create_logger(
            "trading_app",
            "app.log",
            level=logging.INFO,
            format_str="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        )
        # API calls logger (requests/responses)
        self.api_logger = self._create_logger(
            "trading_api",
            "api_calls.log",
            level=logging.DEBUG,
            format_str="%(asctime)s | %(levelname)-8s | API | %(message)s",
        )
        # Error logger (errors and exceptions)
        self.error_logger = self._create_logger(
            "trading_errors",
            "errors.log",
            level=logging.ERROR,
            format_str=(
                "%(asctime)s | %(levelname)-8s | ERROR | " "%(name)s:%(lineno)d | %(message)s"
            ),
        )
        # Performance logger (timing and metrics)
        self.perf_logger = self._create_logger(
            "trading_performance",
            "performance.log",
            level=logging.INFO,
            format_str="%(asctime)s | PERF | %(message)s",
        )
        # User actions logger (user interactions)
        self.user_logger = self._create_logger(
            "trading_user",
            "user_actions.log",
            level=logging.INFO,
            format_str="%(asctime)s | USER | %(message)s",
        )
        # System status logger (health checks, startup, etc.)
        self.system_logger = self._create_logger(
            "trading_system",
            "system.log",
            level=logging.INFO,
            format_str="%(asctime)s | SYSTEM | %(message)s",
        )
        # Telegram alerts logger
        self.telegram_logger = self._create_logger(
            "trading_telegram",
            "telegram_alerts.log",
            level=logging.INFO,
            format_str="%(asctime)s | TELEGRAM | %(message)s",
        )

    def _create_logger(self, name, filename, level=logging.INFO, format_str=None):
        """Create a logger with file and console handlers"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / filename, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        )
        file_handler.setLevel(level)
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        # Only warnings and errors to console
        console_handler.setLevel(logging.WARNING)
        # Formatter
        if format_str is None:
            format_str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        formatter = logging.Formatter(format_str)
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        return logger

    # Main logging methods

    def info(self, message, category="app"):
        """Log info message"""
        logger = getattr(self, "{category}_logger", self.app_logger)
        logger.info(message)

    def warning(self, message, category="app"):
        """Log warning message"""
        logger = getattr(self, "{category}_logger", self.app_logger)
        logger.warning(message)

    def error(self, message, category="error", exc_info=None):
        """Log error message with optional exception info"""
        logger = getattr(self, "{category}_logger", self.error_logger)
        if exc_info:
            logger.error(message, exc_info=exc_info)
        else:
            logger.error(message)

    def debug(self, message, category="app"):
        """Log debug message"""
        logger = getattr(self, "{category}_logger", self.app_logger)
        logger.debug(message)

    # Specialized logging methods

    def log_api_call(
        self,
        url,
        method="GET",
        params=None,
        headers=None,
        response_status=None,
        response_time=None,
        error=None,
    ):
        """Log API call details"""
        status = "SUCCESS" if response_status and 200 <= response_status < 300 else "ERROR"
        message = (
            f"{status} | {method} {url} | Status: {response_status} | " f"Time: {response_time}ms"
        )
        if error:
            message += f" | Error: {error}"
        self.api_logger.info(message)

        log_details = {
            "url": url,
            "method": method,
            "params": params,
            "response_status": response_status,
            "response_time_ms": response_time,
            "error": str(error) if error else None,
        }
        self.api_logger.debug(f"Full details: {json.dumps(log_details, indent=2)}")

    def log_user_action(self, action, symbol=None, details=None, user_ip=None):
        """Log user actions"""
        message = "{action}"
        if symbol:
            message += " | Symbol: {symbol}"
        if user_ip:
            message += " | IP: {user_ip}"
        if details:
            message += " | Details: {details}"
        self.user_logger.info(message)

    def log_performance(self, operation, duration_ms, details=None):
        """Log performance metrics"""
        message = "{operation} | Duration: {duration_ms:.2f}ms"
        if details:
            message += " | {details}"
        self.perf_logger.info(message)

    def log_system_event(self, event, status="INFO", details=None):
        """Log system events"""
        message = "{status} | {event}"
        if details:
            message += " | {details}"
        self.system_logger.info(message)

    def log_timeout(self, operation, timeout_duration, details=None):
        """Log timeout events"""
        message = "TIMEOUT | {operation} | Timeout: {timeout_duration}s"
        if details:
            message += " | {details}"
        self.error_logger.warning(message)

    def log_exception(self, operation, exception, context=None):
        """Log exceptions with full traceback"""
        message = "EXCEPTION in {operation}: {str(exception)}"
        if context:
            message += " | Context: {context}"
        self.error_logger.error(message, exc_info=exception)

    def log_telegram_message(
        self,
        message_type,
        symbol,
        recipients,
        success_count,
        failed_recipients=None,
        message_preview=None,
    ):
        """Log Telegram message sending activity"""
        log_data = {
            "message_type": message_type,
            "symbol": symbol,
            "total_recipients": len(recipients),
            "successful_deliveries": success_count,
            "recipients": recipients,  # List of chat IDs
            "failed_recipients": failed_recipients or [],
            "timestamp": datetime.now().isoformat(),
        }
        if message_preview:
            # Log only first few chars to avoid sensitive data
            log_data["message_preview"] = (
                message_preview[:50] + "..." if len(message_preview) > 50 else message_preview
            )
        message = f"{message_type} | Symbol: {symbol} | " f"Sent: {success_count}/{len(recipients)}"
        self.telegram_logger.info(message)
        self.telegram_logger.debug(f"Details: {json.dumps(log_data, indent=2)}")


# Decorators for automatic logging


def log_api_calls(logger_instance):
    """Decorator to automatically log API calls"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            operation = "{func.__module__}.{func.__name__}"
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                logger_instance.log_performance(operation, duration)
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger_instance.log_exception(operation, e)
                logger_instance.log_performance(operation, duration, "FAILED")
                raise

        return wrapper

    return decorator


def log_user_actions(logger_instance):
    """Decorator to automatically log user actions"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            operation = "{func.__module__}.{func.__name__}"
            # Try to extract symbol from args/kwargs
            symbol = None
            if args and len(args) > 0 and isinstance(args[0], str):
                symbol = args[0]
            elif "symbol" in kwargs:
                symbol = kwargs["symbol"]
            try:
                result = func(*args, **kwargs)
                logger_instance.log_user_action(operation, symbol=symbol, details="SUCCESS")
                return result
            except Exception:
                logger_instance.log_user_action(operation, symbol=symbol, details="ERROR: {str(e)}")
                raise

        return wrapper

    return decorator


def log_timing(logger_instance):
    """Decorator to automatically log execution timing"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            operation = "{func.__module__}.{func.__name__}"
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                logger_instance.log_performance(operation, duration)
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger_instance.log_performance(operation, duration, "FAILED")
                logger_instance.log_exception(operation, e)
                raise

        return wrapper

    return decorator


# Global logger instance
trading_logger = TradingLogger()
# Convenience functions for easy import


def log_info(message, category="app"):
    trading_logger.info(message, category)


def log_warning(message, category="app"):
    trading_logger.warning(message, category)


def log_error(message, category="error", exc_info=None):
    trading_logger.error(message, category, exc_info)


def log_debug(message, category="app"):
    trading_logger.debug(message, category)


def log_api_call(
    url, method="GET", params=None, response_status=None, response_time=None, error=None
):
    trading_logger.log_api_call(url, method, params, None, response_status, response_time, error)


def log_user_action(action, symbol=None, details=None, user_ip=None):
    trading_logger.log_user_action(action, symbol, details, user_ip)


def log_performance(operation, duration_ms, details=None):
    trading_logger.log_performance(operation, duration_ms, details)


def log_system_event(event, status="INFO", details=None):
    trading_logger.log_system_event(event, status, details)


def log_timeout(operation, timeout_duration, details=None):
    trading_logger.log_timeout(operation, timeout_duration, details)


def log_exception(operation, exception, context=None):
    trading_logger.log_exception(operation, exception, context)


def log_telegram_message(
    message_type,
    symbol,
    recipients,
    success_count,
    failed_recipients=None,
    message_preview=None,
):
    """Log Telegram message sending"""
    trading_logger.log_telegram_message(
        message_type=message_type,
        symbol=symbol,
        recipients=recipients,
        success_count=success_count,
        failed_recipients=failed_recipients,
        message_preview=message_preview,
    )


def generate_key(*args, **kwargs):
    """Generate a unique key based on the function signature"""
    key_data = json.dumps((args, sorted(kwargs.items())), sort_keys=True)
    return hashlib.sha256(key_data.encode()).hexdigest()
