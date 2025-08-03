"""
Enhanced Trading Strategy for Trading AI Platform.
Provides advanced trading analysis and recommendations.
"""

import numpy as np
import pandas as pd
import time
import requests
import yfinance as yf
from typing import Dict, List, Optional, cast
from datetime import datetime, timedelta
from ..core.config import Config
from ..core.recommendation_manager import get_recommendation_manager
from .trading_strategy import TradingStrategy

# Use config for historical data period
HISTORICAL_LOOKBACK_DAYS = Config.HISTORICAL_LOOKBACK_DAYS  # 2 years (730 days)


class EnhancedTradingStrategy(TradingStrategy):
    """
    Enhanced trading strategy that generates multiple recommendations
    and tests them against historical data for confidence calculation
    """

    def __init__(self):
        super().__init__()
        self.alpha_vantage_api_key = Config.ALPHA_VANTAGE_API_KEY
        self.cache = {}  # Simple cache for historical data
        self.rate_limit_delay = 12  # Alpha Vantage free tier: 5 calls per minute
        self.recommendation_manager = get_recommendation_manager()

    def generate_multiple_recommendations(
        self, symbol: str, current_price: float, sentiment_data: Dict, signal_data: Dict
    ) -> List[Dict]:
        """
        Generate 5 different trading recommendations with varying parameters
        """
        recommendations = []

        # Base parameters
        sentiment_score = sentiment_data["sentiment_score"]
        base_confidence = sentiment_data["confidence"]
        action = signal_data["action"]

        # Even for HOLD, generate recommendations with neutral bias
        if action == "HOLD":
            # Generate both bullish and bearish recommendations with lower confidence
            bullish_recs = self._generate_hold_recommendations(
                symbol, current_price, sentiment_score, base_confidence, "CALL"
            )
            bearish_recs = self._generate_hold_recommendations(
                symbol, current_price, sentiment_score, base_confidence, "PUT"
            )
            recommendations.extend(bullish_recs)
            recommendations.extend(bearish_recs)
            return recommendations

        # Strategy 1: Conservative (Closest to current implementation)
        rec1 = self._generate_conservative_recommendation(
            symbol, current_price, sentiment_score, base_confidence, action
        )
        recommendations.append(rec1)

        # Strategy 2: Moderate (Balanced approach)
        rec2 = self._generate_moderate_recommendation(
            symbol, current_price, sentiment_score, base_confidence, action
        )
        recommendations.append(rec2)

        # Strategy 3: Income-focused (Longer expiry, smaller moves)
        rec3 = self._generate_income_recommendation(
            symbol, current_price, sentiment_score, base_confidence, action
        )
        recommendations.append(rec3)

        # Strategy 4: Aggressive (Short-term, higher risk/reward)
        rec4 = self._generate_aggressive_recommendation(
            symbol, current_price, sentiment_score, base_confidence, action
        )
        recommendations.append(rec4)

        # Strategy 5: Momentum-based
        rec5 = self._generate_momentum_recommendation(
            symbol, current_price, sentiment_score, base_confidence, action
        )
        recommendations.append(rec5)

        return recommendations

    def _generate_hold_recommendations(
        self,
        symbol: str,
        current_price: float,
        sentiment_score: float,
        confidence: float,
        bias: str,
    ) -> List[Dict]:
        """Generate neutral-biased recommendations during HOLD signals"""
        recommendations = []

        # Conservative neutral strategy
        if bias == "CALL":
            strike_price = current_price * 1.01  # Slightly OTM
            option_type = "call"
            direction = "NEUTRAL-BULLISH"
        else:
            strike_price = current_price * 0.99  # Slightly OTM
            option_type = "put"
            direction = "NEUTRAL-BEARISH"

        days_to_expiry = 45  # Longer expiry for time decay
        target_gain = 0.15  # 15% target gain
        stop_loss = 0.10  # 10% stop loss

        option_price = self.calculate_option_price_estimate(
            current_price, strike_price, days_to_expiry, option_type
        )

        neutral_rec = {
            "rank": 1,
            "symbol": symbol,
            "action": "HOLD",
            "direction": direction,
            "recommendation_type": f"Neutral {bias}",
            "option_type": option_type,
            "strike_price": round(strike_price, 2),
            "current_price": current_price,
            "option_price": round(option_price, 2),
            "days_to_expiry": days_to_expiry,
            "target_gain_percent": round(target_gain * 100, 1),
            "stop_loss_percent": round(stop_loss * 100, 1),
            "sentiment_score": sentiment_score,
            "base_confidence": confidence * 0.5,  # Lower confidence due to HOLD
            "historical_confidence": 0,
            "confidence": 0,
            "reasoning": f"Neutral {bias}-biased strategy with longer expiry for premium collection",
        }
        recommendations.append(neutral_rec)

        return recommendations

    def _generate_conservative_recommendation(
        self,
        symbol: str,
        current_price: float,
        sentiment_score: float,
        confidence: float,
        action: str,
    ) -> Dict:
        """Generate conservative trading recommendation"""

        if action == "CALL":
            strike_price = current_price * 1.02  # 2% OTM
            option_type = "call"
            direction = "BULLISH"
        else:
            strike_price = current_price * 0.98  # 2% OTM
            option_type = "put"
            direction = "BEARISH"

        days_to_expiry = 30  # Conservative 30-day expiry
        target_gain = 0.25  # 25% target gain
        stop_loss = 0.15  # 15% stop loss

        option_price = self.calculate_option_price_estimate(
            current_price, strike_price, days_to_expiry, option_type
        )

        return {
            "rank": 1,
            "symbol": symbol,
            "action": action,
            "direction": direction,
            "recommendation_type": "Conservative",
            "option_type": option_type,
            "strike_price": round(strike_price, 2),
            "current_price": current_price,
            "option_price": round(option_price, 2),
            "days_to_expiry": days_to_expiry,
            "target_gain_percent": round(target_gain * 100, 1),
            "stop_loss_percent": round(stop_loss * 100, 1),
            "sentiment_score": sentiment_score,
            "base_confidence": confidence,
            "historical_confidence": 0,  # Will be calculated later
            "confidence": 0,  # Final confidence after historical testing
            "reasoning": f"Conservative {action} strategy with 30-day expiry targeting {target_gain * 100:.0f}% gains",
        }

    def _generate_aggressive_recommendation(
        self,
        symbol: str,
        current_price: float,
        sentiment_score: float,
        confidence: float,
        action: str,
    ) -> Dict:
        """Generate aggressive trading recommendation"""

        if action == "CALL":
            strike_price = current_price * 1.05  # 5% OTM for higher leverage
            option_type = "call"
            direction = "BULLISH"
        else:
            strike_price = current_price * 0.95  # 5% OTM
            option_type = "put"
            direction = "BEARISH"

        days_to_expiry = 7  # Short 7-day expiry for high gamma
        target_gain = 0.50  # 50% target gain
        stop_loss = 0.25  # 25% stop loss

        option_price = self.calculate_option_price_estimate(
            current_price, strike_price, days_to_expiry, option_type
        )

        return {
            "rank": 2,
            "symbol": symbol,
            "action": action,
            "direction": direction,
            "recommendation_type": "Aggressive",
            "option_type": option_type,
            "strike_price": round(strike_price, 2),
            "current_price": current_price,
            "option_price": round(option_price, 2),
            "days_to_expiry": days_to_expiry,
            "target_gain_percent": round(target_gain * 100, 1),
            "stop_loss_percent": round(stop_loss * 100, 1),
            "sentiment_score": sentiment_score,
            "base_confidence": confidence,
            "historical_confidence": 0,
            "confidence": 0,
            "reasoning": f"Aggressive {action} strategy with 7-day expiry targeting {target_gain * 100:.0f}% gains",
        }

    def _generate_moderate_recommendation(
        self,
        symbol: str,
        current_price: float,
        sentiment_score: float,
        confidence: float,
        action: str,
    ) -> Dict:
        """Generate moderate risk trading recommendation"""

        if action == "CALL":
            strike_price = current_price * 1.03  # 3% OTM
            option_type = "call"
            direction = "BULLISH"
        else:
            strike_price = current_price * 0.97  # 3% OTM
            option_type = "put"
            direction = "BEARISH"

        days_to_expiry = 14  # 2-week expiry
        target_gain = 0.35  # 35% target gain
        stop_loss = 0.20  # 20% stop loss

        option_price = self.calculate_option_price_estimate(
            current_price, strike_price, days_to_expiry, option_type
        )

        return {
            "rank": 3,
            "symbol": symbol,
            "action": action,
            "direction": direction,
            "recommendation_type": "Moderate",
            "option_type": option_type,
            "strike_price": round(strike_price, 2),
            "current_price": current_price,
            "option_price": round(option_price, 2),
            "days_to_expiry": days_to_expiry,
            "target_gain_percent": round(target_gain * 100, 1),
            "stop_loss_percent": round(stop_loss * 100, 1),
            "sentiment_score": sentiment_score,
            "base_confidence": confidence,
            "historical_confidence": 0,
            "confidence": 0,
            "reasoning": f"Moderate {action} strategy with 14-day expiry targeting {target_gain * 100:.0f}% gains",
        }

    def _generate_income_recommendation(
        self,
        symbol: str,
        current_price: float,
        sentiment_score: float,
        confidence: float,
        action: str,
    ) -> Dict:
        """Generate income-focused trading recommendation"""

        if action == "CALL":
            strike_price = current_price * 1.01  # 1% OTM for better probability
            option_type = "call"
            direction = "BULLISH"
        else:
            strike_price = current_price * 0.99  # 1% OTM
            option_type = "put"
            direction = "BEARISH"

        days_to_expiry = 45  # Longer expiry for time premium
        target_gain = 0.20  # 20% target gain
        stop_loss = 0.10  # 10% stop loss

        option_price = self.calculate_option_price_estimate(
            current_price, strike_price, days_to_expiry, option_type
        )

        return {
            "rank": 4,
            "symbol": symbol,
            "action": action,
            "direction": direction,
            "recommendation_type": "Income-Focused",
            "option_type": option_type,
            "strike_price": round(strike_price, 2),
            "current_price": current_price,
            "option_price": round(option_price, 2),
            "days_to_expiry": days_to_expiry,
            "target_gain_percent": round(target_gain * 100, 1),
            "stop_loss_percent": round(stop_loss * 100, 1),
            "sentiment_score": sentiment_score,
            "base_confidence": confidence,
            "historical_confidence": 0,
            "confidence": 0,
            "reasoning": f"Income-focused {action} strategy with 45-day expiry targeting {target_gain * 100:.0f}% gains",
        }

    def _generate_momentum_recommendation(
        self,
        symbol: str,
        current_price: float,
        sentiment_score: float,
        confidence: float,
        action: str,
    ) -> Dict:
        """Generate momentum-based trading recommendation"""

        # Adjust strike based on momentum strength
        momentum_factor = 1 + (abs(sentiment_score) * 0.02)  # 0-2% additional OTM

        if action == "CALL":
            strike_price = current_price * (1.025 * momentum_factor)  # Dynamic OTM
            option_type = "call"
            direction = "BULLISH"
        else:
            strike_price = current_price * (0.975 / momentum_factor)  # Dynamic OTM
            option_type = "put"
            direction = "BEARISH"

        days_to_expiry = 21  # 3-week expiry
        target_gain = 0.40  # 40% target gain
        stop_loss = 0.18  # 18% stop loss

        option_price = self.calculate_option_price_estimate(
            current_price, strike_price, days_to_expiry, option_type
        )

        return {
            "rank": 5,
            "symbol": symbol,
            "action": action,
            "direction": direction,
            "recommendation_type": "Momentum-Based",
            "option_type": option_type,
            "strike_price": round(strike_price, 2),
            "current_price": current_price,
            "option_price": round(option_price, 2),
            "days_to_expiry": days_to_expiry,
            "target_gain_percent": round(target_gain * 100, 1),
            "stop_loss_percent": round(stop_loss * 100, 1),
            "sentiment_score": sentiment_score,
            "base_confidence": confidence,
            "historical_confidence": 0,
            "confidence": 0,
            "reasoning": f"Momentum-based {action} strategy with 21-day expiry targeting {target_gain * 100:.0f}% gains",
        }

    def test_recommendations_against_historical_data(
        self, recommendations: List[Dict], lookback_days: int = 90
    ) -> List[Dict]:
        """
        Test each recommendation against historical data using Alpha Vantage
        """
        if not recommendations:
            return recommendations

        symbol = recommendations[0]["symbol"]

        # Get historical data (try Alpha Vantage first, fallback to Yahoo Finance)
        historical_data = self._get_alpha_vantage_historical_data(symbol, lookback_days)
        if historical_data is None or (
            isinstance(historical_data, pd.DataFrame) and historical_data.empty
        ):
            historical_data = self._get_yahoo_historical_data(symbol, lookback_days)

        if historical_data is None or (
            isinstance(historical_data, pd.DataFrame) and historical_data.empty
        ):
            print(f"❌ No historical data available for {symbol}")
            for rec in recommendations:
                rec["historical_confidence"] = rec["base_confidence"]
                rec["confidence"] = rec["base_confidence"]
            return recommendations

        # Get historical performance from database if available
        try:
            db_performance = self.recommendation_manager.get_historical_performance(
                symbol, days_back=lookback_days
            )
        except Exception as e:
            print(f"⚠️ Could not get database performance history: {e}")
            db_performance = None

        # Test each recommendation
        for rec in recommendations:
            # Test against historical price data
            if isinstance(historical_data, pd.DataFrame):
                historical_performance = self._backtest_recommendation(
                    rec, historical_data
                )
                rec["historical_confidence"] = historical_performance["confidence"]
                rec["historical_stats"] = historical_performance["stats"]
            else:
                rec["historical_confidence"] = rec["base_confidence"]
                rec["historical_stats"] = {
                    "total_trades": 0,
                    "win_rate": 0,
                    "avg_return": 0,
                    "max_gain": 0,
                    "max_loss": 0,
                }

            # Apply database performance adjustment if available
            if db_performance and db_performance.get("total_with_outcomes", 0) > 0:
                # Find matching recommendation type in DB history
                matching_types = [
                    r
                    for r in db_performance.get("recommendation_performance", [])
                    if r.get("recommendation_type") == rec.get("recommendation_type")
                    and r.get("action") == rec.get("action")
                ]

                if (
                    matching_types and matching_types[0].get("count", 0) >= 5
                ):  # Need at least 5 samples
                    db_win_rate = matching_types[0].get("win_rate", 0)
                    # Adjust confidence based on past performance (weight increases with more data)
                    count = min(
                        matching_types[0].get("count", 0), 100
                    )  # Cap at 100 for weighting
                    weight_factor = min(
                        0.5, count / 200
                    )  # Max 0.5 weight for DB performance

                    # Weighted average of backtest and actual historical performance
                    final_confidence = (
                        rec["historical_confidence"] * (1 - weight_factor)
                        + db_win_rate * weight_factor
                    )

                    rec["db_confidence_factor"] = db_win_rate
                    rec["db_samples"] = matching_types[0].get("count", 0)
                    rec["confidence"] = round(final_confidence, 3)

                    print(
                        f"📊 Adjusted confidence for {rec['recommendation_type']} using DB history: "
                        + f"{rec['historical_confidence']:.3f} → {final_confidence:.3f}"
                    )
                else:
                    # Calculate final confidence (weighted average)
                    final_confidence = (
                        rec["base_confidence"] * 0.3
                        + rec["historical_confidence"] * 0.7
                    )
                    rec["confidence"] = round(final_confidence, 3)
            else:
                # Calculate final confidence (weighted average)
                final_confidence = (
                    rec["base_confidence"] * 0.3 + rec["historical_confidence"] * 0.7
                )
                rec["confidence"] = round(final_confidence, 3)

        # Sort by final confidence (highest first)
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)

        # Update ranks
        for i, rec in enumerate(recommendations):
            rec["rank"] = i + 1

        return recommendations

    def _get_alpha_vantage_historical_data(
        self, symbol: str, days: int
    ) -> Optional[pd.DataFrame]:
        """
        Get historical data from Alpha Vantage
        """
        cache_key = f"alpha_historical_{symbol}_{days}"

        # Check cache first
        if cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if datetime.now() - cache_time < timedelta(hours=1):  # 1-hour cache
                return data

        if not self.alpha_vantage_api_key:
            return None

        try:
            # Rate limiting for Alpha Vantage free tier
            time.sleep(self.rate_limit_delay)

            url = "https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "outputsize": "full" if days > 100 else "compact",
                "apikey": self.alpha_vantage_api_key,
            }

            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()

                if "Error Message" in data:
                    print(f"❌ Alpha Vantage error: {data['Error Message']}")
                    return None

                if "Note" in data:
                    print(f"⚠️ Alpha Vantage rate limit: {data['Note']}")
                    return None

                time_series_key = "Time Series (Daily)"
                if time_series_key not in data:
                    print(f"❌ No daily time series data for {symbol}")
                    return None

                # Convert to DataFrame
                df_data = []
                for date_str, values in data[time_series_key].items():
                    df_data.append(
                        {
                            "Date": pd.to_datetime(date_str),
                            "Open": float(values["1. open"]),
                            "High": float(values["2. high"]),
                            "Low": float(values["3. low"]),
                            "Close": float(values["4. close"]),
                            "Volume": int(values["5. volume"]),
                        }
                    )

                df = pd.DataFrame(df_data)
                df.set_index("Date", inplace=True)
                df.sort_index(inplace=True)

                # Get last N days
                cutoff_date = datetime.now() - timedelta(days=days)
                df = df[df.index >= cutoff_date]

                # Cache the result
                self.cache[cache_key] = (datetime.now(), df)

                print(
                    f"✅ Got {len(df)} days of Alpha Vantage historical data for {symbol}"
                )
                return df

            else:
                print(f"❌ Alpha Vantage API error {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Alpha Vantage historical data fetch failed for {symbol}: {e}")
            return None

    def _get_yahoo_historical_data(
        self, symbol: str, days: int
    ) -> Optional[pd.DataFrame]:
        """
        Get historical data from Yahoo Finance

        Args:
            symbol: Stock symbol
            days: Number of days of historical data to fetch

        Returns:
            DataFrame with historical data or None if error

        Note:
            There is a known type hint issue with yfinance's history() method.
            The method can return either a pandas Series or DataFrame, but its
            type hints don't properly reflect this. This causes type checking
            errors even though the code handles both cases correctly at runtime.

            Related issues:
            - yfinance doesn't provide accurate type hints for the history() method
            - The return type can be pd.Series | pd.DataFrame but is not properly typed
            - Type casting and isinstance checks are used to handle this safely

            This has been documented and the code handles all cases correctly at runtime,
            even though the type checker may show errors.
        """
        try:
            stock = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Fetch historical data and cast to DataFrame
            # Note: history() can return Series or DataFrame, we handle both cases
            hist_data = stock.history(start=start_date, end=end_date)
            df = cast(pd.DataFrame, hist_data)

            if df.empty:
                print(
                    f"❌ No historical data available from Yahoo Finance for {symbol}"
                )
                return None

            return df

        except Exception as e:
            print(f"❌ Error fetching Yahoo Finance data for {symbol}: {e}")
            return None

    def _backtest_recommendation(
        self, recommendation: Dict, historical_data: pd.DataFrame
    ) -> Dict:
        """
        Backtest a single recommendation against historical data
        """
        if historical_data.empty:
            return {
                "confidence": recommendation["base_confidence"],
                "stats": {
                    "total_trades": 0,
                    "win_rate": 0,
                    "avg_return": 0,
                    "max_gain": 0,
                    "max_loss": 0,
                },
            }

        action = recommendation["action"]
        strike_price_factor = (
            recommendation["strike_price"] / recommendation["current_price"]
        )
        days_to_expiry = recommendation["days_to_expiry"]
        target_gain = recommendation["target_gain_percent"] / 100
        stop_loss = recommendation["stop_loss_percent"] / 100
        option_type = recommendation["option_type"]

        trades = []

        # Simulate trades over historical data
        for i in range(len(historical_data) - days_to_expiry):
            entry_date = historical_data.index[i]
            entry_price = historical_data.iloc[i]["Close"]

            # Calculate option strike and entry price
            strike_price = entry_price * strike_price_factor
            option_entry_price = self.calculate_option_price_estimate(
                entry_price, strike_price, days_to_expiry, option_type
            )

            # Find exit conditions over the next days_to_expiry days
            exit_idx = min(i + days_to_expiry, len(historical_data) - 1)
            best_profit = -float("inf")
            worst_loss = float("inf")
            final_exit_price = None
            exit_reason = "expiry"

            # Check each day for profit/loss targets
            for j in range(i + 1, exit_idx + 1):
                current_price = historical_data.iloc[j]["Close"]
                days_remaining = days_to_expiry - (j - i)

                # Calculate current option value
                current_option_price = self.calculate_option_price_estimate(
                    current_price, strike_price, max(1, days_remaining), option_type
                )

                profit_loss = (
                    current_option_price - option_entry_price
                ) / option_entry_price

                # Check exit conditions
                if profit_loss >= target_gain:
                    final_exit_price = current_option_price
                    exit_reason = "target_hit"
                    break
                elif profit_loss <= -stop_loss:
                    final_exit_price = current_option_price
                    exit_reason = "stop_loss"
                    break

                # Track best and worst during holding period
                best_profit = max(best_profit, profit_loss)
                worst_loss = min(worst_loss, profit_loss)

            # If no early exit, use final price
            if final_exit_price is None:
                final_price = historical_data.iloc[exit_idx]["Close"]
                final_exit_price = self.calculate_option_price_estimate(
                    final_price, strike_price, 1, option_type
                )

            # Calculate final P&L
            final_pnl = (final_exit_price - option_entry_price) / option_entry_price

            trades.append(
                {
                    "entry_date": entry_date,
                    "entry_price": entry_price,
                    "option_entry_price": option_entry_price,
                    "exit_price": final_exit_price,
                    "pnl": final_pnl,
                    "exit_reason": exit_reason,
                    "best_profit": best_profit,
                    "worst_loss": worst_loss,
                }
            )

        # Calculate statistics
        if not trades:
            return {
                "confidence": recommendation["base_confidence"],
                "stats": {
                    "total_trades": 0,
                    "win_rate": 0,
                    "avg_return": 0,
                    "max_gain": 0,
                    "max_loss": 0,
                },
            }

        winning_trades = [t for t in trades if t["pnl"] > 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0
        avg_return = np.mean([t["pnl"] for t in trades])
        max_gain = max([t["pnl"] for t in trades])
        max_loss = min([t["pnl"] for t in trades])

        # Calculate historical confidence based on performance
        # Win rate * average return with adjustments for consistency
        base_historical_confidence = win_rate * (1 + max(0, avg_return))

        # Adjust for trade count (more trades = more reliable)
        trade_count_factor = min(1.0, len(trades) / 20)  # Full confidence at 20+ trades

        # Adjust for consistency (penalize high volatility)
        returns_std = np.std([t["pnl"] for t in trades])
        consistency_factor = max(0.5, 1 - returns_std)  # Penalize high volatility

        historical_confidence = (
            base_historical_confidence * trade_count_factor * consistency_factor
        )
        historical_confidence = max(0, min(1, historical_confidence))  # Clamp to [0, 1]

        stats = {
            "total_trades": len(trades),
            "win_rate": round(win_rate * 100, 1),
            "avg_return": round(avg_return * 100, 1),
            "max_gain": round(max_gain * 100, 1),
            "max_loss": round(max_loss * 100, 1),
            "returns_std": round(returns_std * 100, 1),
            "consistency_score": round(consistency_factor * 100, 1),
        }

        return {"confidence": historical_confidence, "stats": stats}

    def get_top_recommendation_with_confidence(
        self, symbol: str, current_price: float, sentiment_data: Dict, signal_data: Dict
    ) -> Dict:
        """
        Main method to get the top recommendation with confidence calculation
        """
        # Generate recommendations
        recommendations = self.generate_multiple_recommendations(
            symbol, current_price, sentiment_data, signal_data
        )

        # Test against historical data
        tested_recommendations = self.test_recommendations_against_historical_data(
            recommendations
        )

        # Return the top recommendation with all alternatives
        top_recommendation = (
            tested_recommendations[0] if tested_recommendations else None
        )

        return {
            "top_recommendation": top_recommendation,
            "all_recommendations": tested_recommendations,
            "total_alternatives": len(tested_recommendations),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    def generate_stock_recommendations(
        self, symbol: str, current_price: float, sentiment_data: Dict, signal_data: Dict
    ) -> List[Dict]:
        """
        Generate stock-based trading recommendations

        Args:
            symbol: Stock symbol
            current_price: Current stock price
            sentiment_data: Sentiment analysis results
            signal_data: Trading signal data

        Returns:
            List of stock recommendations with confidence scores
        """
        recommendations = []
        sentiment_score = sentiment_data.get("sentiment_score", 0)
        base_confidence = sentiment_data.get("confidence", 0.5)
        action = signal_data.get("action", "HOLD")

        if action == "HOLD":
            return [
                {
                    "recommendation_type": "Stock HOLD",
                    "action": "HOLD",
                    "symbol": symbol,
                    "current_price": current_price,
                    "sentiment_score": sentiment_score,
                    "reasoning": "Neutral sentiment suggests holding current position",
                    "base_confidence": base_confidence,
                    "confidence": base_confidence * 0.7,  # Lower confidence for holds
                    "rank": 1,
                }
            ]

        # Generate different stock strategies based on sentiment strength
        if sentiment_score > 0.1:  # Bullish
            # Conservative stock buy
            conservative_stock = {
                "recommendation_type": "Stock BUY (Conservative)",
                "action": "BUY",
                "symbol": symbol,
                "current_price": current_price,
                "sentiment_score": sentiment_score,
                "shares_recommended": max(
                    1, int(1000 / current_price)
                ),  # $1000 position
                "target_price": current_price * 1.15,  # 15% target
                "stop_loss_price": current_price * 0.92,  # 8% stop
                "reasoning": "Conservative stock purchase based on positive sentiment",
                "base_confidence": base_confidence,
                "confidence": base_confidence * 0.85,  # Stock confidence factor
                "risk_level": "Low",
                "time_horizon": "3-6 months",
            }
            recommendations.append(conservative_stock)

            # Aggressive stock buy
            if sentiment_score > 0.5:
                aggressive_stock = {
                    "recommendation_type": "Stock BUY (Aggressive)",
                    "action": "BUY",
                    "symbol": symbol,
                    "current_price": current_price,
                    "sentiment_score": sentiment_score,
                    "shares_recommended": max(
                        1, int(2000 / current_price)
                    ),  # $2000 position
                    "target_price": current_price * 1.25,  # 25% target
                    "stop_loss_price": current_price * 0.90,  # 10% stop
                    "reasoning": "Aggressive stock purchase based on strong positive sentiment",
                    "base_confidence": base_confidence,
                    "confidence": base_confidence
                    * 0.75,  # More aggressive = lower confidence
                    "risk_level": "High",
                    "time_horizon": "1-3 months",
                }
                recommendations.append(aggressive_stock)

        elif sentiment_score < -0.1:  # Bearish
            # Short selling strategy
            short_stock = {
                "recommendation_type": "Stock SELL (Short)",
                "action": "SELL_SHORT",
                "symbol": symbol,
                "current_price": current_price,
                "sentiment_score": sentiment_score,
                "shares_recommended": max(
                    1, int(1500 / current_price)
                ),  # $1500 position
                "target_price": current_price * 0.85,  # 15% target drop
                "stop_loss_price": current_price * 1.08,  # 8% stop loss
                "reasoning": "Short selling based on negative sentiment",
                "base_confidence": base_confidence,
                "confidence": base_confidence * 0.70,  # Shorting is riskier
                "risk_level": "High",
                "time_horizon": "1-3 months",
            }
            recommendations.append(short_stock)

            # Conservative sell (if holding)
            conservative_sell = {
                "recommendation_type": "Stock SELL (Conservative)",
                "action": "SELL",
                "symbol": symbol,
                "current_price": current_price,
                "sentiment_score": sentiment_score,
                "reasoning": "Conservative position exit based on negative sentiment",
                "base_confidence": base_confidence,
                "confidence": base_confidence * 0.80,
                "risk_level": "Low",
                "time_horizon": "Immediate",
            }
            recommendations.append(conservative_sell)

        # Add rank to each recommendation
        for i, rec in enumerate(recommendations):
            rec["rank"] = i + 1

        return recommendations

    def get_comprehensive_recommendations(
        self, symbol: str, current_price: float, sentiment_data: Dict, signal_data: Dict
    ) -> Dict:
        """
        Get comprehensive recommendations across multiple strategy types.

        Args:
            symbol: Stock symbol
            current_price: Current stock price
            sentiment_data: Sentiment analysis results
            signal_data: Trading signal data

        Returns:
            Dict: Comprehensive recommendations with rankings
        """
        # Generate options recommendations
        options_recommendations = self.generate_multiple_recommendations(
            symbol, current_price, sentiment_data, signal_data
        )

        # Test options recommendations against historical data
        enhanced_recommendations = self.test_recommendations_against_historical_data(
            options_recommendations
        )

        # Generate stock recommendations
        stock_recommendations = self.generate_stock_recommendations(
            symbol, current_price, sentiment_data, signal_data
        )

        # Test stock recommendations against historical data
        enhanced_stock_recommendations = (
            self.test_stock_recommendations_against_historical_data(
                stock_recommendations
            )
        )

        # Add category labels
        for rec in enhanced_recommendations:
            rec["category"] = "Options"

        for rec in enhanced_stock_recommendations:
            rec["category"] = "Stock"

        # Combine all recommendations
        all_recommendations = enhanced_recommendations + enhanced_stock_recommendations

        # Sort by confidence (highest first)
        all_recommendations.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        # Re-rank all recommendations
        for i, rec in enumerate(all_recommendations):
            rec["overall_rank"] = i + 1

        # Determine top recommendation
        top_recommendation = all_recommendations[0] if all_recommendations else None

        # Separate by category for display
        top_stock = next(
            (rec for rec in all_recommendations if rec["category"] == "Stock"), None
        )
        top_options = next(
            (rec for rec in all_recommendations if rec["category"] == "Options"), None
        )

        # Save recommendations to database
        try:
            # Add timestamp for tracking
            for rec in all_recommendations:
                rec["timestamp"] = datetime.now().isoformat()

            # Save to database
            self.recommendation_manager.save_recommendations(all_recommendations)
        except Exception as e:
            print(f"⚠️ Error saving recommendations to database: {e}")

        return {
            "top_recommendation": top_recommendation,
            "top_stock_recommendation": top_stock,
            "top_options_recommendation": top_options,
            "all_recommendations": all_recommendations,
            "stock_recommendations": [
                rec for rec in all_recommendations if rec["category"] == "Stock"
            ],
            "options_recommendations": [
                rec for rec in all_recommendations if rec["category"] == "Options"
            ],
            "recommendation_summary": {
                "total_strategies": len(all_recommendations),
                "best_category": top_recommendation["category"]
                if top_recommendation
                else "None",
                "best_confidence": top_recommendation.get("confidence", 0)
                if top_recommendation
                else 0,
                "stock_vs_options_winner": top_recommendation["category"]
                if top_recommendation
                else "None",
            },
            "analysis_timestamp": datetime.now().isoformat(),
        }

    def test_stock_recommendations_against_historical_data(
        self, recommendations: List[Dict]
    ) -> List[Dict]:
        """
        Test stock recommendations against historical price data

        Args:
            recommendations: List of stock recommendations

        Returns:
            List of recommendations with updated confidence scores
        """
        if not recommendations:
            return recommendations

        symbol = recommendations[0]["symbol"]

        # Get historical data (90 days)
        historical_data = self._get_alpha_vantage_historical_data(symbol, 90)
        if historical_data is None or (
            isinstance(historical_data, pd.DataFrame) and historical_data.empty
        ):
            historical_data = self._get_yahoo_historical_data(symbol, 90)

        if historical_data is None or (
            isinstance(historical_data, pd.DataFrame) and historical_data.empty
        ):
            print(f"❌ No historical data available for stock backtesting of {symbol}")
            return recommendations

        print(
            f"✅ Testing {len(recommendations)} stock recommendations against {len(historical_data)} days of data"
        )

        # Test each recommendation
        for rec in recommendations:
            if isinstance(historical_data, pd.DataFrame):
                backtest_result = self._backtest_stock_recommendation(
                    rec, historical_data
                )

                # Update confidence with historical performance
                historical_confidence = backtest_result["confidence"]
                base_confidence = rec["base_confidence"]

                # Combine base confidence with historical performance (70% historical, 30% sentiment)
                rec["historical_confidence"] = historical_confidence
                rec["confidence"] = (historical_confidence * 0.7) + (
                    base_confidence * 0.3
                )

                # Add historical stats
                rec["historical_stats"] = backtest_result["stats"]
            else:
                rec["historical_confidence"] = rec["base_confidence"]
                rec["confidence"] = rec["base_confidence"]
                rec["historical_stats"] = {
                    "total_trades": 0,
                    "win_rate": 0,
                    "avg_return": 0,
                    "max_gain": 0,
                    "max_loss": 0,
                }

        # Sort by updated confidence
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)

        # Update ranks
        for i, rec in enumerate(recommendations):
            rec["rank"] = i + 1

        return recommendations

    def _backtest_stock_recommendation(
        self, recommendation: Dict, historical_data: pd.DataFrame
    ) -> Dict:
        """
        Backtest a stock recommendation against historical data

        Args:
            recommendation: Stock recommendation dict
            historical_data: Historical price data DataFrame

        Returns:
            Dict with confidence score and performance stats
        """
        if historical_data.empty:
            return {
                "confidence": recommendation.get("base_confidence", 0.5),
                "stats": {"total_trades": 0, "win_rate": 0, "avg_return": 0},
            }

        action = recommendation.get("action", "HOLD")
        target_gain = 0.15  # Default 15% target
        stop_loss = 0.08  # Default 8% stop loss

        # Extract targets if available
        if "target_price" in recommendation and "current_price" in recommendation:
            current_price = recommendation["current_price"]
            target_price = recommendation["target_price"]
            stop_price = recommendation.get("stop_loss_price", current_price * 0.92)

            if action in ["BUY", "BUY_STOCK"]:
                target_gain = (target_price - current_price) / current_price
                stop_loss = (current_price - stop_price) / current_price
            elif action in ["SELL_SHORT", "SHORT"]:
                target_gain = (current_price - target_price) / current_price
                stop_loss = (stop_price - current_price) / current_price

        trades = []

        # Simulate trades over historical data
        for i in range(len(historical_data) - 30):  # Need at least 30 days to evaluate
            entry_price = historical_data.iloc[i]["Close"]

            # Look ahead for exit conditions
            for j in range(
                i + 1, min(i + 31, len(historical_data))
            ):  # Max 30 days holding
                current_price = historical_data.iloc[j]["Close"]

                if action in ["BUY", "BUY_STOCK"]:
                    # Long position
                    price_change = (current_price - entry_price) / entry_price

                    if price_change >= target_gain:
                        # Hit target
                        trades.append(
                            {
                                "return": target_gain,
                                "days_held": j - i,
                                "exit_reason": "target",
                            }
                        )
                        break
                    elif price_change <= -stop_loss:
                        # Hit stop loss
                        trades.append(
                            {
                                "return": -stop_loss,
                                "days_held": j - i,
                                "exit_reason": "stop",
                            }
                        )
                        break
                    elif j == min(i + 30, len(historical_data) - 1):
                        # Time exit
                        trades.append(
                            {
                                "return": price_change,
                                "days_held": j - i,
                                "exit_reason": "time",
                            }
                        )

                elif action in ["SELL_SHORT", "SHORT"]:
                    # Short position
                    price_change = (entry_price - current_price) / entry_price

                    if price_change >= target_gain:
                        # Hit target (price fell)
                        trades.append(
                            {
                                "return": target_gain,
                                "days_held": j - i,
                                "exit_reason": "target",
                            }
                        )
                        break
                    elif price_change <= -stop_loss:
                        # Hit stop loss (price rose)
                        trades.append(
                            {
                                "return": -stop_loss,
                                "days_held": j - i,
                                "exit_reason": "stop",
                            }
                        )
                        break
                    elif j == min(i + 30, len(historical_data) - 1):
                        # Time exit
                        trades.append(
                            {
                                "return": price_change,
                                "days_held": j - i,
                                "exit_reason": "time",
                            }
                        )

        # Calculate statistics
        if trades:
            returns = [trade["return"] for trade in trades]
            winning_trades = [r for r in returns if r > 0]

            stats = {
                "total_trades": len(trades),
                "win_rate": round((len(winning_trades) / len(trades)) * 100, 1),
                "avg_return": round(np.mean(returns) * 100, 1),
                "max_gain": round(max(returns) * 100, 1),
                "max_loss": round(min(returns) * 100, 1),
                "returns_std": round(np.std(returns) * 100, 1),
                "consistency_score": 50.0,  # Placeholder for now
            }

            # Calculate confidence based on win rate and average return
            win_rate_factor = stats["win_rate"] / 100
            return_factor = max(
                0, min(1, (stats["avg_return"] + 20) / 40)
            )  # Normalize around 0-40% returns
            confidence = (win_rate_factor * 0.6) + (return_factor * 0.4)

        else:
            stats = {
                "total_trades": 0,
                "win_rate": 0,
                "avg_return": 0,
                "max_gain": 0,
                "max_loss": 0,
            }
            confidence = recommendation.get("base_confidence", 0.5)

        return {"confidence": confidence, "stats": stats}


class OptionsStrategy:
    def __init__(self):
        self.positions = []
        self.trade_history = []
        self.initial_capital = 10000
        self.current_capital = self.initial_capital
        try:
            from ..core.go_service_client import GoServiceClient

            self.go_client = GoServiceClient()
        except ImportError:
            self.go_client = None

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
        action = signal_data["action"]
        signal_strength = signal_data.get("signal_strength", 0.5)
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

        # Use shorter expiry for day trading (0-2 DTE for better theta decay management)
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

            position_recommendations[f"${amount}"] = {
                "contracts": contracts,
                "total_cost": round(total_cost, 2),
                "risk_amount": round(total_cost, 2),
                "target_price": round(target_price, 2),
                "stop_price": round(stop_price, 2),
                "potential_gain": round(potential_gain, 2),
                "potential_loss": round(potential_loss, 2),
                "risk_reward_ratio": round(potential_gain / potential_loss, 2)
                if potential_loss > 0
                else 0,
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
            "position_size": position_recommendations.get("$1000", {}).get(
                "contracts", 1
            ),  # Default position size for execute_trade
            "position_recommendations": position_recommendations,
            "entry_strategy": entry_strategy,
            "exit_strategy": exit_strategy,
            "reasoning": signal_data.get("reasoning", "No specific reasoning provided"),
            "day_trading_notes": self._generate_day_trading_notes(
                sentiment_score, confidence, strategy_type
            ),
        }

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
            f"Strategy: {strategy_type} based on sentiment analysis",
            f"Conviction Level: {'High' if abs(sentiment_score) >= 0.7 else 'Medium' if abs(sentiment_score) >= 0.5 else 'Low'}",
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

    def get_recommendation(
        self, symbol: str, price_data: Dict, sentiment_data: Dict, signal_data: Dict
    ) -> Dict:
        """
        Get a trading recommendation based on price, sentiment and signal data.

        Args:
            symbol: Stock symbol
            price_data: Price information dictionary
            sentiment_data: Sentiment analysis results
            signal_data: Trading signal data

        Returns:
            Dict: Trading recommendation
        """
        # Extract necessary data
        current_price = price_data.get("current_price", 0)
        if current_price <= 0:
            return {
                "status": "error",
                "message": "Invalid price data",
                "recommendation": "HOLD",
            }

        # If signal is HOLD, return early
        if signal_data.get("action", "HOLD") == "HOLD":
            return {
                "symbol": symbol,
                "action": "HOLD",
                "recommendation": "No position recommended at this time",
                "reasoning": signal_data.get(
                    "reasoning", "No clear trading signal available"
                ),
                "confidence": sentiment_data.get("confidence", 0.5),
                "price": current_price,
            }

        # Generate a detailed trade signal
        trade_signal = self.generate_trade_signal(
            symbol, current_price, sentiment_data, signal_data
        )

        # Format the recommendation for display
        recommendation = {
            "symbol": symbol,
            "action": trade_signal["action"],
            "option_type": trade_signal["option_type"],
            "strike_price": trade_signal["strike_price"],
            "days_to_expiry": trade_signal["days_to_expiry"],
            "current_price": current_price,
            "option_price": trade_signal["option_price"],
            "target_gain": f"{trade_signal['target_gain_percent']}%",
            "stop_loss": f"{trade_signal['stop_loss_percent']}%",
            "confidence": sentiment_data.get("confidence", 0.5),
            "sentiment_score": sentiment_data.get("sentiment_score", 0),
            "reasoning": trade_signal.get(
                "reasoning", "Based on sentiment and technical analysis"
            ),
            "position_size": trade_signal.get("position_size", 1),
            "strategy_type": trade_signal.get("strategy_type", "Standard"),
            "timestamp": datetime.now().isoformat(),
        }

        return recommendation
