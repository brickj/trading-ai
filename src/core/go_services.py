"""
Go Services Integration Layer
Connects Python Flask app with Go microservices for maximum performance
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional
from .logger import log_debug, log_info, log_error
from .config import Config

class GoServiceClient:
    """Base client for Go microservices"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TradingAI-Python/1.0'
        })
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make HTTP request to Go service"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=self.timeout)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            log_error(f"Go service request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            log_error(f"Failed to parse Go service response: {e}")
            raise

class GoDataFetcherClient(GoServiceClient):
    """Client for Go Data Fetcher Service"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        super().__init__(base_url)
    
    def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """Get stock price from Go service"""
        try:
            response = self._make_request('POST', '/api/stock/price', {'symbol': symbol})
            log_debug(f"Go data fetcher returned price for {symbol}")
            return response
        except Exception as e:
            log_error(f"Failed to get stock price for {symbol}: {e}")
            return None
    
    def get_stock_news(self, symbol: str, days_back: int = 7, limit: int = 20) -> Dict[str, Any]:
        """Get stock news from Go service"""
        try:
            response = self._make_request('POST', '/api/stock/news', {
                'symbol': symbol,
                'days_back': days_back,
                'limit': limit
            })
            log_debug(f"Go data fetcher returned news for {symbol}")
            return response
        except Exception as e:
            log_error(f"Failed to get stock news for {symbol}: {e}")
            return None
    
    def get_bulk_stock_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """Get bulk stock prices from Go service"""
        try:
            response = self._make_request('POST', '/api/stock/bulk/price', {'symbols': symbols})
            log_debug(f"Go data fetcher returned bulk prices for {len(symbols)} symbols")
            return response
        except Exception as e:
            log_error(f"Failed to get bulk stock prices: {e}")
            return None
    
    def get_bulk_stock_news(self, symbols: List[str], days_back: int = 7, limit: int = 20) -> Dict[str, Any]:
        """Get bulk stock news from Go service"""
        try:
            response = self._make_request('POST', '/api/stock/bulk/news', {
                'symbols': symbols,
                'days_back': days_back,
                'limit': limit
            })
            log_debug(f"Go data fetcher returned bulk news for {len(symbols)} symbols")
            return response
        except Exception as e:
            log_error(f"Failed to get bulk stock news: {e}")
            return None
    
    def health_check(self) -> bool:
        """Check if Go data fetcher service is healthy"""
        try:
            response = self._make_request('GET', '/health')
            return response.get('status') == 'healthy'
        except:
            return False

class GoCacheClient(GoServiceClient):
    """Client for Go Cache Service"""
    
    def __init__(self, base_url: str = "http://localhost:8081"):
        super().__init__(base_url)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Go cache service"""
        try:
            response = self._make_request('GET', f'/api/cache/get/{key}')
            if response.get('found'):
                return response.get('value')
            return None
        except Exception as e:
            log_error(f"Failed to get cache key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in Go cache service"""
        try:
            self._make_request('POST', '/api/cache/set', {
                'key': key,
                'value': value,
                'ttl': ttl
            })
            log_debug(f"Set cache key {key} with TTL {ttl}")
            return True
        except Exception as e:
            log_error(f"Failed to set cache key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from Go cache service"""
        try:
            self._make_request('DELETE', f'/api/cache/delete/{key}')
            log_debug(f"Deleted cache key {key}")
            return True
        except Exception as e:
            log_error(f"Failed to delete cache key {key}: {e}")
            return False
    
    def bulk_get(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from Go cache service"""
        try:
            response = self._make_request('POST', '/api/cache/bulk/get', {'keys': keys})
            return response.get('results', {})
        except Exception as e:
            log_error(f"Failed to bulk get cache keys: {e}")
            return {}
    
    def bulk_set(self, data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Set multiple values in Go cache service"""
        try:
            bulk_data = {}
            for key, value in data.items():
                bulk_data[key] = {'value': value, 'ttl': ttl}
            
            self._make_request('POST', '/api/cache/bulk/set', bulk_data)
            log_debug(f"Bulk set {len(data)} cache keys with TTL {ttl}")
            return True
        except Exception as e:
            log_error(f"Failed to bulk set cache keys: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache"""
        try:
            self._make_request('DELETE', '/api/cache/clear')
            log_info("Cleared all cache")
            return True
        except Exception as e:
            log_error(f"Failed to clear cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            return self._make_request('GET', '/api/cache/stats')
        except Exception as e:
            log_error(f"Failed to get cache stats: {e}")
            return {}
    
    def health_check(self) -> bool:
        """Check if Go cache service is healthy"""
        try:
            response = self._make_request('GET', '/health')
            return response.get('status') == 'healthy'
        except:
            return False

class GoBackgroundWorkerClient(GoServiceClient):
    """Client for Go Background Workers Service"""
    
    def __init__(self, base_url: str = "http://localhost:8082"):
        super().__init__(base_url)
    
    def submit_job(self, job_type: str, data: Dict[str, Any], priority: int = 1, delay: int = 0) -> bool:
        """Submit job to Go background workers"""
        try:
            self._make_request('POST', '/api/jobs/submit', {
                'type': job_type,
                'data': data,
                'priority': priority,
                'delay': delay
            })
            log_debug(f"Submitted job {job_type} to background workers")
            return True
        except Exception as e:
            log_error(f"Failed to submit job {job_type}: {e}")
            return False
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status from Go background workers"""
        try:
            return self._make_request('GET', f'/api/jobs/status/{job_id}')
        except Exception as e:
            log_error(f"Failed to get job status {job_id}: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get background worker statistics"""
        try:
            return self._make_request('GET', '/api/jobs/stats')
        except Exception as e:
            log_error(f"Failed to get worker stats: {e}")
            return {}
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """Get worker statistics"""
        try:
            return self._make_request('GET', '/api/workers/stats')
        except Exception as e:
            log_error(f"Failed to get worker stats: {e}")
            return {}
    
    def clear_jobs(self) -> bool:
        """Clear all jobs"""
        try:
            self._make_request('DELETE', '/api/jobs/clear')
            log_info("Cleared all background jobs")
            return True
        except Exception as e:
            log_error(f"Failed to clear jobs: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if Go background workers service is healthy"""
        try:
            response = self._make_request('GET', '/health')
            return response.get('status') == 'healthy'
        except:
            return False

class GoServicesManager:
    """Manages all Go microservices"""
    
    def __init__(self):
        self.data_fetcher = GoDataFetcherClient()
        self.cache = GoCacheClient()
        self.background_workers = GoBackgroundWorkerClient()
        self.enabled = self._check_services_health()
    
    def _check_services_health(self) -> bool:
        """Check if all Go services are healthy"""
        try:
            data_fetcher_healthy = self.data_fetcher.health_check()
            cache_healthy = self.cache.health_check()
            workers_healthy = self.background_workers.health_check()
            
            all_healthy = data_fetcher_healthy and cache_healthy and workers_healthy
            
            if all_healthy:
                log_info("All Go services are healthy and ready")
            else:
                log_error(f"Go services health check failed - DataFetcher: {data_fetcher_healthy}, Cache: {cache_healthy}, Workers: {workers_healthy}")
            
            return all_healthy
            
        except Exception as e:
            log_error(f"Failed to check Go services health: {e}")
            return False
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics from all Go services"""
        try:
            stats = {
                'data_fetcher': self.data_fetcher._make_request('GET', '/api/cache/stats'),
                'cache': self.cache.get_stats(),
                'background_workers': self.background_workers.get_stats(),
                'worker_stats': self.background_workers.get_worker_stats(),
                'overall_health': self.enabled
            }
            return stats
        except Exception as e:
            log_error(f"Failed to get performance stats: {e}")
            return {'overall_health': False, 'error': str(e)}

# Global instance
go_services = GoServicesManager()
