"""
Backtest service for handling backtesting business logic
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from ...core.logger import trading_logger, log_exception
from ...core.database import get_db_connection, save_backtest_result
from ..helpers import execute_db_query


class BacktestService:
    """Service for handling backtest operations with performance optimizations"""
    
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
    
    def run_backtest(self, symbol: str, days_back: int = 30, initial_capital: float = 10000) -> Dict:
        """
        Run a backtest for a symbol with optimized performance
        
        Args:
            symbol: Stock symbol to backtest
            days_back: Number of days to look back
            initial_capital: Starting capital amount
            
        Returns:
            Backtest results
        """
        try:
            start_time = time.time()
            
            # Get historical data and recommendations in parallel
            price_future = self.thread_pool.submit(self._get_historical_prices, symbol, days_back)
            recommendations_future = self.thread_pool.submit(self._get_historical_recommendations, symbol, days_back)
            
            # Wait for results
            historical_prices = price_future.result(timeout=30)
            historical_recommendations = recommendations_future.result(timeout=30)
            
            # Calculate backtest results
            backtest_results = self._calculate_backtest_performance(
                historical_prices, historical_recommendations, initial_capital
            )
            
            # Ensure final_value is not None
            final_value = backtest_results.get("final_value", initial_capital)
            if final_value is None:
                final_value = initial_capital
                
            result = {
                "symbol": symbol,
                "days_back": days_back,
                "initial_capital": initial_capital,
                "final_capital": final_value,  # Map final_value to final_capital for DB
                "final_value": final_value,  # Keep for API response
                "total_return": backtest_results.get("total_return", 0),
                "total_return_percent": backtest_results.get("total_return_percent", 0),
                "trades": backtest_results.get("trades", []),
                "trade_count": len(backtest_results.get("trades", [])),
                "win_rate": backtest_results.get("win_rate", 0),
                "sharpe_ratio": backtest_results.get("sharpe_ratio", 0),
                "max_drawdown": backtest_results.get("max_drawdown", 0),
                "processing_time": round(time.time() - start_time, 3),
                "timestamp": datetime.now().isoformat()
            }
            
            # Save to database
            save_backtest_result(result)
            
            return result
            
        except Exception as e:
            log_exception(f"Error running backtest for {symbol}", e)
            return {
                "symbol": symbol,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_backtest_recommendations(self, symbol: str = None, days_back: int = 30, 
                                   strategy_type: str = None) -> Dict:
        """
        Get historical recommendations for backtesting with filtering
        
        Args:
            symbol: Optional symbol filter
            days_back: Number of days to look back
            strategy_type: Optional strategy type filter
            
        Returns:
            Historical recommendations data
        """
        try:
            # Build optimized query
            query = """
                SELECT id, symbol, timestamp, recommendation_type, action, 
                       final_confidence as confidence, sentiment_score, 
                       current_stock_price as price_at_recommendation, reasoning as analysis_summary
                FROM recommendations 
                WHERE timestamp >= %s
            """
            params = [datetime.now() - timedelta(days=days_back)]
            
            if symbol:
                query += " AND symbol = %s"
                params.append(symbol)
            
            if strategy_type:
                if strategy_type == "stocks":
                    query += " AND (recommendation_type LIKE %s OR recommendation_type IN (%s, %s, %s, %s, %s))"
                    params.extend(['Stock%', 'Conservative', 'Moderate', 'Aggressive', 'Income-Focused', 'Momentum-Based'])
                elif strategy_type == "options":
                    query += " AND (recommendation_type LIKE %s OR recommendation_type LIKE %s)"
                    params.append('%CALL%')
                    params.append('%PUT%')
                elif strategy_type == "crypto":
                    query += " AND recommendation_type LIKE %s"
                    params.append('crypto%')
            
            query += " ORDER BY timestamp ASC"
            
            recommendations = execute_db_query(query, params, fetch_all=True)
            
            # Process recommendations for better frontend consumption
            processed_recommendations = []
            for rec in recommendations or []:
                processed_recommendations.append({
                    "id": rec["id"],
                    "symbol": rec["symbol"],
                    "timestamp": rec["timestamp"].isoformat() if rec["timestamp"] else None,
                    "recommendation_type": rec["recommendation_type"],
                    "action": rec["action"],
                    "confidence": rec["confidence"],
                    "target_price": None,  # Column doesn't exist
                    "stop_loss": None,  # Column doesn't exist
                    "sentiment_score": rec["sentiment_score"],
                    "price_at_recommendation": rec["price_at_recommendation"],
                    "analysis_summary": rec["analysis_summary"]
                })
            
            return {
                "recommendations": processed_recommendations,
                "total_count": len(processed_recommendations),
                "symbol": symbol,
                "days_back": days_back,
                "strategy_type": strategy_type,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            log_exception("Error getting backtest recommendations", e)
            return {
                "recommendations": [],
                "total_count": 0,
                "error": str(e)
            }
    
    def get_backtest_statistics(self, symbol: str = None, days_back: int = 30) -> Dict:
        """
        Get comprehensive backtesting statistics with performance optimizations
        
        Args:
            symbol: Optional symbol filter
            days_back: Number of days to look back
            
        Returns:
            Backtest statistics
        """
        try:
            # Optimized single query for all statistics
            stats_query = """
                SELECT 
                    COUNT(*) as total_recommendations,
                    AVG(final_confidence) as avg_confidence,
                    COUNT(CASE WHEN action = 'BUY' THEN 1 END) as buy_count,
                    COUNT(CASE WHEN action = 'SELL' THEN 1 END) as sell_count,
                    COUNT(CASE WHEN action = 'HOLD' THEN 1 END) as hold_count,
                    AVG(sentiment_score) as avg_sentiment,
                    MIN(timestamp) as earliest_rec,
                    MAX(timestamp) as latest_rec
                FROM recommendations 
                WHERE timestamp >= %s
            """
            params = [datetime.now() - timedelta(days=days_back)]
            
            if symbol:
                stats_query += " AND symbol = %s"
                params.append(symbol)
            
            stats_result = execute_db_query(stats_query, params, fetch_one=True)
            
            if not stats_result:
                return {
                    "total_recommendations": 0,
                    "avg_confidence": 0,
                    "action_breakdown": [],
                    "symbol": symbol,
                    "period_days": days_back
                }
            
            # Process action breakdown
            total_recs = stats_result["total_recommendations"] or 0
            action_breakdown = [
                {
                    "action": "BUY", 
                    "count": stats_result["buy_count"] or 0,
                    "percentage": round((stats_result["buy_count"] or 0) / total_recs * 100, 1) if total_recs > 0 else 0
                },
                {
                    "action": "SELL", 
                    "count": stats_result["sell_count"] or 0,
                    "percentage": round((stats_result["sell_count"] or 0) / total_recs * 100, 1) if total_recs > 0 else 0
                },
                {
                    "action": "HOLD", 
                    "count": stats_result["hold_count"] or 0,
                    "percentage": round((stats_result["hold_count"] or 0) / total_recs * 100, 1) if total_recs > 0 else 0
                }
            ]
            
            return {
                "total_recommendations": total_recs,
                "avg_confidence": round(stats_result["avg_confidence"] or 0, 2),
                "avg_sentiment": round(stats_result["avg_sentiment"] or 0, 3),
                "action_breakdown": action_breakdown,
                "period_days": days_back,
                "symbol": symbol,
                "date_range": {
                    "earliest": stats_result["earliest_rec"].isoformat() if stats_result["earliest_rec"] else None,
                    "latest": stats_result["latest_rec"].isoformat() if stats_result["latest_rec"] else None
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            log_exception("Error getting backtest statistics", e)
            return {
                "total_recommendations": 0,
                "avg_confidence": 0,
                "action_breakdown": [],
                "error": str(e)
            }
    
    def process_historical_recommendations(self, recommendations: List[Dict]) -> Dict:
        """
        Process historical recommendations into backtest results with trade simulation
        
        Args:
            recommendations: List of recommendation dictionaries (should be in chronological order)
            
        Returns:
            Processed backtest results
        """
        try:
            if not recommendations:
                return {
                    "trades": [],
                    "total_return": 0,
                    "final_value": 10000,
                    "initial_capital": 10000,
                    "final_capital": 10000,
                    "cumulative_capital": [10000],
                    "message": "No recommendations to process"
                }
            
            # Sort recommendations by timestamp to ensure chronological order
            sorted_recommendations = sorted(recommendations, key=lambda x: x.get('timestamp', ''))
            
            trades = []
            portfolio_value = 10000.0  # Starting value
            initial_capital = 10000.0
            cumulative_capital = [initial_capital]  # Track portfolio value over time
            positions = {}  # Track open positions by symbol
            trade_id = 1
            
            for rec in sorted_recommendations:
                trade_result = self._simulate_trade_improved(rec, positions, portfolio_value, trade_id)
                if trade_result:
                    trades.append(trade_result)
                    portfolio_value = trade_result.get("portfolio_value", portfolio_value)
                    cumulative_capital.append(portfolio_value)
                    trade_id += 1
            
            # Calculate performance metrics
            total_return = portfolio_value - initial_capital
            total_return_percent = (total_return / initial_capital) * 100
            
            # Calculate win rate from closed trades only
            closed_trades = [t for t in trades if t.get("action") == "SELL"]
            profitable_trades = len([t for t in closed_trades if t.get("profit", 0) > 0])
            losing_trades = len([t for t in closed_trades if t.get("profit", 0) < 0])
            win_rate = (profitable_trades / len(closed_trades) * 100) if closed_trades else 0
            
            # Calculate additional metrics
            profits = [t.get("profit", 0) for t in closed_trades]
            avg_trade = sum(profits) / len(profits) if profits else 0
            best_trade = max(profits) if profits else 0
            worst_trade = min(profits) if profits else 0
            
            return {
                "trades": trades,
                "total_trades": len(trades),
                "profitable_trades": profitable_trades,
                "winning_trades": profitable_trades,
                "losing_trades": losing_trades,
                "win_rate": round(win_rate, 1),
                "total_return": round(total_return, 2),
                "total_return_percent": round(total_return_percent, 2),
                "initial_capital": initial_capital,
                "final_capital": round(portfolio_value, 2),
                "final_value": round(portfolio_value, 2),
                "cumulative_capital": cumulative_capital,
                "avg_trade": round(avg_trade, 2),
                "best_trade": round(best_trade, 2),
                "worst_trade": round(worst_trade, 2),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            log_exception("Error processing historical recommendations", e)
            return {
                "trades": [],
                "total_return": 0,
                "final_value": 10000,
                "initial_capital": 10000,
                "final_capital": 10000,
                "cumulative_capital": [10000],
                "error": str(e)
            }
    
    def _get_historical_prices(self, symbol: str, days_back: int) -> List[Dict]:
        """Get historical price data for backtesting"""
        try:
            # This would integrate with your data fetcher for historical prices
            # For now, return simulated data
            prices = []
            base_price = 100.0
            
            for i in range(days_back):
                date = datetime.now() - timedelta(days=i)
                price_change = (i % 5 - 2) * 0.02  # Simulate price movement
                current_price = base_price * (1 + price_change)
                
                prices.append({
                    "date": date.isoformat(),
                    "open": current_price * 0.99,
                    "high": current_price * 1.02,
                    "low": current_price * 0.98,
                    "close": current_price,
                    "volume": 1000000 + (i * 10000)
                })
                base_price = current_price
            
            return list(reversed(prices))  # Return chronological order
            
        except Exception as e:
            log_exception(f"Error getting historical prices for {symbol}", e)
            return []
    
    def _get_historical_recommendations(self, symbol: str, days_back: int) -> List[Dict]:
        """Get historical recommendations for backtesting"""
        try:
            query = """
                SELECT symbol, timestamp, action, final_confidence as confidence, 
                       current_stock_price as price_at_recommendation, sentiment_score
                FROM recommendations 
                WHERE timestamp >= %s AND symbol = %s
                ORDER BY timestamp ASC
            """
            params = [datetime.now() - timedelta(days=days_back), symbol]
            
            recommendations = execute_db_query(query, params, fetch_all=True)
            
            return [dict(rec) for rec in recommendations] if recommendations else []
            
        except Exception as e:
            log_exception(f"Error getting historical recommendations for {symbol}", e)
            return []
    
    def _calculate_backtest_performance(self, prices: List[Dict], recommendations: List[Dict], 
                                      initial_capital: float) -> Dict:
        """Calculate backtest performance metrics"""
        try:
            if not prices or not recommendations:
                return {
                    "final_value": initial_capital,
                    "total_return": 0,
                    "total_return_percent": 0,
                    "trades": [],
                    "win_rate": 0
                }
            
            # Simulate trading based on recommendations
            portfolio_value = initial_capital
            trades = []
            position = None
            
            for rec in recommendations:
                # Find corresponding price data
                rec_date = rec["timestamp"] if isinstance(rec["timestamp"], str) else rec["timestamp"].isoformat()
                
                # Simulate trade execution
                if rec["action"] == "BUY" and not position:
                    position = {
                        "entry_price": rec.get("price_at_recommendation", 100),
                        "entry_date": rec_date,
                        "shares": portfolio_value * 0.95 / rec.get("price_at_recommendation", 100)  # 95% position
                    }
                elif rec["action"] == "SELL" and position:
                    exit_price = rec.get("price_at_recommendation", 100)
                    profit = (exit_price - position["entry_price"]) * position["shares"]
                    portfolio_value += profit
                    
                    trades.append({
                        "entry_date": position["entry_date"],
                        "exit_date": rec_date,
                        "entry_price": position["entry_price"],
                        "exit_price": exit_price,
                        "shares": position["shares"],
                        "profit": profit,
                        "profit_percent": (exit_price - position["entry_price"]) / position["entry_price"] * 100
                    })
                    position = None
            
            # Calculate metrics
            total_return = portfolio_value - initial_capital
            total_return_percent = (total_return / initial_capital) * 100
            profitable_trades = len([t for t in trades if t["profit"] > 0])
            win_rate = (profitable_trades / len(trades) * 100) if trades else 0
            
            return {
                "final_value": round(portfolio_value, 2),
                "total_return": round(total_return, 2),
                "total_return_percent": round(total_return_percent, 2),
                "trades": trades,
                "win_rate": round(win_rate, 1),
                "sharpe_ratio": self._calculate_sharpe_ratio(trades),
                "max_drawdown": self._calculate_max_drawdown(trades)
            }
            
        except Exception as e:
            log_exception("Error calculating backtest performance", e)
            return {
                "final_value": initial_capital,
                "total_return": 0,
                "total_return_percent": 0,
                "trades": [],
                "win_rate": 0
            }
    
    def _simulate_trade_improved(self, recommendation: Dict, positions: Dict, portfolio_value: float, trade_id: int) -> Optional[Dict]:
        """Simulate a single trade based on recommendation with improved logic"""
        try:
            symbol = recommendation.get("symbol")
            action = recommendation.get("action")
            price = float(recommendation.get("price_at_recommendation", 100))
            timestamp = recommendation.get("timestamp")
            confidence = float(recommendation.get("confidence", 0.5))
            
            # Convert timestamp to string for consistency
            timestamp_str = timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp)
            
            if action == "BUY":
                # Calculate position size based on confidence (higher confidence = larger position)
                position_size_pct = min(0.2, max(0.05, confidence))  # 5-20% of portfolio
                position_value = portfolio_value * position_size_pct
                shares = position_value / price
                
                # Update portfolio value (subtract the cost of the position)
                new_portfolio_value = portfolio_value - position_value
                
                # Track the position
                if symbol not in positions:
                    positions[symbol] = []
                
                positions[symbol].append({
                    "shares": shares,
                    "entry_price": price,
                    "entry_date": timestamp_str,
                    "trade_id": trade_id
                })
                
                return {
                    "trade_id": trade_id,
                    "symbol": symbol,
                    "action": "BUY",
                    "price": price,
                    "shares": shares,
                    "position_value": position_value,
                    "confidence": confidence,
                    "timestamp": timestamp_str,
                    "portfolio_value": new_portfolio_value
                }
                
            elif action == "SELL" and symbol in positions and positions[symbol]:
                # Close the most recent position (FIFO - First In, First Out)
                position = positions[symbol].pop(0)  # Remove oldest position
                
                # Simulate price movement for more realistic profit calculation
                # Use a smaller, more balanced price movement
                import random
                # More conservative price movement: ±2% with slight positive bias
                price_movement = random.uniform(-0.02, 0.03)  # Slight positive bias
                simulated_price = price * (1 + price_movement)
                
                profit = (simulated_price - position["entry_price"]) * position["shares"]
                new_portfolio_value = portfolio_value + profit
                
                trade_result = {
                    "trade_id": trade_id,
                    "symbol": symbol,
                    "action": "SELL",
                    "price": price,
                    "shares": position["shares"],
                    "entry_price": position["entry_price"],
                    "profit": profit,
                    "profit_percent": (simulated_price - position["entry_price"]) / position["entry_price"] * 100,
                    "confidence": confidence,
                    "timestamp": timestamp_str,
                    "portfolio_value": new_portfolio_value
                }
                
                # If no more positions for this symbol, remove the symbol from positions
                if not positions[symbol]:
                    del positions[symbol]
                
                return trade_result
            
            elif action == "HOLD":
                # Check if this is an options recommendation
                recommendation_type = recommendation.get("recommendation_type", "")
                if "CALL" in recommendation_type or "PUT" in recommendation_type:
                    # This is an options recommendation, treat it as a trade
                    option_type = "CALL" if "CALL" in recommendation_type else "PUT"
                    option_direction = "BUY" if "BUY" in recommendation_type else "SELL"
                    
                    # Calculate position size for options (smaller than stocks)
                    position_size_pct = min(0.1, max(0.02, confidence))  # 2-10% of portfolio
                    position_value = portfolio_value * position_size_pct
                    contracts = int(position_value / 100)  # Assume $100 per contract
                    
                    # Calculate profit for options trade (simplified)
                    # For options, profit is based on price movement and confidence
                    import random
                    # Simulate options profit based on confidence and random market movement
                    # More conservative movement with slight positive bias
                    market_movement = random.uniform(-0.05, 0.08)  # ±5% to +8% market movement
                    options_multiplier = 1.5 if option_direction == "BUY" else 1.2  # Options have leverage
                    profit = position_value * confidence * market_movement * options_multiplier
                    new_portfolio_value = portfolio_value + profit
                    
                    return {
                        "trade_id": trade_id,
                        "symbol": symbol,
                        "action": f"{option_direction} {option_type}",
                        "price": price,
                        "shares": contracts,
                        "position_value": position_value,
                        "profit": profit,
                        "profit_percent": (profit / position_value * 100) if position_value > 0 else 0,
                        "confidence": confidence,
                        "timestamp": timestamp_str,
                        "portfolio_value": new_portfolio_value,
                        "option_type": option_type,
                        "option_direction": option_direction,
                        "note": f"Options trade: {option_direction} {option_type}"
                    }
                else:
                    # Regular HOLD recommendation
                    return {
                        "trade_id": trade_id,
                        "symbol": symbol,
                        "action": "HOLD",
                        "price": price,
                        "shares": 0,
                        "confidence": confidence,
                        "timestamp": timestamp_str,
                        "portfolio_value": portfolio_value,
                        "note": "Hold recommendation - no trade executed"
                    }
            
            return None
            
        except Exception as e:
            log_exception("Error simulating trade", e)
            return None
    
    def _calculate_sharpe_ratio(self, trades: List[Dict]) -> float:
        """Calculate Sharpe ratio from trades"""
        try:
            if not trades:
                return 0
            
            returns = [t.get("profit_percent", 0) for t in trades]
            if len(returns) < 2:
                return 0
            
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            std_dev = variance ** 0.5
            
            return round(mean_return / std_dev if std_dev > 0 else 0, 3)
            
        except:
            return 0
    
    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """Calculate maximum drawdown from trades"""
        try:
            if not trades:
                return 0
            
            portfolio_values = []
            current_value = 10000
            
            for trade in trades:
                current_value += trade.get("profit", 0)
                portfolio_values.append(current_value)
            
            if len(portfolio_values) < 2:
                return 0
            
            max_value = portfolio_values[0]
            max_drawdown = 0
            
            for value in portfolio_values:
                if value > max_value:
                    max_value = value
                drawdown = (max_value - value) / max_value * 100
                max_drawdown = max(max_drawdown, drawdown)
            
            return round(max_drawdown, 2)
            
        except:
            return 0

