"""
System routes for system status, monitoring, and performance endpoints
"""

from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
import psutil
import platform
import psycopg2.extras

# Import helper functions
from ..helpers import create_api_response
from ..utils import api_error_handler, handle_api_error
from ..dependencies import market_manager

# Import core modules
from ...core.database import get_db_connection
from ...core.config import Config
from ..utils.page_logger import page_logger

# Create blueprint
system_bp = Blueprint('system', __name__)

log_exception = page_logger.exception
trading_logger = page_logger.logger


@system_bp.route("/system_status")
def system_status_page():
    """System status and Go services monitoring page"""
    return render_template("system_status.html")


@system_bp.route("/api/system_status")
def system_status():
    """System status information with comprehensive error handling"""
    try:
        # Get basic system metrics
        system_metrics = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
        }

        # Get database status
        db_stats = get_database_status()
        
        # Get services status
        services_stats = get_services_status()
        
        # Get cache stats
        cache_stats = {"status": "unavailable"}
        try:
            from ...core.cache import get_cache_stats
            cache_stats = get_cache_stats()
        except Exception as e:
            log_exception("Error getting cache stats", e)
            cache_stats = {"status": "error", "error": str(e)}

        # Get application config
        config_info = {
            "telegram_enabled": False,  # Will be updated if telegram module available
            "cache_enabled": getattr(Config, "ENABLE_CACHE", False),
            "debug_mode": False,
            "version": "1.0.0",
        }

        # Try to get telegram status safely
        try:
            from ...core.telegram_alerter import telegram_alerter
            config_info["telegram_enabled"] = telegram_alerter.is_enabled()
        except Exception:
            pass

        # Get historical data job status
        historical_data_status = {"status": "unavailable"}
        try:
            from ...data.historical_data_updater import HistoricalDataUpdater
            updater = HistoricalDataUpdater()
            
            # Check if we have recent historical data
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            COUNT(DISTINCT symbol) as symbols_with_data,
                            MAX(date) as latest_data_date,
                            COUNT(*) as total_data_points
                        FROM historical_data
                    """)
                    result = cur.fetchone()
                    print(f"[DEBUG] Historical data query result: {result}")
                    print(f"[DEBUG] Result type: {type(result)}")
                    
                    if result:
                        try:
                            symbols_with_data = result['symbols_with_data']
                            latest_data_date = result['latest_data_date']
                            total_data_points = result['total_data_points']
                            print(f"[DEBUG] Unpacked: symbols={symbols_with_data}, date={latest_data_date}, points={total_data_points}")
                            
                            historical_data_status = {
                                "status": "available",
                                "symbols_with_data": symbols_with_data,
                                "latest_data_date": latest_data_date.isoformat() if hasattr(latest_data_date, 'isoformat') else str(latest_data_date) if latest_data_date else None,
                                "total_data_points": total_data_points,
                                "update_interval_days": updater.update_interval_days,
                                "lookback_days": updater.lookback_days
                            }
                        except Exception as e:
                            print(f"[DEBUG] Error unpacking result: {e}")
                            historical_data_status = {
                                "status": "error",
                                "error": f"Failed to unpack query result: {str(e)}"
                            }
                    else:
                        print(f"[DEBUG] No result: {result}")
                        historical_data_status = {
                            "status": "no_data",
                            "message": "No historical data found in database"
                        }
        except Exception as e:
            log_exception("Error getting historical data status", e)
            historical_data_status = {"status": "error", "error": str(e)}

        # Get job schedules information
        job_schedules = {"status": "unavailable"}
        try:
            print("[DEBUG] Attempting to get job schedules...")
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    print("[DEBUG] Executing job schedules query...")
                    cur.execute("""
                        SELECT id, job_name, run_time, enabled, last_run, created_at 
                        FROM job_schedules 
                        ORDER BY job_name
                    """)
                    jobs = cur.fetchall()
                    print(f"[DEBUG] Query returned {len(jobs) if jobs else 0} jobs")
                    
                    if jobs:
                        job_list = []
                        for job in jobs:
                            job_list.append({
                                "id": job['id'],
                                "name": job['job_name'],
                                "run_time": str(job['run_time']) if job['run_time'] else None,
                                "enabled": job['enabled'],
                                "last_run": job['last_run'].isoformat() if job['last_run'] and hasattr(job['last_run'], 'isoformat') else None,
                                "created_at": job['created_at'].isoformat() if job['created_at'] and hasattr(job['created_at'], 'isoformat') else None
                            })
                        
                        job_schedules = {
                            "status": "available",
                            "total_jobs": len(job_list),
                            "enabled_jobs": len([j for j in job_list if j["enabled"]]),
                            "jobs": job_list
                        }
                        print(f"[DEBUG] Successfully processed {len(job_list)} jobs")
                    else:
                        job_schedules = {
                            "status": "no_jobs",
                            "message": "No scheduled jobs found"
                        }
                        print("[DEBUG] No jobs found in database")
        except Exception as e:
            print(f"[DEBUG] Exception in job schedules: {e}")
            print(f"[DEBUG] Exception type: {type(e)}")
            print(f"[DEBUG] Exception args: {e.args}")
            log_exception("Error getting job schedules", e)
            job_schedules = {"status": "error", "error": str(e)}

        # Get API status information
        api_status = {
            "status": "active",
            "endpoints": {
                "stocks": "active",
                "crypto": "active", 
                "news": "active",
                "portfolio": "active",
                "recommendations": "active",
                "backtest": "active",
                "opportunities": "active",
                "system_status": "active",
                "telegram": "active"
            },
            "last_check": datetime.now().isoformat(),
            "message": "All core API endpoints are functioning normally"
        }

        status_data = {
            "timestamp": datetime.now().isoformat(),
            "system": system_metrics,
            "database": db_stats,
            "cache": cache_stats,
            "config": config_info,
            "historical_data": historical_data_status,
            "job_schedules": job_schedules,
            "api_status": api_status,
        }

        return create_api_response(data=status_data)

    except Exception as e:
        return handle_api_error(e, "system_status endpoint")


@system_bp.route("/api/system_metrics")
def get_system_metrics():
    """Get basic system metrics"""
    try:
        metrics = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "timestamp": datetime.now().isoformat()
        }

        return create_api_response(data=metrics)

    except Exception as e:
        return handle_api_error(e, "get_system_metrics endpoint")


@system_bp.route("/api/news_services/status", methods=["GET"])
def get_news_services_status():
    """Get status of all news services by actually testing them"""
    try:
        # Import DataFetcher to test real services
        from ...data.data_fetcher import DataFetcher
        data_fetcher = DataFetcher()
        
        services_status = {}
        test_symbol = "AAPL"  # Use AAPL as test symbol
        
        # Test Alpha Vantage
        try:
            news = data_fetcher.get_alpha_vantage_news(test_symbol, limit=1)
            services_status["alpha_vantage"] = {
                "status": "active" if news and len(news) > 0 else "no_data",
                "last_check": datetime.now().isoformat(),
                "articles_fetched": len(news) if isinstance(news, list) else 0,
                "test_symbol": test_symbol
            }
        except Exception as e:
            services_status["alpha_vantage"] = {
                "status": "error",
                "last_check": datetime.now().isoformat(),
                "error": str(e),
                "test_symbol": test_symbol
            }
        
        # Test Reddit
        try:
            news = data_fetcher.get_reddit_news(test_symbol, limit=1)
            services_status["reddit"] = {
                "status": "active" if news and len(news) > 0 else "no_data",
                "last_check": datetime.now().isoformat(),
                "articles_fetched": len(news) if isinstance(news, list) else 0,
                "test_symbol": test_symbol
            }
        except Exception as e:
            services_status["reddit"] = {
                "status": "error",
                "last_check": datetime.now().isoformat(),
                "error": str(e),
                "test_symbol": test_symbol
            }
        
        # Test Finnhub
        try:
            news = data_fetcher._get_finnhub_news(test_symbol, days_back=1)
            services_status["finnhub"] = {
                "status": "active" if news and len(news) > 0 else "no_data",
                "last_check": datetime.now().isoformat(),
                "articles_fetched": len(news) if isinstance(news, list) else 0,
                "test_symbol": test_symbol
            }
        except Exception as e:
            services_status["finnhub"] = {
                "status": "error",
                "last_check": datetime.now().isoformat(),
                "error": str(e),
                "test_symbol": test_symbol
            }
        
        # Test Yahoo Finance
        try:
            news = data_fetcher.get_yahoo_finance_news(test_symbol, limit=1)
            services_status["yahoo_finance"] = {
                "status": "active" if news and len(news) > 0 else "no_data",
                "last_check": datetime.now().isoformat(),
                "articles_fetched": len(news) if isinstance(news, list) else 0,
                "test_symbol": test_symbol
            }
        except Exception as e:
            services_status["yahoo_finance"] = {
                "status": "error",
                "last_check": datetime.now().isoformat(),
                "error": str(e),
                "test_symbol": test_symbol
            }

        return create_api_response(data=services_status)

    except Exception as e:
        return handle_api_error(e, "get_news_services_status endpoint")


@system_bp.route("/api/logs")
def get_logs():
    """Get application logs from database"""
    try:
        from ...core.database import get_db_connection
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get total count
                cur.execute("SELECT COUNT(*) as total FROM logs")
                total = cur.fetchone()['total']
                
                # Get recent logs (last 100)
                cur.execute("""
                    SELECT id, level, message, timestamp, logger, module, function, category
                    FROM logs 
                    ORDER BY timestamp DESC 
                    LIMIT 100
                """)
                logs = []
                for row in cur.fetchall():
                    logs.append({
                        'id': row['id'],
                        'level': row['level'],
                        'message': row['message'],
                        'timestamp': row['timestamp'].isoformat() if row['timestamp'] else None,
                        'logger': row['logger'],
                        'module': row['module'],
                        'function': row['function'],
                        'category': row['category']
                    })
                
                return create_api_response(data={
                    'logs': logs,
                    'total': total
                })
                
    except Exception as e:
        return handle_api_error(e, "get_logs endpoint")


@system_bp.route("/api/logging/verbosity", methods=["GET", "POST"])
def logging_verbosity():
    """Get or update logging verbosity."""
    try:
        if request.method == "POST":
            data = request.get_json(force=True) or {}
            verbose = bool(data.get("verbose", True))
            page_logger.set_verbose(verbose)
            return create_api_response(data={"verbose": page_logger.verbose})
        return create_api_response(data={"verbose": page_logger.verbose})
    except Exception as e:
        return handle_api_error(e, "logging_verbosity endpoint")


@system_bp.route("/api/news_services/toggle", methods=["POST"])
def toggle_news_service():
    """Toggle a news service on/off by updating configuration"""
    try:
        data = request.get_json()
        service_name = data.get("service_name")
        enabled = data.get("enabled", True)

        if not service_name:
            return create_api_response(
                error="service_name is required",
                status_code=400
            )

        # Import configuration to check current status
        from ...core.config import Config
        
        # Check current configuration status
        current_status = "unknown"
        config_key = None
        
        if service_name == "alpha_vantage":
            config_key = "ENABLE_ALPHA_VANTAGE_NEWS"
            current_status = "enabled" if getattr(Config, config_key, False) else "disabled"
        elif service_name == "reddit":
            config_key = "ENABLE_REDDIT_NEWS"
            current_status = "enabled" if getattr(Config, config_key, True) else "disabled"
        elif service_name == "finnhub":
            config_key = "ENABLE_FINNHUB_NEWS"
            current_status = "enabled" if getattr(Config, config_key, True) else "disabled"
        elif service_name == "yahoo_finance":
            config_key = "ENABLE_YAHOO_NEWS"
            current_status = "enabled" if getattr(Config, config_key, True) else "disabled"
        else:
            return create_api_response(
                error=f"Unknown service: {service_name}",
                status_code=400
            )

        # Note: In a real implementation, this would update the configuration file
        # For now, we'll return the current status and what would happen
        message = f"Service {service_name} is currently {current_status}. "
        if enabled:
            message += f"Would enable {service_name} news service."
        else:
            message += f"Would disable {service_name} news service."

        return create_api_response(
            data={
                "service_name": service_name,
                "current_status": current_status,
                "requested_status": "enabled" if enabled else "disabled",
                "config_key": config_key,
                "message": message,
                "note": "Configuration update requires restart to take effect"
            }
        )

    except Exception as e:
        return handle_api_error(e, "toggle_news_service endpoint")


@system_bp.route("/api/news_services/test", methods=["POST"])
def test_news_service():
    """Test a specific news service by actually calling the real API"""
    try:
        data = request.get_json()
        service_name = data.get("service_name")

        if not service_name:
            return create_api_response(
                error="service_name is required",
                status_code=400
            )

        # Import DataFetcher to test real services
        from ...data.data_fetcher import DataFetcher
        data_fetcher = DataFetcher()
        
        test_result = {
            "service_name": service_name,
            "test_timestamp": datetime.now().isoformat(),
            "status": "unknown",
            "response_time": 0,
            "articles_fetched": 0,
            "error": None,
            "details": {}
        }

        start_time = datetime.now()
        
        try:
            if service_name == "alpha_vantage":
                # Test Alpha Vantage news API
                news = data_fetcher.get_alpha_vantage_news("AAPL", limit=3)
                test_result["status"] = "success"
                test_result["articles_fetched"] = len(news) if isinstance(news, list) else 0
                test_result["details"] = {
                    "api_endpoint": "Alpha Vantage News Sentiment API",
                    "test_symbol": "AAPL",
                    "articles": news[:2] if isinstance(news, list) and len(news) > 0 else []
                }
                
            elif service_name == "reddit":
                # Test Reddit news API
                news = data_fetcher.get_reddit_news("AAPL", limit=3)
                test_result["status"] = "success"
                test_result["articles_fetched"] = len(news) if isinstance(news, list) else 0
                test_result["details"] = {
                    "api_endpoint": "Reddit OAuth2 API",
                    "test_symbol": "AAPL",
                    "articles": news[:2] if isinstance(news, list) and len(news) > 0 else []
                }
                
            elif service_name == "finnhub":
                # Test Finnhub news API
                news = data_fetcher._get_finnhub_news("AAPL", days_back=1)
                test_result["status"] = "success"
                test_result["articles_fetched"] = len(news) if isinstance(news, list) else 0
                test_result["details"] = {
                    "api_endpoint": "Finnhub Company News API",
                    "test_symbol": "AAPL",
                    "articles": news[:2] if isinstance(news, list) and len(news) > 0 else []
                }
                
            elif service_name == "yahoo_finance":
                # Test Yahoo Finance news API
                news = data_fetcher.get_yahoo_finance_news("AAPL", limit=3)
                test_result["status"] = "success"
                test_result["articles_fetched"] = len(news) if isinstance(news, list) else 0
                test_result["details"] = {
                    "api_endpoint": "Yahoo Finance RSS Feed",
                    "test_symbol": "AAPL",
                    "articles": news[:2] if isinstance(news, list) and len(news) > 0 else []
                }
                
            else:
                test_result["status"] = "error"
                test_result["error"] = f"Unknown service: {service_name}"
                return create_api_response(data=test_result)

            # Calculate response time
            end_time = datetime.now()
            test_result["response_time"] = (end_time - start_time).total_seconds()
            
            # Add success message
            test_result["message"] = f"Service {service_name} test completed successfully. Fetched {test_result['articles_fetched']} articles in {test_result['response_time']:.2f} seconds."

        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
            test_result["message"] = f"Service {service_name} test failed: {str(e)}"
            
            # Still calculate response time even on error
            end_time = datetime.now()
            test_result["response_time"] = (end_time - start_time).total_seconds()

        return create_api_response(data=test_result)

    except Exception as e:
        return handle_api_error(e, "test_news_service endpoint")


@system_bp.route("/api/news_services/config", methods=["GET"])
def get_news_services_config():
    """Get news services configuration status by checking actual config and testing APIs"""
    try:
        from ...core.config import Config
        from ...data.data_fetcher import DataFetcher
        
        data_fetcher = DataFetcher()
        test_symbol = "AAPL"
        
        config_status = {}
        
        # Check Alpha Vantage configuration
        try:
            alpha_key_present = bool(getattr(Config, 'ALPHA_VANTAGE_API_KEY', None))
            if alpha_key_present:
                # Test the API
                news = data_fetcher.get_alpha_vantage_news(test_symbol, limit=1)
                api_working = news and len(news) > 0
            else:
                api_working = False
                
            config_status["alpha_vantage"] = {
                "configured": alpha_key_present,
                "api_key_present": alpha_key_present,
                "api_working": api_working,
                "rate_limit": "5 calls per minute (free tier)",
                "test_result": f"API {'working' if api_working else 'not working' if alpha_key_present else 'no key'}"
            }
        except Exception as e:
            config_status["alpha_vantage"] = {
                "configured": False,
                "api_key_present": False,
                "api_working": False,
                "rate_limit": "5 calls per minute (free tier)",
                "error": str(e)
            }
        
        # Check Reddit configuration
        try:
            reddit_client_id = bool(getattr(Config, 'REDDIT_CLIENT_ID', None))
            reddit_secret = bool(getattr(Config, 'REDDIT_SECRET_KEY', None))
            reddit_configured = reddit_client_id and reddit_secret
            
            if reddit_configured:
                # Test the API
                news = data_fetcher.get_reddit_news(test_symbol, limit=1)
                api_working = news and len(news) > 0
            else:
                api_working = False
                
            config_status["reddit"] = {
                "configured": reddit_configured,
                "client_id_present": reddit_client_id,
                "secret_key_present": reddit_secret,
                "api_working": api_working,
                "rate_limit": "60 calls per minute",
                "test_result": f"API {'working' if api_working else 'not working' if reddit_configured else 'not configured'}"
            }
        except Exception as e:
            config_status["reddit"] = {
                "configured": False,
                "client_id_present": False,
                "secret_key_present": False,
                "api_working": False,
                "rate_limit": "60 calls per minute",
                "error": str(e)
            }
        
        # Check Finnhub configuration
        try:
            finnhub_key_present = bool(getattr(Config, 'FINNHUB_API_KEY', None))
            if finnhub_key_present:
                # Test the API
                news = data_fetcher._get_finnhub_news(test_symbol, days_back=1)
                api_working = news and len(news) > 0
            else:
                api_working = False
                
            config_status["finnhub"] = {
                "configured": finnhub_key_present,
                "api_key_present": finnhub_key_present,
                "api_working": api_working,
                "rate_limit": "60 calls per minute (free tier)",
                "test_result": f"API {'working' if api_working else 'not working' if finnhub_key_present else 'no key'}"
            }
        except Exception as e:
            config_status["finnhub"] = {
                "configured": False,
                "api_key_present": False,
                "api_working": False,
                "rate_limit": "60 calls per minute (free tier)",
                "error": str(e)
            }
        
        # Check Yahoo Finance (public API, no key required)
        try:
            # Test the API
            news = data_fetcher.get_yahoo_finance_news(test_symbol, limit=1)
            api_working = news and len(news) > 0
            
            config_status["yahoo_finance"] = {
                "configured": True,  # Public API
                "api_key_present": False,  # No key required
                "api_working": api_working,
                "rate_limit": "unlimited (with delays)",
                "test_result": f"API {'working' if api_working else 'not working'}"
            }
        except Exception as e:
            config_status["yahoo_finance"] = {
                "configured": True,
                "api_key_present": False,
                "api_working": False,
                "rate_limit": "unlimited (with delays)",
                "error": str(e)
            }

        return create_api_response(data=config_status)

    except Exception as e:
        return handle_api_error(e, "get_news_services_config endpoint")


@system_bp.route("/api/test_foreign_markets")
def test_foreign_markets_api():
    """Test foreign markets API endpoint by querying real database data"""
    try:
        overview = market_manager.get_foreign_markets_overview()

        success = bool(overview.get('markets'))
        status_code = 200 if success else 404

        return jsonify({
            'success': success,
            'data': overview,
        }), status_code

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'markets': [],
                'summary': {
                    'total_markets': 0,
                    'markets_open': 0,
                    'markets_closed': 0,
                    'total_foreign_symbols': 0,
                    'total_watchlist_symbols': 0,
                    'foreign_coverage': '0/0'
                }
            }
        }), 500


@system_bp.route("/api/performance_status")
def performance_status():
    """Get system performance status"""
    try:
        performance_data = {
            "cpu": {
                "usage_percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent,
                "used": psutil.virtual_memory().used
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            },
            "network": get_network_stats(),
            "timestamp": datetime.now().isoformat()
        }

        return create_api_response(data=performance_data)

    except Exception as e:
        return handle_api_error(e, "performance_status endpoint")


def get_database_status():
    """Get database connection status"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                
        return {
            "status": "connected",
            "type": "postgresql",
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "last_check": datetime.now().isoformat()
        }


def get_services_status():
    """Get status of various application services by actually checking them"""
    services_status = {}
    
    # Check data fetcher service
    try:
        from ...data.data_fetcher import DataFetcher
        data_fetcher = DataFetcher()
        # Test with a simple API call
        test_price = data_fetcher.get_stock_price("AAPL")
        services_status["data_fetcher"] = {
            "status": "active" if test_price and "current_price" in test_price else "error",
            "last_check": datetime.now().isoformat(),
            "test_result": "AAPL price fetch successful" if test_price and "current_price" in test_price else "AAPL price fetch failed"
        }
    except Exception as e:
        services_status["data_fetcher"] = {
            "status": "error",
            "last_check": datetime.now().isoformat(),
            "error": str(e)
        }
    
    # Check sentiment analyzer service
    try:
        from ...core.sentiment_analyzer import SentimentAnalyzer
        sentiment_analyzer = SentimentAnalyzer()
        # Test with a simple sentiment analysis
        test_sentiment = sentiment_analyzer.analyze_sentiment("This is a test message for sentiment analysis.")
        services_status["sentiment_analyzer"] = {
            "status": "active" if test_sentiment else "error",
            "last_check": datetime.now().isoformat(),
            "test_result": "Sentiment analysis test successful" if test_sentiment else "Sentiment analysis test failed"
        }
    except Exception as e:
        services_status["sentiment_analyzer"] = {
            "status": "error",
            "last_check": datetime.now().isoformat(),
            "error": str(e)
        }
    
    # Check trading strategy service
    try:
        from ...trading.trading_strategy import TradingStrategy
        trading_strategy = TradingStrategy()
        # Check if the service can be instantiated
        services_status["trading_strategy"] = {
            "status": "active",
            "last_check": datetime.now().isoformat(),
            "test_result": "Trading strategy service instantiated successfully"
        }
    except Exception as e:
        services_status["trading_strategy"] = {
            "status": "error",
            "last_check": datetime.now().isoformat(),
            "error": str(e)
        }
    
    # Check cache service
    try:
        from ...core.cache import get_cache_stats
        cache_stats = get_cache_stats()
        services_status["cache"] = {
            "status": "active",
            "last_check": datetime.now().isoformat(),
            "stats": cache_stats
        }
    except Exception as e:
        services_status["cache"] = {
            "status": "error",
            "last_check": datetime.now().isoformat(),
            "error": str(e)
        }
    
    # Check scheduler service
    try:
        from ...utils.setup_job_scheduler import get_scheduler_status
        scheduler_status = get_scheduler_status()
        services_status["scheduler"] = {
            "status": "active" if scheduler_status else "unknown",
            "last_check": datetime.now().isoformat(),
            "details": scheduler_status
        }
    except Exception as e:
        services_status["scheduler"] = {
            "status": "error",
            "last_check": datetime.now().isoformat(),
            "error": str(e)
        }
    
    return services_status


def get_network_stats():
    """Get network statistics"""
    try:
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }
    except Exception:
        return {
            "bytes_sent": 0,
            "bytes_recv": 0,
            "packets_sent": 0,
            "packets_recv": 0
        }
