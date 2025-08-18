"""
Market Calendar for handling trading calendar functionality.
"""

from datetime import datetime, timedelta


class MarketCalendar:
    """Handles market calendar operations."""
    
    def __init__(self):
        """Initialize the market calendar."""
        pass
    
    def is_trading_day(self, date=None):
        """Check if a given date is a trading day."""
        if date is None:
            date = datetime.now()
        
        # Simple check - weekends are not trading days
        if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Add more sophisticated checks here if needed
        return True
    
    def get_next_trading_day(self, date=None):
        """Get the next trading day."""
        if date is None:
            date = datetime.now()
        
        next_day = date + timedelta(days=1)
        while not self.is_trading_day(next_day):
            next_day += timedelta(days=1)
        
        return next_day
