"""
API Usage Tracker
Tracks API usage across the application for monitoring and rate limiting
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class APITracker:
    """Singleton API tracker for monitoring API usage"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(APITracker, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.max_requests = 100
        self.time_window = 60  # seconds
        self.request_history: Dict[str, list] = {}
        self.circuit_breaker: Dict[str, Dict[str, Any]] = {}
        self._initialized = True

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

    def record_request(self, api_name: str):
        """Record a successful API request"""
        if api_name not in self.request_history:
            self.request_history[api_name] = []
        self.request_history[api_name].append(self._get_current_time())
        logger.debug(f"Recorded API request for {api_name}")

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
            logger.error(f"Circuit breaker opened for {api_name} after {circuit['failures']} failures")

    def get_api_status(self, api_name: str) -> Dict[str, Any]:
        """Get status information for an API"""
        self._cleanup_old_requests(api_name)
        
        current_requests = len(self.request_history.get(api_name, []))
        
        circuit = self.circuit_breaker.get(api_name, {
            "failures": 0,
            "last_failure": None,
            "state": "closed",
        })
        
        return {
            "rate_limit": {
                "current_requests": current_requests,
                "max_requests": self.max_requests,
                "time_window": self.time_window
            },
            "circuit_breaker": circuit
        }

    def get_all_api_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status for all tracked APIs"""
        apis = ["yahoo_finance", "alpha_vantage", "finnhub", "reddit", "ollama"]
        return {api: self.get_api_status(api) for api in apis}


# Global instance
api_tracker = APITracker() 