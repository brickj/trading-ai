#!/usr/bin/env python3
"""
Historical Data Updater

This module handles updating 2-year historical data for stocks and crypto
to ensure Enhanced Analysis has fresh data for backtesting.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import time

from ..core.config import Config
from ..core.database import get_db_connection
from ..core.logger import trading_logger
from .data_fetcher import DataFetcher

logger = trading_logger


class HistoricalDataUpdater:
    """Updates 2-year historical data for enhanced analysis backtesting"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.update_interval_days = 7  # Update every 7 days
        self.lookback_days = 730  # 2 years
        
    def update_all_historical_data(self) -> Dict:
        """Update historical data for all watchlist symbols"""
        try:
            logger.info("Starting historical data update for all watchlist symbols")
            
            # Get watchlist symbols
            watchlist_symbols = self._get_watchlist_symbols()
            if not watchlist_symbols:
                logger.warning("No watchlist symbols found")
                return {"status": "error", "message": "No watchlist symbols found"}
            
            updated_count = 0
            failed_count = 0
            results = []
            
            for symbol in watchlist_symbols:
                try:
                    logger.info(f"Updating historical data for {symbol}")
                    result = self._update_symbol_historical_data(symbol)
                    if result["success"]:
                        updated_count += 1
                    else:
                        failed_count += 1
                    results.append(result)
                    
                    # Rate limiting for API calls
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error updating historical data for {symbol}: {e}")
                    failed_count += 1
                    results.append({
                        "symbol": symbol,
                        "success": False,
                        "error": str(e)
                    })
            
            summary = {
                "status": "success",
                "total_symbols": len(watchlist_symbols),
                "updated_count": updated_count,
                "failed_count": failed_count,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Historical data update completed: {updated_count} updated, {failed_count} failed")
            return summary
            
        except Exception as e:
            logger.error(f"Error in update_all_historical_data: {e}")
            return {"status": "error", "message": str(e)}
    
    def _get_watchlist_symbols(self) -> List[str]:
        """Get list of symbols from watchlist"""
        try:
            from psycopg2.extras import RealDictCursor
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT DISTINCT symbol FROM watchlists WHERE type = 'stock'")
                    results = cur.fetchall()
                    return [row['symbol'] for row in results] if results else []
        except Exception as e:
            logger.error(f"Error getting watchlist symbols: {e}")
            return []
    
    def _update_symbol_historical_data(self, symbol: str) -> Dict:
        """Update historical data for a specific symbol"""
        try:
            # Check if update is needed
            if not self._needs_update(symbol):
                return {
                    "symbol": symbol,
                    "success": True,
                    "message": "Data is current, no update needed",
                    "data_points": 0
                }
            
            # Get historical data from Alpha Vantage
            historical_data = self._get_alpha_vantage_historical_data(symbol)
            if historical_data is None or historical_data.empty:
                # Fallback to Yahoo Finance
                historical_data = self._get_yahoo_historical_data(symbol)
            
            if historical_data is None or historical_data.empty:
                return {
                    "symbol": symbol,
                    "success": False,
                    "error": "Could not fetch historical data",
                    "data_points": 0
                }
            
            # Store in database
            data_points = self._store_historical_data(symbol, historical_data)
            
            return {
                "symbol": symbol,
                "success": True,
                "message": f"Updated {data_points} data points",
                "data_points": data_points
            }
            
        except Exception as e:
            logger.error(f"Error updating historical data for {symbol}: {e}")
            return {
                "symbol": symbol,
                "success": False,
                "error": str(e),
                "data_points": 0
            }
    
    def _needs_update(self, symbol: str) -> bool:
        """Check if historical data needs updating"""
        try:
            from psycopg2.extras import RealDictCursor
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Check if we have recent data
                    cutoff_date = datetime.now() - timedelta(days=self.update_interval_days)
                    cur.execute("""
                        SELECT MAX(date) as latest_date, COUNT(*) as data_points 
                        FROM historical_data 
                        WHERE symbol = %s
                    """, (symbol,))
                    result = cur.fetchone()
                    
                    if not result or result['latest_date'] is None:
                        return True  # No data exists
                    
                    latest_date = result['latest_date']
                    data_points = result['data_points']
                    
                    # Need update if data is old or insufficient
                    # Convert cutoff_date to date object to match latest_date type
                    cutoff_date_only = cutoff_date.date()
                    return (latest_date < cutoff_date_only or data_points < 400)  # At least 400 days of data
                    
        except Exception as e:
            logger.error(f"Error checking update need for {symbol}: {e}")
            return True  # Assume update needed on error
    
    def _get_alpha_vantage_historical_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get historical data from Alpha Vantage"""
        try:
            if not Config.ALPHA_VANTAGE_API_KEY:
                logger.warning("Alpha Vantage API key not configured")
                return None
            
            # Map foreign stock symbols to Alpha Vantage supported symbols
            foreign_stock_mapping = {
                '0005.HK': 'HSBC',      # HSBC Holdings (Hong Kong) -> HSBC ADR
                '0700.HK': 'TCEHY',     # Tencent Holdings (Hong Kong) -> Tencent ADR
                '6758.T': 'SNE',        # Sony Group (Japan) -> Sony ADR
                '7203.T': 'TM',         # Toyota Motor (Japan) -> Toyota ADR
            }
            alpha_vantage_symbol = foreign_stock_mapping.get(symbol, symbol)
            
            # Rate limiting for Alpha Vantage free tier
            time.sleep(12)  # 5 calls per minute limit
            
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": alpha_vantage_symbol,
                "outputsize": "full",
                "apikey": Config.ALPHA_VANTAGE_API_KEY,
            }
            
            import requests
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if "Error Message" in data:
                    logger.error(f"Alpha Vantage error for {symbol} (mapped to {alpha_vantage_symbol}): {data['Error Message']}")
                    return None
                
                if "Note" in data:
                    logger.warning(f"Alpha Vantage rate limit for {symbol}: {data['Note']}")
                    return None
                
                time_series_key = "Time Series (Daily)"
                if time_series_key not in data:
                    logger.error(f"No daily time series data for {symbol}")
                    return None
                
                # Convert to DataFrame
                df_data = []
                for date_str, values in data[time_series_key].items():
                    df_data.append({
                        "Date": pd.to_datetime(date_str),
                        "Open": float(values["1. open"]),
                        "High": float(values["2. high"]),
                        "Low": float(values["3. low"]),
                        "Close": float(values["4. close"]),
                        "Volume": int(values["5. volume"]),
                    })
                
                df = pd.DataFrame(df_data)
                df.set_index("Date", inplace=True)
                df.sort_index(inplace=True)
                
                # Get last N days
                cutoff_date = datetime.now() - timedelta(days=self.lookback_days)
                df = df[df.index >= cutoff_date]
                
                logger.info(f"Got {len(df)} days of Alpha Vantage data for {symbol} (mapped to {alpha_vantage_symbol})")
                return df
            else:
                logger.error(f"Alpha Vantage API error {response.status_code} for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {symbol}: {e}")
            return None
    
    def _get_yahoo_historical_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get historical data from Yahoo Finance as fallback"""
        try:
            # This would use the existing Yahoo Finance method from DataFetcher
            # For now, return None to avoid duplicating code
            logger.info(f"Yahoo Finance fallback not implemented for {symbol}")
            return None
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data for {symbol}: {e}")
            return None
    
    def _store_historical_data(self, symbol: str, historical_data: pd.DataFrame) -> int:
        """Store historical data in database"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Clear existing data for this symbol
                    cur.execute("DELETE FROM historical_data WHERE symbol = %s", (symbol,))
                    
                    # Insert new data
                    data_points = 0
                    for date, row in historical_data.iterrows():
                        cur.execute("""
                            INSERT INTO historical_data (symbol, date, open, high, low, close, volume)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (symbol, date) DO UPDATE SET
                                open = EXCLUDED.open,
                                high = EXCLUDED.high,
                                low = EXCLUDED.low,
                                close = EXCLUDED.close,
                                volume = EXCLUDED.volume
                        """, (
                            symbol,
                            date.date(),
                            float(row["Open"].item()),
                            float(row["High"].item()),
                            float(row["Low"].item()),
                            float(row["Close"].item()),
                            int(row["Volume"].item())
                        ))
                        data_points += 1
                    
                    conn.commit()
                    logger.info(f"Stored {data_points} data points for {symbol}")
                    return data_points
                    
        except Exception as e:
            logger.error(f"Error storing historical data for {symbol}: {e}")
            return 0


def update_historical_data_job():
    """Scheduled job function to update historical data"""
    try:
        updater = HistoricalDataUpdater()
        result = updater.update_all_historical_data()
        
        if result["status"] == "success":
            logger.info(f"Historical data update job completed successfully: {result['updated_count']} updated")
        else:
            logger.error(f"Historical data update job failed: {result['message']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in historical data update job: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    # Test the updater
    result = update_historical_data_job()
    print(f"Update result: {result}")
