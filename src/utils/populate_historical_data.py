#!/usr/bin/env python3
"""
Historical Data Population Script for Trading AI Platform
This script populates the database with 6 months of historical data for S&P 500 stocks
from Alpha Vantage, with intelligent caching to minimize API calls.
Features:
- Checks existing data before making API calls
- Fetches only missing data from Alpha Vantage
- Stores historical data for backtesting
- Provides progress tracking and statistics
- Handles rate limiting gracefully
"""
from src.core.logger import log_info, log_error, log_system_event
from src.core.database import get_db_connection
from src.core.config import Config
import sys
import os
import time
import argparse
from datetime import datetime, timedelta, date
from typing import Dict, Optional, Tuple
import requests

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


class HistoricalDataPopulator:
    """Handles population of historical stock data with smart caching."""

    def __init__(self):
        self.alpha_vantage_api_key = Config.ALPHA_VANTAGE_API_KEY
        self.alpha_vantage_base_url = "https://www.alphavantage.co/query"
        # Changed from 6 to 12 months (1 year) for better backtesting
        self.months_back = 12
        self.rate_limit_delay = 1  # Yahoo Finance: much faster, no API limits
        #         self.api_calls_made = 0
        self.api_calls_saved = 0

    def get_existing_data_range(self, symbol: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Get the date range of existing data for a symbol."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if we have a historical_data table
                    cur.execute(
                        """
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = 'historical_data'
                        );
                    """
                    )
                    table_exists = cur.fetchone()[0]
                    if not table_exists:
                        return None, None
                    # Get the date range of existing data
                    cur.execute(
                        """
                        SELECT MIN(date), MAX(date)
                        FROM historical_data
                        WHERE symbol = %s
                    """,
                        (symbol,),
                    )
                    result = cur.fetchone()
                    if result and result[0] and result[1]:
                        return result[0], result[1]
                    return None, None
        except Exception:
            log_error("Error checking existing data for {symbol}: {e}")
            return None, None

    def create_historical_data_table(self):
        """Create the historical_data table if it doesn't exist."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS historical_data (
                            id SERIAL PRIMARY KEY,
                            symbol VARCHAR(10) NOT NULL,
                            date DATE NOT NULL,
                            open DECIMAL(10,4),
                            high DECIMAL(10,4),
                            low DECIMAL(10,4),
                            close DECIMAL(10,4),
                            volume BIGINT,
                            adjusted_close DECIMAL(10,4),
                            dividend_amount DECIMAL(10,4),
                            split_coefficient DECIMAL(10,4),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(symbol, date)
                        );
                    """
                    )
                    # Create indexes for performance
                    cur.execute(
                        """
                        CREATE INDEX IF NOT EXISTS idx_historical_data_symbol_date
                        ON historical_data(symbol, date);
                    """
                    )
                    cur.execute(
                        """
                        CREATE INDEX IF NOT EXISTS idx_historical_data_symbol
                        ON historical_data(symbol);
                    """
                    )
                    conn.commit()
                    log_info("Historical data table created with indexes")
        except Exception:
            log_error("Error creating historical data table: {e}")
            raise

    def fetch_yahoo_finance_data(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> Optional[Dict]:
        """Fetch historical data from Yahoo Finance (free, no API limits)."""
        try:
            import yfinance as yf

            print(
                f"    📊 Fetching Yahoo Finance data for {symbol} from {start_date.date()} to {end_date.date()}"
            )
            # Use yfinance to get historical data
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            if df is not None and not df.empty:
                # Convert DataFrame to the expected format
                data = {}
                for date_idx, row in df.iterrows():
                    date_str = date_idx.strftime("%Y-%m-%d")
                    data[date_str] = {
                        "1. open": str(row.get("Open", 0)),
                        "2. high": str(row.get("High", 0)),
                        "3. low": str(row.get("Low", 0)),
                        "4. close": str(row.get("Close", 0)),
                        "5. volume": str(int(row.get("Volume", 0))),
                        "5. adjusted close": str(row.get("Adj Close", row.get("Close", 0))),
                        "7. dividend amount": str(row.get("Dividends", 0)),
                        "8. split coefficient": str(row.get("Stock Splits", 1)),
                    }
                print(f"    ✅ Fetched {len(data)} days of Yahoo Finance data for {symbol}")
                return data
            else:
                print(f"    ❌ No Yahoo Finance data found for {symbol}")
                return None
        except Exception as e:
            print(f"    ❌ Error fetching Yahoo Finance data for {symbol}: {e}")
            return None

    def fetch_alpha_vantage_data(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> Optional[Dict]:
        """Fetch historical data from Alpha Vantage API (fallback)."""
        try:
            # Try Yahoo Finance first (free, no limits)
            yahoo_data = self.fetch_yahoo_finance_data(symbol, start_date, end_date)
            if yahoo_data:
                return yahoo_data
            # Fallback to Alpha Vantage if Yahoo Finance fails
            print(f"    🔄 Yahoo Finance failed for {symbol}, trying Alpha Vantage...")
            # Alpha Vantage daily time series
            params = {
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": symbol,
                "apikey": self.alpha_vantage_api_key,
                "outputsize": "full",  # Get full history
            }
            response = requests.get(self.alpha_vantage_base_url, params=params, timeout=30)
            self.api_calls_made += 1
            if response.status_code == 200:
                data = response.json()
                # Check for API errors
                if "Error Message" in data:
                    log_error(f"Alpha Vantage API error for {symbol}: {data['Error Message']}")
                    return None
                if "Note" in data:
                    log_error(f"Alpha Vantage rate limit for {symbol}: {data['Note']}")
                    return None
                # Extract time series data
                time_series = data.get("Time Series (Daily)", {})
                if not time_series:
                    log_error(f"No time series data found for {symbol}")
                    return None
                # Filter data to requested date range
                filtered_data = {}
                start_str = start_date.strftime("%Y-%m-%d")
                end_str = end_date.strftime("%Y-%m-%d")
                for date_str, values in time_series.items():
                    if start_str <= date_str <= end_str:
                        filtered_data[date_str] = values
                log_info(
                    f"Fetched {len(filtered_data)} days of data for {symbol} from Alpha Vantage"
                )
                return filtered_data
            else:
                log_error(f"Alpha Vantage API request failed for {symbol}: {response.status_code}")
                return None
        except Exception as e:
            log_error(f"Error fetching Alpha Vantage data for {symbol}: {e}")
            return None

    def store_historical_data(self, symbol: str, data: Dict) -> int:
        """Store historical data in the database. Handles both Yahoo Finance and Alpha Vantage formats."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    stored_count = 0
                    for date_str, values in data.items():
                        try:
                            # Detect data format and extract values accordingly
                            if "1. open" in values:
                                # Alpha Vantage format
                                open_price = float(values.get("1. open", 0))
                                high_price = float(values.get("2. high", 0))
                                low_price = float(values.get("3. low", 0))
                                close_price = float(values.get("4. close", 0))
                                volume = int(values.get("5. volume", 0))
                                adjusted_close = float(values.get("5. adjusted close", close_price))
                                dividend_amount = float(values.get("7. dividend amount", 0))
                                split_coefficient = float(values.get("8. split coefficient", 1))
                            else:
                                # Yahoo Finance format (pandas DataFrame
                                # converted to dict)
                                open_price = float(values.get("Open", 0))
                                high_price = float(values.get("High", 0))
                                low_price = float(values.get("Low", 0))
                                close_price = float(values.get("Close", 0))
                                volume = int(values.get("Volume", 0))
                                adjusted_close = float(values.get("Adj Close", close_price))
                                dividend_amount = float(values.get("Dividends", 0))
                                split_coefficient = float(values.get("Stock Splits", 1))
                            # Check if record already exists
                            cur.execute(
                                """
                                SELECT COUNT(*) as count FROM historical_data
                                WHERE symbol = %s AND date = %s
                            """,
                                (symbol, date_str),
                            )
                            result = cur.fetchone()
                            exists = result["count"] > 0 if result else False
                            if not exists:
                                cur.execute(
                                    """
                                    INSERT INTO historical_data
                                    (symbol, date, open, high, low, close, volume, adjusted_close, dividend_amount, split_coefficient)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                                    (
                                        symbol,
                                        date_str,
                                        open_price,
                                        high_price,
                                        low_price,
                                        close_price,
                                        volume,
                                        adjusted_close,
                                        dividend_amount,
                                        split_coefficient,
                                    ),
                                )
                                stored_count += 1
                        except Exception as e:
                            log_error(f"Error storing data for {symbol} on {date_str}: {e}")
                            print(f"    DEBUG - Error details: {e}")
                            print(f"    DEBUG - Date: {date_str}, Values: {values}")
                            continue
                    conn.commit()
                    log_info(f"Stored {stored_count} new records for {symbol}")
                    return stored_count
        except Exception:
            log_error("Error storing historical data for {symbol}: {e}")
            return 0

    def get_missing_date_range(self, symbol: str) -> Tuple[datetime, datetime]:
        """Determine what date range needs to be fetched for a symbol."""
        start_date, end_date = self.get_existing_data_range(symbol)
        # Calculate target date range (6 months back from today)
        today = datetime.now().date()
        target_start = today - timedelta(days=180)  # 6 months
        if not start_date or not end_date:
            # No existing data, fetch full range
            return target_start, today
        # Convert to date objects for comparison
        existing_start = start_date.date() if isinstance(start_date, datetime) else start_date
        existing_end = end_date.date() if isinstance(end_date, datetime) else end_date
        # Determine what's missing
        fetch_start = target_start
        fetch_end = today
        if existing_start <= target_start and existing_end >= today:
            # We have all the data we need
            return None, None
        if existing_end < today:
            # Need to fetch from existing_end to today
            fetch_start = existing_end + timedelta(days=1)
        if existing_start > target_start:
            # Need to fetch from target_start to existing_start
            fetch_end = existing_start - timedelta(days=1)
        return fetch_start, fetch_end

    def process_symbol(self, symbol: str) -> Dict:
        """Process a single symbol and return results."""
        result = {
            "symbol": symbol,
            "api_calls_made": 0,
            "records_stored": 0,
            "status": "success",
            "error": None,
        }
        try:
            # Check what data we need
            fetch_start, fetch_end = self.get_missing_date_range(symbol)
            if fetch_start is None or fetch_end is None:
                result["status"] = "skipped"
                result["error"] = "No new data needed"
                self.api_calls_saved += 1
                return result
            # Fetch data from Alpha Vantage
            data = self.fetch_alpha_vantage_data(symbol, fetch_start, fetch_end)
            if data is None:
                result["status"] = "failed"
                result["error"] = "Failed to fetch data from Alpha Vantage"
                return result
            # Store data in database
            records_stored = self.store_historical_data(symbol, data)
            result["records_stored"] = records_stored
            result["api_calls_made"] = 1
            # Rate limiting
            time.sleep(self.rate_limit_delay)
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            log_error(f"Error processing {symbol}: {e}")
        return result

    def populate_sp500_data(self, max_symbols: int = None) -> Dict:
        """Populate historical data for S&P 500 symbols."""
        print("🚀 Starting S&P 500 Historical Data Population")
        print("=" * 60)
        # Create table if it doesn't exist
        print("📋 Setting up database table...")
        self.create_historical_data_table()
        # Get S&P 500 symbols
        symbols = Config.SP500_STOCKS
        if max_symbols:
            symbols = symbols[:max_symbols]
        print("📊 Processing {len(symbols)} S&P 500 symbols")
        print("📅 Fetching {self.months_back} months of historical data")
        print("⏱️ Rate limit: {self.rate_limit_delay} seconds between API calls")
        print()
        results = []
        successful = 0
        failed = 0
        skipped = 0
        total_records = 0
        for i, symbol in enumerate(symbols, 1):
            print("[{i}/{len(symbols)}] Processing {symbol}...")
            result = self.process_symbol(symbol)
            results.append(result)
            if result["status"] == "success":
                successful += 1
                total_records += result["records_stored"]
                print("  ✅ Success: {result['records_stored']} records stored")
            elif result["status"] == "skipped":
                skipped += 1
                print("  ⏭️ Skipped: {result['error']}")
            else:
                failed += 1
                print("  ❌ Failed: {result['error']}")
            print()
        # Print summary
        print("=" * 60)
        print("📊 POPULATION SUMMARY")
        print("=" * 60)
        print("✅ Successful: {successful}/{len(symbols)} symbols")
        print("⏭️ Skipped: {skipped}/{len(symbols)} symbols")
        print("❌ Failed: {failed}/{len(symbols)} symbols")
        print("📈 Total records stored: {total_records:,}")
        print("🌐 API calls made: {self.api_calls_made}")
        print("💾 API calls saved: {self.api_calls_saved}")
        print(
            "⏱️ Estimated time saved: {self.api_calls_saved * self.rate_limit_delay / 60:.1f} minutes"
        )
        # Database statistics
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM historical_data")
                    cur.fetchone()[0]
                    cur.execute("SELECT COUNT(DISTINCT symbol) FROM historical_data")
                    cur.fetchone()[0]
                    cur.execute("SELECT MIN(date), MAX(date) FROM historical_data")
                    date_range = cur.fetchone()
                    print("\n📋 Database Statistics:")
                    print("  - Total records: {total_records_in_db:,}")
                    print("  - Symbols covered: {symbols_in_db}")
                    if date_range[0] and date_range[1]:
                        print("  - Date range: {date_range[0]} to {date_range[1]}")
        except Exception:
            log_error("Error getting database statistics: {e}")
        return {
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "total_records": total_records,
            "api_calls_made": self.api_calls_made,
            "api_calls_saved": self.api_calls_saved,
            "results": results,
        }


def ensure_historical_data_up_to_date(months_back: int = 6):
    """
    Ensure all S&P 500 historical data is up to date in the database.
    Fetches missing data for each symbol and prints progress.
    """
    from src.core.config import Config

    print("\n🚀 [STARTUP] Checking and updating S&P 500 historical data in the database...")
    symbols = Config.SP500_STOCKS
    today = date.today()
    populator = HistoricalDataPopulator()
    updated = 0
    loaded = 0
    skipped = 0
    for i, symbol in enumerate(symbols, 1):
        print("[{i}/{len(symbols)}] Checking {symbol}...", end=" ")
        min_date, max_date = populator.get_existing_data_range(symbol)
        if max_date is not None and max_date.date() >= today:
            print("✅ Up to date")
            skipped += 1
            continue
        if min_date is None or max_date is None:
            print("📥 No data, loading full history...")
            # Load full history
            fetch_start = today - timedelta(days=months_back * 30)
            fetch_end = today
            data = populator.fetch_alpha_vantage_data(symbol, fetch_start, fetch_end)
            if data:
                populator.store_historical_data(symbol, data)
                print("✅ Loaded {len(data)} days")
                loaded += 1
            else:
                print("❌ Failed to load")
        else:
            # Update only missing days
            fetch_start = max_date.date() + timedelta(days=1)
            fetch_end = today
            if fetch_start > fetch_end:
                print("✅ Already current")
                skipped += 1
                continue
            print("🔄 Updating {symbol} from {fetch_start} to {fetch_end}...")
            data = populator.fetch_alpha_vantage_data(symbol, fetch_start, fetch_end)
            if data:
                populator.store_historical_data(symbol, data)
                print("✅ Updated {len(data)} days")
                updated += 1
            else:
                print("❌ Failed to update")
    print("\n📊 [SUMMARY] S&P 500 historical data check complete.")
    print("  - Loaded full history for: {loaded}")
    print("  - Updated recent days for: {updated}")
    print("  - Already up to date: {skipped}")
    print("[END]\n")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Populate database with S&P 500 historical data")
    parser.add_argument(
        "--max-symbols",
        type=int,
        default=None,
        help="Maximum number of symbols to process (default: all S&P 500)",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=12,
        help="Number of months of historical data to fetch (default: 12)",
    )
    args = parser.parse_args()
    # Initialize logging
    log_system_event("=== HISTORICAL DATA POPULATION STARTED ===", "INFO")
    try:
        populator = HistoricalDataPopulator()
        populator.months_back = args.months
        results = populator.populate_sp500_data(max_symbols=args.max_symbols)
        log_system_event("=== HISTORICAL DATA POPULATION COMPLETED ===", "INFO")
        # Exit with appropriate code
        if results["failed"] == 0:
            print("\n✅ All symbols processed successfully!")
            sys.exit(0)
        else:
            print("\n⚠️ {results['failed']} symbols failed to process")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
        sys.exit(1)
    except Exception:
        print("\n❌ Error: {e}")
        log_error("Historical data population failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
