"""Routes for market overviews, calendars, and weekly plans."""
from datetime import datetime, timedelta
from typing import Optional

from flask import Blueprint, jsonify, request

from ..helpers import create_api_response
from ..utils.page_logger import page_logger
from ..dependencies import market_manager
from ..services import system_service


market_bp = Blueprint("market", __name__)

trading_logger = page_logger.logger
log_exception = page_logger.exception


EVENT_TYPE_TO_GROUP = {
    "earnings": "earnings",
    "federal_reserve": "federal_reserve",
    "economic": "economic",
    "economic_data": "economic",
    "economic_event": "economic",
    "economic_events": "economic",
    "options_expiration": "options_expiration",
    "market_holiday": "market_holidays",
    "market_holidays": "market_holidays",
}


def _safe_int(value: Optional[str], default: int, *, param_name: str) -> int:
    """Parse integers from query params without surfacing ValueError."""

    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        trading_logger.error_logger.warning(
            "[WARN] Invalid integer for %s in weekly_events API: %s", param_name, value
        )
        return default


@market_bp.route("/api/foreign_markets/overview")
def foreign_markets_overview_api():
    """Return overview of foreign markets from the database."""
    try:
        trading_logger.api_logger.info(
            "[DEBUG] Entering foreign_markets_overview_api route handler"
        )
        markets_data = market_manager.get_foreign_markets_overview()
        return create_api_response(data=markets_data)
    except Exception as exc:
        error_msg = f"Error in foreign_markets_overview_api: {str(exc)}"
        trading_logger.error_logger.error(error_msg)
        log_exception("foreign_markets_overview_api", exc)
        return create_api_response(error=error_msg, status_code=500)


@market_bp.route("/api/weekly_events")
def weekly_events_api():
    """Return weekly market events grouped by type."""
    try:
        trading_logger.api_logger.info("[DEBUG] Entered weekly_events API endpoint")

        # Determine the reference date for the query window. If the UI supplies
        # a specific start date we use that week as our anchor, otherwise we
        # default to "today" so the page shows recent data when first loaded.
        start_date_param = request.args.get("start_date")
        if start_date_param:
            try:
                reference_date = datetime.strptime(start_date_param, "%Y-%m-%d").date()
            except ValueError:
                trading_logger.error_logger.warning(
                    "[WARN] Invalid start_date supplied to weekly_events API: %s",
                    start_date_param,
                )
                reference_date = datetime.now().date()
        else:
            reference_date = datetime.now().date()

        # Allow callers to customise the lookback/lookahead window while
        # defaulting to a full month in each direction as requested.
        days_back = request.args.get("days_back")
        days_ahead = request.args.get("days_ahead")
        weeks_back = request.args.get("weeks_back")
        weeks_ahead = request.args.get("weeks_ahead")

        if weeks_back is not None or weeks_ahead is not None:
            # Preserve backwards compatibility if any callers still rely on the
            # old weeks-based parameters.  Fall back to four weeks (~one month)
            # when one of the values is missing or invalid.
            weeks_back_value = _safe_int(weeks_back, 4, param_name="weeks_back")
            weeks_ahead_value = _safe_int(weeks_ahead, 4, param_name="weeks_ahead")
            start_date = reference_date - timedelta(weeks=weeks_back_value)
            end_date = reference_date + timedelta(weeks=weeks_ahead_value)
        else:
            days_back_value = _safe_int(days_back, 30, param_name="days_back")
            days_ahead_value = _safe_int(days_ahead, 30, param_name="days_ahead")
            start_date = reference_date - timedelta(days=days_back_value)
            end_date = reference_date + timedelta(days=days_ahead_value)

        grouped_events = {
            "earnings": [],
            "federal_reserve": [],
            "economic": [],
            "options_expiration": [],
            "market_holidays": [],
        }

        try:
            with system_service.get_database_connection() as conn:
                with conn.cursor() as cur:
                    # Check what data exists in the table
                    cur.execute("SELECT COUNT(*) FROM weekly_plan_events")
                    total_events = cur.fetchone()['count']
                    trading_logger.api_logger.info(f"[DEBUG] Total events in table: {total_events}")
                    
                    # Check date range of existing data
                    cur.execute("SELECT MIN(event_date), MAX(event_date) FROM weekly_plan_events")
                    result = cur.fetchone()
                    min_date, max_date = result['min'], result['max']
                    trading_logger.api_logger.info(f"[DEBUG] Data range in table: {min_date} to {max_date}")
                    trading_logger.api_logger.info(f"[DEBUG] Querying range: {start_date} to {end_date}")
                    
                    cur.execute(
                        """
                        SELECT event_date, event_type, event_name, impact, symbol, timing
                        FROM weekly_plan_events
                        WHERE event_date BETWEEN %s AND %s
                        ORDER BY event_date, event_type
                        """,
                        (start_date, end_date),
                    )
                    events = cur.fetchall()
                    trading_logger.api_logger.info(f"[DEBUG] Found {len(events)} events in query range")
                    
                    for event in events:
                        event_data = {
                            "date": event["event_date"].strftime("%Y-%m-%d"),
                            "name": event["event_name"],
                            "event_type": event["event_type"],
                            "impact": event["impact"],
                            "symbol": event["symbol"],
                            "timing": event["timing"] or "all_day",
                        }
                        event_type = event["event_type"]
                        group_key = EVENT_TYPE_TO_GROUP.get(event_type, event_type)

                        if group_key not in grouped_events:
                            grouped_events[group_key] = []

                        grouped_events[group_key].append(event_data)
        except Exception as db_error:
            trading_logger.error_logger.error(
                f"[ERROR] Database query failed: {str(db_error)}"
            )

        return create_api_response(data=grouped_events)
    except Exception as exc:
        trading_logger.error_logger.error(
            f"[ERROR] Failed to fetch weekly events: {str(exc)}"
        )
        return create_api_response(
            success=False,
            message=f"Failed to fetch weekly events: {str(exc)}",
            status_code=500,
        )


@market_bp.route("/api/weekly_plan/populate", methods=["POST"])
def populate_weekly_plan():
    """Populate weekly plan data with sample events."""
    try:
        trading_logger.api_logger.info("[DEBUG] Populating weekly plan data")
        
        from src.data.weekly_plan_populator import populate_weekly_plan_events
        results = populate_weekly_plan_events()
        
        return create_api_response(
            data=results,
            message=f"Weekly plan populated successfully with {results.get('total_inserted', 0)} events",
        )
    except Exception as exc:
        trading_logger.error_logger.error(
            f"[ERROR] Failed to populate weekly plan: {str(exc)}"
        )
        return create_api_response(
            success=False,
            message=f"Failed to populate weekly plan: {str(exc)}",
            status_code=500,
        )


@market_bp.route("/api/weekly_plan/available_weeks")
def available_weeks_api():
    """Return placeholder list of available weeks."""
    try:
        weeks_back = int(request.args.get("weeks_back", 4))
        weeks_ahead = int(request.args.get("weeks_ahead", 8))
        trading_logger.api_logger.info(
            f"[DEBUG] Weekly plan requested weeks_back={weeks_back}, weeks_ahead={weeks_ahead}"
        )
        return create_api_response(
            data={"weeks": []},
            message="Weekly plan module not available",
        )
    except Exception as exc:
        trading_logger.error_logger.error(
            f"[ERROR] Failed to get available weeks: {str(exc)}"
        )
        return create_api_response(
            success=False,
            message=f"Failed to get available weeks: {str(exc)}",
            status_code=500,
        )


@market_bp.route("/api/market_calendar/<date_str>")
def market_calendar_api(date_str):
    """Return events for a specific market date."""
    try:
        trading_logger.api_logger.info(
            f"[DEBUG] Entered market_calendar API endpoint for date: {date_str}"
        )
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return create_api_response(
                success=False,
                message="Invalid date format. Use YYYY-MM-DD",
                status_code=400,
            )

        real_events = []
        try:
            with system_service.get_database_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT event_name, event_type, impact, timing
                        FROM weekly_plan_events
                        WHERE event_date = %s
                        ORDER BY event_type, event_name
                        """,
                        (target_date,),
                    )
                    for event in cur.fetchall():
                        real_events.append(
                            {
                                "name": event["event_name"],
                                "event_type": event["event_type"],
                                "impact": event["impact"],
                                "timing": event["timing"] or "all_day",
                            }
                        )
        except Exception as db_error:
            trading_logger.error_logger.error(
                f"[ERROR] Database query failed: {str(db_error)}"
            )

        return create_api_response(
            data={"date": date_str, "events": real_events},
            message=f"Events for {date_str} retrieved successfully from database",
        )
    except Exception as exc:
        trading_logger.error_logger.error(
            f"[ERROR] Failed to fetch events for {date_str}: {str(exc)}"
        )
        return create_api_response(
            success=False,
            message=f"Failed to fetch market events: {str(exc)}",
            status_code=500,
        )


@market_bp.route("/api/earnings_calendar")
def earnings_calendar_api():
    """Return upcoming earnings from the database."""
    try:
        trading_logger.api_logger.info(
            "[DEBUG] Entered earnings_calendar API endpoint"
        )
        days_ahead = int(request.args.get("days", 7))
        max_symbols = int(request.args.get("limit", 50))

        try:
            with system_service.get_database_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT symbol, company_name, event_date, event_time, estimate, actual
                        FROM earnings_calendar
                        WHERE event_date BETWEEN NOW() AND NOW() + INTERVAL '%s days'
                        ORDER BY event_date
                        LIMIT %s
                        """,
                        (days_ahead, max_symbols),
                    )
                    rows = cur.fetchall()
                    earnings = [
                        {
                            "symbol": row["symbol"],
                            "company_name": row["company_name"],
                            "event_date": row["event_date"].isoformat()
                            if row["event_date"]
                            else None,
                            "event_time": row["event_time"],
                            "estimate": row["estimate"],
                            "actual": row["actual"],
                        }
                        for row in rows
                    ]
        except Exception as db_error:
            trading_logger.error_logger.error(
                f"[ERROR] Database query failed: {str(db_error)}"
            )
            earnings = []

        return create_api_response(
            data={"earnings": earnings},
            message="Earnings calendar retrieved successfully",
        )
    except Exception as exc:
        trading_logger.error_logger.error(
            f"[ERROR] Failed to fetch earnings calendar: {str(exc)}"
        )
        return create_api_response(
            success=False,
            message=f"Failed to fetch earnings calendar: {str(exc)}",
            status_code=500,
        )


__all__ = ["market_bp"]
