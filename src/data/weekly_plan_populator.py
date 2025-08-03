"""
Weekly Plan Populator Service
Populates the weekly_plan_events table with market calendar data a month in advance.
Should be run as a scheduled job (daily or weekly).
"""

import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import json
from src.core.database import get_db_connection
from src.data.market_calendar import MarketCalendar


class WeeklyPlanPopulator:
    def __init__(self):
        self.market_calendar = MarketCalendar()
        self.logger = logging.getLogger(__name__)

    def get_week_start(self, target_date: date) -> date:
        """Get Monday of the week for a given date"""
        days_ahead = target_date.weekday()
        return target_date - timedelta(days=days_ahead)

    def populate_advance_data(self, weeks_ahead: int = 6) -> Dict[str, int]:
        """
        Populate weekly plan data for the next N weeks
        Default: 6 weeks (1.5 months) to ensure we're always ahead
        """
        start_date = date.today()
        end_date = start_date + timedelta(weeks=weeks_ahead)

        self.logger.info(f"Populating weekly plan data from {start_date} to {end_date}")

        # Clear existing future data to avoid duplicates
        self._clear_future_data(start_date)

        counts = {
            "earnings": 0,
            "economic": 0,
            "federal_reserve": 0,
            "options_expiration": 0,
            "market_holidays": 0,
        }

        # Get all data types
        earnings_data = self._get_earnings_data(start_date, end_date)
        economic_data = self._get_economic_data(start_date, end_date)
        fed_data = self._get_federal_reserve_data(start_date, end_date)
        options_data = self._get_options_expiration_data(start_date, end_date)
        holidays_data = self._get_market_holidays_data(start_date, end_date)

        # Insert all data
        counts["earnings"] = self._insert_events(earnings_data)
        counts["economic"] = self._insert_events(economic_data)
        counts["federal_reserve"] = self._insert_events(fed_data)
        counts["options_expiration"] = self._insert_events(options_data)
        counts["market_holidays"] = self._insert_events(holidays_data)

        total = sum(counts.values())
        self.logger.info(f"Successfully populated {total} events: {counts}")

        return counts

    def _clear_future_data(self, from_date: date):
        """Clear existing future data to avoid duplicates"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM weekly_plan_events WHERE event_date >= %s",
                        (from_date,),
                    )
                    deleted = cursor.rowcount
                    self.logger.info(f"Cleared {deleted} existing future events")
        except Exception as e:
            self.logger.error(f"Error clearing future data: {e}")

    def _get_earnings_data(self, start_date: date, end_date: date) -> List[Dict]:
        """Get earnings events from market calendar"""
        try:
            earnings_events = self.market_calendar._get_earnings_events(
                start_date, end_date
            )
            formatted_events = []

            for event in earnings_events:
                event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
                week_start = self.get_week_start(event_date)

                formatted_events.append(
                    {
                        "week_start_date": week_start,
                        "event_date": event_date,
                        "event_name": event["name"],
                        "event_type": "earnings",
                        "event_subtype": "earnings_release",
                        "impact": event.get("impact", "medium"),
                        "timing": event.get("timing", "after_hours"),
                        "source": event.get("source", "api"),
                        "symbol": event.get("symbol"),
                        "description": f"Earnings release for {event.get('symbol', 'Unknown')}",
                        "details": {
                            "estimate": event.get("estimate"),
                            "previous": event.get("previous"),
                            "market_cap": event.get("market_cap"),
                        },
                    }
                )

            return formatted_events
        except Exception as e:
            self.logger.error(f"Error getting earnings data: {e}")
            return []

    def _get_economic_data(self, start_date: date, end_date: date) -> List[Dict]:
        """Get economic events from market calendar"""
        try:
            economic_events = self.market_calendar._get_economic_events(
                start_date, end_date
            )
            formatted_events = []

            for event in economic_events:
                event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
                week_start = self.get_week_start(event_date)

                formatted_events.append(
                    {
                        "week_start_date": week_start,
                        "event_date": event_date,
                        "event_name": event["name"],
                        "event_type": "economic_data",
                        "event_subtype": event.get(
                            "indicator_type", "economic_release"
                        ),
                        "impact": event.get("impact", "medium"),
                        "timing": event.get("timing", "market_hours"),
                        "source": event.get("source", "api"),
                        "symbol": None,
                        "description": f"Economic data release: {event['name']}",
                        "details": {
                            "frequency": event.get("frequency"),
                            "unit": event.get("unit"),
                            "forecast": event.get("forecast"),
                            "previous": event.get("previous"),
                        },
                    }
                )

            return formatted_events
        except Exception as e:
            self.logger.error(f"Error getting economic data: {e}")
            return []

    def _get_federal_reserve_data(self, start_date: date, end_date: date) -> List[Dict]:
        """Get Federal Reserve events"""
        try:
            fed_events = self.market_calendar._get_fed_events(start_date, end_date)
            formatted_events = []

            for event in fed_events:
                event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
                week_start = self.get_week_start(event_date)

                formatted_events.append(
                    {
                        "week_start_date": week_start,
                        "event_date": event_date,
                        "event_name": event["name"],
                        "event_type": "federal_reserve",
                        "event_subtype": event.get("meeting_type", "fomc_meeting"),
                        "impact": event.get("impact", "high"),
                        "timing": event.get("timing", "market_hours"),
                        "source": "calculated",
                        "symbol": None,
                        "description": f"Federal Reserve event: {event['name']}",
                        "details": {
                            "meeting_days": event.get("meeting_days", 1),
                            "rate_decision_expected": event.get("rate_decision", False),
                        },
                    }
                )

            return formatted_events
        except Exception as e:
            self.logger.error(f"Error getting Federal Reserve data: {e}")
            return []

    def _get_options_expiration_data(
        self, start_date: date, end_date: date
    ) -> List[Dict]:
        """Calculate options expiration dates"""
        try:
            formatted_events = []
            current_date = start_date

            while current_date <= end_date:
                if current_date.weekday() == 4:  # Friday
                    week_start = self.get_week_start(current_date)

                    # Weekly options expiration (every Friday)
                    formatted_events.append(
                        {
                            "week_start_date": week_start,
                            "event_date": current_date,
                            "event_name": "Weekly Options Expiration",
                            "event_type": "options_expiration",
                            "event_subtype": "weekly",
                            "impact": "medium",
                            "timing": "market_close",
                            "source": "calculated",
                            "symbol": None,
                            "description": "Weekly options contracts expire",
                            "details": {
                                "expiration_type": "weekly",
                                "affected_symbols": [
                                    "SPY",
                                    "QQQ",
                                    "IWM",
                                    "Most ETFs and Stocks",
                                ],
                            },
                        }
                    )

                    # Monthly options expiration (3rd Friday)
                    if 15 <= current_date.day <= 21:  # 3rd Friday of month
                        formatted_events.append(
                            {
                                "week_start_date": week_start,
                                "event_date": current_date,
                                "event_name": "Monthly Options Expiration (OPEX)",
                                "event_type": "options_expiration",
                                "event_subtype": "monthly",
                                "impact": "high",
                                "timing": "market_close",
                                "source": "calculated",
                                "symbol": None,
                                "description": "Monthly options and index options expire - high volume expected",
                                "details": {
                                    "expiration_type": "monthly",
                                    "affected_symbols": [
                                        "SPX",
                                        "SPY",
                                        "QQQ",
                                        "IWM",
                                        "All Monthly Options",
                                    ],
                                    "opex_week": True,
                                },
                            }
                        )

                        # Quarterly expiration (March, June, September, December)
                        if current_date.month in [3, 6, 9, 12]:
                            formatted_events.append(
                                {
                                    "week_start_date": week_start,
                                    "event_date": current_date,
                                    "event_name": "Quarterly Options Expiration (Triple Witching)",
                                    "event_type": "options_expiration",
                                    "event_subtype": "quarterly",
                                    "impact": "high",
                                    "timing": "market_close",
                                    "source": "calculated",
                                    "symbol": None,
                                    "description": "Quarterly expiration - stock options, index options, and futures expire simultaneously",
                                    "details": {
                                        "expiration_type": "quarterly",
                                        "triple_witching": True,
                                        "affected_symbols": [
                                            "All Options",
                                            "Index Futures",
                                            "Stock Futures",
                                        ],
                                    },
                                }
                            )

                current_date += timedelta(days=1)

            return formatted_events
        except Exception as e:
            self.logger.error(f"Error calculating options expiration data: {e}")
            return []

    def _get_market_holidays_data(self, start_date: date, end_date: date) -> List[Dict]:
        """Get market holidays"""
        try:
            holidays_events = self.market_calendar._get_market_holidays(
                start_date, end_date
            )
            formatted_events = []

            for event in holidays_events:
                event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
                week_start = self.get_week_start(event_date)

                formatted_events.append(
                    {
                        "week_start_date": week_start,
                        "event_date": event_date,
                        "event_name": event["name"],
                        "event_type": "market_holidays",
                        "event_subtype": "market_closure",
                        "impact": "high",
                        "timing": "all_day",
                        "source": "calculated",
                        "symbol": None,
                        "description": f"Market closed for {event['name']}",
                        "details": {
                            "market_closed": True,
                            "early_close": event.get("early_close", False),
                        },
                    }
                )

            return formatted_events
        except Exception as e:
            self.logger.error(f"Error getting market holidays data: {e}")
            return []

    def _insert_events(self, events: List[Dict]) -> int:
        """Insert events into database"""
        if not events:
            return 0

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    insert_query = """
                        INSERT INTO weekly_plan_events 
                        (week_start_date, event_date, event_name, event_type, event_subtype, 
                         impact, timing, source, symbol, description, details)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    for event in events:
                        cursor.execute(
                            insert_query,
                            (
                                event["week_start_date"],
                                event["event_date"],
                                event["event_name"],
                                event["event_type"],
                                event["event_subtype"],
                                event["impact"],
                                event["timing"],
                                event["source"],
                                event["symbol"],
                                event["description"],
                                json.dumps(event["details"])
                                if event["details"]
                                else None,
                            ),
                        )

                    return len(events)
        except Exception as e:
            self.logger.error(f"Error inserting events: {e}")
            return 0

    def get_weekly_plan(
        self, week_start_date: Optional[date] = None
    ) -> Dict[str, List[Dict]]:
        """
        Get weekly plan data for a specific week
        If no date provided, defaults to current week
        """
        if week_start_date is None:
            week_start_date = self.get_week_start(date.today())

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT event_date, event_name, event_type, event_subtype, impact, 
                               timing, source, symbol, description, details
                        FROM weekly_plan_events 
                        WHERE week_start_date = %s
                        ORDER BY event_date, event_type, impact DESC
                    """,
                        (week_start_date,),
                    )

                    rows = cursor.fetchall()

                    # Group events by type
                    grouped_events = {
                        "earnings": [],
                        "economic": [],
                        "federal_reserve": [],
                        "options_expiration": [],
                        "market_holidays": [],
                    }

                    for row in rows:
                        event = {
                            "date": row[0].isoformat(),
                            "name": row[1],
                            "event_type": row[2],
                            "event_subtype": row[3],
                            "impact": row[4],
                            "timing": row[5],
                            "source": row[6],
                            "symbol": row[7],
                            "description": row[8],
                            "details": json.loads(row[9]) if row[9] else {},
                        }

                        # Map to correct group
                        if row[2] == "economic_data":
                            grouped_events["economic"].append(event)
                        else:
                            grouped_events[row[2]].append(event)

                    return grouped_events

        except Exception as e:
            self.logger.error(f"Error getting weekly plan: {e}")
            return {
                "earnings": [],
                "economic": [],
                "federal_reserve": [],
                "options_expiration": [],
                "market_holidays": [],
            }

    def get_available_weeks(
        self, weeks_back: int = 4, weeks_ahead: int = 8
    ) -> List[Dict]:
        """Get list of available weeks with data"""
        base_date = date.today()
        start_date = base_date - timedelta(weeks=weeks_back)
        end_date = base_date + timedelta(weeks=weeks_ahead)

        weeks = []
        current = self.get_week_start(start_date)

        while current <= self.get_week_start(end_date):
            week_end = current + timedelta(days=6)
            weeks.append(
                {
                    "week_start": current.isoformat(),
                    "week_end": week_end.isoformat(),
                    "label": f"Week of {current.strftime('%b %d, %Y')}",
                    "is_current": current == self.get_week_start(base_date),
                }
            )
            current += timedelta(weeks=1)

        return weeks


if __name__ == "__main__":
    # For testing - populate data
    populator = WeeklyPlanPopulator()
    results = populator.populate_advance_data()
    print(f"Populated weekly plan data: {results}")
