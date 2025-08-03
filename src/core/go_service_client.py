import requests
import time
from typing import Dict, List, Optional
from datetime import datetime
from .config import Config


class GoServiceClient:
    """
    Client for interfacing with Go microservices.
    Provides fallback to Python implementations when Go services are unavailable.
    """

    def __init__(self):
        self.use_go_services = Config.USE_GO_SERVICES
        self.timeout = Config.GO_SERVICE_TIMEOUT
        self.retry_count = Config.GO_SERVICE_RETRY_COUNT
        # Service URLs
        self.news_service_url = Config.GO_NEWS_SERVICE_URL
        self.signal_service_url = Config.GO_SIGNAL_SERVICE_URL
        self.risk_service_url = Config.GO_RISK_SERVICE_URL
        self.data_service_url = Config.GO_DATA_SERVICE_URL
        # Track service health
        self.service_health = {"news": True, "signal": True, "risk": True, "data": True}

    def _make_request(
        self, service_name: str, endpoint: str, data: Dict = None, method: str = "POST"
    ) -> Optional[Dict]:
        """
        Make HTTP request to Go service with retry logic and health tracking
        """
        if not self.use_go_services or not self.service_health.get(service_name, False):
            return None
        service_urls = {
            "news": self.news_service_url,
            "signal": self.signal_service_url,
            "risk": self.risk_service_url,
            "data": self.data_service_url,
        }
        base_url = service_urls.get(service_name)
        if not base_url:
            return None
        url = "{base_url}{endpoint}"
        for attempt in range(self.retry_count):
            try:
                if method.upper() == "GET":
                    response = requests.get(url, timeout=self.timeout, params=data)
                else:
                    response = requests.post(url, json=data, timeout=self.timeout)
                if response.status_code == 200:
                    self.service_health[service_name] = True
                    return response.json()
                else:
                    print(
                        f"Go {service_name} service returned status "
                        f"{response.status_code}"
                    )
            except requests.exceptions.RequestException:
                print("Go {service_name} service error (attempt {attempt + 1})")
                if attempt == self.retry_count - 1:
                    self.service_health[service_name] = False
                else:
                    time.sleep(1)  # Brief delay before retry
        return None

    def fetch_news_data(
        self, symbols: List[str], hours_back: int = 2
    ) -> Optional[Dict]:
        """
        Fetch news data using Go news service
        """
        data = {
            "symbols": symbols,
            "hours_back": hours_back,
            "categories": Config.NEWS_CATEGORIES,
            "min_articles": Config.MIN_NEWS_ARTICLES,
        }
        result = self._make_request("news", "/api/v1/news/fetch", data)
        if result:
            print("✅ Go news service processed {len(symbols)} symbols")
            return result
        print("⚠️ Go news service unavailable, falling back to Python")
        return None

    def process_trending_news(self, hours_back: int = 2) -> Optional[Dict]:
        """
        Process trending news using Go news service
        """
        data = {
            "hours_back": hours_back,
            "watchlist_stocks": Config.WATCHLIST_STOCKS,
            "watchlist_crypto": [],  # No crypto support
            "categories": Config.NEWS_CATEGORIES,
        }
        result = self._make_request("news", "/api/v1/news/trending", data)
        if result:
            print(
                "✅ Go news service found "
                f"{result.get('symbol_count', 0)} trending symbols"
            )
            return result
        print("⚠️ Go news service unavailable, falling back to Python")
        return None

    def fetch_market_data(
        self, symbols: List[str], data_type: str = "both"
    ) -> Optional[Dict]:
        """
        Fetch real-time market data using Go data service
        """
        data = {
            "symbols": symbols,
            "data_type": data_type,  # 'stocks', 'crypto', or 'both'
            "include_volume": True,
            "include_market_cap": True,
        }
        result = self._make_request("data", "/api/v1/data/market", data)
        if result:
            print("✅ Go data service fetched data for {len(symbols)} symbols")
            return result
        print("⚠️ Go data service unavailable, falling back to Python")
        return None

    def calculate_trading_signals(
        self, market_data: Dict, sentiment_data: Dict
    ) -> Optional[Dict]:
        """
        Calculate trading signals using Go signal service
        """
        data = {
            "market_data": market_data,
            "sentiment_data": sentiment_data,
            "sentiment_threshold": Config.SENTIMENT_THRESHOLD,
            "news_sentiment_threshold": Config.NEWS_SENTIMENT_THRESHOLD,
            "confidence_threshold": Config.NEWS_CONFIDENCE_THRESHOLD,
            "max_position_size": Config.MAX_POSITION_SIZE,
        }
        result = self._make_request("signal", "/api/v1/signals/calculate", data)
        if result:
            len(result.get("signals", []))
            print("✅ Go signal service calculated {signal_count} trading signals")
            return result
        print("⚠️ Go signal service unavailable, falling back to Python")
        return None

    def process_options_pricing(self, signals: List[Dict]) -> Optional[Dict]:
        """
        Process options pricing using Go signal service
        """
        data = {
            "signals": signals,
            "days_to_expiry": 30,
            "volatility": 0.25,
            "risk_free_rate": 0.05,
            "otm_percentage": 0.02,  # 2% out-of-the-money
        }
        result = self._make_request("signal", "/api/v1/signals/options-pricing", data)
        if result:
            print("✅ Go signal service priced {len(signals)} options")
            return result
        print("⚠️ Go signal service unavailable, falling back to Python")
        return None

    def check_risk_limits(self, portfolio: Dict, new_trade: Dict) -> Optional[Dict]:
        """
        Check risk limits using Go risk service
        """
        data = {
            "portfolio": portfolio,
            "new_trade": new_trade,
            "max_position_size": Config.MAX_POSITION_SIZE,
            "max_risk_per_trade": 0.05,  # 5%
            "max_portfolio_risk": 0.25,  # 25%
        }
        result = self._make_request("risk", "/api/v1/risk/check", data)
        if result:
            print(
                "✅ Go risk service validated trade for "
                f"{new_trade.get('symbol', 'unknown')}"
            )
            return result
        print("⚠️ Go risk service unavailable, falling back to Python")
        return None

    def monitor_portfolio_risk(self, portfolio: Dict) -> Optional[Dict]:
        """
        Monitor overall portfolio risk using Go risk service
        """
        data = {
            "portfolio": portfolio,
            "risk_metrics": ["var", "sharpe", "max_drawdown", "correlation"],
            "time_horizon": 30,  # days
        }
        result = self._make_request("risk", "/api/v1/risk/monitor", data)
        if result:
            print("✅ Go risk service completed portfolio risk analysis")
            return result
        print("⚠️ Go risk service unavailable, falling back to Python")
        return None

    def get_service_health(self) -> Dict:
        """
        Get health status of all Go services
        """
        health_status = {}
        for service_name in ["news", "signal", "risk", "data"]:
            try:
                if service_name == "news":
                    url = f"{self.news_service_url}/health"
                elif service_name == "signal":
                    url = f"{self.signal_service_url}/health"
                elif service_name == "risk":
                    url = f"{self.risk_service_url}/health"
                else:  # data
                    url = f"{self.data_service_url}/health"
                response = requests.get(url, timeout=5)
                health_status[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds(),
                    "last_check": datetime.now().isoformat(),
                }
                self.service_health[service_name] = response.status_code == 200
            except requests.exceptions.RequestException:
                health_status[service_name] = {
                    "status": "unavailable",
                    "response_time": None,
                    "last_check": datetime.now().isoformat(),
                }
                self.service_health[service_name] = False
        return {
            "go_services_enabled": self.use_go_services,
            "services": health_status,
            "overall_health": (
                all(self.service_health.values())
                if self.use_go_services
                else "disabled"
            ),
        }

    def is_service_available(self, service_name: str) -> bool:
        """
        Check if a specific Go service is available
        """
        return self.use_go_services and self.service_health.get(service_name, False)
