import time
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class APIManager:
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        """
        Initialize API manager with rate limiting and circuit breaker patterns
        Args:
            max_requests: Maximum number of requests allowed in the time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_history: Dict[str, list] = {}
        self.circuit_breaker: Dict[str, Dict[str, Any]] = {}

    def _get_current_time(self) -> float:
        """Get current timestamp"""
        return time.time()

    def _cleanup_old_requests(self, api_name: str):
        """Remove requests older than the time window"""
        current_time = self._get_current_time()
        self.request_history[api_name] = [
            req_time
            for req_time in self.request_history.get(api_name, [])
            if current_time - req_time < self.time_window
        ]

    def check_rate_limit(self, api_name: str) -> bool:
        """
        Check if the API request is within rate limits
        Args:
            api_name: Name of the API service
        Returns:
            bool: True if request is allowed, False if rate limited
        """
        if api_name not in self.request_history:
            self.request_history[api_name] = []
        self._cleanup_old_requests(api_name)
        if len(self.request_history[api_name]) >= self.max_requests:
            logger.warning("Rate limit exceeded for {api_name}")
            return False
        return True

    def record_request(self, api_name: str):
        """Record a successful API request"""
        if api_name not in self.request_history:
            self.request_history[api_name] = []
        self.request_history[api_name].append(self._get_current_time())

    def check_circuit_breaker(self, api_name: str) -> bool:
        """
        Check if the circuit breaker is open for an API
        Args:
            api_name: Name of the API service
        Returns:
            bool: True if circuit is closed (requests allowed), False if open
        """
        if api_name not in self.circuit_breaker:
            self.circuit_breaker[api_name] = {
                "failures": 0,
                "last_failure": None,
                "state": "closed",
            }
        circuit = self.circuit_breaker[api_name]
        # If circuit is open, check if it's time to try again
        if circuit["state"] == "open":
            if circuit["last_failure"] and datetime.now() - circuit[
                "last_failure"
            ] > timedelta(minutes=5):
                circuit["state"] = "half-open"
                circuit["failures"] = 0
                return True
            return False
        return True

    def record_failure(self, api_name: str):
        """Record an API failure and potentially open the circuit breaker"""
        if api_name not in self.circuit_breaker:
            self.circuit_breaker[api_name] = {
                "failures": 0,
                "last_failure": None,
                "state": "closed",
            }
        circuit = self.circuit_breaker[api_name]
        circuit["failures"] += 1
        circuit["last_failure"] = datetime.now()
        # Open circuit after 5 consecutive failures
        if circuit["failures"] >= 5:
            circuit["state"] = "open"
            logger.error(
                "Circuit breaker opened for {api_name} after {circuit['failures']} failures"
            )

    def record_success(self, api_name: str):
        """Record a successful API call and reset circuit breaker"""
        if api_name in self.circuit_breaker:
            self.circuit_breaker[api_name]["failures"] = 0
            self.circuit_breaker[api_name]["state"] = "closed"

    def get_api_status(self, api_name: str) -> Dict[str, Any]:
        """
        Get current status of an API including rate limits and circuit breaker
        Args:
            api_name: Name of the API service
        Returns:
            Dict containing API status information
        """
        self._cleanup_old_requests(api_name)
        return {
            "rate_limit": {
                "current_requests": len(self.request_history.get(api_name, [])),
                "max_requests": self.max_requests,
                "time_window": self.time_window,
            },
            "circuit_breaker": self.circuit_breaker.get(
                api_name, {"failures": 0, "last_failure": None, "state": "closed"}
            ),
        }
