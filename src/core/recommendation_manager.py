#!/usr/bin/env python3
"""
⚠️  WARNING: THIS FILE IS LOCKED (READ-ONLY) ⚠️
This file contains CRITICAL recommendation logic used throughout the application:
- Dashboard (index.html)
- S&P 500 Analysis (stocks.html)
- Opportunities Page (opportunities.html)
- Watchlist Analysis
- All trading recommendation endpoints
DO NOT MODIFY THIS FILE UNLESS ABSOLUTELY NECESSARY!
If you need to make changes:
1. Unlock the file: chmod u+w src/core/recommendation_manager.py
2. Make your changes
3. Test thoroughly
4. Re-lock the file: chmod 444 src/core/recommendation_manager.py
Any changes here affect ALL trading recommendations across the entire
application.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List
from contextlib import contextmanager
import numpy as np
from src.core.database import get_db_connection

logger = logging.getLogger(__name__)


def convert_numpy_values(value):
    """Convert numpy values to Python native types for database storage"""
    if isinstance(value, (np.integer, np.floating)):
        return float(value)
    elif isinstance(value, np.ndarray):
        return value.tolist()
    elif value is None:
        return None
    else:
        return value


class RecommendationManager:
    """
    PostgreSQL-backed recommendation manager system.
    Stores and analyzes trading recommendations for improved future confidence.
    """

    def __init__(self):
        self.table_name = "recommendations"  # Hardcoded for reliability
        logger.info("Recommendation Manager initialized")

    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup."""
        with get_db_connection() as conn:
            yield conn

    def save_recommendation(self, recommendation: Dict) -> bool:
        """
        Save a single trading recommendation to the database.
        Args:
            recommendation: Dictionary containing recommendation data
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Extract fields from recommendation
                    symbol = recommendation.get("symbol", "")
                    recommendation_type = recommendation.get("recommendation_type", "")
                    action = recommendation.get("action", "")
                    strike_price = convert_numpy_values(
                        recommendation.get("strike_price")
                    )
                    days_to_expiry = convert_numpy_values(
                        recommendation.get("days_to_expiry")
                    )
                    option_price = convert_numpy_values(
                        recommendation.get("option_price")
                    )
                    sentiment_confidence = convert_numpy_values(
                        recommendation.get("base_confidence")
                    )
                    historical_confidence = convert_numpy_values(
                        recommendation.get("historical_confidence")
                    )
                    final_confidence = convert_numpy_values(
                        recommendation.get("confidence")
                    )
                    sentiment_score = convert_numpy_values(
                        recommendation.get("sentiment_score")
                    )
                    current_stock_price = convert_numpy_values(
                        recommendation.get("current_price")
                    )
                    reasoning = recommendation.get("reasoning", "")
                    # Insert recommendation
                    cur.execute(
                        f"""
                        INSERT INTO {self.table_name} (
                            symbol, recommendation_type, action, strike_price,
                            days_to_expiry, option_price, sentiment_confidence,
                            historical_confidence, final_confidence, sentiment_score,
                            current_stock_price, reasoning
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                        """,
                        (
                            symbol,
                            recommendation_type,
                            action,
                            strike_price,
                            days_to_expiry,
                            option_price,
                            sentiment_confidence,
                            historical_confidence,
                            final_confidence,
                            sentiment_score,
                            current_stock_price,
                            reasoning,
                        ),
                    )
                    result = cur.fetchone()
                    if result:
                        recommendation_id = result[
                            "id"
                        ]  # Ensure result is a dictionary
                        conn.commit()
                        logger.info(
                            f"Saved recommendation {recommendation_id} for {symbol}"
                        )
                        # Add logging for when a request is made
                        logger.debug("Requesting stock recommendations")

                        # Log input parameters
                        logger.debug(f"Input parameters: {recommendation}")

                        # Log whether the API request succeeded or failed
                        logger.debug("API request succeeded")

                        # Log the API response
                        logger.debug(f"API response: {result}")
                        return True
                    else:
                        logger.error(f"Failed to save recommendation for {symbol}")
                        return False
        except Exception as e:
            logger.error(f"Error saving recommendation: {e}")
            return False

    def save_recommendations(self, recommendations: List[Dict]) -> bool:
        """
        Save multiple trading recommendations to the database.
        Args:
            recommendations: List of recommendation dictionaries
        Returns:
            bool: True if all saved successfully, False otherwise
        """
        if not recommendations:
            return True  # Nothing to save
        success = True
        for rec in recommendations:
            if not self.save_recommendation(rec):
                success = False
        return success

    def get_historical_performance(
        self, symbol: str, recommendation_type: str = None, days_back: int = 90
    ) -> Dict:
        """
        Get historical performance statistics for a symbol.
        Args:
            symbol: Stock or crypto symbol
            recommendation_type: Optional filter by recommendation type
            days_back: Number of days to look back
        Returns:
            Dict: Performance statistics
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Calculate date cutoff
                    cutoff_date = datetime.now() - timedelta(days=days_back)
                    # Build query based on filters
                    query = f"""
                    SELECT action, recommendation_type,
                        COUNT(*) as total_recommendations,
                        COUNT(CASE WHEN profitable = TRUE THEN 1 END)
                            as profitable_count,
                        AVG(CASE WHEN actual_outcome IS NOT NULL THEN actual_outcome ELSE NULL END) as avg_outcome
                    FROM {self.table_name}
                    WHERE symbol = %s
                    AND timestamp > %s
                    """
                    params = [symbol, cutoff_date]
                    if recommendation_type:
                        query += " AND recommendation_type = %s"
                        params.append(recommendation_type)
                    query += " GROUP BY action, recommendation_type"
                    cur.execute(query, params)
                    results = cur.fetchall()
                    # Calculate overall statistics
                    total_recs = sum(
                        row["total_recommendations"] for row in results if row
                    )
                    total_profitable = sum(
                        row["profitable_count"] for row in results if row
                    )
                    if total_recs > 0:
                        overall_win_rate = (total_profitable / total_recs) * 100
                    else:
                        overall_win_rate = 0
                    # Calculate average outcome
                    all_outcomes = []
                    for row in results:
                        if row and row["avg_outcome"] is not None:
                            all_outcomes.extend(
                                [row["avg_outcome"]] * row["total_recommendations"]
                            )
                    avg_outcome = (
                        sum(all_outcomes) / len(all_outcomes) if all_outcomes else 0
                    )
                    return {
                        "symbol": symbol,
                        "total_recommendations": total_recs,
                        "profitable_count": total_profitable,
                        "win_rate": round(overall_win_rate, 1),
                        "avg_outcome": round(avg_outcome, 3),
                        "breakdown_by_action": [
                            {
                                "action": row["action"],
                                "recommendation_type": row["recommendation_type"],
                                "total_recommendations": row["total_recommendations"],
                                "profitable_count": row["profitable_count"],
                                "avg_outcome": row["avg_outcome"],
                            }
                            for row in results
                            if row
                        ],
                    }
        except Exception as e:
            logger.error(f"Error retrieving historical performance: {e}")
            return {}

    def get_crypto_specific_recommendations(
        self, symbol: str, sentiment_data: Dict, price_data: Dict
    ) -> Dict:
        """
        Generate crypto-specific recommendations with enhanced logic.
        Args:
            symbol: Crypto symbol (e.g., 'BTCUSD')
            sentiment_data: Sentiment analysis results
            price_data: Current price and market data
        Returns:
            Dict: Crypto-specific recommendation
        """
        try:
            # Extract data
            sentiment_score = sentiment_data.get("sentiment_score", 0)
            confidence = sentiment_data.get("confidence", 0.5)
            current_price = price_data.get("current_price", 0)
            # Determine action based on sentiment
            if sentiment_score > 0.2:
                action = "BUY"
                recommendation_type = "crypto_bullish"
            elif sentiment_score < -0.2:
                action = "SELL"
                recommendation_type = "crypto_bearish"
            else:
                action = "HOLD"
                recommendation_type = "crypto_neutral"
            # Get historical performance for this crypto
            historical_performance = self.get_historical_performance(
                symbol, days_back=30
            )
            # Adjust confidence based on historical performance
            historical_confidence = historical_performance.get("win_rate", 50) / 100
            adjusted_confidence = (confidence * 0.4) + (historical_confidence * 0.6)
            # Crypto-specific reasoning
            reasoning = self._generate_crypto_reasoning(
                symbol, sentiment_score, action, historical_performance
            )
            # Create recommendation
            recommendation = {
                "symbol": symbol,
                "action": action,
                "recommendation_type": recommendation_type,
                "current_price": current_price,
                "sentiment_score": sentiment_score,
                "base_confidence": confidence,
                "historical_confidence": historical_confidence,
                "confidence": adjusted_confidence,
                "reasoning": reasoning,
                "crypto_specific": True,
                "volatility_adjusted": True,
                "historical_performance": historical_performance,
                "timestamp": datetime.now().isoformat(),
            }
            # Save the recommendation
            self.save_recommendation(recommendation)
            return recommendation
        except Exception as e:
            logger.error("Error generating crypto recommendation for {symbol}: {e}")
            return {
                "symbol": symbol,
                "action": "HOLD",
                "recommendation_type": "crypto_error",
                "error": str(e),
                "confidence": 0,
                "reasoning": "Error generating recommendation: {str(e)}",
            }

    def _generate_crypto_reasoning(
        self,
        symbol: str,
        sentiment_score: float,
        action: str,
        historical_performance: Dict,
    ) -> str:
        """
        Generate crypto-specific reasoning for recommendations.
        Args:
            symbol: Crypto symbol
            sentiment_score: Sentiment score
            action: Recommended action
            historical_performance: Historical performance data
        Returns:
            str: Detailed reasoning
        """
        win_rate = historical_performance.get("win_rate", 0)
        total_recs = historical_performance.get("total_recommendations", 0)
        reasoning_parts = []
        # Sentiment analysis
        if abs(sentiment_score) > 0.3:
            reasoning_parts.append(
                "Strong {'positive' if sentiment_score > 0 else 'negative'} sentiment detected"
            )
        elif abs(sentiment_score) > 0.1:
            reasoning_parts.append(
                "Moderate {'positive' if sentiment_score > 0 else 'negative'} sentiment detected"
            )
        else:
            reasoning_parts.append("Neutral sentiment - no strong directional bias")
        # Historical performance
        if total_recs > 0:
            if win_rate > 60:
                reasoning_parts.append(
                    "Strong historical performance ({win_rate}% win rate)"
                )
            elif win_rate > 45:
                reasoning_parts.append(
                    "Moderate historical performance ({win_rate}% win rate)"
                )
            else:
                reasoning_parts.append(
                    "Poor historical performance ({win_rate}% win rate) - exercise caution"
                )
        else:
            reasoning_parts.append(
                "No historical data available - using sentiment only"
            )
        # Crypto-specific factors
        reasoning_parts.append(
            "Crypto markets are highly volatile - consider smaller position sizes"
        )
        reasoning_parts.append("24/7 trading means rapid price movements possible")
        # Action-specific reasoning
        if action == "BUY":
            reasoning_parts.append(
                "Bullish crypto recommendation - consider buying the asset"
            )
        elif action == "SELL":
            reasoning_parts.append(
                "Bearish crypto recommendation - consider selling the asset"
            )
        else:
            reasoning_parts.append("Neutral recommendation - wait for clearer signals")
        return " | ".join(reasoning_parts)

    def get_crypto_recommendation_stats(self) -> Dict:
        """
        Get statistics specifically for crypto recommendations.
        Returns:
            Dict: Crypto recommendation statistics
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Get crypto-specific stats
                    cur.execute(
                        f"""
                        SELECT
                            COUNT(*) as total_crypto_recs,
                            COUNT(CASE WHEN profitable = TRUE THEN 1 END) as profitable_crypto,
                            AVG(CASE WHEN actual_outcome IS NOT NULL THEN actual_outcome ELSE NULL END) as avg_crypto_outcome,
                            AVG(CASE WHEN final_confidence IS NOT NULL THEN final_confidence ELSE NULL END) as avg_crypto_confidence
                        FROM {self.table_name}
                        WHERE recommendation_type LIKE 'crypto_%'
                        AND timestamp > NOW() - INTERVAL '90 days'
                    """
                    )
                    crypto_stats = cur.fetchone()
                    # Get top performing cryptos
                    cur.execute(
                        f"""
                        SELECT
                            symbol,
                            COUNT(*) as total_recs,
                            COUNT(CASE WHEN profitable = TRUE THEN 1 END) as profitable_recs,
                            AVG(CASE WHEN actual_outcome IS NOT NULL THEN actual_outcome ELSE NULL END) as avg_outcome
                        FROM {self.table_name}
                        WHERE recommendation_type LIKE 'crypto_%'
                        AND timestamp > NOW() - INTERVAL '90 days'
                        GROUP BY symbol
                        HAVING COUNT(*) >= 3
                        ORDER BY (COUNT(CASE WHEN profitable = TRUE THEN 1 END)::float / COUNT(*)) DESC
                        LIMIT 5
                    """
                    )
                    top_cryptos = cur.fetchall()
                    return {
                        "total_crypto_recommendations": crypto_stats[
                            "total_crypto_recs"
                        ]
                        or 0,
                        "profitable_crypto_recommendations": crypto_stats[
                            "profitable_crypto"
                        ]
                        or 0,
                        "crypto_win_rate": round(
                            (crypto_stats["profitable_crypto"] or 0)
                            / max(crypto_stats["total_crypto_recs"] or 1, 1)
                            * 100,
                            1,
                        ),
                        "avg_crypto_outcome": round(
                            crypto_stats["avg_crypto_outcome"] or 0, 3
                        ),
                        "avg_crypto_confidence": round(
                            crypto_stats["avg_crypto_confidence"] or 0, 3
                        ),
                        "top_performing_cryptos": [
                            {
                                "symbol": row["symbol"],
                                "total_recommendations": row["total_recs"],
                                "profitable_recommendations": row["profitable_recs"],
                                "win_rate": round(
                                    (row["profitable_recs"] / row["total_recs"]) * 100,
                                    1,
                                ),
                                "avg_outcome": round(row["avg_outcome"] or 0, 3),
                            }
                            for row in top_cryptos
                        ],
                    }
        except Exception as e:
            logger.error("Error getting crypto recommendation stats: {e}")
            return {
                "total_crypto_recommendations": 0,
                "profitable_crypto_recommendations": 0,
                "crypto_win_rate": 0,
                "avg_crypto_outcome": 0,
                "avg_crypto_confidence": 0,
                "top_performing_cryptos": [],
                "error": str(e),
            }

    def update_recommendations_with_outcomes(self, days_threshold: int = 30) -> int:
        """
        Update recommendations with actual outcomes based on current prices.
        Args:
            days_threshold: Number of days to wait before evaluating outcomes
        Returns:
            int: Number of recommendations updated
        """
        try:
            # Get data fetcher for price data
            from ..data.data_fetcher import DataFetcher

            data_fetcher = DataFetcher()
            # Track counts
            updated_count = 0
            error_count = 0
            # Find recommendations that need evaluation
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Calculate cutoff date based on threshold
                    cutoff_date = datetime.now() - timedelta(days=days_threshold)
                    # Find recommendations without outcomes that are old enough
                    # to evaluate
                    cur.execute(
                        f"""
                        SELECT id, symbol, recommendation_type, action, current_stock_price,
                               strike_price, timestamp
                        FROM {self.table_name}
                        WHERE outcome_timestamp IS NULL
                        AND timestamp < %s
                        ORDER BY timestamp
                    """,
                        (cutoff_date,),
                    )
                    pending_recommendations = cur.fetchall()
                    if not pending_recommendations:
                        logger.info("No recommendations found to update outcomes")
                        return 0
                    logger.info(
                        "Found {len(pending_recommendations)} recommendations to update with outcomes"
                    )
                    # Process each recommendation
                    for rec in pending_recommendations:
                        try:
                            symbol = rec["symbol"]
                            rec_id = rec["id"]
                            rec_type = rec["recommendation_type"]
                            action = rec["action"]
                            original_price = rec["current_stock_price"]
                            strike_price = rec["strike_price"]
                            # Get current price
                            try:
                                price_data = data_fetcher.get_stock_price(symbol)
                                current_price = price_data["current_price"]
                                # Calculate outcome based on recommendation
                                # type and action
                                outcome = 0
                                profitable = False
                                if rec_type == "stock":
                                    if action == "buy":
                                        # For buy recommendations, positive
                                        # outcome means price went up
                                        outcome = (
                                            current_price - original_price
                                        ) / original_price
                                        profitable = outcome > 0
                                    elif action == "sell":
                                        # For sell recommendations, positive
                                        # outcome means price went down
                                        outcome = (
                                            original_price - current_price
                                        ) / original_price
                                        profitable = outcome > 0
                                    else:
                                        # Hold or other actions
                                        outcome = (
                                            abs(current_price - original_price)
                                            / original_price
                                        )
                                        profitable = (
                                            action == "hold" and abs(outcome) < 0.05
                                        ) or (action != "hold" and outcome > 0)
                                elif rec_type == "option" and strike_price is not None:
                                    if action == "call":
                                        # For call options, positive outcome if
                                        # price > strike
                                        outcome = (
                                            current_price - strike_price
                                        ) / strike_price
                                        profitable = current_price > strike_price
                                    elif action == "put":
                                        # For put options, positive outcome if
                                        # price < strike
                                        outcome = (
                                            strike_price - current_price
                                        ) / strike_price
                                        profitable = current_price < strike_price
                                # Update the recommendation with outcome
                                cur.execute(
                                    f"""
                                    UPDATE {self.table_name}
                                    SET actual_outcome = %s,
                                        outcome_timestamp = CURRENT_TIMESTAMP,
                                        profitable = %s
                                    WHERE id = %s
                                """,
                                    (outcome, profitable, rec_id),
                                )
                                conn.commit()
                                updated_count += 1
                                logger.info(
                                    "Updated recommendation {rec_id} for {symbol}: "
                                    "outcome={outcome:.4f}, profitable={profitable}"
                                )
                            except Exception:
                                logger.error(
                                    "Error getting current price for {symbol}: {e}"
                                )
                                error_count += 1
                                continue
                        except Exception:
                            logger.error(
                                "Error updating recommendation {rec['id']}: {e}"
                            )
                            error_count += 1
                            continue
            logger.info(
                "Successfully updated {updated_count} recommendations with outcomes"
            )
            if error_count > 0:
                logger.warning("Failed to update {error_count} recommendations")
            return updated_count
        except Exception:
            logger.error("Error updating recommendation outcomes: {e}")
            return 0

    def get_recommendation_stats(self) -> Dict:
        """
        Get overall statistics about recommendations in the database.
        Returns:
            Dict: Statistics about recommendations
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Get total count
                    cur.execute(
                        f"""
                        SELECT COUNT(*) as total FROM {self.table_name}
                    """
                    )
                    total = cur.fetchone()["total"]
                    # Get count by action
                    cur.execute(
                        f"""
                        SELECT action, COUNT(*) as count
                        FROM {self.table_name}
                        GROUP BY action
                        ORDER BY count DESC
                    """
                    )
                    actions = cur.fetchall()
                    # Get count by recommendation type
                    cur.execute(
                        f"""
                        SELECT recommendation_type, COUNT(*) as count
                        FROM {self.table_name}
                        GROUP BY recommendation_type
                        ORDER BY count DESC
                    """
                    )
                    types = cur.fetchall()
                    # Get count by symbol
                    cur.execute(
                        f"""
                        SELECT symbol, COUNT(*) as count
                        FROM {self.table_name}
                        GROUP BY symbol
                        ORDER BY count DESC
                        LIMIT 10
                    """
                    )
                    symbols = cur.fetchall()
                    # Get overall win rate
                    cur.execute(
                        f"""
                        SELECT
                            COUNT(*) as total_evaluated,
                            COUNT(CASE WHEN profitable = TRUE THEN 1 END) as profitable_count,
                            AVG(CASE WHEN actual_outcome IS NOT NULL THEN actual_outcome ELSE NULL END) as avg_outcome
                        FROM {self.table_name}
                        WHERE actual_outcome IS NOT NULL
                    """
                    )
                    performance = cur.fetchone()
                    return {
                        "total_recommendations": total,
                        "actions": actions,
                        "recommendation_types": types,
                        "top_symbols": symbols,
                        "performance": {
                            "total_evaluated": (
                                performance["total_evaluated"] if performance else 0
                            ),
                            "profitable_count": (
                                performance["profitable_count"] if performance else 0
                            ),
                            "win_rate": (
                                (
                                    performance["profitable_count"]
                                    / performance["total_evaluated"]
                                )
                                if performance and performance["total_evaluated"] > 0
                                else 0
                            ),
                            "avg_outcome": (
                                performance["avg_outcome"] if performance else 0
                            ),
                        },
                    }
        except Exception as e:
            logger.error("Error getting recommendation stats: {e}")
            return {"total_recommendations": 0, "error": str(e)}


# Global recommendation manager instance
recommendation_manager = None


def get_recommendation_manager() -> RecommendationManager:
    """Get global recommendation manager instance."""
    global recommendation_manager
    if recommendation_manager is None:
        try:
            recommendation_manager = RecommendationManager()
            logger.info("Recommendation manager initialized successfully")
        except Exception:
            logger.error("Failed to initialize recommendation manager: {e}")
            # Create anyway to avoid None errors, operations will fail
            # gracefully
            recommendation_manager = RecommendationManager()
    return recommendation_manager
