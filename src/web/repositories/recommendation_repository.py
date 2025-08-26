"""
Repository for recommendation data with optimized queries
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .base_repository import BaseRepository


class RecommendationRepository(BaseRepository):
    """
    Optimized repository for recommendation data operations
    """
    
    def __init__(self):
        super().__init__()
        self.table = "recommendations"
    
    def get_recent_recommendations(self, limit: int = 20, 
                                 symbol: str = None) -> List[Dict]:
        """
        Get recent recommendations with optimized query
        
        Args:
            limit: Number of recommendations to return
            symbol: Optional symbol filter
            
        Returns:
            List of recommendation dictionaries
        """
        query = f"""
            SELECT id, symbol, timestamp, recommendation_type, action, 
                   confidence, target_price, stop_loss, sentiment_score, 
                   price_at_recommendation, analysis_summary
            FROM {self.table}
            WHERE 1=1
        """
        params = []
        
        if symbol:
            query += " AND symbol = %s"
            params.append(symbol.upper())
        
        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)
        
        results = self.execute_query(query, params, fetch_all=True)
        
        return [dict(row) for row in results] if results else []
    
    def get_recommendations_by_date_range(self, start_date: datetime, 
                                        end_date: datetime,
                                        symbol: str = None,
                                        action: str = None) -> List[Dict]:
        """
        Get recommendations within date range with filters
        
        Args:
            start_date: Start date
            end_date: End date
            symbol: Optional symbol filter
            action: Optional action filter (BUY, SELL, HOLD)
            
        Returns:
            List of recommendation dictionaries
        """
        query = f"""
            SELECT id, symbol, timestamp, recommendation_type, action, 
                   confidence, target_price, stop_loss, sentiment_score, 
                   price_at_recommendation, analysis_summary
            FROM {self.table}
            WHERE timestamp BETWEEN %s AND %s
        """
        params = [start_date, end_date]
        
        if symbol:
            query += " AND symbol = %s"
            params.append(symbol.upper())
        
        if action:
            query += " AND action = %s"
            params.append(action.upper())
        
        query += " ORDER BY timestamp DESC"
        
        results = self.execute_query(query, params, fetch_all=True)
        
        return [dict(row) for row in results] if results else []
    
    def get_recommendation_statistics(self, days_back: int = 30,
                                    symbol: str = None) -> Dict:
        """
        Get comprehensive recommendation statistics
        
        Args:
            days_back: Number of days to look back
            symbol: Optional symbol filter
            
        Returns:
            Statistics dictionary
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        query = f"""
            SELECT 
                COUNT(*) as total_recommendations,
                AVG(confidence) as avg_confidence,
                AVG(sentiment_score) as avg_sentiment,
                COUNT(CASE WHEN action = 'BUY' THEN 1 END) as buy_count,
                COUNT(CASE WHEN action = 'SELL' THEN 1 END) as sell_count,
                COUNT(CASE WHEN action = 'HOLD' THEN 1 END) as hold_count,
                MIN(timestamp) as earliest_rec,
                MAX(timestamp) as latest_rec,
                COUNT(DISTINCT symbol) as unique_symbols
            FROM {self.table}
            WHERE timestamp >= %s
        """
        params = [cutoff_date]
        
        if symbol:
            query += " AND symbol = %s"
            params.append(symbol.upper())
        
        result = self.execute_query(query, params, fetch_one=True)
        
        if result:
            stats = dict(result)
            
            # Calculate action percentages
            total = stats['total_recommendations'] or 0
            if total > 0:
                stats['buy_percentage'] = round((stats['buy_count'] or 0) / total * 100, 1)
                stats['sell_percentage'] = round((stats['sell_count'] or 0) / total * 100, 1)
                stats['hold_percentage'] = round((stats['hold_count'] or 0) / total * 100, 1)
            else:
                stats['buy_percentage'] = stats['sell_percentage'] = stats['hold_percentage'] = 0
            
            # Format timestamps
            if stats['earliest_rec']:
                stats['earliest_rec'] = stats['earliest_rec'].isoformat()
            if stats['latest_rec']:
                stats['latest_rec'] = stats['latest_rec'].isoformat()
            
            return stats
        
        return {}
    
    def save_recommendation(self, recommendation_data: Dict) -> int:
        """
        Save a new recommendation with optimized insert
        
        Args:
            recommendation_data: Recommendation data dictionary
            
        Returns:
            ID of inserted recommendation
        """
        query = f"""
            INSERT INTO {self.table} 
            (symbol, timestamp, recommendation_type, action, confidence, 
             target_price, stop_loss, sentiment_score, price_at_recommendation, 
             analysis_summary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        params = [
            recommendation_data.get('symbol', '').upper(),
            recommendation_data.get('timestamp', datetime.now()),
            recommendation_data.get('recommendation_type', 'stock'),
            recommendation_data.get('action', 'HOLD'),
            recommendation_data.get('confidence', 0.0),
            recommendation_data.get('target_price'),
            recommendation_data.get('stop_loss'),
            recommendation_data.get('sentiment_score', 0.0),
            recommendation_data.get('price_at_recommendation'),
            recommendation_data.get('analysis_summary', '')
        ]
        
        result = self.execute_query(query, params, fetch_one=True)
        return result[0] if result else None
    
    def bulk_save_recommendations(self, recommendations: List[Dict]) -> int:
        """
        Bulk save recommendations for performance
        
        Args:
            recommendations: List of recommendation dictionaries
            
        Returns:
            Number of recommendations saved
        """
        if not recommendations:
            return 0
        
        # Ensure all recommendations have required fields
        processed_recommendations = []
        for rec in recommendations:
            processed_rec = {
                'symbol': rec.get('symbol', '').upper(),
                'timestamp': rec.get('timestamp', datetime.now()),
                'recommendation_type': rec.get('recommendation_type', 'stock'),
                'action': rec.get('action', 'HOLD'),
                'confidence': rec.get('confidence', 0.0),
                'target_price': rec.get('target_price'),
                'stop_loss': rec.get('stop_loss'),
                'sentiment_score': rec.get('sentiment_score', 0.0),
                'price_at_recommendation': rec.get('price_at_recommendation'),
                'analysis_summary': rec.get('analysis_summary', '')
            }
            processed_recommendations.append(processed_rec)
        
        return self.bulk_insert(self.table, processed_recommendations, "IGNORE")
    
    def get_performance_metrics(self, symbol: str = None, 
                               days_back: int = 30) -> Dict:
        """
        Calculate performance metrics for recommendations
        
        Args:
            symbol: Optional symbol filter
            days_back: Number of days to analyze
            
        Returns:
            Performance metrics dictionary
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # This is a simplified version - in practice you'd need price data
        # to calculate actual performance
        query = f"""
            SELECT 
                action,
                AVG(confidence) as avg_confidence,
                COUNT(*) as count,
                AVG(sentiment_score) as avg_sentiment
            FROM {self.table}
            WHERE timestamp >= %s
        """
        params = [cutoff_date]
        
        if symbol:
            query += " AND symbol = %s"
            params.append(symbol.upper())
        
        query += " GROUP BY action"
        
        results = self.execute_query(query, params, fetch_all=True)
        
        metrics = {}
        for row in results or []:
            action = row['action']
            metrics[action] = {
                'count': row['count'],
                'avg_confidence': round(row['avg_confidence'] or 0, 3),
                'avg_sentiment': round(row['avg_sentiment'] or 0, 3)
            }
        
        return metrics
    
    def cleanup_old_recommendations(self, days_to_keep: int = 90) -> int:
        """
        Clean up old recommendations to maintain performance
        
        Args:
            days_to_keep: Number of days of recommendations to keep
            
        Returns:
            Number of recommendations deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        query = f"DELETE FROM {self.table} WHERE timestamp < %s"
        
        return self.execute_query(query, [cutoff_date], fetch_all=False)
    
    def get_symbol_recommendation_history(self, symbol: str, 
                                        limit: int = 50) -> List[Dict]:
        """
        Get recommendation history for a specific symbol
        
        Args:
            symbol: Stock/crypto symbol
            limit: Maximum number of recommendations
            
        Returns:
            List of recommendations for the symbol
        """
        query = f"""
            SELECT id, timestamp, action, confidence, target_price, 
                   stop_loss, sentiment_score, price_at_recommendation,
                   analysis_summary
            FROM {self.table}
            WHERE symbol = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """
        
        results = self.execute_query(query, [symbol.upper(), limit], fetch_all=True)
        
        return [dict(row) for row in results] if results else []

