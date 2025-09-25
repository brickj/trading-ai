"""
Data service for handling data processing and management operations
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor
import json

from ...core.logger import trading_logger, log_exception
from ...core.cache import get_cached_result, cache_result
from ...core.database import get_db_connection
from ..helpers import execute_db_query, get_preloaded_opportunities


class DataService:
    """Service for handling data operations with performance optimizations"""
    
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=6)
        self._cache_timeout = 300  # 5 minutes default
    
    def get_dashboard_data(self, use_cache: bool = True) -> Dict:
        """
        Get optimized dashboard data with parallel data fetching
        
        Args:
            use_cache: Whether to use cached results
            
        Returns:
            Dashboard data dictionary
        """
        try:
            cache_key = "dashboard_data"
            
            if use_cache:
                cached_result = get_cached_result(cache_key)
                if cached_result:
                    return cached_result
            
            start_time = time.time()
            
            # Parallel data fetching for dashboard components
            futures = {
                'market_status': self.thread_pool.submit(self._get_market_status),
                'top_gainers': self.thread_pool.submit(self._get_top_gainers),
                'top_losers': self.thread_pool.submit(self._get_top_losers),
                'recent_recommendations': self.thread_pool.submit(self._get_recent_recommendations, 10),
                'portfolio_summary': self.thread_pool.submit(self._get_portfolio_summary),
                'market_movers': self.thread_pool.submit(self._get_market_movers)
            }
            
            # Collect results
            dashboard_data = {}
            for key, future in futures.items():
                try:
                    dashboard_data[key] = future.result(timeout=15)
                except Exception as e:
                    trading_logger.error_logger.error(f"Error getting {key}: {e}")
                    dashboard_data[key] = {"error": str(e)}
            
            # Add metadata
            dashboard_data.update({
                "loading_time": round(time.time() - start_time, 3),
                "timestamp": datetime.now().isoformat(),
                "cached": False
            })
            
            # Cache successful results
            if not any("error" in v for v in dashboard_data.values() if isinstance(v, dict)):
                cache_result(cache_key, dashboard_data, ttl=self._cache_timeout)
            
            return dashboard_data
            
        except Exception as e:
            log_exception("Error getting dashboard data", e)
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_preloaded_data_status(self) -> Dict:
        """
        Get status of preloaded data across all tables
        
        Returns:
            Preloaded data status information
        """
        try:
            status_data = {}
            
            # Check each preloaded data table
            tables = [
                ('preloaded_watchlist_opportunities', 'watchlist'),
                ('preloaded_news_opportunities', 'news'),
                ('market_movers', 'market_movers')
            ]
            
            for table_name, data_type in tables:
                try:
                    query = f"""
                        SELECT 
                            COUNT(*) as record_count,
                            MAX(timestamp) as latest_update
                        FROM {table_name}
                    """
                    result = execute_db_query(query, fetch_one=True)
                    
                    status_data[data_type] = {
                        "table": table_name,
                        "record_count": result["record_count"] if result else 0,
                        "latest_update": result["latest_update"].isoformat() if result and result["latest_update"] else None,
                        "status": "active" if result and result["record_count"] > 0 else "empty"
                    }
                    
                except Exception as e:
                    status_data[data_type] = {
                        "table": table_name,
                        "error": str(e),
                        "status": "error"
                    }
            
            return {
                "preloaded_data": status_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            log_exception("Error getting preloaded data status", e)
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def refresh_market_movers(self) -> Dict:
        """
        Refresh market movers data with performance optimization
        
        Returns:
            Market movers refresh status
        """
        try:
            start_time = time.time()
            
            # This would integrate with your market data service
            # For now, simulate the refresh
            
            # Delete old data
            delete_query = "DELETE FROM market_movers WHERE timestamp < %s"
            cutoff_time = datetime.now() - timedelta(hours=1)
            execute_db_query(delete_query, [cutoff_time])
            
            # Insert new market movers data (simulated)
            sample_movers = {
                'gainers': ['AAPL', 'MSFT', 'GOOGL'],
                'losers': ['META', 'TSLA', 'NFLX'],
                'timestamp': datetime.now().isoformat(),
                'source': 'refresh_service'
            }
            
            insert_query = """
                INSERT INTO market_movers (gainers, losers, timestamp, source)
                VALUES (%s, %s, %s, %s)
            """
            execute_db_query(insert_query, [
                json.dumps(sample_movers['gainers']),
                json.dumps(sample_movers['losers']),
                datetime.now(),
                sample_movers['source']
            ])
            
            return {
                "status": "success",
                "market_movers": sample_movers,
                "refresh_time": round(time.time() - start_time, 3),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            log_exception("Error refreshing market movers", e)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_logs_data(self, log_level: str = "all", limit: int = 100) -> Dict:
        """
        Get application logs with filtering and pagination
        
        Args:
            log_level: Filter by log level (all, info, warning, error)
            limit: Maximum number of log entries to return
            
        Returns:
            Logs data
        """
        try:
            # This would read from your actual log files or database
            # For now, return simulated log data
            
            sample_logs = []
            log_levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
            
            for i in range(min(limit, 50)):  # Simulate some logs
                log_entry = {
                    "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(),
                    "level": log_levels[i % len(log_levels)],
                    "message": f"Sample log message {i}",
                    "source": "trading_app",
                    "details": f"Additional details for log entry {i}"
                }
                
                # Filter by log level
                if log_level != "all" and log_entry["level"].lower() != log_level.lower():
                    continue
                    
                sample_logs.append(log_entry)
            
            return {
                "logs": sample_logs,
                "total_count": len(sample_logs),
                "log_level": log_level,
                "limit": limit,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            log_exception("Error getting logs data", e)
            return {
                "logs": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def export_logs(self, format_type: str = "json", days_back: int = 7) -> Dict:
        """
        Export logs in specified format
        
        Args:
            format_type: Export format (json, csv, txt)
            days_back: Number of days of logs to export
            
        Returns:
            Export result with download information
        """
        try:
            start_time = time.time()
            
            # Get logs for the specified period
            logs_data = self.get_logs_data(limit=1000)  # Get more logs for export
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days_back)
            filtered_logs = []
            
            for log in logs_data.get("logs", []):
                log_time = datetime.fromisoformat(log["timestamp"].replace('Z', '+00:00'))
                if log_time >= cutoff_date:
                    filtered_logs.append(log)
            
            # Format data based on requested format
            if format_type == "json":
                export_data = json.dumps(filtered_logs, indent=2)
                content_type = "application/json"
                file_extension = "json"
            elif format_type == "csv":
                # Convert to CSV format
                csv_lines = ["timestamp,level,source,message,details"]
                for log in filtered_logs:
                    csv_lines.append(f"{log['timestamp']},{log['level']},{log['source']},{log['message']},{log['details']}")
                export_data = "\n".join(csv_lines)
                content_type = "text/csv"
                file_extension = "csv"
            else:  # txt format
                txt_lines = []
                for log in filtered_logs:
                    txt_lines.append(f"[{log['timestamp']}] {log['level']}: {log['message']}")
                export_data = "\n".join(txt_lines)
                content_type = "text/plain"
                file_extension = "txt"
            
            filename = f"trading_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
            
            return {
                "status": "success",
                "filename": filename,
                "content_type": content_type,
                "data": export_data,
                "record_count": len(filtered_logs),
                "days_back": days_back,
                "export_time": round(time.time() - start_time, 3),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            log_exception("Error exporting logs", e)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_market_status(self) -> Dict:
        """Get current market status"""
        try:
            # Determine if market is open (simplified logic)
            now = datetime.now()
            weekday = now.weekday()  # 0 = Monday, 6 = Sunday
            hour = now.hour
            
            is_market_open = (
                weekday < 5 and  # Monday to Friday
                9 <= hour < 16   # 9 AM to 4 PM (simplified)
            )
            
            return {
                "is_open": is_market_open,
                "session": "regular" if is_market_open else "closed",
                "next_open": "Next trading day 9:00 AM" if not is_market_open else None,
                "timezone": "Eastern",
                "timestamp": now.isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_top_gainers(self) -> List[Dict]:
        """Get top gaining stocks"""
        try:
            # Simulate top gainers data
            return [
                {"symbol": "AAPL", "change_percent": 5.2, "price": 150.25},
                {"symbol": "MSFT", "change_percent": 3.8, "price": 310.50},
                {"symbol": "GOOGL", "change_percent": 2.9, "price": 2750.00}
            ]
        except Exception as e:
            return [{"error": str(e)}]
    
    def _get_top_losers(self) -> List[Dict]:
        """Get top losing stocks"""
        try:
            # Simulate top losers data
            return [
                {"symbol": "META", "change_percent": -4.1, "price": 280.75},
                {"symbol": "TSLA", "change_percent": -3.5, "price": 195.20},
                {"symbol": "NFLX", "change_percent": -2.8, "price": 420.30}
            ]
        except Exception as e:
            return [{"error": str(e)}]
    
    def _get_recent_recommendations(self, limit: int = 10) -> List[Dict]:
        """Get recent trading recommendations"""
        try:
            query = """
                SELECT symbol, action, confidence, timestamp, recommendation_type
                FROM recommendations 
                ORDER BY timestamp DESC 
                LIMIT %s
            """
            recommendations = execute_db_query(query, [limit], fetch_all=True)
            
            result = []
            for rec in recommendations or []:
                result.append({
                    "symbol": rec["symbol"],
                    "action": rec["action"],
                    "confidence": rec["confidence"],
                    "timestamp": rec["timestamp"].isoformat() if rec["timestamp"] else None,
                    "type": rec["recommendation_type"]
                })
            
            return result
        except Exception as e:
            return [{"error": str(e)}]
    
    def _get_portfolio_summary(self) -> Dict:
        """Get portfolio summary data"""
        try:
            # Simulate portfolio data
            return {
                "total_value": 50000.00,
                "day_change": 1250.50,
                "day_change_percent": 2.56,
                "positions_count": 12,
                "cash_balance": 5000.00
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_market_movers(self) -> Dict:
        """Get market movers data"""
        try:
            query = """
                SELECT symbol, type, price, change_amount, change_percent, volume, timestamp, analysis_data
                FROM market_movers 
                ORDER BY timestamp DESC 
                LIMIT 50
            """
            results = execute_db_query(query, fetch_all=True)
            
            if results:
                gainers = []
                losers = []
                
                for row in results:
                    stock_data = {
                        'symbol': row['symbol'],
                        'price': float(row['price']) if row['price'] else 0,
                        'change_amount': float(row['change_amount']) if row['change_amount'] else 0,
                        'change_percent': float(row['change_percent']) if row['change_percent'] else 0,
                        'volume': int(row['volume']) if row['volume'] else 0,
                        'timestamp': row['timestamp'].isoformat() if row['timestamp'] else None,
                        'analysis_data': row['analysis_data'] or {}
                    }
                    
                    if row['type'] == 'GAINER':
                        gainers.append(stock_data)
                    elif row['type'] == 'LOSER':
                        losers.append(stock_data)
                
                # Sort and limit
                gainers.sort(key=lambda x: x['change_percent'], reverse=True)
                losers.sort(key=lambda x: x['change_percent'])
                
                return {
                    "gainers": gainers[:10],
                    "losers": losers[:10],
                    "timestamp": results[0]['timestamp'].isoformat() if results and results[0]['timestamp'] else None,
                    "source": "market_movers_table"
                }
            else:
                return {
                    "gainers": [],
                    "losers": [],
                    "message": "No market movers data available"
                }
        except Exception as e:
            return {"error": str(e)}

