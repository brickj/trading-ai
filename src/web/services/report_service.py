"""
Report service for handling report generation and analytics
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from concurrent.futures import ThreadPoolExecutor

from ...core.logger import trading_logger, log_exception
from ...core.cache import get_cached_result, cache_result
from ..helpers import execute_db_query


class ReportService:
    """Service for handling report generation with performance optimizations"""
    
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self._cache_timeout = 600  # 10 minutes for reports
    
    def generate_comprehensive_report(self, report_type: str = "weekly", 
                                    symbol: str = None, use_cache: bool = True) -> Dict:
        """
        Generate comprehensive trading report with parallel data processing
        
        Args:
            report_type: Type of report (daily, weekly, monthly)
            symbol: Optional symbol filter
            use_cache: Whether to use cached results
            
        Returns:
            Comprehensive report data
        """
        try:
            cache_key = f"comprehensive_report_{report_type}_{symbol or 'all'}"
            
            if use_cache:
                cached_result = get_cached_result(cache_key)
                if cached_result:
                    return cached_result
            
            start_time = time.time()
            
            # Determine date range based on report type
            date_range = self._get_date_range(report_type)
            
            # Parallel data collection for report sections
            futures = {
                'performance_summary': self.thread_pool.submit(
                    self._get_performance_summary, date_range, symbol
                ),
                'trading_activity': self.thread_pool.submit(
                    self._get_trading_activity, date_range, symbol
                ),
                'recommendation_analysis': self.thread_pool.submit(
                    self._get_recommendation_analysis, date_range, symbol
                ),
                'sector_breakdown': self.thread_pool.submit(
                    self._get_sector_breakdown, date_range, symbol
                ),
                'risk_metrics': self.thread_pool.submit(
                    self._get_risk_metrics, date_range, symbol
                )
            }
            
            # Collect results
            report_data = {
                "report_metadata": {
                    "type": report_type,
                    "symbol": symbol,
                    "date_range": {
                        "start": date_range["start"].isoformat(),
                        "end": date_range["end"].isoformat()
                    },
                    "generated_at": datetime.now().isoformat(),
                    "generation_time": None  # Will be filled later
                }
            }
            
            for section, future in futures.items():
                try:
                    report_data[section] = future.result(timeout=30)
                except Exception as e:
                    trading_logger.error_logger.error(f"Error generating {section}: {e}")
                    report_data[section] = {"error": str(e)}
            
            # Calculate generation time
            generation_time = round(time.time() - start_time, 3)
            report_data["report_metadata"]["generation_time"] = generation_time
            
            # Cache successful reports
            if not any("error" in v for v in report_data.values() if isinstance(v, dict)):
                cache_result(cache_key, report_data, ttl=self._cache_timeout)
            
            return report_data
            
        except Exception as e:
            log_exception("Error generating comprehensive report", e)
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_recommendation_metrics(self, days_back: int = 30, symbol: str = None) -> Dict:
        """
        Get detailed recommendation performance metrics
        
        Args:
            days_back: Number of days to analyze
            symbol: Optional symbol filter
            
        Returns:
            Recommendation metrics data
        """
        try:
            start_time = time.time()
            date_cutoff = datetime.now() - timedelta(days=days_back)
            
            # Parallel metrics calculation
            futures = {
                'accuracy_metrics': self.thread_pool.submit(
                    self._calculate_accuracy_metrics, date_cutoff, symbol
                ),
                'performance_by_action': self.thread_pool.submit(
                    self._get_performance_by_action, date_cutoff, symbol
                ),
                'confidence_analysis': self.thread_pool.submit(
                    self._analyze_confidence_levels, date_cutoff, symbol
                ),
                'temporal_analysis': self.thread_pool.submit(
                    self._analyze_temporal_patterns, date_cutoff, symbol
                )
            }
            
            # Collect results
            metrics_data = {
                "analysis_period": {
                    "days_back": days_back,
                    "start_date": date_cutoff.isoformat(),
                    "end_date": datetime.now().isoformat(),
                    "symbol": symbol
                }
            }
            
            for metric_type, future in futures.items():
                try:
                    metrics_data[metric_type] = future.result(timeout=20)
                except Exception as e:
                    metrics_data[metric_type] = {"error": str(e)}
            
            metrics_data["calculation_time"] = round(time.time() - start_time, 3)
            metrics_data["timestamp"] = datetime.now().isoformat()
            
            return metrics_data
            
        except Exception as e:
            log_exception("Error getting recommendation metrics", e)
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_job_schedules_report(self) -> Dict:
        """
        Generate report on scheduled job performance
        
        Returns:
            Job schedules performance report
        """
        try:
            # This would integrate with your job scheduler
            # For now, return simulated job performance data
            
            job_schedules = [
                {
                    "name": "Stock Data Preloader",
                    "schedule": "Every 30 minutes",
                    "last_run": (datetime.now() - timedelta(minutes=15)).isoformat(),
                    "next_run": (datetime.now() + timedelta(minutes=15)).isoformat(),
                    "status": "active",
                    "success_rate": 98.5,
                    "avg_execution_time": 45.2
                },
                {
                    "name": "News Opportunities",
                    "schedule": "Every hour",
                    "last_run": (datetime.now() - timedelta(minutes=45)).isoformat(),
                    "next_run": (datetime.now() + timedelta(minutes=15)).isoformat(),
                    "status": "active",
                    "success_rate": 95.2,
                    "avg_execution_time": 120.8
                },
                {
                    "name": "Watchlist Opportunities",
                    "schedule": "Every 2 hours",
                    "last_run": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "next_run": (datetime.now() + timedelta(hours=1)).isoformat(),
                    "status": "active",
                    "success_rate": 97.8,
                    "avg_execution_time": 180.5
                }
            ]
            
            # Calculate summary statistics
            total_jobs = len(job_schedules)
            active_jobs = len([j for j in job_schedules if j["status"] == "active"])
            avg_success_rate = sum(j["success_rate"] for j in job_schedules) / total_jobs
            
            return {
                "job_schedules": job_schedules,
                "summary": {
                    "total_jobs": total_jobs,
                    "active_jobs": active_jobs,
                    "inactive_jobs": total_jobs - active_jobs,
                    "avg_success_rate": round(avg_success_rate, 1),
                    "overall_status": "healthy" if avg_success_rate > 90 else "needs_attention"
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            log_exception("Error generating job schedules report", e)
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_date_range(self, report_type: str) -> Dict[str, datetime]:
        """Get date range based on report type"""
        end_date = datetime.now()
        
        if report_type == "daily":
            start_date = end_date - timedelta(days=1)
        elif report_type == "weekly":
            start_date = end_date - timedelta(weeks=1)
        elif report_type == "monthly":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(weeks=1)  # Default to weekly
        
        return {"start": start_date, "end": end_date}
    
    def _get_performance_summary(self, date_range: Dict, symbol: str = None) -> Dict:
        """Get performance summary for the date range"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_recommendations,
                    AVG(final_confidence) as avg_confidence,
                    COUNT(CASE WHEN action = 'BUY' THEN 1 END) as buy_actions,
                    COUNT(CASE WHEN action = 'SELL' THEN 1 END) as sell_actions,
                    AVG(sentiment_score) as avg_sentiment
                FROM recommendations 
                WHERE timestamp BETWEEN %s AND %s
            """
            params = [date_range["start"], date_range["end"]]
            
            if symbol:
                query += " AND symbol = %s"
                params.append(symbol)
            
            result = execute_db_query(query, params, fetch_one=True)
            
            if result:
                return {
                    "total_recommendations": result["total_recommendations"] or 0,
                    "avg_confidence": round(result["avg_confidence"] or 0, 2),
                    "buy_actions": result["buy_actions"] or 0,
                    "sell_actions": result["sell_actions"] or 0,
                    "avg_sentiment": round(result["avg_sentiment"] or 0, 3),
                    "buy_sell_ratio": round(
                        (result["buy_actions"] or 0) / max(result["sell_actions"] or 1, 1), 2
                    )
                }
            else:
                return {"message": "No data available for the specified period"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _get_trading_activity(self, date_range: Dict, symbol: str = None) -> Dict:
        """Get trading activity metrics"""
        try:
            query = """
                SELECT 
                    DATE(timestamp) as trade_date,
                    COUNT(*) as daily_recommendations,
                    AVG(final_confidence) as daily_avg_confidence
                FROM recommendations 
                WHERE timestamp BETWEEN %s AND %s
            """
            params = [date_range["start"], date_range["end"]]
            
            if symbol:
                query += " AND symbol = %s"
                params.append(symbol)
            
            query += " GROUP BY DATE(timestamp) ORDER BY trade_date"
            
            results = execute_db_query(query, params, fetch_all=True)
            
            daily_activity = []
            for row in results or []:
                daily_activity.append({
                    "date": row["trade_date"].isoformat() if row["trade_date"] else None,
                    "recommendations": row["daily_recommendations"] or 0,
                    "avg_confidence": round(row["daily_avg_confidence"] or 0, 2)
                })
            
            return {
                "daily_activity": daily_activity,
                "total_active_days": len(daily_activity),
                "avg_daily_recommendations": round(
                    sum(d["recommendations"] for d in daily_activity) / max(len(daily_activity), 1), 1
                )
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _get_recommendation_analysis(self, date_range: Dict, symbol: str = None) -> Dict:
        """Analyze recommendation patterns"""
        try:
            query = """
                SELECT 
                    recommendation_type,
                    action,
                    COUNT(*) as count,
                    AVG(final_confidence) as avg_confidence
                FROM recommendations 
                WHERE timestamp BETWEEN %s AND %s
            """
            params = [date_range["start"], date_range["end"]]
            
            if symbol:
                query += " AND symbol = %s"
                params.append(symbol)
            
            query += " GROUP BY recommendation_type, action"
            
            results = execute_db_query(query, params, fetch_all=True)
            
            analysis = {}
            for row in results or []:
                rec_type = row["recommendation_type"] or "unknown"
                if rec_type not in analysis:
                    analysis[rec_type] = {}
                
                analysis[rec_type][row["action"]] = {
                    "count": row["count"] or 0,
                    "avg_confidence": round(row["avg_confidence"] or 0, 2)
                }
            
            return {
                "by_type_and_action": analysis,
                "total_types": len(analysis)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _get_sector_breakdown(self, date_range: Dict, symbol: str = None) -> Dict:
        """Get sector-wise breakdown (simulated for now)"""
        try:
            # This would integrate with actual sector classification
            # For now, return simulated sector data
            
            sectors = {
                "Technology": {"count": 25, "avg_performance": 2.3},
                "Healthcare": {"count": 18, "avg_performance": 1.8},
                "Financial": {"count": 22, "avg_performance": 1.5},
                "Energy": {"count": 12, "avg_performance": -0.5},
                "Consumer": {"count": 15, "avg_performance": 1.2}
            }
            
            return {
                "sector_breakdown": sectors,
                "top_performing_sector": "Technology",
                "total_sectors": len(sectors)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _get_risk_metrics(self, date_range: Dict, symbol: str = None) -> Dict:
        """Calculate risk metrics"""
        try:
            # Simulate risk calculations
            return {
                "volatility": 0.15,
                "max_drawdown": 0.08,
                "sharpe_ratio": 1.35,
                "var_95": 0.025,
                "risk_adjusted_return": 0.12,
                "correlation_to_market": 0.75
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_accuracy_metrics(self, date_cutoff: datetime, symbol: str = None) -> Dict:
        """Calculate recommendation accuracy metrics"""
        try:
            # This would calculate actual vs predicted performance
            # For now, return simulated accuracy data
            
            return {
                "overall_accuracy": 0.68,
                "buy_accuracy": 0.72,
                "sell_accuracy": 0.65,
                "hold_accuracy": 0.70,
                "precision": 0.71,
                "recall": 0.66,
                "f1_score": 0.68
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _get_performance_by_action(self, date_cutoff: datetime, symbol: str = None) -> Dict:
        """Get performance breakdown by action type"""
        try:
            query = """
                SELECT 
                    action,
                    COUNT(*) as count,
                    AVG(final_confidence) as avg_confidence,
                    AVG(sentiment_score) as avg_sentiment
                FROM recommendations 
                WHERE timestamp >= %s
            """
            params = [date_cutoff]
            
            if symbol:
                query += " AND symbol = %s"
                params.append(symbol)
            
            query += " GROUP BY action"
            
            results = execute_db_query(query, params, fetch_all=True)
            
            performance_data = {}
            for row in results or []:
                action = row["action"] or "UNKNOWN"
                performance_data[action] = {
                    "count": row["count"] or 0,
                    "avg_confidence": round(row["avg_confidence"] or 0, 2),
                    "avg_sentiment": round(row["avg_sentiment"] or 0, 3)
                }
            
            return performance_data
            
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_confidence_levels(self, date_cutoff: datetime, symbol: str = None) -> Dict:
        """Analyze confidence level distributions"""
        try:
            query = """
                SELECT 
                    CASE 
                        WHEN final_confidence >= 0.8 THEN 'high'
                        WHEN final_confidence >= 0.6 THEN 'medium'
                        ELSE 'low'
                    END as confidence_level,
                    COUNT(*) as count,
                    AVG(final_confidence) as avg_confidence
                FROM recommendations 
                WHERE timestamp >= %s
            """
            params = [date_cutoff]
            
            if symbol:
                query += " AND symbol = %s"
                params.append(symbol)
            
            query += " GROUP BY confidence_level"
            
            results = execute_db_query(query, params, fetch_all=True)
            
            confidence_analysis = {}
            for row in results or []:
                level = row["confidence_level"] or "unknown"
                confidence_analysis[level] = {
                    "count": row["count"] or 0,
                    "avg_confidence": round(row["avg_confidence"] or 0, 2)
                }
            
            return confidence_analysis
            
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_temporal_patterns(self, date_cutoff: datetime, symbol: str = None) -> Dict:
        """Analyze temporal patterns in recommendations"""
        try:
            query = """
                SELECT 
                    EXTRACT(hour FROM timestamp) as hour_of_day,
                    EXTRACT(dow FROM timestamp) as day_of_week,
                    COUNT(*) as count
                FROM recommendations 
                WHERE timestamp >= %s
            """
            params = [date_cutoff]
            
            if symbol:
                query += " AND symbol = %s"
                params.append(symbol)
            
            query += " GROUP BY hour_of_day, day_of_week ORDER BY hour_of_day, day_of_week"
            
            results = execute_db_query(query, params, fetch_all=True)
            
            hourly_patterns = {}
            daily_patterns = {}
            
            for row in results or []:
                hour = int(row["hour_of_day"] or 0)
                day = int(row["day_of_week"] or 0)
                count = row["count"] or 0
                
                hourly_patterns[hour] = hourly_patterns.get(hour, 0) + count
                daily_patterns[day] = daily_patterns.get(day, 0) + count
            
            return {
                "hourly_distribution": hourly_patterns,
                "daily_distribution": daily_patterns,
                "peak_hour": max(hourly_patterns, key=hourly_patterns.get) if hourly_patterns else None,
                "peak_day": max(daily_patterns, key=daily_patterns.get) if daily_patterns else None
            }
            
        except Exception as e:
            return {"error": str(e)}

