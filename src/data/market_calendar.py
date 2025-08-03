"""
Market Calendar Data Fetcher
Handles fetching various market calendar events including earnings, Federal Reserve events,
economic data releases, options expirations, and market holidays.
"""

import requests
import json
import time
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Any
import calendar
import logging
from src.core.config import Config
from src.core.cache import Cache

logger = logging.getLogger(__name__)


class MarketCalendar:
    """Fetches and manages market calendar events"""

    def __init__(self):
        self.cache = Cache()
        self.alpha_vantage_key = Config.ALPHA_VANTAGE_API_KEY
        self.finnhub_key = Config.FINNHUB_API_KEY

    def get_weekly_events(self, start_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get all market events for a week starting from start_date (database-backed)

        Args:
            start_date: Start of the week (defaults to current week Monday)

        Returns:
            Dictionary with categorized events for the week
        """
        from src.data.weekly_plan_populator import WeeklyPlanPopulator

        if start_date is None:
            # Get current Monday
            today = date.today()
            start_date = today - timedelta(days=today.weekday())

        end_date = start_date + timedelta(days=6)  # Sunday

        # Cache key for the week
        cache_key = f"weekly_events_{start_date.strftime('%Y%m%d')}"

        # Check cache first
        cached_events = self.cache.get(cache_key)
        if cached_events:
            logger.info(f"Returning cached weekly events for {start_date}")
            return json.loads(cached_events)

        logger.info(f"Fetching weekly events for {start_date} to {end_date}")

        # Use the database-backed populator to get events
        populator = WeeklyPlanPopulator()
        weekly_events_data = populator.get_weekly_plan(start_date)

        # Add metadata and organize response to match expected format
        events = {
            "week_start": start_date.isoformat(),
            "week_end": end_date.isoformat(),
            "earnings": weekly_events_data.get("earnings", []),
            "economic": weekly_events_data.get("economic", []),
            "federal_reserve": weekly_events_data.get("federal_reserve", []),
            "options_expiration": weekly_events_data.get("options_expiration", []),
            "market_holidays": weekly_events_data.get("market_holidays", []),
            "dividends": [],  # Kept for compatibility, can be populated later
            "ipos": [],  # Kept for compatibility, can be populated later
            "daily_breakdown": self._organize_events_by_day(
                weekly_events_data, start_date
            ),
        }

        # Cache for 4 hours
        self.cache.set(cache_key, json.dumps(events, default=str), ttl=14400)

        return events

    def _organize_events_by_day(
        self, weekly_events_data: Dict, start_date: date
    ) -> Dict[str, List[Dict]]:
        """Organize events by day of the week for daily breakdown"""
        daily_breakdown = {}

        # Initialize each day of the week
        for i in range(7):
            day_date = start_date + timedelta(days=i)
            day_key = day_date.strftime("%Y-%m-%d")
            daily_breakdown[day_key] = []

        # Organize all events by day
        for event_type, events in weekly_events_data.items():
            for event in events:
                event_date = event.get("date")
                if event_date and event_date in daily_breakdown:
                    daily_breakdown[event_date].append(event)

        return daily_breakdown

    def _get_earnings_events(self, start_date: date, end_date: date) -> List[Dict]:
        """Get comprehensive earnings events from Alpha Vantage and Finnhub"""
        earnings = []

        # Try Alpha Vantage earnings calendar first
        try:
            url = "https://www.alphavantage.co/query"
            params = {"function": "EARNINGS_CALENDAR", "apikey": self.alpha_vantage_key}

            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.text
                # Parse CSV data (Alpha Vantage returns CSV)
                lines = data.strip().split("\n")
                if (
                    len(lines) > 1 and "Error Message" not in data
                ):  # Has header and data
                    headers = lines[0].split(",")
                    logger.info(f"Alpha Vantage earnings headers: {headers}")

                    for line in lines[1:]:
                        try:
                            # Handle CSV parsing more carefully
                            values = []
                            current_value = ""
                            in_quotes = False

                            for char in line:
                                if char == '"':
                                    in_quotes = not in_quotes
                                elif char == "," and not in_quotes:
                                    values.append(current_value.strip('"'))
                                    current_value = ""
                                else:
                                    current_value += char
                            values.append(current_value.strip('"'))  # Add last value

                            if len(values) >= 3:
                                earnings_date = datetime.strptime(
                                    values[0], "%Y-%m-%d"
                                ).date()
                                if start_date <= earnings_date <= end_date:
                                    # Determine impact based on company size/importance
                                    symbol = values[1].upper()
                                    company_name = (
                                        values[2] if len(values) > 2 else symbol
                                    )

                                    # Major companies get high impact
                                    major_companies = [
                                        "AAPL",
                                        "MSFT",
                                        "GOOGL",
                                        "GOOG",
                                        "AMZN",
                                        "TSLA",
                                        "META",
                                        "NVDA",
                                        "JPM",
                                        "V",
                                        "UNH",
                                        "JNJ",
                                        "WMT",
                                        "PG",
                                        "HD",
                                        "MA",
                                        "DIS",
                                        "BAC",
                                        "XOM",
                                        "LLY",
                                    ]
                                    impact = (
                                        "high"
                                        if symbol in major_companies
                                        else "medium"
                                    )

                                    earnings.append(
                                        {
                                            "date": earnings_date.isoformat(),
                                            "symbol": symbol,
                                            "name": f"{company_name} Earnings",
                                            "company": company_name,
                                            "event_type": "earnings",
                                            "impact": impact,
                                            "source": "alpha_vantage",
                                            "timing": "pre_market",  # Most earnings are pre-market
                                            "estimate": values[3]
                                            if len(values) > 3
                                            else None,
                                            "currency": values[4]
                                            if len(values) > 4
                                            else "USD",
                                        }
                                    )
                        except (ValueError, IndexError) as e:
                            logger.warning(
                                f"Error parsing earnings line: {line[:50]}... Error: {e}"
                            )
                            continue

                    logger.info(f"Alpha Vantage: Found {len(earnings)} earnings events")
                else:
                    logger.warning(
                        "Alpha Vantage earnings: No valid data or API limit reached"
                    )

        except Exception as e:
            logger.warning(f"Failed to fetch Alpha Vantage earnings: {e}")

        # Try Finnhub as backup/supplement
        try:
            from_date = start_date.strftime("%Y-%m-%d")
            to_date = end_date.strftime("%Y-%m-%d")

            url = "https://finnhub.io/api/v1/calendar/earnings"
            params = {"from": from_date, "to": to_date, "token": self.finnhub_key}

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                earnings_data = data.get("earningsCalendar", [])

                # Track symbols we already have to avoid duplicates
                existing_symbols = {e["symbol"] + e["date"] for e in earnings}

                for earning in earnings_data:
                    symbol = earning.get("symbol", "").upper()
                    earning_date = earning.get("date", "")

                    # Skip if we already have this symbol+date combination
                    if symbol + earning_date in existing_symbols:
                        continue

                    # Determine impact
                    major_companies = [
                        "AAPL",
                        "MSFT",
                        "GOOGL",
                        "GOOG",
                        "AMZN",
                        "TSLA",
                        "META",
                        "NVDA",
                        "JPM",
                        "V",
                        "UNH",
                        "JNJ",
                        "WMT",
                        "PG",
                        "HD",
                        "MA",
                        "DIS",
                        "BAC",
                        "XOM",
                        "LLY",
                    ]
                    impact = "high" if symbol in major_companies else "medium"

                    earnings.append(
                        {
                            "date": earning_date,
                            "symbol": symbol,
                            "name": f"{symbol} Earnings",
                            "company": symbol,
                            "event_type": "earnings",
                            "impact": impact,
                            "source": "finnhub",
                            "timing": "after_market",
                            "estimate": earning.get("epsEstimate"),
                            "quarter": earning.get("quarter"),
                            "year": earning.get("year"),
                        }
                    )

                logger.info(
                    f"Finnhub: Added {len(earnings_data)} additional earnings events"
                )

        except Exception as e:
            logger.warning(f"Failed to fetch Finnhub earnings: {e}")

        # Sort by date and symbol
        earnings.sort(key=lambda x: (x["date"], x["symbol"]))
        logger.info(f"Total earnings events found: {len(earnings)}")

        return earnings

    def _get_economic_events(self, start_date: date, end_date: date) -> List[Dict]:
        """Get comprehensive economic data release events using Alpha Vantage economic indicators"""
        economic_events = []

        # Try to get real economic calendar data from Alpha Vantage
        economic_indicators = [
            {
                "function": "CPI",
                "name": "Consumer Price Index (CPI)",
                "impact": "high",
                "frequency": "monthly",
            },
            {
                "function": "RETAIL_SALES",
                "name": "Retail Sales",
                "impact": "medium",
                "frequency": "monthly",
            },
            {
                "function": "NONFARM_PAYROLL",
                "name": "Nonfarm Payrolls",
                "impact": "high",
                "frequency": "monthly",
            },
            {
                "function": "UNEMPLOYMENT",
                "name": "Unemployment Rate",
                "impact": "high",
                "frequency": "monthly",
            },
            {
                "function": "FEDERAL_FUNDS_RATE",
                "name": "Federal Funds Rate",
                "impact": "high",
                "frequency": "meeting",
            },
            {
                "function": "REAL_GDP",
                "name": "Real GDP",
                "impact": "high",
                "frequency": "quarterly",
            },
            {
                "function": "CONSUMER_SENTIMENT",
                "name": "Consumer Sentiment",
                "impact": "medium",
                "frequency": "monthly",
            },
        ]

        # Try to fetch actual release dates from Alpha Vantage (they sometimes have calendar data)
        for indicator in economic_indicators:
            try:
                url = "https://www.alphavantage.co/query"
                params = {
                    "function": indicator["function"],
                    "apikey": self.alpha_vantage_key,
                    "datatype": "json",
                }

                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()

                    # Look for the most recent data to estimate next release
                    if "data" in data:
                        latest_data = data["data"]
                        if latest_data and len(latest_data) > 0:
                            # Get the most recent release date
                            latest_date_str = latest_data[0].get("date", "")
                            if latest_date_str:
                                try:
                                    latest_date = datetime.strptime(
                                        latest_date_str, "%Y-%m-%d"
                                    ).date()

                                    # Estimate next release date based on frequency
                                    if indicator["frequency"] == "monthly":
                                        # Monthly data usually releases around the same day next month
                                        next_release = (
                                            self._estimate_next_monthly_release(
                                                latest_date
                                            )
                                        )
                                    elif indicator["frequency"] == "quarterly":
                                        # Quarterly data releases about 3 months later
                                        next_release = (
                                            self._estimate_next_quarterly_release(
                                                latest_date
                                            )
                                        )
                                    else:
                                        continue

                                    # Check if estimated date falls in our range
                                    if start_date <= next_release <= end_date:
                                        economic_events.append(
                                            {
                                                "date": next_release.isoformat(),
                                                "name": indicator["name"],
                                                "event_type": "economic_data",
                                                "impact": indicator["impact"],
                                                "source": "alpha_vantage_estimated",
                                                "timing": "morning",
                                                "frequency": indicator["frequency"],
                                                "latest_value": latest_data[0].get(
                                                    "value", "N/A"
                                                ),
                                            }
                                        )

                                except ValueError:
                                    continue

                # Small delay to respect API limits
                time.sleep(0.1)

            except Exception as e:
                logger.warning(
                    f"Failed to fetch {indicator['name']} from Alpha Vantage: {e}"
                )
                continue

        # Add well-known economic release dates (backup/supplement)
        known_releases = [
            # Monthly releases with typical dates
            {"name": "Consumer Price Index (CPI)", "typical_day": 10, "impact": "high"},
            {
                "name": "Producer Price Index (PPI)",
                "typical_day": 12,
                "impact": "medium",
            },
            {"name": "Retail Sales", "typical_day": 15, "impact": "medium"},
            {"name": "Industrial Production", "typical_day": 17, "impact": "medium"},
            {"name": "Housing Starts", "typical_day": 18, "impact": "low"},
            {"name": "Existing Home Sales", "typical_day": 20, "impact": "low"},
            {"name": "Durable Goods Orders", "typical_day": 25, "impact": "medium"},
            {
                "name": "Personal Income & Spending",
                "typical_day": 30,
                "impact": "medium",
            },
            {"name": "Consumer Confidence", "typical_day": 28, "impact": "medium"},
            {"name": "ISM Manufacturing PMI", "typical_day": 1, "impact": "medium"},
            {"name": "ISM Services PMI", "typical_day": 3, "impact": "medium"},
            {
                "name": "Initial Jobless Claims",
                "typical_day": "thursday",
                "impact": "medium",
            },  # Weekly on Thursdays
        ]

        # Track events we already have to avoid duplicates
        existing_events = {e["name"] + e["date"] for e in economic_events}

        # Add known releases for upcoming months
        current_date = start_date.replace(day=1)  # Start of month
        end_month = end_date.replace(day=1)

        while current_date <= end_month:
            for release in known_releases:
                try:
                    if release["typical_day"] == "thursday":
                        # Weekly Thursday releases (jobless claims)
                        week_start = current_date
                        while (
                            week_start <= end_date
                            and week_start.month == current_date.month
                        ):
                            if week_start.weekday() == 3:  # Thursday
                                if start_date <= week_start <= end_date:
                                    event_key = release["name"] + week_start.isoformat()
                                    if event_key not in existing_events:
                                        economic_events.append(
                                            {
                                                "date": week_start.isoformat(),
                                                "name": release["name"],
                                                "event_type": "economic_data",
                                                "impact": release["impact"],
                                                "source": "typical_schedule",
                                                "timing": "morning",
                                                "frequency": "weekly",
                                            }
                                        )
                            week_start += timedelta(days=1)
                    else:
                        # Monthly releases
                        event_date = date(
                            current_date.year,
                            current_date.month,
                            min(
                                release["typical_day"],
                                calendar.monthrange(
                                    current_date.year, current_date.month
                                )[1],
                            ),
                        )

                        if start_date <= event_date <= end_date:
                            event_key = release["name"] + event_date.isoformat()
                            if event_key not in existing_events:
                                economic_events.append(
                                    {
                                        "date": event_date.isoformat(),
                                        "name": release["name"],
                                        "event_type": "economic_data",
                                        "impact": release["impact"],
                                        "source": "typical_schedule",
                                        "timing": "morning",
                                        "frequency": "monthly",
                                    }
                                )

                except ValueError:
                    continue

            # Move to next month
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)

        # Sort by date
        economic_events.sort(key=lambda x: x["date"])
        logger.info(f"Found {len(economic_events)} economic events")

        return economic_events

    def _estimate_next_monthly_release(self, latest_date: date) -> date:
        """Estimate next monthly release date"""
        # Most monthly data releases around the same day of the following month
        if latest_date.month == 12:
            next_month = date(latest_date.year + 1, 1, latest_date.day)
        else:
            try:
                next_month = date(
                    latest_date.year, latest_date.month + 1, latest_date.day
                )
            except ValueError:
                # Handle month-end dates (e.g., Jan 31 -> Feb 28)
                next_month = date(
                    latest_date.year,
                    latest_date.month + 1,
                    calendar.monthrange(latest_date.year, latest_date.month + 1)[1],
                )
        return next_month

    def _estimate_next_quarterly_release(self, latest_date: date) -> date:
        """Estimate next quarterly release date"""
        # Quarterly data typically releases about 3 months later
        month = latest_date.month + 3
        year = latest_date.year

        if month > 12:
            month -= 12
            year += 1

        try:
            next_quarter = date(year, month, latest_date.day)
        except ValueError:
            # Handle month-end dates
            next_quarter = date(year, month, calendar.monthrange(year, month)[1])

        return next_quarter

    def _get_fed_events(self, start_date: date, end_date: date) -> List[Dict]:
        """Get comprehensive Federal Reserve events"""
        fed_events = []

        # FOMC meeting dates for 2024-2025 (these are scheduled in advance)
        fomc_meetings = [
            {
                "dates": ["2024-12-17", "2024-12-18"],
                "name": "FOMC Meeting",
                "press_conference": True,
            },
            {
                "dates": ["2025-01-28", "2025-01-29"],
                "name": "FOMC Meeting",
                "press_conference": True,
            },
            {
                "dates": ["2025-03-18", "2025-03-19"],
                "name": "FOMC Meeting",
                "press_conference": True,
            },
            {
                "dates": ["2025-04-29", "2025-04-30"],
                "name": "FOMC Meeting",
                "press_conference": False,
            },
            {
                "dates": ["2025-06-10", "2025-06-11"],
                "name": "FOMC Meeting",
                "press_conference": True,
            },
            {
                "dates": ["2025-07-29", "2025-07-30"],
                "name": "FOMC Meeting",
                "press_conference": True,
            },
            {
                "dates": ["2025-09-16", "2025-09-17"],
                "name": "FOMC Meeting",
                "press_conference": True,
            },
            {
                "dates": ["2025-10-28", "2025-10-29"],
                "name": "FOMC Meeting",
                "press_conference": False,
            },
            {
                "dates": ["2025-12-09", "2025-12-10"],
                "name": "FOMC Meeting",
                "press_conference": True,
            },
        ]

        # Add FOMC meetings and related events
        for meeting in fomc_meetings:
            for date_str in meeting["dates"]:
                try:
                    event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    if start_date <= event_date <= end_date:
                        # Main FOMC meeting
                        fed_events.append(
                            {
                                "date": event_date.isoformat(),
                                "name": meeting["name"],
                                "event_type": "federal_reserve",
                                "impact": "high",
                                "source": "federal_reserve_schedule",
                                "timing": "afternoon",
                                "details": "Federal Open Market Committee meeting",
                            }
                        )

                        # Press conference (if applicable)
                        if (
                            meeting["press_conference"]
                            and date_str == meeting["dates"][-1]
                        ):  # Last day
                            fed_events.append(
                                {
                                    "date": event_date.isoformat(),
                                    "name": "Fed Chair Press Conference",
                                    "event_type": "federal_reserve",
                                    "impact": "high",
                                    "source": "federal_reserve_schedule",
                                    "timing": "afternoon",
                                    "details": "Fed Chair Powell press conference following FOMC meeting",
                                }
                            )

                        # FOMC Minutes release (3 weeks later)
                        minutes_date = event_date + timedelta(weeks=3)
                        if start_date <= minutes_date <= end_date:
                            fed_events.append(
                                {
                                    "date": minutes_date.isoformat(),
                                    "name": "FOMC Minutes Release",
                                    "event_type": "federal_reserve",
                                    "impact": "medium",
                                    "source": "federal_reserve_schedule",
                                    "timing": "afternoon",
                                    "details": f"Minutes from {meeting['name']} on {date_str}",
                                }
                            )

                except ValueError:
                    continue

        # Add other regular Fed events
        regular_events = [
            {
                "name": "Beige Book Release",
                "frequency": 8,
                "impact": "medium",
            },  # 8 times per year
            {
                "name": "Fed Chair Congressional Testimony",
                "frequency": 2,
                "impact": "high",
            },  # Semi-annual
            {
                "name": "Financial Stability Report",
                "frequency": 2,
                "impact": "medium",
            },  # Semi-annual
        ]

        # Add estimated dates for regular events
        current_date = start_date
        while current_date <= end_date:
            # Beige Book typically releases 2 weeks before FOMC meetings
            for meeting in fomc_meetings:
                try:
                    meeting_date = datetime.strptime(
                        meeting["dates"][0], "%Y-%m-%d"
                    ).date()
                    beige_book_date = meeting_date - timedelta(weeks=2)

                    if start_date <= beige_book_date <= end_date:
                        fed_events.append(
                            {
                                "date": beige_book_date.isoformat(),
                                "name": "Fed Beige Book Release",
                                "event_type": "federal_reserve",
                                "impact": "medium",
                                "source": "federal_reserve_schedule",
                                "timing": "afternoon",
                                "details": "Federal Reserve Beige Book economic conditions report",
                            }
                        )
                except ValueError:
                    continue

            current_date += timedelta(days=30)  # Check monthly

        # Try to get Fed-related news from our news APIs for speeches and events
        try:
            # This would integrate with existing news fetching
            # For now, we'll add typical Fed speech dates
            fed_speech_dates = self._estimate_fed_speech_dates(start_date, end_date)
            fed_events.extend(fed_speech_dates)

        except Exception as e:
            logger.warning(f"Failed to fetch Fed speeches: {e}")

        # Sort by date and remove duplicates
        fed_events.sort(key=lambda x: (x["date"], x["name"]))

        # Remove duplicate events (same date + name)
        unique_events = []
        seen = set()
        for event in fed_events:
            event_key = event["date"] + event["name"]
            if event_key not in seen:
                unique_events.append(event)
                seen.add(event_key)

        logger.info(f"Found {len(unique_events)} Federal Reserve events")
        return unique_events

    def _estimate_fed_speech_dates(
        self, start_date: date, end_date: date
    ) -> List[Dict]:
        """Estimate Fed official speech dates based on typical patterns"""
        speech_events = []

        # Fed officials typically speak at various economic conferences
        # We'll estimate some common speaking engagement patterns
        common_venues = [
            {"name": "Economic Club Speech", "frequency": "monthly"},
            {"name": "Jackson Hole Symposium", "month": 8, "impact": "high"},  # August
            {"name": "Fed Governor Speech", "frequency": "biweekly"},
        ]

        current_date = start_date
        while current_date <= end_date:
            # Jackson Hole Symposium (late August)
            if current_date.month == 8 and 20 <= current_date.day <= 30:
                speech_events.append(
                    {
                        "date": current_date.isoformat(),
                        "name": "Jackson Hole Economic Symposium",
                        "event_type": "federal_reserve",
                        "impact": "high",
                        "source": "estimated_schedule",
                        "timing": "all_day",
                        "details": "Annual Fed symposium in Jackson Hole, Wyoming",
                    }
                )

            # Monthly economic club speeches (estimate mid-month)
            if current_date.day == 15:
                speech_events.append(
                    {
                        "date": current_date.isoformat(),
                        "name": "Fed Official Economic Speech",
                        "event_type": "federal_reserve",
                        "impact": "low",
                        "source": "estimated_schedule",
                        "timing": "varies",
                        "details": "Estimated Fed official speaking engagement",
                    }
                )

            current_date += timedelta(days=1)

        return speech_events

    def _get_options_expiration(self, start_date: date, end_date: date) -> List[Dict]:
        """Get options expiration dates"""
        expiration_events = []

        # Check each Friday in the date range
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() == 4:  # Friday
                # Weekly options expire every Friday
                expiration_events.append(
                    {
                        "date": current_date.isoformat(),
                        "name": "Weekly Options Expiration",
                        "event_type": "options_expiration",
                        "impact": "medium",
                        "source": "calculated",
                        "timing": "market_close",
                    }
                )

                # Monthly options expire on 3rd Friday
                if 15 <= current_date.day <= 21:  # 3rd Friday of month
                    expiration_events.append(
                        {
                            "date": current_date.isoformat(),
                            "name": "Monthly Options Expiration",
                            "event_type": "options_expiration",
                            "impact": "high",
                            "source": "calculated",
                            "timing": "market_close",
                        }
                    )

            current_date += timedelta(days=1)

        return expiration_events

    def _get_market_holidays(self, start_date: date, end_date: date) -> List[Dict]:
        """Get market holidays"""
        holidays = []

        # US Market holidays for 2024-2025
        market_holidays = [
            ("2024-12-25", "Christmas Day"),
            ("2025-01-01", "New Year's Day"),
            ("2025-01-20", "Martin Luther King Jr. Day"),
            ("2025-02-17", "Presidents Day"),
            ("2025-04-18", "Good Friday"),
            ("2025-05-26", "Memorial Day"),
            ("2025-06-19", "Juneteenth"),
            ("2025-07-04", "Independence Day"),
            ("2025-09-01", "Labor Day"),
            ("2025-11-27", "Thanksgiving"),
            ("2025-12-25", "Christmas Day"),
        ]

        for date_str, name in market_holidays:
            try:
                holiday_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if start_date <= holiday_date <= end_date:
                    holidays.append(
                        {
                            "date": holiday_date.isoformat(),
                            "name": name,
                            "event_type": "market_holiday",
                            "impact": "high",
                            "source": "nyse_nasdaq",
                            "timing": "all_day",
                        }
                    )
            except ValueError:
                continue

        return holidays

    def _get_dividend_events(self, start_date: date, end_date: date) -> List[Dict]:
        """Get dividend ex-dates for watchlist stocks"""
        dividend_events = []

        # This would ideally fetch from Alpha Vantage or another API
        # For now, return empty list - can be enhanced later

        return dividend_events

    def _get_ipo_events(self, start_date: date, end_date: date) -> List[Dict]:
        """Get IPO events"""
        ipo_events = []

        # This would ideally fetch from financial news APIs
        # For now, return empty list - can be enhanced later

        return ipo_events

    def _organize_by_day(self, start_date: date, end_date: date) -> Dict[str, List]:
        """Organize all events by day for easy calendar display"""
        # This would be called after all events are fetched
        # For now, return empty structure
        daily_events = {}

        current_date = start_date
        while current_date <= end_date:
            daily_events[current_date.isoformat()] = []
            current_date += timedelta(days=1)

        return daily_events

    def get_events_for_date(self, target_date: date) -> List[Dict]:
        """Get all events for a specific date"""
        weekly_events = self.get_weekly_events(
            target_date - timedelta(days=target_date.weekday())
        )

        all_events = []
        for category in [
            "earnings",
            "economic",
            "federal_reserve",
            "options_expiration",
            "market_holidays",
        ]:
            events = weekly_events.get(category, [])
            for event in events:
                if event.get("date") == target_date.isoformat():
                    all_events.append(event)

        return all_events

    def get_earnings_for_symbols(
        self, symbols: List[str], days_ahead: int = 30
    ) -> List[Dict]:
        """Get earnings events for specific symbols"""
        end_date = date.today() + timedelta(days=days_ahead)
        start_date = date.today()

        earnings = self._get_earnings_events(start_date, end_date)

        # Filter for requested symbols
        symbol_earnings = []
        for earning in earnings:
            if earning.get("symbol", "").upper() in [s.upper() for s in symbols]:
                symbol_earnings.append(earning)

        return symbol_earnings
