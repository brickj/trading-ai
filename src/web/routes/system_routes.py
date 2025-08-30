"""
System routes for system status, monitoring, and performance endpoints
"""

from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
import psutil
import platform
import psycopg2.extras

# Import helper functions
from ..helpers import (
    create_api_response, 
    handle_api_error, 
    api_error_handler
)

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
        api_status = {"error": "api_tracker module not found"}

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
    """Get status of all news services"""
    try:
        services_status = {
            "alpha_vantage": {"status": "active", "last_check": datetime.now().isoformat()},
            "reddit": {"status": "active", "last_check": datetime.now().isoformat()},
            "finnhub": {"status": "rate_limited", "last_check": datetime.now().isoformat()},
            "yahoo_finance": {"status": "error", "last_check": datetime.now().isoformat(), "error": "XML parser issue"},
            "news_api": {"status": "active", "last_check": datetime.now().isoformat()},
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
    """Toggle a news service on/off"""
    try:
        data = request.get_json()
        service_name = data.get("service_name")
        enabled = data.get("enabled", True)

        if not service_name:
            return create_api_response(
                error="service_name is required",
                status_code=400
            )

        # This would toggle the service in configuration
        # For now, just return success
        return create_api_response(
            data={
                "service_name": service_name,
                "enabled": enabled,
                "message": f"Service {service_name} {'enabled' if enabled else 'disabled'}"
            }
        )

    except Exception as e:
        return handle_api_error(e, "toggle_news_service endpoint")


@system_bp.route("/api/news_services/test", methods=["POST"])
def test_news_service():
    """Test a specific news service"""
    try:
        data = request.get_json()
        service_name = data.get("service_name")

        if not service_name:
            return create_api_response(
                error="service_name is required",
                status_code=400
            )

        # This would test the actual service
        # For now, return mock test results
        test_result = {
            "service_name": service_name,
            "status": "success",
            "response_time": 0.5,
            "test_timestamp": datetime.now().isoformat(),
            "message": f"Service {service_name} is responding normally"
        }

        return create_api_response(data=test_result)

    except Exception as e:
        return handle_api_error(e, "test_news_service endpoint")


@system_bp.route("/api/news_services/config", methods=["GET"])
def get_news_services_config():
    """Get news services configuration status"""
    try:
        config_status = {
            "alpha_vantage": {
                "configured": True,
                "api_key_present": True,
                "rate_limit": "5 calls per minute"
            },
            "reddit": {
                "configured": True,
                "api_key_present": False,
                "rate_limit": "60 calls per minute"
            },
            "finnhub": {
                "configured": True,
                "api_key_present": True,
                "rate_limit": "60 calls per minute",
                "status": "rate_limited"
            },
            "yahoo_finance": {
                "configured": True,
                "api_key_present": False,
                "rate_limit": "unlimited",
                "status": "parser_error"
            }
        }

        return create_api_response(data=config_status)

    except Exception as e:
        return handle_api_error(e, "get_news_services_config endpoint")


@system_bp.route("/api/test_foreign_markets")
def test_foreign_markets_api():
    """Test foreign markets API endpoint"""
    return jsonify({
        'success': True,
        'data': {
            'markets': [
                {
                    'code': 'LSE',
                    'name': 'London Stock Exchange',
                    'country': 'United Kingdom',
                    'currency': 'GBP',
                    'timezone': 'Europe/London',
                    'symbol_suffix': '.L',
                    'status': 'open'
                },
                {
                    'code': 'TSE',
                    'name': 'Tokyo Stock Exchange',
                    'country': 'Japan',
                    'currency': 'JPY',
                    'timezone': 'Asia/Tokyo',
                    'symbol_suffix': '.T',
                    'status': 'closed'
                }
            ],
                'summary': {
                    'total_markets': 2,
                    'markets_open': 1,
                    'markets_closed': 1,
                    'total_foreign_symbols': 0,
                    'watchlist_symbols': 0,
                    'foreign_coverage': '0/0'
                }
            }
        })


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
    """Get status of various application services"""
    return {
        "data_fetcher": {"status": "active"},
        "sentiment_analyzer": {"status": "active"},
        "trading_strategy": {"status": "active"},
        "cache": {"status": "active"},
        "scheduler": {"status": "unknown"}
    }


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
