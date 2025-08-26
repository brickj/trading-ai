#!/usr/bin/env python3
"""
Simple test for Market Movers functionality
Tests the complete flow from API to database
"""

import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.config import Config

class MarketMoversSimpleTest:
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.db_config = Config.DATABASE_CONFIG
    
    def test_market_movers_system(self):
        """Test the complete market movers system"""
        print("🧪 Starting Market Movers System Test (Simple)")
        print("=" * 50)
        
        try:
            # Test 1: Check if Flask app is running
            print("\n📡 Test 1: Flask App Status")
            self.test_flask_status()
            
            # Test 2: Test the preload API endpoint
            print("\n🔄 Test 2: Preload Stock Data API")
            self.test_preload_api()
            
            # Test 3: Verify database data
            print("\n🗄️  Test 3: Database Verification")
            self.test_database_data()
            
            # Test 4: Test system status endpoint
            print("\n📊 Test 4: System Status API")
            self.test_system_status()
            
            print("\n✅ All tests completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    def test_flask_status(self):
        """Test if Flask app is responding"""
        try:
            response = requests.get(f"{self.base_url}/api/system_status", timeout=10)
            assert response.status_code == 200, f"Flask app not responding: {response.status_code}"
            print("  ✅ Flask app is running and responding")
        except Exception as e:
            print(f"  ❌ Flask app test failed: {e}")
            raise
    
    def test_preload_api(self):
        """Test the preload stock data API endpoint"""
        try:
            # Test the POST endpoint
            response = requests.post(f"{self.base_url}/api/preload_stock_data", timeout=30)
            assert response.status_code == 200, f"Preload API failed: {response.status_code}"
            
            data = response.json()
            assert data['status'] == 'success', f"Preload API returned error: {data}"
            print("  ✅ Preload stock data API working")
            print(f"  📝 Response: {data['message']}")
            
        except Exception as e:
            print(f"  ❌ Preload API test failed: {e}")
            raise
    
    def test_database_data(self):
        """Verify data was saved to database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if we have recent data
                cur.execute("""
                    SELECT symbol, type, price, change_percent, timestamp 
                    FROM market_movers 
                    WHERE timestamp > NOW() - INTERVAL '1 hour'
                    ORDER BY timestamp DESC
                """)
                rows = cur.fetchall()
                
                assert len(rows) > 0, "No recent market movers data found"
                
                print(f"  ✅ Found {len(rows)} recent market movers records")
                
                # Verify data quality
                for row in rows:
                    assert row['price'] > 0, f"Invalid price for {row['symbol']}: {row['price']}"
                    assert row['change_percent'] != 0, f"Invalid change % for {row['symbol']}: {row['change_percent']}"
                    assert row['symbol'], f"Missing symbol: {row}"
                    assert row['type'] in ['GAINER', 'LOSER'], f"Invalid type for {row['symbol']}: {row['type']}"
                
                print("  ✅ All data records have valid values")
                
                # Show sample data
                print("  📊 Sample data:")
                for row in rows[:3]:
                    print(f"    {row['symbol']} ({row['type']}): ${row['price']} ({row['change_percent']}%)")
                
            conn.close()
            
        except Exception as e:
            print(f"  ❌ Database test failed: {e}")
            raise
    
    def test_system_status(self):
        """Test the system status endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/system_status", timeout=10)
            assert response.status_code == 200, f"System status failed: {response.status_code}"
            
            data = response.json()
            assert data['status'] == 'success', f"System status error: {data}"
            
            # Check if job_schedules section exists
            assert 'job_schedules' in data['data'], "Missing job_schedules in system status"
            
            # Find preload_stock_data job
            preload_job = None
            for job in data['data']['job_schedules']['jobs']:
                if job['name'] == 'preload_stock_data':
                    preload_job = job
                    break
            
            assert preload_job, "preload_stock_data job not found in system status"
            print("  ✅ System status shows preload_stock_data job")
            print(f"  📅 Job schedule: {preload_job['run_time']} ({preload_job['enabled']})")
            
            # Check if historical_data section exists
            if 'historical_data' in data['data']:
                hist_data = data['data']['historical_data']
                print(f"  📈 Historical data status: {hist_data['status']}")
                print(f"  📊 Historical data: {hist_data['symbols_with_data']} symbols, {hist_data['total_data_points']} data points")
            else:
                print("  ⚠️  Historical data section not found in system status")
            
        except Exception as e:
            print(f"  ❌ System status test failed: {e}")
            raise

def main():
    """Main test runner"""
    test = MarketMoversSimpleTest()
    test.test_market_movers_system()

if __name__ == "__main__":
    main()
