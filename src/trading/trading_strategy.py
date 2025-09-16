import numpy as np
from datetime import datetime
from typing import Dict, List
# from ..core.go_service_client import GoServiceClient  # Module removed


class TradingStrategy:
    def __init__(self):
        self.positions = []
        self.trade_history = []
        self.initial_capital = 10000
        self.current_capital = self.initial_capital
        # self.go_client = GoServiceClient()  # Module removed

    def calculate_option_price_estimate(
        self,
        stock_price: float,
        strike_price: float,
        days_to_expiry: int,
        option_type: str = "call",
    ) -> float:
        """
        Simple Black-Scholes approximation for option pricing
        This is a simplified version for demonstration purposes
        """
        # Simplified option pricing (not actual Black-Scholes)
        time_value = max(0.01, days_to_expiry / 365)
        volatility = 0.25  # Assumed 25% volatility
        if option_type.lower() == "call":
            intrinsic_value = max(0, stock_price - strike_price)
        else:  # put
            intrinsic_value = max(0, strike_price - stock_price)
        # Simple time value calculation
        time_premium = stock_price * volatility * np.sqrt(time_value) * 0.4
        return intrinsic_value + time_premium

    def generate_trade_signal(
        self, symbol: str, current_price: float, sentiment_data: Dict, signal_data: Dict
    ) -> Dict:
        """
        Generate specific day trading and scalping recommendations based on sentiment
        """
        # Handle both old and new signal data structures
        if "action" in signal_data:
            action = signal_data["action"]
        elif "stock_recommendation" in signal_data and "action" in signal_data["stock_recommendation"]:
            action = signal_data["stock_recommendation"]["action"]
        else:
            action = "HOLD"  # Default fallback
        # signal_strength = signal_data['signal_strength']  # Currently unused
        confidence = sentiment_data["confidence"]
        sentiment_score = sentiment_data["sentiment_score"]
        if action == "HOLD":
            return {
                "symbol": symbol,
                "action": "HOLD",
                "reasoning": signal_data.get(
                    "reasoning", "No clear trading signal available"
                ),
                "trading_strategy": "No position recommended - wait for clearer signals",
            }
        # Day trading specific parameters based on sentiment strength
        if abs(sentiment_score) >= 0.7 and confidence >= 0.8:
            # High conviction scalp (1-5 minutes)
            hold_time = "1-5 minutes"
            target_gain = (
                0.3 if abs(sentiment_score) >= 0.8 else 0.2
            )  # 20-30% gain target
            stop_loss = 0.15  # 15% stop loss
            strategy_type = "High Conviction Scalp"
        elif abs(sentiment_score) >= 0.5 and confidence >= 0.7:
            # Medium conviction day trade (15-60 minutes)
            hold_time = "15-60 minutes"
            target_gain = (
                0.25 if abs(sentiment_score) >= 0.6 else 0.15
            )  # 15-25% gain target
            stop_loss = 0.12  # 12% stop loss
            strategy_type = "Day Trade"
        elif abs(sentiment_score) >= 0.3 and confidence >= 0.6:
            # Conservative swing (2-4 hours)
            hold_time = "2-4 hours"
            target_gain = 0.15  # 15% gain target
            stop_loss = 0.10  # 10% stop loss
            strategy_type = "Intraday Swing"
        else:
            # Low conviction - smaller position
            hold_time = "30-120 minutes"
            target_gain = 0.10  # 10% gain target
            stop_loss = 0.08  # 8% stop loss
            strategy_type = "Conservative Day Trade"
        # Calculate option parameters for day trading
        if action == "CALL":
            # For day trading calls, use closer to ATM for better delta
            strike_price = current_price * 1.005  # 0.5% OTM for better liquidity
            option_type = "call"
            direction = "BULLISH"
        else:  # PUT
            # For day trading puts, use closer to ATM
            strike_price = current_price * 0.995  # 0.5% OTM for better liquidity
            option_type = "put"
            direction = "BEARISH"
        # Use shorter expiry for day trading (0-2 DTE for better theta decay
        # management)
        days_to_expiry = 1 if abs(sentiment_score) >= 0.6 else 2
        # Estimate option price with day trading adjustments
        option_price = self.calculate_option_price_estimate(
            current_price, strike_price, days_to_expiry, option_type
        )
        # Calculate position sizes for different account sizes
        trading_amounts = [500, 1000, 2000]
        position_recommendations = {}
        for amount in trading_amounts:
            # Risk 2-5% of account per trade based on conviction
            risk_percent = (
                0.05
                if abs(sentiment_score) >= 0.7
                else 0.03
                if abs(sentiment_score) >= 0.5
                else 0.02
            )
            max_risk = amount * risk_percent
            # Calculate contracts (minimum 1)
            contracts = max(1, int(max_risk / option_price))
            total_cost = option_price * contracts
            # Calculate potential outcomes
            target_price = option_price * (1 + target_gain)
            stop_price = option_price * (1 - stop_loss)
            potential_gain = (target_price - option_price) * contracts
            potential_loss = (option_price - stop_price) * contracts
            position_recommendations["${amount}"] = {
                "contracts": contracts,
                "total_cost": round(total_cost, 2),
                "risk_amount": round(total_cost, 2),
                "target_price": round(target_price, 2),
                "stop_price": round(stop_price, 2),
                "potential_gain": round(potential_gain, 2),
                "potential_loss": round(potential_loss, 2),
                "risk_reward_ratio": (
                    round(potential_gain / potential_loss, 2)
                    if potential_loss > 0
                    else 0
                ),
                "risk_percent": round((total_cost / amount) * 100, 1),
            }
        # Generate specific entry and exit strategy
        entry_strategy = self._generate_entry_strategy(
            sentiment_score, confidence, current_price
        )
        exit_strategy = self._generate_exit_strategy(target_gain, stop_loss, hold_time)
        return {
            "symbol": symbol,
            "action": action,
            "direction": direction,
            "strategy_type": strategy_type,
            "option_type": option_type,
            "strike_price": round(strike_price, 2),
            "current_price": current_price,
            "option_price": round(option_price, 2),
            "days_to_expiry": days_to_expiry,
            "hold_time": hold_time,
            "target_gain_percent": round(target_gain * 100, 1),
            "stop_loss_percent": round(stop_loss * 100, 1),
            "signal_strength": signal_data.get("signal_strength", 0.5),
            "confidence": signal_data.get("confidence", 0.5),
            "sentiment_score": sentiment_score,
            # Default position size for execute_trade
            "position_size": position_recommendations.get("$1000", {}).get(
                "contracts", 1
            ),
            "position_recommendations": position_recommendations,
            "entry_strategy": entry_strategy,
            "exit_strategy": exit_strategy,
            "reasoning": signal_data.get("reasoning", "No specific reasoning provided"),
            "day_trading_notes": self._generate_day_trading_notes(
                sentiment_score, confidence, strategy_type
            ),
        }

        # Send Telegram alert for high-confidence signals
        try:
            from src.core.telegram_alerts import telegram_alerter
            
            if confidence >= 0.7:  # Only alert for high confidence signals
                # Prepare additional data for the alert
                additional_data = {}
                if "sentiment_score" in signal_data:
                    additional_data["sentiment_score"] = signal_data["sentiment_score"]
                
                # Send the trading signal alert
                telegram_alerter.send_trading_signal(
                    symbol=symbol,
                    action=action,
                    confidence=confidence,
                    price=current_price,
                    reason=signal_data.get("reasoning", ""),
                    additional_data=additional_data
                )
        except Exception as e:
            print(f"⚠️ Error sending Telegram alert: {e}")

    def _generate_entry_strategy(
        self, sentiment_score: float, confidence: float, current_price: float
    ) -> Dict:
        """Generate specific entry strategy for day trading"""
        if abs(sentiment_score) >= 0.7 and confidence >= 0.8:
            return {
                "timing": "Enter immediately on market open or at current levels",
                "method": "Market order for immediate execution",
                "confirmation": "High conviction - no additional confirmation needed",
                "volume_check": "Ensure high option volume and tight bid-ask spread",
            }
        elif abs(sentiment_score) >= 0.5:
            return {
                "timing": "Wait for 5-15 minute confirmation of price direction",
                "method": "Limit order at mid-price or better",
                "confirmation": "Look for volume spike or technical confirmation",
                "volume_check": "Check option chain liquidity before entry",
            }
        else:
            return {
                "timing": "Wait for technical confirmation and volume",
                "method": "Limit order with patience for better fill",
                "confirmation": "Require additional technical or news catalyst",
                "volume_check": "Only trade highly liquid options",
            }

    def _generate_exit_strategy(
        self, target_gain: float, stop_loss: float, hold_time: str
    ) -> Dict:
        """Generate specific exit strategy for day trading"""
        return {
            "profit_target": f"Exit at {target_gain * 100:.0f}% gain or better",
            "stop_loss": f"Hard stop at {stop_loss * 100:.0f}% loss",
            "time_stop": f"Exit before {hold_time} regardless of P&L if no momentum",
            "trailing_stop": "Consider trailing stop after 50% of target is reached",
            "market_close": "Close all positions 30 minutes before market close",
            "partial_exits": "Consider taking 50% profits at half target, let rest run",
        }

    def _generate_day_trading_notes(
        self, sentiment_score: float, confidence: float, strategy_type: str
    ) -> List[str]:
        """Generate specific notes for day trading execution"""
        notes = [
            "Strategy: {strategy_type} based on sentiment analysis",
            "Conviction Level: {self._get_conviction_level(sentiment_score)}",
            "⚠️ Day trading options carries high risk - never risk more than you can afford to lose",
            "📊 Monitor option Greeks: Focus on Delta for directional moves, Theta for time decay",
            "⏰ Time decay accelerates rapidly on 0-2 DTE options",
            "💧 Ensure sufficient liquidity - avoid wide bid-ask spreads",
            "📈 Consider market conditions: trending vs. choppy markets affect success rates",
        ]
        if abs(sentiment_score) >= 0.7:
            notes.append(
                "🚀 High conviction trade - sentiment strongly supports direction"
            )
            notes.append("⚡ Consider larger position size within risk limits")
        elif abs(sentiment_score) >= 0.5:
            notes.append("📊 Moderate conviction - wait for technical confirmation")
            notes.append("🎯 Stick to planned exit levels")
        else:
            notes.append("⚠️ Lower conviction - consider paper trading first")
            notes.append("🛡️ Use smaller position sizes")
        if confidence >= 0.8:
            notes.append("✅ High confidence in sentiment analysis")
        elif confidence >= 0.6:
            notes.append("⚖️ Moderate confidence - monitor for changes")
        else:
            notes.append("❓ Lower confidence - be extra cautious")
        return notes

    def execute_trade(self, trade_signal: Dict) -> Dict:
        """
        Execute a trade based on the signal (simulation)
        """
        if trade_signal["action"] == "HOLD":
            return {"status": "no_trade", "message": "Holding position"}
        total_cost = trade_signal["option_price"] * trade_signal["position_size"]
        # Check risk limits using Go service if available
        if False:  # self.go_client.is_service_available("risk") removed
            portfolio_data = {
                "positions": self.positions,
                "current_capital": self.current_capital,
                "total_value": self.current_capital
                + sum([p["total_cost"] for p in self.positions]),
            }
            # risk_check = self.go_client.check_risk_limits(portfolio_data, trade_signal)  # Module removed
            if risk_check and not risk_check.get("approved", True):
                return {
                    "status": "risk_rejected",
                    "message": f"Trade rejected by risk management: {risk_check.get('reason', 'Unknown')}",
                }
        if total_cost > self.current_capital:
            return {
                "status": "insufficient_funds",
                "message": f"Insufficient capital. Need ${total_cost:.2f}, have ${self.current_capital:.2f}",
            }
        # Execute the trade
        trade = {
            "timestamp": datetime.now(),
            "symbol": trade_signal["symbol"],
            "action": trade_signal["action"],
            "option_type": trade_signal["option_type"],
            "strike_price": trade_signal["strike_price"],
            "option_price": trade_signal["option_price"],
            "position_size": trade_signal["position_size"],
            "total_cost": total_cost,
            "days_to_expiry": trade_signal["days_to_expiry"],
            "sentiment_score": trade_signal["sentiment_score"],
            "status": "open",
        }
        self.positions.append(trade)
        self.trade_history.append(trade.copy())
        self.current_capital -= total_cost
        return {
            "status": "executed",
            "trade": trade,
            "remaining_capital": self.current_capital,
        }

    def get_portfolio_summary(self) -> Dict:
        """
        Get current portfolio summary
        """
        total_positions_value = sum(
            [pos["option_price"] * pos["position_size"] for pos in self.positions]
        )
        return {
            "initial_capital": self.initial_capital,
            "current_capital": round(self.current_capital, 2),
            "positions_value": round(total_positions_value, 2),
            "total_value": round(self.current_capital + total_positions_value, 2),
            "unrealized_pnl": round(
                total_positions_value
                - sum([pos["total_cost"] for pos in self.positions]),
                2,
            ),
            "open_positions": len(self.positions),
            "total_trades": len(self.trade_history),
        }

    def get_recommendation(
        self, symbol: str, price_data: Dict, sentiment_data: Dict, signal_data: Dict
    ) -> Dict:
        """
        Get trading recommendation based on sentiment and price data
        """
        # Extract current price
        current_price = price_data.get("current_price", 0)
        # Generate signal data if not provided
        if not signal_data:
            signal_data = {
                "action": "HOLD",
                "signal_strength": 0.5,
                "confidence": sentiment_data.get("confidence", 0.5),
                "reasoning": "No clear signal available",
            }
        # Use the existing generate_trade_signal method
        return self.generate_trade_signal(
            symbol, current_price, sentiment_data, signal_data
        )

    def _get_conviction_level(self, sentiment_score: float) -> str:
        """Get the conviction level based on sentiment score."""
        score = abs(sentiment_score)
        if score >= 0.7:
            return "High"
        elif score >= 0.5:
            return "Medium"
        return "Low"
