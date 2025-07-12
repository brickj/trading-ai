#!/usr/bin/env python3
"""
Scalping Analysis Runner
Runs the morning scalping analysis for stocks and cryptocurrencies.
Designed to be executed as a scheduled task between 9:30-10:00 AM ET.
"""

import sys
import os
import logging
from datetime import datetime, timezone, timedelta
import pytz

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.scalping_analyzer import scalping_analyzer
from src.core.logger import log_info, log_error, log_warning
from src.core.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scalping_analysis.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def is_market_hours():
    """Check if it's currently market hours (9:30 AM - 4:00 PM ET, weekdays)"""
    et_tz = pytz.timezone('US/Eastern')
    now_et = datetime.now(et_tz)
    
    # Check if it's a weekday (Monday = 0, Sunday = 6)
    if now_et.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Check if it's between 9:30 AM and 4:00 PM ET
    market_start = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    market_end = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return market_start <= now_et <= market_end

def main():
    """Main function to run scalping analysis"""
    try:
        log_info("Starting scalping analysis runner...")
        
        # Check if it's market hours (optional - can be disabled for testing)
        if not is_market_hours():
            log_warning("Not during market hours. Analysis will still run for testing purposes.")
        
        # Setup database tables if needed
        log_info("Setting up scalping tables...")
        if not scalping_analyzer.create_tables_if_not_exists():
            log_error("Failed to setup scalping tables")
            return False
        
        # Run the analysis
        log_info("Running morning scalping analysis...")
        opportunities = scalping_analyzer.run_morning_scalping_analysis()
        
        # Log results
        log_info(f"Scalping analysis completed. Found {len(opportunities)} opportunities.")
        
        # Log details of each opportunity
        for opp in opportunities:
            log_info(f"Opportunity: {opp['ticker']} - {opp['recommendation']} "
                    f"(Volume: {opp.get('volume_ratio', 0):.2f}x, "
                    f"Change: {opp.get('price_change_pct', 0):.2f}%, "
                    f"Sentiment: {opp.get('sentiment', 'Unknown')})")
        
        return True
        
    except Exception as e:
        log_error(f"Error in scalping analysis runner: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 