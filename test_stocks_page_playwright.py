#!/usr/bin/env python3
"""
Playwright test for /stocks page functionality
Tests that the page loads data from /api/sp500_analysis and displays winners/losers correctly
"""

import asyncio
import time
from playwright.async_api import async_playwright

async def test_stocks_page():
    """Test the /stocks page functionality end-to-end"""
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Set to True for headless
        page = await browser.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        
        try:
            print("🧪 Starting /stocks page test...")
            
            # Navigate to the stocks page
            print("📱 Navigating to /stocks...")
            await page.goto("http://localhost:5001/stocks")
            
            # Wait for page to load
            await page.wait_for_load_state("networkidle")
            print("✅ Page loaded successfully")
            
            # Wait for the loading spinner to appear and then disappear
            print("⏳ Waiting for data to load...")
            
            # Check if loading spinner exists and wait for it to disappear
            loading_spinner = page.locator("#loadingSpinner")
            if await loading_spinner.is_visible():
                print("🔄 Loading spinner visible, waiting for data...")
                await loading_spinner.wait_for(state="hidden", timeout=60000)  # 60 second timeout
                print("✅ Loading spinner hidden")
            else:
                print("ℹ️ No loading spinner found, checking for data directly...")
            
            # Wait a bit more for data to populate
            await page.wait_for_timeout(2000)
            
            # Check for winners
            print("🔍 Checking for winners...")
            winners_list = page.locator("#winnersList")
            await winners_list.wait_for(state="visible", timeout=10000)
            
            # Look for winner rows (should have at least one)
            winner_rows = page.locator("#winnersList .card-body .row, #winnersList .stock-item, #winnersList tr")
            winner_count = await winner_rows.count()
            print(f"📊 Found {winner_count} winner elements")
            
            # Check for losers
            print("🔍 Checking for losers...")
            losers_list = page.locator("#losersList")
            await losers_list.wait_for(state="visible", timeout=10000)
            
            # Look for loser rows (should have at least one)
            loser_rows = page.locator("#losersList .card-body .row, #losersList .stock-item, #losersList tr")
            loser_count = await loser_rows.count()
            print(f"📊 Found {loser_count} loser elements")
            
            # Check for table data as well
            print("🔍 Checking for table data...")
            table_body = page.locator("#stocksTableBody")
            if await table_body.is_visible():
                table_rows = page.locator("#stocksTableBody tr")
                table_row_count = await table_rows.count()
                print(f"📊 Found {table_row_count} table rows")
                
                # Check if table has actual data (not just loading message)
                if table_row_count > 0:
                    first_row_text = await table_rows.first.text_content()
                    if first_row_text and ("Loading" in first_row_text):
                        print("⚠️ Table still shows loading message")
                    else:
                        print("✅ Table has loaded data")
                else:
                    print("ℹ️ No table rows found")
            else:
                print("ℹ️ Table not visible")
            
            # Check for any error messages (exclude disclaimers)
            print("🔍 Checking for error messages...")
            error_alerts = page.locator(".alert-danger, .alert-warning")
            error_count = await error_alerts.count()
            
            # Only count .alert-warning as error if it does NOT contain disclaimer/educational text
            actual_errors = 0
            if error_count > 0:
                print(f"⚠️ Found {error_count} error/warning alerts:")
                for i in range(error_count):
                    error_text = await error_alerts.nth(i).text_content()
                    if error_text:
                        print(f"   Alert {i+1}: {error_text[:100]}...")
                        # Don't count disclaimer/educational messages as errors
                        if ("Disclaimer" not in error_text and 
                            "educational purposes" not in error_text and
                            "Important Disclaimer" not in error_text):
                            actual_errors += 1
                            print(f"   ⚠️ This is an actual error (not a disclaimer)")
                        else:
                            print(f"   ℹ️ This is a disclaimer/educational message (not an error)")
                    else:
                        print(f"   Alert {i+1}: [empty]")
            else:
                print("✅ No error messages found")
            
            print(f"📊 Actual errors (excluding disclaimers): {actual_errors}")
            
            # Verify we have at least some data
            print("🔍 Verifying data presence...")
            
            # Check if we have any winners or losers data
            winners_text = await winners_list.text_content()
            losers_text = await losers_list.text_content()
            
            print(f"📊 Winners section content: {winners_text[:200] if winners_text else '[empty]'}...")
            print(f"📊 Losers section content: {losers_text[:200] if losers_text else '[empty]'}...")
            
            # Check for specific indicators of loaded data
            has_winners_data = (
                winners_text and
                "Loading" not in winners_text and 
                len(winners_text.strip()) > 50 and
                ("%" in winners_text or "$" in winners_text or "AAPL" in winners_text or "MSFT" in winners_text or "AMZN" in winners_text)
            )
            
            has_losers_data = (
                losers_text and
                "Loading" not in losers_text and 
                len(losers_text.strip()) > 50 and
                ("%" in losers_text or "$" in losers_text or "META" in losers_text or "NVDA" in losers_text or "ABBV" in losers_text)
            )
            
            print(f"✅ Winners data loaded: {has_winners_data}")
            print(f"✅ Losers data loaded: {has_losers_data}")
            
            # Final verification
            if has_winners_data and has_losers_data and actual_errors == 0:
                print("🎉 SUCCESS: /stocks page is working correctly!")
                print("✅ Winners and losers data is displayed")
                print("✅ Loading spinner is hidden")
                print("✅ No critical errors found")
                return True
            else:
                print("❌ FAILURE: Data not properly loaded or errors found")
                print(f"   Winners data: {has_winners_data}")
                print(f"   Losers data: {has_losers_data}")
                print(f"   Actual errors: {actual_errors}")
                return False
                
        except Exception as e:
            print(f"❌ TEST FAILED: {str(e)}")
            return False
        finally:
            await browser.close()

async def main():
    """Main test runner"""
    print("🚀 Starting Playwright test for /stocks page...")
    
    # Check if Flask app is running
    import requests
    try:
        response = requests.get("http://localhost:5001/", timeout=5)
        print("✅ Flask app is running")
    except:
        print("❌ Flask app is not running on localhost:5001")
        print("Please start the app with: python start_app.py")
        return
    
    # Run the test
    success = await test_stocks_page()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("The /stocks page is working correctly and displaying SP500 data.")
    else:
        print("\n❌ TESTS FAILED!")
        print("The /stocks page has issues that need to be fixed.")

if __name__ == "__main__":
    asyncio.run(main()) 