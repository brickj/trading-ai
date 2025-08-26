#!/usr/bin/env python3
"""
Playwright test for Market Movers functionality
Tests the complete flow from API to database to frontend
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.config import Config

class MarketMoversTest:
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.db_config = Config.DATABASE_CONFIG
    
    async def test_market_movers_system(self):
        """Test the complete market movers system"""
        print("🧪 Starting Market Movers System Test")
        print("=" * 50)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                # Test 1: Check if Flask app is running
                print("\n📡 Test 1: Flask App Status")
                await self.test_flask_status(page)
                
                # Test 2: Test the preload API endpoint
                print("\n🔄 Test 2: Preload Stock Data API")
                await self.test_preload_api(page)
                
                # Test 3: Verify database data
                print("\n🗄️  Test 3: Database Verification")
                await self.test_database_data()
                
                # Test 4: Test system status endpoint
                print("\n📊 Test 4: System Status API")
                await self.test_system_status(page)
                
                # Test 5: Test stocks page (if it exists)
                print("\n📈 Test 5: Stocks Page Frontend")
                await self.test_stocks_page(page)
                
                print("\n✅ All tests completed successfully!")
                
            except Exception as e:
                print(f"\n❌ Test failed: {e}")
                import traceback
                traceback.print_exc()
            finally:
                await browser.close()
    
    async def test_flask_status(self, page):
        """Test if Flask app is responding"""
        try:
            response = await page.goto(f"{self.base_url}/api/system_status")
            assert response.status == 200, f"Flask app not responding: {response.status}"
            print("  ✅ Flask app is running and responding")
        except Exception as e:
            print(f"  ❌ Flask app test failed: {e}")
            raise
    
    async def test_preload_api(self, page):
        """Test the preload stock data API endpoint"""
        try:
            # Test the POST endpoint
            response = await page.request.post(f"{self.base_url}/api/preload_stock_data")
            assert response.status == 200, f"Preload API failed: {response.status}"
            
            data = await response.json()
            assert data['status'] == 'success', f"Preload API returned error: {data}"
            print("  ✅ Preload stock data API working")
            print(f"  📝 Response: {data['message']}")
            
        except Exception as e:
            print(f"  ❌ Preload API test failed: {e}")
            raise
    
    async def test_database_data(self):
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
    
    async def test_system_status(self, page):
        """Test the system status endpoint"""
        try:
            response = await page.goto(f"{self.base_url}/api/system_status")
            assert response.status == 200, f"System status failed: {response.status}"
            
            data = await response.json()
            assert data['status'] == 'success', f"System status error: {data}"
            
            # Check if job_schedules section exists
            assert 'job_schedules' in data, "Missing job_schedules in system status"
            
            # Find preload_stock_data job
            preload_job = None
            for job in data['job_schedules']:
                if job['job_name'] == 'preload_stock_data':
                    preload_job = job
                    break
            
            assert preload_job, "preload_stock_data job not found in system status"
            print("  ✅ System status shows preload_stock_data job")
            print(f"  📅 Job schedule: {preload_job['run_time']} ({preload_job['enabled']})")
            
        except Exception as e:
            print(f"  ❌ System status test failed: {e}")
            raise
    
    async def test_stocks_page(self, page):
        """Test the stocks page frontend (if it exists)"""
        try:
            # Try to access the stocks page
            response = await page.goto(f"{self.base_url}/stocks")
            
            if response.status == 200:
                print("  ✅ Stocks page accessible")
                
                # Check if page loads without errors
                await page.wait_for_load_state('networkidle')
                
                # Look for market movers data on the page
                content = await page.content()
                
                # Check for common market movers indicators
                if any(indicator in content for indicator in ['winners', 'losers', 'gainers', 'market movers']):
                    print("  ✅ Stocks page contains market movers content")
                else:
                    print("  ⚠️  Stocks page accessible but no market movers content found")
                    
            else:
                print(f"  ⚠️  Stocks page not accessible (status: {response.status})")
                
        except Exception as e:
            print(f"  ⚠️  Stocks page test failed (non-critical): {e}")

async def main():
    """Main test runner"""
    test = MarketMoversTest()
    await test.test_market_movers_system()

if __name__ == "__main__":
    asyncio.run(main())
