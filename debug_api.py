#!/usr/bin/env python3
"""
Debug script to test the database connection and query logic
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.resolve()
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from src.web.app import get_db_connection

def test_database_query():
    """Test the exact query logic from the API endpoint"""
    try:
        print("Testing database connection and query...")
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Test the exact query from the API endpoint
                print("1. Testing timestamp query...")
                cur.execute("""
                    SELECT timestamp FROM market_movers 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                row = cur.fetchone()
                
                if row:
                    timestamp = row[0]
                    print(f"✅ Found timestamp: {timestamp}")
                    
                    # Test the main query
                    print("2. Testing main query...")
                    cur.execute("""
                        SELECT symbol, type, price, change_amount, change_percent, volume, analysis_data 
                        FROM market_movers
                        ORDER BY 
                            CASE WHEN type = 'GAINER' THEN 0 ELSE 1 END,
                            ABS(change_percent) DESC
                    """)
                    
                    rows = cur.fetchall()
                    print(f"✅ Found {len(rows)} rows")
                    
                    for i, row in enumerate(rows):
                        symbol, type, price, change_amount, change_percent, volume, analysis_data = row
                        print(f"   Row {i+1}: {symbol} - {type} - ${price} - {change_percent}%")
                        
                        if analysis_data and isinstance(analysis_data, dict):
                            print(f"      ✅ analysis_data is valid dict")
                        else:
                            print(f"      ❌ analysis_data is not valid: {type(analysis_data)}")
                    
                    # Test the data processing logic
                    print("3. Testing data processing logic...")
                    enhanced_analysis = []
                    
                    for row in rows:
                        symbol, type, price, change_amount, change_percent, volume, analysis_data = row
                        if analysis_data and isinstance(analysis_data, dict):
                            analysis_data['price'] = price
                            analysis_data['change'] = change_amount
                            analysis_data['change_percent'] = change_percent
                            analysis_data['volume'] = volume
                            enhanced_analysis.append(analysis_data)
                    
                    print(f"✅ Processed {len(enhanced_analysis)} stocks into enhanced_analysis")
                    
                else:
                    print("❌ No timestamp found - no rows in market_movers table")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_query() 