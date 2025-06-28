#!/usr/bin/env python3
"""
Application Startup Module
Handles daily updates of historical stock data when the application starts.
Checks if data is current and updates missing data with clear progress messages.
"""
from src.data.data_fetcher import DataFetcher
from src.utils.populate_historical_data import HistoricalDataPopulator
from src.core.logger import log_error, log_system_event, log_debug
from src.core.database import get_db_connection
import sys
import os
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import psycopg2.extras
from src.core.config import Config
import pytz
import time
import requests
import yfinance as yf
from .database import get_system_flag, set_system_flag

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def get_last_trading_day() -> date:
    """
    Get the last trading day (excluding weekends and holidays).
    If today is a weekend or before market close, use the previous weekday.
    """
    # Use US/Eastern for market time
    eastern = pytz.timezone("US/Eastern")
    now = datetime.now(eastern)
    today = now.date()

    # First, try to get the last trading day from an API
    last_trading = get_last_trading_day_from_api()
    if last_trading:
        print(f"[DEBUG] Using last trading day from API: {last_trading}")
        return last_trading

    # If API fails, try using Ollama to determine the last trading day
    last_trading = get_last_trading_day_from_ollama()
    if last_trading:
        print(f"[DEBUG] Using last trading day from Ollama: {last_trading}")
        return last_trading

    # Fallback to basic logic if both API and Ollama fail
    print("[DEBUG] Using basic logic for last trading day")
    
    # If today is Saturday (5) or Sunday (6), go back to Friday
    if today.weekday() >= 5:  # Saturday = 5, Sunday = 6
        days_back = today.weekday() - 4  # Go back to Friday
        return today - timedelta(days=days_back)
    
    # If today is a weekday, check if it's before market close (4 PM ET)
    if now.hour < 16:  # Before 4 PM ET
        # Use previous trading day
        if today.weekday() == 0:  # Monday
            return today - timedelta(days=3)  # Go back to Friday
        else:
            return today - timedelta(days=1)
    
    # After market close, today is the last trading day
    return today


def get_last_trading_day_from_api() -> Optional[date]:
    """Try to get the last trading day from various APIs."""
    try:
        # Try Yahoo Finance API to get the last trading day
        # Use SPY (S&P 500 ETF) to get the last trading day
        print("[DEBUG] Trying Yahoo Finance API for last trading day...")
        
        # Get SPY data for the last few days to find the last trading day
        spy = yf.Ticker("SPY")
        
        # Get data for the last 10 days to ensure we find the last trading day
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=10)
        
        hist = spy.history(start=start_date, end=end_date)
        
        if not hist.empty:
            # Get the last date with actual trading data
            last_trading_date = hist.index[-1].strftime('%Y-%m-%d')
            last_trading_date = datetime.strptime(last_trading_date, '%Y-%m-%d').date()
            print(f"[DEBUG] Yahoo Finance returned last trading day: {last_trading_date}")
            return last_trading_date
        else:
            print("[DEBUG] No data returned from Yahoo Finance")
            return None
            
    except Exception as e:
        print(f"⚠️ Yahoo Finance API call for last trading day failed: {e}")
        
        # Fallback: Try Alpha Vantage API for market status
        try:
            api_key = Config.ALPHA_VANTAGE_API_KEY
            if api_key:
                url = f"https://www.alphavantage.co/query?function=MARKET_STATUS&apikey={api_key}"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    print(f"[DEBUG] Alpha Vantage fallback response: {data}")
                    
                    if 'markets' in data:
                        # Find US market
                        for market in data['markets']:
                            if market.get('region') == 'United States':
                                current_status = market.get('current_status', '')
                                print(f"[DEBUG] US Market status from Alpha Vantage: {current_status}")
                                
                                # If market is closed, we need to determine the last trading day
                                if current_status == 'closed':
                                    print("[DEBUG] Market is closed, but Alpha Vantage doesn't provide last trading day")
                                    return None
                                
                                # If market is open, use today's date
                                elif current_status == 'open':
                                    today = datetime.now().date()
                                    print(f"[DEBUG] Market open, using today: {today}")
                                    return today
        except Exception as e2:
            print(f"⚠️ Alpha Vantage fallback also failed: {e2}")
    
    return None


def get_last_trading_day_from_ollama() -> Optional[date]:
    """Use Ollama to determine the last trading day."""
    try:
        from src.core.sentiment_analyzer import SentimentAnalyzer
        
        # Create a simple prompt to get the last trading day
        prompt = """
        What was the last trading day for the US stock market? 
        Consider that:
        - Markets are closed on weekends (Saturday and Sunday)
        - Markets are closed on major US holidays
        - Today's date is {today}
        
        Please respond with just the date in YYYY-MM-DD format, nothing else.
        """.format(today=datetime.now().strftime('%Y-%m-%d'))
        
        # Use the sentiment analyzer's Ollama client
        sentiment_analyzer = SentimentAnalyzer()
        
        # Try to get response from Ollama using the internal method
        messages = [{"role": "user", "content": prompt}]
        response_data = sentiment_analyzer._call_ollama_api(messages, max_tokens=50)
        
        if response_data and 'choices' in response_data:
            response = response_data['choices'][0]['message']['content']
            
            # Parse the response to extract the date
            import re
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', response)
            if date_match:
                date_str = date_match.group()
                return datetime.strptime(date_str, '%Y-%m-%d').date()
        
    except Exception as e:
        print(f"⚠️ Ollama call for last trading day failed: {e}")
    
    return None


class StartupManager:
    """Manages application startup tasks including daily data updates."""

    def __init__(self):
        self.populator = HistoricalDataPopulator()
        self.data_fetcher = DataFetcher()
        self.update_threshold_days = 2  # Consider data stale if older than 2 days

    def get_current_sp500_symbols(self) -> List[str]:
        """Get the current S&P 500 symbols dynamically."""
        return self.data_fetcher.get_current_sp500_symbols()

    def check_market_hours(self) -> bool:
        """Check if it's currently market hours (simplified check)."""
        now = datetime.now()
        # Simple check: Monday-Friday, 9:30 AM - 4:00 PM EST
        # This is a basic implementation - you might want to add holiday checks
        if now.weekday() >= 5:  # Saturday/Sunday
            return False
        # For now, assume market is open during weekdays
        return True

    def get_latest_data_date(self, symbol: str) -> Optional[datetime]:
        """Get the latest date for which we have data for a symbol."""
        try:
            # Use direct connection instead of connection pool to avoid KeyError: 0
            conn = psycopg2.connect(
                Config.get_database_url(), 
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT MAX(date) as max
                    FROM historical_data
                    WHERE symbol = %s
                """,
                    (symbol,),
                )
                result = cur.fetchone()
                log_debug(f"get_latest_data_date for {symbol}: result={result}, type={type(result)}")
                if result:
                    if isinstance(result, dict):
                        log_debug(f"Result is dict, keys={list(result.keys())}")
                        return result.get('max')
                    elif isinstance(result, (tuple, list)):
                        log_debug(f"Result is tuple/list, length={len(result)}, value={result}")
                        return result[0]
                    else:
                        log_debug(f"Result is unknown type: {type(result)}")
                        return result
                return None
        except Exception as e:
            log_debug(f"Exception in get_latest_data_date for {symbol}: type={type(e)}, value={e}")
            log_error(f"Error getting latest data date for {symbol}: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()

    def needs_update(self, symbol: str) -> bool:
        """Check if a symbol needs data update."""
        latest_date = self.get_latest_data_date(symbol)
        if latest_date is None:
            # No data exists - needs full update
            return True
        # Check if data is recent enough
        days_since_latest = (datetime.now().date() - latest_date).days
        return days_since_latest > self.update_threshold_days

    def get_symbols_needing_update(self) -> List[str]:
        """Get list of symbols that need data updates."""
        symbols_needing_update = []
        print("🔍 Checking which stocks need data updates...")
        # Get current S&P 500 symbols dynamically
        current_sp500_symbols = self.get_current_sp500_symbols()
        print(f"📊 Found {len(current_sp500_symbols)} current S&P 500 stocks")
        for symbol in current_sp500_symbols:
            if self.needs_update(symbol):
                symbols_needing_update.append(symbol)
        return symbols_needing_update

    def update_symbol_data(self, symbol: str) -> Dict:
        """Update data for a single symbol."""
        result = {
            "symbol": symbol,
            "status": "success",
            "records_added": 0,
            "error": None,
        }
        try:
            print(f"  📊 Updating {symbol}...")
            # Check what data we need
            latest_date = self.get_latest_data_date(symbol)
            if latest_date is None:
                # No data exists - fetch 6 months of data
                print(f"    ⚡ No existing data - fetching 6 months for {symbol}")
                last_trading_day = get_last_trading_day()
                start_date = last_trading_day - timedelta(days=180)  # 6 months
                data = self.populator.fetch_yahoo_finance_data(
                    symbol,
                    datetime.combine(start_date, datetime.min.time()),
                    datetime.combine(last_trading_day, datetime.min.time()),
                )
            else:
                # Fetch only missing data
                start_date = latest_date + timedelta(days=1)
                last_trading_day = get_last_trading_day()
                
                # Skip if we're trying to fetch weekend data
                if start_date.weekday() >= 5:  # Saturday or Sunday
                    print(f"    ✅ {symbol} is already up to date (next update would be on weekend)")
                    result["status"] = "skipped"
                    return result
                
                if start_date > last_trading_day:
                    print(f"    ✅ {symbol} is already up to date")
                    result["status"] = "skipped"
                    return result
                
                # Ensure we're not trying to fetch a very small date range
                days_diff = (last_trading_day - start_date).days
                if days_diff < 1:
                    print(f"    ✅ {symbol} is already up to date (only {days_diff} days difference)")
                    result["status"] = "skipped"
                    return result
                
                # Only fetch if we have actual trading days to fetch
                if start_date <= last_trading_day:
                    print(f"    🔄 Fetching missing data from {start_date} to {last_trading_day} ({days_diff} days)")
                    data = self.populator.fetch_yahoo_finance_data(
                        symbol,
                        datetime.combine(start_date, datetime.min.time()),
                        datetime.combine(last_trading_day, datetime.min.time()),
                    )
                else:
                    print(f"    ✅ {symbol} is already up to date")
                    result["status"] = "skipped"
                    return result
            if data:
                records_added = self.populator.store_historical_data(symbol, data)
                result["records_added"] = records_added
                print(f"    ✅ Added {records_added} records for {symbol}")
            else:
                result["status"] = "failed"
                result["error"] = "No data received from API"
                print(f"    ❌ Failed to get data for {symbol}")
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"    ❌ Error updating {symbol}: {e}")
        return result

    def update_sp500_symbols_and_historical_data(self):
        """
        Update S&P 500 symbols table and fetch historical data for new symbols.
        Note: This is optional since we now use Alpha Vantage TOP_GAINERS_LOSERS API
        """
        print("\n🔄 Checking for S&P 500 symbol updates...")
        old_symbols = set()
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT symbol FROM sp500_symbols")
                    old_symbols = {row[0] for row in cur.fetchall()}
        except Exception as e:
            log_debug(f"S&P 500 symbols table not available: {e}")
            print("⚠️ S&P 500 symbols table not available - using Alpha Vantage TOP_GAINERS_LOSERS instead")
            return  # Exit early if table is not available
        
        self.data_fetcher.update_sp500_symbols_table()
        # Get new symbols after update
        new_symbols = set()
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT symbol FROM sp500_symbols")
                    new_symbols = {row[0] for row in cur.fetchall()}
        except Exception as e:
            log_debug(f"Failed to get updated symbols: {e}")
            return
        
        added_symbols = new_symbols - old_symbols
        if added_symbols:
            print(f"🆕 New S&P 500 symbols detected: {added_symbols}")
            for symbol in added_symbols:
                self.data_fetcher.fetch_and_store_historical_data_for_symbol(symbol, months=12)
        else:
            print("✅ No new S&P 500 symbols.")

    def run_daily_update(self) -> Dict:
        """
        Run the daily update process, including S&P 500 symbol check.
        """
        self.update_sp500_symbols_and_historical_data()
        print("\n" + "=" * 80)
        print("🚀 TRADING AI - DAILY STOCK DATA UPDATE")
        print("=" * 80)
        print(f"📅 Update started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        # Get current S&P 500 symbols dynamically
        current_sp500_symbols = self.get_current_sp500_symbols()
        print(f"🏢 Checking {len(current_sp500_symbols)} current S&P 500 stocks")
        print()
        # Check which symbols need updates
        symbols_needing_update = self.get_symbols_needing_update()
        if not symbols_needing_update:
            print("✅ All stocks are up to date! No updates needed.")
            return {
                "status": "success",
                "updated": 0,
                "skipped": len(current_sp500_symbols),
                "failed": 0,
                "total_records_added": 0,
            }
        print(f"🔄 Found {len(symbols_needing_update)} stocks needing updates:")
        for symbol in symbols_needing_update[:10]:  # Show first 10
            print(f"   • {symbol}")
        if len(symbols_needing_update) > 10:
            print(f"   ... and {len(symbols_needing_update) - 10} more")
        print()
        # Update each symbol
        results = []
        successful = 0
        failed = 0
        skipped = 0
        total_records = 0
        
        # Limit the number of symbols to process to prevent memory issues
        max_symbols_to_process = 50  # Process only first 50 symbols
        symbols_to_process = symbols_needing_update[:max_symbols_to_process]
        
        if len(symbols_needing_update) > max_symbols_to_process:
            print(f"⚠️ Limiting processing to first {max_symbols_to_process} symbols to prevent memory issues")
            print(f"📊 Remaining {len(symbols_needing_update) - max_symbols_to_process} symbols will be processed in next run")
        
        for i, symbol in enumerate(symbols_to_process, 1):
            print(f"[{i}/{len(symbols_to_process)}] ", end="")
            result = self.update_symbol_data(symbol)
            results.append(result)
            if result["status"] == "success":
                successful += 1
                total_records += result["records_added"]
            elif result["status"] == "skipped":
                skipped += 1
            else:
                failed += 1
            # Rate limiting between API calls
            if i < len(symbols_to_process):
                print("    ⏱️ Waiting for rate limit...")
                time.sleep(self.populator.rate_limit_delay)
        # Print summary
        print("\n" + "=" * 80)
        print("📊 DAILY UPDATE SUMMARY")
        print("=" * 80)
        print(f"✅ Successfully updated: {successful} stocks")
        print(f"⏭️ Skipped (already current): {skipped} stocks")
        print(f"❌ Failed: {failed} stocks")
        print(f"📈 Total records added: {total_records:,}")
        print(f"⏱️ Update completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        # Log the update
        log_system_event(
            f"Daily update completed: {successful} updated, {skipped} skipped, {failed} failed",
            "INFO",
        )
        return {
            "status": "success" if failed == 0 else "partial",
            "updated": successful,
            "skipped": skipped,
            "failed": failed,
            "total_records_added": total_records,
            "results": results,
        }

    def ensure_database_ready(self):
        """Ensure the database is ready for the application."""
        try:
            print("🔧 Ensuring database is ready...")
            # Create historical_data table if it doesn't exist
            self.populator.create_historical_data_table()
            print("✅ Database is ready")
        except Exception:
            log_error("Database setup failed: {e}")
            print("❌ Database setup failed: {e}")
            raise

    def ensure_2_year_historical_data(self):
        """
        Ensure all S&P 500 symbols have 2 years of historical data.
        Only runs once per day using a database flag.
        """
        flag_name = "historical_data_2year_update_date"
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Check if we already ran today using database flag
        last_update = get_system_flag(flag_name)
        if last_update == today:
            print(f"✅ 2-year historical data check already performed today ({today})")
            log_system_event(f"2-year historical data check skipped (already updated today: {today})")
            return
        
        print("\n" + "=" * 80)
        print("📊 ENSURING 2-YEAR HISTORICAL DATA FOR ALL S&P 500 SYMBOLS")
        print("=" * 80)
        
        try:
            # Get symbols missing 2 years of data
            missing_symbols = self.get_missing_symbols_for_2_years()
            
            if not missing_symbols:
                print("✅ All S&P 500 symbols already have 2 years of historical data!")
                # Still mark as completed today in database
                set_system_flag(flag_name, today, "Date when 2-year historical data check was last performed")
                log_system_event(f"2-year historical data check completed - all symbols up to date for {today}")
                return
            
            print(f"📊 Found {len(missing_symbols)} S&P 500 symbols missing 2 years of historical data")
            print("🔄 Loading historical data for the last 2 years (730 days)...")
            
            success_count = 0
            error_count = 0
            
            for i, symbol in enumerate(missing_symbols, 1):
                try:
                    print(f"[{i}/{len(missing_symbols)}] Loading 2 years of data for {symbol}...")
                    self.data_fetcher.fetch_and_store_historical_data_for_symbol(symbol, months=24)
                    success_count += 1
                    print(f"✅ Loaded data for {symbol}")
                except Exception as e:
                    error_count += 1
                    print(f"❌ Failed to load data for {symbol}: {e}")
            
            print(f"\n📈 2-Year Historical Data Summary:")
            print(f"   ✅ Successfully loaded: {success_count} symbols")
            print(f"   ❌ Failed to load: {error_count} symbols")
            print(f"   📊 Total processed: {len(missing_symbols)} symbols")
            
            # Mark as completed today in database
            set_system_flag(flag_name, today, "Date when 2-year historical data check was last performed")
            
            log_system_event(f"2-year historical data update completed for {today}: {success_count} success, {error_count} failed")
            
        except Exception as e:
            log_error(f"2-year historical data update failed: {e}")
            print(f"❌ 2-year historical data update failed: {e}")

    def get_missing_symbols_for_2_years(self):
        """Return symbols missing any data in the last 2 years."""
        missing_symbols = []
        try:
            with get_db_connection() as conn:
                if conn is None:
                    log_error("Database connection failed")
                    return missing_symbols
                with conn.cursor() as cur:
                    two_years_ago = (datetime.now() - timedelta(days=730)).date()
                    cur.execute("""
                        SELECT s.symbol
                        FROM sp500_symbols s
                        LEFT JOIN (
                            SELECT symbol, MIN(date) AS min_date, MAX(date) AS max_date, COUNT(*) AS cnt
                            FROM historical_data
                            WHERE date >= %s
                            GROUP BY symbol
                        ) h ON s.symbol = h.symbol
                        WHERE h.symbol IS NULL OR h.min_date > %s OR h.max_date < %s OR h.cnt < 500
                    """, (two_years_ago, two_years_ago, datetime.now().date()))
                    missing_symbols = [row[0] for row in cur.fetchall()]
        except Exception as e:
            log_error(f"Error getting missing symbols for 2 years: {e}")
        return missing_symbols


def run_startup_checks():
    """Run all startup checks and updates."""
    try:
        startup_manager = StartupManager()
        # Ensure database is ready
        startup_manager.ensure_database_ready()
        
        # Ensure 2-year historical data (runs once per day)
        startup_manager.ensure_2_year_historical_data()
        
        # Run daily update
        update_result = startup_manager.run_daily_update()
        
        print("🔄 Checking/updating S&P 500 symbols from Wikipedia (once per day)...")
        sp500_flag_name = "sp500_update_date"
        today = datetime.now().strftime("%Y-%m-%d")
        last_update = get_system_flag(sp500_flag_name)
        
        if last_update != today:
            fetcher = DataFetcher()
            fetcher.update_sp500_symbols_table()
            set_system_flag(sp500_flag_name, today, "Date when S&P 500 symbols table was last updated")
            print(f"✅ S&P 500 table updated for {today}")
            log_system_event(f"S&P 500 update check performed and table updated for {today}")
        else:
            print(f"✅ S&P 500 table already updated today ({today})")
            log_system_event(f"S&P 500 update check performed but skipped (already updated today: {today})")
        return update_result
    except Exception as e:
        log_error("Startup process failed: {e}")
        print("❌ Startup process failed: {e}")
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    # Test the startup process
    result = run_startup_checks()
    print("\nStartup result: {result}")
