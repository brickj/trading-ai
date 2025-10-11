"""
Enhanced API Error Handling Utility
Provides better error handling for rate-limited APIs with graceful fallbacks
"""

import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from src.core.logger import trading_logger

logger = trading_logger

class APIRateLimitHandler:
    """Handles API rate limiting with exponential backoff and fallbacks"""
    
    def __init__(self):
        self.rate_limit_cache = {}
        self.fallback_providers = {
            'stock_price': ['alpha_vantage', 'finnhub', 'yahoo_finance'],
            'news': ['newsapi', 'finnhub', 'reddit'],
            'crypto': ['coingecko', 'coinmarketcap']
        }
    
    def with_rate_limit_handling(self, api_name: str, fallback_providers: list = None):
        """Decorator to handle rate limiting with automatic fallbacks"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Check if API is currently rate limited
                if self._is_rate_limited(api_name):
                    logger.warning(f"API {api_name} is rate limited, using fallback")
                    return self._use_fallback(api_name, fallback_providers, *args, **kwargs)
                
                try:
                    result = func(*args, **kwargs)
                    # Reset rate limit status on success
                    self._reset_rate_limit(api_name)
                    return result
                    
                except Exception as e:
                    if self._is_rate_limit_error(e):
                        logger.warning(f"Rate limit detected for {api_name}: {e}")
                        self._mark_rate_limited(api_name)
                        return self._use_fallback(api_name, fallback_providers, *args, **kwargs)
                    else:
                        # Re-raise non-rate-limit errors
                        raise e
                        
            return wrapper
        return decorator
    
    def _is_rate_limited(self, api_name: str) -> bool:
        """Check if API is currently marked as rate limited"""
        if api_name not in self.rate_limit_cache:
            return False
        
        rate_limit_info = self.rate_limit_cache[api_name]
        current_time = time.time()
        
        # Check if cooldown period has passed
        if current_time > rate_limit_info['reset_time']:
            self._reset_rate_limit(api_name)
            return False
        
        return True
    
    def _mark_rate_limited(self, api_name: str, cooldown_minutes: int = 15):
        """Mark API as rate limited with cooldown period"""
        reset_time = time.time() + (cooldown_minutes * 60)
        self.rate_limit_cache[api_name] = {
            'rate_limited': True,
            'reset_time': reset_time,
            'marked_at': time.time()
        }
        logger.info(f"Marked {api_name} as rate limited until {time.ctime(reset_time)}")
    
    def _reset_rate_limit(self, api_name: str):
        """Reset rate limit status for API"""
        if api_name in self.rate_limit_cache:
            del self.rate_limit_cache[api_name]
            logger.info(f"Reset rate limit status for {api_name}")
    
    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Detect if error is due to rate limiting"""
        error_str = str(error).lower()
        rate_limit_indicators = [
            '429', 'too many requests', 'rate limit', 'quota exceeded',
            'limit exceeded', 'throttled', 'rate exceeded'
        ]
        
        return any(indicator in error_str for indicator in rate_limit_indicators)
    
    def _use_fallback(self, api_name: str, fallback_providers: list, *args, **kwargs):
        """Use fallback providers when primary API is rate limited"""
        if not fallback_providers:
            fallback_providers = self.fallback_providers.get(api_name.split('_')[0], [])
        
        for provider in fallback_providers:
            if provider == api_name:
                continue  # Skip the failed provider
                
            try:
                logger.info(f"Trying fallback provider: {provider}")
                # This would need to be implemented based on specific fallback logic
                return self._call_fallback_provider(provider, *args, **kwargs)
            except Exception as e:
                logger.warning(f"Fallback provider {provider} also failed: {e}")
                continue
        
        # If all fallbacks fail, return a graceful error response
        return {
            'error': f'All providers for {api_name} are currently unavailable',
            'status': 'rate_limited',
            'retry_after': 900,  # 15 minutes
            'fallback_used': True
        }
    
    def _call_fallback_provider(self, provider: str, *args, **kwargs):
        """Call specific fallback provider - to be implemented per use case"""
        # This is a placeholder - actual implementation would depend on the specific API
        return {
            'data': None,
            'provider': provider,
            'status': 'fallback_unavailable',
            'message': f'Fallback to {provider} not implemented'
        }
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get current status of all APIs"""
        current_time = time.time()
        status_report = {
            'timestamp': current_time,
            'rate_limited_apis': {},
            'healthy_apis': []
        }
        
        for api_name, info in self.rate_limit_cache.items():
            if current_time < info['reset_time']:
                status_report['rate_limited_apis'][api_name] = {
                    'reset_time': info['reset_time'],
                    'minutes_remaining': (info['reset_time'] - current_time) / 60,
                    'marked_at': info['marked_at']
                }
        
        return status_report

# Global instance
api_rate_limit_handler = APIRateLimitHandler()
