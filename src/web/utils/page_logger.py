import logging
from src.core.logger import trading_logger as _core_logger


class PageLogger:
    """Wrapper around the core trading logger with verbosity control."""

    def __init__(self):
        self.base_logger = _core_logger
        self.verbose = True
        self._set_level()

    def _set_level(self):
        level = logging.DEBUG if self.verbose else logging.INFO
        # Adjust levels for relevant loggers except error logger
        for logger in [
            self.base_logger.app_logger,
            self.base_logger.api_logger,
            self.base_logger.user_logger,
            self.base_logger.system_logger,
            self.base_logger.perf_logger,
        ]:
            logger.setLevel(level)

    def set_verbose(self, verbose: bool):
        """Toggle verbose logging."""
        self.verbose = verbose
        self._set_level()

    # Expose logging methods with extensive defaults
    def info(self, message, category: str = "app"):
        self.base_logger.info(message, category=category)

    def error(self, message, category: str = "error", exc_info=None):
        self.base_logger.error(message, category=category, exc_info=exc_info)

    def debug(self, message, category: str = "app"):
        if self.verbose:
            logger = getattr(self.base_logger, f"{category}_logger", self.base_logger.app_logger)
            logger.debug(message)

    def exception(self, operation, exception, context=None):
        self.base_logger.log_exception(operation, exception, context)

    @property
    def logger(self):
        """Expose underlying logger for compatibility."""
        return self.base_logger

page_logger = PageLogger()
