#!/usr/bin/env python3
"""
Weekly Plan Populator - Populates weekly market events table
"""

from datetime import datetime, timedelta, date
from typing import Dict, List
import random
from ..core.database import get_db_connection, ensure_weekly_plan_events_table
from ..core.logger import log_info, log_error

class WeeklyPlanPopulator:
    """Populates weekly market events with sample data"""
    
    def __init__(self):
        self.ensure_table_exists()
    
    def ensure_table_exists(self):
        """Ensure the weekly_plan_events table exists"""
        try:
            ensure_weekly_plan_events_table()
            log_info("Weekly plan events table ensured")
        except Exception as e:
            log_error(f"Failed to ensure weekly_plan_events table: {e}")
    
    def populate_advance_data(self, weeks_back: int = 8, weeks_ahead: int = 8) -> Dict[str, int]:
        """Populate the table with sample market events for past and future weeks"""
        try:
            log_info(f"Starting weekly plan population: {weeks_back} weeks back, {weeks_ahead} weeks ahead")
            
            # Calculate date range
            start_date = datetime.now().date() - timedelta(weeks=weeks_back)
            end_date = datetime.now().date() + timedelta(weeks=weeks_ahead)
            
            # Generate sample events
            events = self._generate_sample_events(start_date, end_date)
            
            # Insert events into database
            inserted_count = self._insert_events(events)
            
            result = {
                "earnings": len([e for e in events if e["event_type"] == "earnings"]),
                "federal_reserve": len([e for e in events if e["event_type"] == "federal_reserve"]),
                "economic": len([e for e in events if e["event_type"] == "economic"]),
                "options_expiration": len([e for e in events if e["event_type"] == "options_expiration"]),
                "market_holidays": len([e for e in events if e["event_type"] == "market_holidays"]),
                "total_inserted": inserted_count
            }
            
            log_info(f"Weekly plan population completed: {inserted_count} events inserted")
            return result
            
        except Exception as e:
            log_error(f"Weekly plan population failed: {e}")
            return {"error": str(e)}
    
    def _generate_sample_events(self, start_date: date, end_date: date) -> List[Dict]:
        """Generate sample market events for the date range"""
        events = []
        current_date = start_date
        
        # Sample data
        # Get earnings companies from watchlist database
        from ..core.watchlist_manager import watchlist_manager
        earnings_companies = watchlist_manager.get_stocks()
        economic_events = [
            "Non-Farm Payrolls", "CPI Inflation Data", "GDP Growth Rate", "Retail Sales",
            "Consumer Confidence", "Manufacturing PMI", "Unemployment Claims", "Housing Starts"
        ]
        fed_events = [
            "FOMC Meeting", "Fed Chair Speech", "Interest Rate Decision", "Fed Minutes Release"
        ]
        
        while current_date <= end_date:
            # Skip weekends for most events
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                
                # Earnings events (randomly distributed)
                if random.random() < 0.3:  # 30% chance per weekday
                    company = random.choice(earnings_companies)
                    events.append({
                        "event_date": current_date,
                        "event_type": "earnings",
                        "event_name": f"{company} Earnings Report",
                        "impact": random.choice(["high", "medium", "low"]),
                        "symbol": company,
                        "timing": random.choice(["pre_market", "after_hours", "all_day"])
                    })
                
                # Economic events (less frequent)
                if random.random() < 0.15:  # 15% chance per weekday
                    event_name = random.choice(economic_events)
                    events.append({
                        "event_date": current_date,
                        "event_type": "economic",
                        "event_name": event_name,
                        "impact": random.choice(["high", "medium", "low"]),
                        "symbol": None,
                        "timing": "all_day"
                    })
                
                # Fed events (rare)
                if random.random() < 0.05:  # 5% chance per weekday
                    event_name = random.choice(fed_events)
                    events.append({
                        "event_date": current_date,
                        "event_type": "federal_reserve",
                        "event_name": event_name,
                        "impact": "high",
                        "symbol": None,
                        "timing": "all_day"
                    })
            
            # Options expiration (every third Friday)
            if current_date.weekday() == 4 and current_date.day >= 15 and current_date.day <= 21:
                events.append({
                    "event_date": current_date,
                    "event_type": "options_expiration",
                    "event_name": "Monthly Options Expiration",
                    "impact": "medium",
                    "symbol": None,
                    "timing": "all_day"
                })
            
            # Market holidays (specific dates)
            if self._is_market_holiday(current_date):
                events.append({
                    "event_date": current_date,
                    "event_type": "market_holidays",
                    "event_name": self._get_holiday_name(current_date),
                    "impact": "high",
                    "symbol": None,
                    "timing": "all_day"
                })
            
            current_date += timedelta(days=1)
        
        return events
    
    def _is_market_holiday(self, check_date: date) -> bool:
        """Check if a date is a market holiday"""
        # Simple holiday check (you can expand this)
        holidays = [
            (1, 1),   # New Year's Day
            (7, 4),   # Independence Day
            (12, 25), # Christmas Day
        ]
        
        for month, day in holidays:
            if check_date.month == month and check_date.day == day:
                return True
        
        # Check for Memorial Day (last Monday in May)
        if check_date.month == 5 and check_date.weekday() == 0:
            # Check if it's the last Monday of May
            next_week = check_date + timedelta(days=7)
            if next_week.month != 5:
                return True
        
        return False
    
    def _get_holiday_name(self, holiday_date: date) -> str:
        """Get the name of a market holiday"""
        if holiday_date.month == 1 and holiday_date.day == 1:
            return "New Year's Day"
        elif holiday_date.month == 7 and holiday_date.day == 4:
            return "Independence Day"
        elif holiday_date.month == 12 and holiday_date.day == 25:
            return "Christmas Day"
        elif holiday_date.month == 5 and holiday_date.weekday() == 0:
            return "Memorial Day"
        else:
            return "Market Holiday"
    
    def _get_week_start_date(self, event_date: date) -> date:
        """Get the Monday of the week for a given date"""
        days_since_monday = event_date.weekday()  # Monday = 0, Sunday = 6
        return event_date - timedelta(days=days_since_monday)
    
    def _insert_events(self, events: List[Dict]) -> int:
        """Insert events into the database"""
        if not events:
            return 0
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Clear existing events in the date range
                    if events:
                        start_date = min(event["event_date"] for event in events)
                        end_date = max(event["event_date"] for event in events)
                        cur.execute(
                            "DELETE FROM weekly_plan_events WHERE event_date BETWEEN %s AND %s",
                            (start_date, end_date)
                        )
                    
                    # Insert new events with correct table structure
                    insert_query = """
                        INSERT INTO weekly_plan_events 
                        (week_start_date, event_date, event_name, event_type, impact, source, symbol, timing)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    event_data = []
                    for event in events:
                        week_start = self._get_week_start_date(event["event_date"])
                        event_data.append((
                            week_start,
                            event["event_date"],
                            event["event_name"],
                            event["event_type"],
                            event["impact"],
                            "sample_data",  # source
                            event["symbol"],
                            event["timing"]
                        ))
                    
                    cur.executemany(insert_query, event_data)
                    conn.commit()
                    
                    return len(events)
                    
        except Exception as e:
            log_error(f"Failed to insert events: {e}")
            return 0

def populate_weekly_plan_events():
    """Convenience function to populate weekly plan events"""
    populator = WeeklyPlanPopulator()
    return populator.populate_advance_data(weeks_back=8, weeks_ahead=8)
