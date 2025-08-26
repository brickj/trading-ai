#!/usr/bin/env python3
"""
Preload Stock Data Module
Handles preloading winners and losers data for the stocks page
"""

import sys
import time
import json
from datetime import datetime
from ..data.data_fetcher import DataFetcher
from ..core.database import get_db_connection


def preload_stock_data():
    """Preload stock data including winners and losers"""
    print("[DEBUG] Starting preload_stock_data()")
    sys.stdout.flush()

    try:
        # Initialize data fetcher
        data_fetcher = DataFetcher()
        
        # Get top 3 gainers and losers from Alpha Vantage
        print("[DEBUG] Fetching top gainers/losers from Alpha Vantage...")
        market_movers = data_fetcher.get_top_gainers_losers(limit=3)
        gainer_symbols = market_movers.get("gainers", [])
        loser_symbols = market_movers.get("losers", [])
        print(f"[DEBUG] Found market movers: {market_movers}")

        # Fetch actual price data for each symbol
        def fetch_symbol_data(symbol, symbol_type):
            try:
                print(f"[DEBUG] Fetching price data for {symbol} ({symbol_type})...")
                price_data = data_fetcher.get_stock_price(symbol)
                print(f"[DEBUG] Raw price data for {symbol}: {price_data}")
                
                if "error" in price_data:
                    print(f"[WARNING] Could not get price data for {symbol}: {price_data['error']}")
                    return None
                
                # Validate price data
                current_price = price_data.get("current_price", 0)
                change_amount = price_data.get("change", 0)
                change_percent_raw = price_data.get("change_percent", 0)
                volume = price_data.get("volume", 0)
                
                # Clean change_percent - remove % sign and convert to float
                if isinstance(change_percent_raw, str):
                    change_percent = float(change_percent_raw.replace('%', ''))
                else:
                    change_percent = float(change_percent_raw or 0)
                
                print(f"[DEBUG] {symbol} data - Price: {current_price}, Change: {change_amount}, Change%: {change_percent}%, Volume: {volume}")
                
                # Check if we have valid price data
                if not current_price or current_price == 0:
                    print(f"[WARNING] {symbol} has invalid price: {current_price}")
                    return None
                
                return {
                    "symbol": symbol,
                    "type": symbol_type,
                    "price": current_price,
                    "change_amount": change_amount,
                    "change_percent": change_percent,
                    "volume": volume,
                    "timestamp": datetime.now(),
                    "analysis_data": price_data
                }
            except Exception as e:
                print(f"[ERROR] Failed to fetch data for {symbol}: {e}")
                import traceback
                traceback.print_exc()
                return None

        # Fetch data for gainers and losers
        gainers = []
        for symbol in gainer_symbols:
            data = fetch_symbol_data(symbol, "GAINER")
            if data:
                gainers.append(data)
        
        losers = []
        for symbol in loser_symbols:
            data = fetch_symbol_data(symbol, "LOSER")
            if data:
                losers.append(data)



        # Save to market_movers table
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Clear existing data
                    cur.execute("DELETE FROM market_movers")
                    
                    # Insert gainers
                    for gainer in gainers:
                        if gainer:  # Only insert if we have valid data
                            cur.execute("""
                                INSERT INTO market_movers (symbol, type, price, change_amount, change_percent, volume, timestamp, analysis_data)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                gainer.get('symbol', ''),
                                'GAINER',
                                gainer.get('price', 0),
                                gainer.get('change_amount', 0),
                                gainer.get('change_percent', 0),
                                gainer.get('volume', 0),
                                datetime.now(),
                                json.dumps(gainer.get('analysis_data', {}))
                            ))
                    
                    # Insert losers
                    for loser in losers:
                        if loser:  # Only insert if we have valid data
                            cur.execute("""
                                INSERT INTO market_movers (symbol, type, price, change_amount, change_percent, volume, timestamp, analysis_data)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                loser.get('symbol', ''),
                                'LOSER',
                                loser.get('price', 0),
                                loser.get('change_amount', 0),
                                loser.get('change_percent', 0),
                                loser.get('volume', 0),
                                datetime.now(),
                                json.dumps(loser.get('analysis_data', {}))
                            ))
                    
                    conn.commit()
                    print(f"[DEBUG] Successfully saved {len(gainers)} gainers and {len(losers)} losers to market_movers table")
        except Exception as e:
            print(f"[ERROR] Failed to save to market_movers table: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[DEBUG] Processed {len(gainers)} gainers and {len(losers)} losers for market_movers table")
        print(f"[DEBUG] Successfully preloaded stock data")

    except Exception as e:
        print(f"[ERROR] Exception in preload_stock_data: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
    
    print("[DEBUG] Finished preload_stock_data()")
    sys.stdout.flush()


if __name__ == "__main__":
    preload_stock_data()
