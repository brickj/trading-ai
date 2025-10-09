"""Routes exposing recommendation data and statistics."""
import traceback
from datetime import datetime

from flask import Blueprint, jsonify, request

from ..helpers import create_api_response
from ..dependencies import recommendation_manager


recommendation_bp = Blueprint("recommendations", __name__)


@recommendation_bp.route("/api/recommendations", methods=["GET"])
def api_recommendations():
    """Paginated, filterable recommendations API."""
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
        symbol = request.args.get("symbol")
        recommendation_type = request.args.get("type")
        action = request.args.get("action")
        outcome = request.args.get("outcome")

        offset = (page - 1) * page_size
        filters = []
        params = []

        if symbol:
            filters.append("symbol = %s")
            params.append(symbol.upper())
        if recommendation_type:
            filters.append("recommendation_type = %s")
            params.append(recommendation_type)
        if action:
            filters.append("action = %s")
            params.append(action.upper())
        if outcome:
            if outcome == "profitable":
                filters.append("profitable = TRUE")
            elif outcome == "unprofitable":
                filters.append("profitable = FALSE")
            elif outcome == "pending":
                filters.append("profitable IS NULL")

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        query = f"""
            SELECT id, symbol, recommendation_type, action, timestamp, final_confidence,
                   current_stock_price, actual_outcome, profitable
            FROM recommendations
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
        """
        count_query = f"SELECT COUNT(*) FROM recommendations {where_clause}"

        params_count = list(params)
        params.extend([page_size, offset])

        with recommendation_manager._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                cur.execute(count_query, params_count)
                count_result = cur.fetchone()
                total_count = count_result["count"] if count_result else 0

        recommendations = [
            {
                "id": row["id"],
                "symbol": row["symbol"],
                "recommendation_type": row["recommendation_type"],
                "action": row["action"],
                "timestamp": row["timestamp"],
                "final_confidence": float(row["final_confidence"])
                if row["final_confidence"] is not None
                else None,
                "current_stock_price": float(row["current_stock_price"])
                if row["current_stock_price"] is not None
                else None,
                "actual_outcome": float(row["actual_outcome"])
                if row["actual_outcome"] is not None
                else None,
                "profitable": row["profitable"],
            }
            for row in rows
        ]

        has_more = (offset + len(recommendations)) < total_count
        return jsonify(
            {
                "recommendations": recommendations,
                "total_count": total_count,
                "has_more": has_more,
            }
        )
    except Exception as exc:
        tb = traceback.format_exc()
        return jsonify({"error": str(exc), "traceback": tb}), 500


@recommendation_bp.route("/api/recommendations/stats", methods=["GET"])
def api_recommendations_stats():
    """Return comprehensive recommendation statistics."""
    try:
        with recommendation_manager._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM recommendations")
                total_recommendations = cur.fetchone()["count"] or 0

                cur.execute(
                    """
                    SELECT COUNT(*) as total_evaluated,
                           COUNT(CASE WHEN profitable = TRUE THEN 1 END) as wins,
                           AVG(actual_outcome) as avg_outcome
                    FROM recommendations
                    WHERE actual_outcome IS NOT NULL
                    """
                )
                perf_row = cur.fetchone()
                total_evaluated = perf_row["total_evaluated"] or 0
                wins = perf_row["wins"] or 0
                avg_outcome = (
                    float(perf_row["avg_outcome"])
                    if perf_row["avg_outcome"] is not None
                    else 0.0
                )
                win_rate = (wins / total_evaluated) if total_evaluated > 0 else 0.0

                cur.execute(
                    """
                    SELECT recommendation_type, COUNT(*) as count
                    FROM recommendations
                    GROUP BY recommendation_type
                    ORDER BY count DESC
                    """
                )
                recommendation_types = [
                    {"recommendation_type": row["recommendation_type"], "count": row["count"]}
                    for row in cur.fetchall()
                ]

                cur.execute(
                    """
                    SELECT action, COUNT(*) as count
                    FROM recommendations
                    GROUP BY action
                    ORDER BY count DESC
                    """
                )
                actions = [
                    {"action": row["action"], "count": row["count"]}
                    for row in cur.fetchall()
                ]

                cur.execute(
                    """
                    SELECT symbol,
                           COUNT(*) as count,
                           COUNT(CASE WHEN profitable = TRUE THEN 1 END) as profitable,
                           COUNT(CASE WHEN profitable = FALSE THEN 1 END) as unprofitable
                    FROM recommendations
                    GROUP BY symbol
                    ORDER BY count DESC
                    LIMIT 5
                    """
                )
                symbol_performance = []
                for row in cur.fetchall():
                    count = row["count"] or 0
                    wins_count = row["profitable"] or 0
                    success_rate = (wins_count / count) if count > 0 else 0.0
                    symbol_performance.append(
                        {
                            "symbol": row["symbol"],
                            "total": count,
                            "profitable": wins_count,
                            "unprofitable": row["unprofitable"] or 0,
                            "success_rate": success_rate,
                        }
                    )

                cur.execute(
                    """
                    SELECT recommendation_type, action,
                           COUNT(*) as count,
                           COUNT(CASE WHEN profitable = TRUE THEN 1 END) as wins,
                           AVG(actual_outcome) as avg_outcome
                    FROM recommendations
                    WHERE actual_outcome IS NOT NULL
                    GROUP BY recommendation_type, action
                    HAVING COUNT(*) >= 3
                    ORDER BY AVG(actual_outcome) DESC
                    LIMIT 10
                    """
                )
                recommendation_performance = []
                for row in cur.fetchall():
                    recommendation_performance.append(
                        {
                            "recommendation_type": row["recommendation_type"],
                            "action": row["action"],
                            "count": row["count"],
                            "wins": row["wins"],
                            "win_rate": (row["wins"] / row["count"])
                            if row["count"] > 0
                            else 0.0,
                            "avg_outcome": float(row["avg_outcome"])
                            if row["avg_outcome"] is not None
                            else 0.0,
                        }
                    )

                cur.execute("SELECT MAX(timestamp) as max FROM recommendations")
                last_updated_row = cur.fetchone()
                last_updated = (
                    last_updated_row["max"].isoformat() if last_updated_row and last_updated_row["max"] else None
                )

        return jsonify(
            {
                "total_recommendations": total_recommendations,
                "performance": {
                    "total_evaluated": total_evaluated,
                    "wins": wins,
                    "win_rate": win_rate,
                    "avg_outcome": avg_outcome,
                },
                "recommendation_types": recommendation_types,
                "actions": actions,
                "symbol_performance": symbol_performance,
                "recommendation_performance": recommendation_performance,
                "last_updated": last_updated,
            }
        )
    except Exception as exc:
        tb = traceback.format_exc()
        return jsonify({"error": str(exc), "traceback": tb}), 500


@recommendation_bp.route("/api/recommendations/metrics", methods=["GET"])
def api_recommendations_metrics():
    """Return win rate, average return, top symbols and types."""
    with recommendation_manager._get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN profitable = TRUE THEN 1 END) as wins,
                       AVG(actual_outcome) as avg_return
                FROM recommendations
                WHERE actual_outcome IS NOT NULL
                """
            )
            row = cur.fetchone()
            total = row["total"] or 0
            wins = row["wins"] or 0
            avg_return = float(row["avg_return"]) if row["avg_return"] is not None else 0.0
            win_rate = (wins / total) if total > 0 else 0.0

            cur.execute(
                """
                SELECT symbol, COUNT(*) as freq
                FROM recommendations
                GROUP BY symbol
                ORDER BY freq DESC
                LIMIT 5
                """
            )
            top_symbols = [{"symbol": r["symbol"], "count": r["freq"]} for r in cur.fetchall()]

            cur.execute(
                """
                SELECT recommendation_type, AVG(actual_outcome) as avg_ret
                FROM recommendations
                WHERE actual_outcome IS NOT NULL
                GROUP BY recommendation_type
                ORDER BY avg_ret DESC
                LIMIT 3
                """
            )
            top_types = [
                {
                    "recommendation_type": r["recommendation_type"],
                    "avg_return": float(r["avg_ret"]) if r["avg_ret"] is not None else 0.0,
                }
                for r in cur.fetchall()
            ]

    return jsonify(
        {
            "win_rate": win_rate,
            "average_return": avg_return,
            "top_symbols": top_symbols,
            "top_types": top_types,
        }
    )


@recommendation_bp.route("/api/test_db", methods=["GET"])
def test_db():
    """Quick database connectivity test."""
    try:
        with recommendation_manager._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM recommendations")
                count_result = cur.fetchone()
                count = count_result["count"] if count_result else 0
                return jsonify({"success": True, "count": count})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


__all__ = ["recommendation_bp"]
