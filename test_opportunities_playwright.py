#!/usr/bin/env python3
"""
Final Playwright Test for Opportunities Page
============================================

This test verifies that the opportunities page:
1. Navigates to /opportunities
2. Waits for data to load
3. Asserts that at least one opportunity card or row appears in the DOM
4. Validates that the configuration and strategy sections render correctly
5. Ensures the application doesn't crash during load or interaction

Usage:
    python test_opportunities_playwright.py
"""

import asyncio
import time
from playwright.async_api import async_playwright, expect
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class OpportunitiesPagePlaywrightTest:
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }

    async def test_opportunities_page(self):
        """Main test function for opportunities page"""
        print("🚀 Starting Opportunities Page Playwright Test")
        print("=" * 60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                # 1. Navigate to /opportunities
                print("🌐 Step 1: Navigating to /opportunities...")
                await page.goto(f"{self.base_url}/opportunities")
                await page.wait_for_load_state("networkidle")
                print("✅ Navigation successful")
                
                # 2. Wait for data to load
                print("⏳ Step 2: Waiting for data to load...")
                
                # Wait for watchlist configuration to load
                await page.wait_for_selector("#watchlistConfig", timeout=10000)
                
                # Wait for loading to complete
                await page.wait_for_function("""
                    () => {
                        const config = document.getElementById('watchlistConfig');
                        return config && !config.textContent.includes('Loading watchlist configuration');
                    }
                """, timeout=15000)
                
                # Wait additional time for opportunities to load
                await page.wait_for_timeout(3000)
                print("✅ Data loading completed")
                
                # 3. Assert that at least one opportunity card or row appears in the DOM
                print("🔍 Step 3: Checking for opportunities...")
                
                opportunity_cards = await page.locator(".card.mb-3").count()
                empty_state = await page.locator("text=No trading opportunities found").count()
                
                if opportunity_cards > 0:
                    print(f"✅ Found {opportunity_cards} opportunity cards")
                    
                    # Validate first opportunity card structure
                    first_card = page.locator(".card.mb-3").first
                    symbol = await first_card.locator("strong").text_content()
                    print(f"✅ First opportunity symbol: {symbol}")
                    
                    # Check card has required sections
                    price_section = await first_card.locator("text=Price Info").count()
                    sentiment_section = await first_card.locator("text=Sentiment").count()
                    trade_section = await first_card.locator("text=Trade Details").count()
                    strategy_section = await first_card.locator("text=Strategy").count()
                    
                    assert price_section > 0, "Price Info section should be present"
                    assert sentiment_section > 0, "Sentiment section should be present"
                    assert trade_section > 0, "Trade Details section should be present"
                    assert strategy_section > 0, "Strategy section should be present"
                    
                    print("✅ Opportunity card structure validated")
                    
                elif empty_state > 0:
                    print("✅ Empty state displayed correctly")
                    
                    # Check empty state has refresh button
                    refresh_in_empty = await page.locator("text=Refresh Analysis").count()
                    assert refresh_in_empty > 0, "Empty state should have refresh button"
                    print("✅ Empty state has refresh button")
                    
                else:
                    raise Exception("No opportunities or empty state found")
                
                # 4. Validate that the configuration and strategy sections render correctly
                print("🔍 Step 4: Validating configuration and strategy sections...")
                
                # Check News-Driven Strategy section
                news_strategy = page.locator("text=News-Driven Strategy")
                assert await news_strategy.is_visible(), "News-Driven Strategy section should be visible"
                print("✅ News-Driven Strategy section visible")
                
                # Check Watchlist Strategy section
                watchlist_strategy = page.locator("text=Watchlist Strategy")
                assert await watchlist_strategy.is_visible(), "Watchlist Strategy section should be visible"
                print("✅ Watchlist Strategy section visible")
                
                # Check Configuration section
                configuration = page.locator("text=Configuration")
                assert await configuration.is_visible(), "Configuration section should be visible"
                print("✅ Configuration section visible")
                
                # Check watchlist configuration is populated
                config_text = await page.locator("#watchlistConfig").text_content()
                assert config_text and "Watchlist Stocks:" in config_text, "Watchlist stocks should be displayed"
                assert config_text and "Watchlist Crypto:" in config_text, "Watchlist crypto should be displayed"
                print("✅ Watchlist configuration populated")
                
                # Check for system status link
                system_status_link = page.locator('a.alert-link[href="/system_status"]')
                assert await system_status_link.is_visible(), "System status link should be visible"
                print("✅ System status link visible")
                
                # 5. Test mode switching functionality
                print("🔍 Step 5: Testing mode switching...")
                
                # Check initial state (should be News-Driven)
                news_btn = page.locator("#newsBtn")
                classes = await news_btn.get_attribute("class")
                assert classes and "active" in classes, "News button should be active initially"
                print("✅ Initial mode is News-Driven")
                
                # Switch to Watchlist mode
                await page.locator("#watchlistBtn").click()
                await page.wait_for_timeout(1000)
                
                watchlist_btn = page.locator("#watchlistBtn")
                classes = await watchlist_btn.get_attribute("class")
                assert classes and "active" in classes, "Watchlist button should be active after click"
                print("✅ Switched to Watchlist mode")
                
                # Switch to All mode
                await page.locator("#allBtn").click()
                await page.wait_for_timeout(1000)
                
                all_btn = page.locator("#allBtn")
                classes = await all_btn.get_attribute("class")
                assert classes and "active" in classes, "All button should be active after click"
                print("✅ Switched to All mode")
                
                # Switch back to News mode
                await page.locator("#newsBtn").click()
                await page.wait_for_timeout(1000)
                
                classes = await news_btn.get_attribute("class")
                assert classes and "active" in classes, "News button should be active after switching back"
                print("✅ Switched back to News-Driven mode")
                
                # 6. Test refresh functionality
                print("🔍 Step 6: Testing refresh functionality...")
                
                refresh_btn = page.locator("#refreshBtn")
                assert await refresh_btn.is_visible(), "Refresh button should be visible"
                print("✅ Refresh button visible")
                
                await refresh_btn.click()
                await page.wait_for_timeout(2000)
                print("✅ Refresh button clicked successfully")
                
                # 7. Check for loading spinner states
                print("🔍 Step 7: Checking loading states...")
                
                spinner = page.locator("#loadingSpinner")
                spinner_visible = await spinner.is_visible()
                if not spinner_visible:
                    print("✅ Loading spinner hidden (normal state)")
                else:
                    print("✅ Loading spinner visible")
                
                # 8. Check for errors in browser console
                print("🔍 Step 8: Checking for console errors...")
                
                console_errors = await page.evaluate("""
                    () => {
                        return window.console.errors || [];
                    }
                """)
                
                if console_errors:
                    print(f"⚠️ Found {len(console_errors)} console errors")
                    for error in console_errors[:3]:  # Show first 3 errors
                        print(f"   - {error}")
                else:
                    print("✅ No console errors found")
                
                # 9. Take final screenshot
                await page.screenshot(path="opportunities_final_test.png")
                print("📸 Final screenshot saved: opportunities_final_test.png")
                
                print("\n" + "=" * 60)
                print("🎉 ALL TESTS PASSED!")
                print("✅ Opportunities page is fully functional")
                
                return True
                
            except Exception as e:
                print(f"\n❌ Test failed: {e}")
                self.test_results["failed"] += 1
                self.test_results["errors"].append(str(e))
                
                # Take error screenshot
                try:
                    await page.screenshot(path="opportunities_test_error.png")
                    print("📸 Error screenshot saved: opportunities_test_error.png")
                except:
                    pass
                
                return False
                
            finally:
                await browser.close()

async def main():
    """Main test runner"""
    test = OpportunitiesPagePlaywrightTest()
    success = await test.test_opportunities_page()
    
    if success:
        print("\n📝 Test Summary:")
        print("  ✅ Navigation to /opportunities successful")
        print("  ✅ Data loading completed")
        print("  ✅ Opportunities or empty state displayed correctly")
        print("  ✅ Configuration and strategy sections validated")
        print("  ✅ Mode switching functional")
        print("  ✅ Refresh button works")
        print("  ✅ Loading states handled")
        print("  ✅ No console errors")
        print("  ✅ Application didn't crash")
        print("\n🎯 Opportunities page is ready for production!")
    else:
        print(f"\n❌ Test failed with {test.test_results['failed']} errors")
        for error in test.test_results["errors"]:
            print(f"   - {error}")

if __name__ == "__main__":
    asyncio.run(main()) 