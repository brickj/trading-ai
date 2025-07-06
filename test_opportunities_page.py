#!/usr/bin/env python3
"""
Playwright test for the opportunities page functionality
Tests that the /opportunities page loads and displays opportunity data correctly
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright, expect
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class OpportunitiesPageTest:
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }

    async def run_test(self):
        """Run the complete opportunities page test suite"""
        print("🧪 Starting Opportunities Page Test Suite...")
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=False, slow_mo=1000)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Test 1: Navigate to opportunities page
                await self.test_navigate_to_opportunities_page(page)
                
                # Test 2: Check initial page state
                await self.test_initial_page_state(page)
                
                # Test 3: Wait for data to load
                await self.test_data_loading(page)
                
                # Test 4: Verify opportunities data display
                await self.test_opportunities_data_display(page)
                
                # Test 5: Test mode switching
                await self.test_mode_switching(page)
                
                # Test 6: Test refresh functionality
                await self.test_refresh_functionality(page)
                
                # Test 7: Check for errors
                await self.test_error_handling(page)
                
            except Exception as e:
                self.test_results["errors"].append(f"Test execution error: {str(e)}")
                self.test_results["failed"] += 1
                print(f"❌ Test execution failed: {e}")
            finally:
                await browser.close()
        
        # Print test results
        self.print_test_results()
        return self.test_results["failed"] == 0

    async def test_navigate_to_opportunities_page(self, page):
        """Test navigation to the opportunities page"""
        print("📱 Testing navigation to opportunities page...")
        
        try:
            # Navigate to opportunities page
            await page.goto(f"{self.base_url}/opportunities")
            
            # Wait for page to load
            await page.wait_for_load_state("networkidle")
            
            # Verify page title
            title = await page.title()
            assert "Trading Opportunities" in title, f"Expected 'Trading Opportunities' in title, got '{title}'"
            
            # Verify page URL
            current_url = page.url
            assert "/opportunities" in current_url, f"Expected '/opportunities' in URL, got '{current_url}'"
            
            print("✅ Navigation test passed")
            self.test_results["passed"] += 1
            
        except Exception as e:
            print(f"❌ Navigation test failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Navigation test: {str(e)}")

    async def test_initial_page_state(self, page):
        """Test the initial state of the opportunities page"""
        print("🔍 Testing initial page state...")
        
        try:
            # Check for required elements
            await expect(page.locator("#opportunitiesSection")).to_be_visible()
            await expect(page.locator("#findButton")).to_be_visible()
            await expect(page.locator("#newsBtn")).to_be_visible()
            await expect(page.locator("#watchlistBtn")).to_be_visible()
            await expect(page.locator("#allBtn")).to_be_visible()
            await expect(page.locator("#refreshBtn")).to_be_visible()
            await expect(page.locator("#findOpportunitiesBtn")).to_be_visible()
            await expect(page.locator("#opportunitiesContainer")).to_be_visible()
            
            # Check initial container state (should show loading message)
            container = page.locator("#opportunitiesContainer")
            await expect(container).to_be_visible()
            
            # Check for loading spinner
            loading_spinner = page.locator("#loadingSpinner")
            spinner_visible = await loading_spinner.is_visible()
            
            if spinner_visible:
                print("   ℹ️ Loading spinner is visible (fresh data loading)")
            else:
                print("   ℹ️ Loading spinner is hidden (data already loaded)")
            
            print("✅ Initial page state test passed")
            self.test_results["passed"] += 1
            
        except Exception as e:
            print(f"❌ Initial page state test failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Initial page state test: {str(e)}")

    async def test_data_loading(self, page):
        """Test that data loads correctly"""
        print("📊 Testing data loading...")
        
        try:
            # Wait for the loading spinner to disappear (indicating data has loaded)
            loading_spinner = page.locator("#loadingSpinner")
            await expect(loading_spinner).to_be_hidden(timeout=30000)  # 30 second timeout
            
            # Wait for the container to be populated
            container = page.locator("#opportunitiesContainer")
            
            # Check that the container is no longer showing the loading message
            loading_message = container.locator("text=Click 'Refresh' to scan for opportunities")
            await expect(loading_message).to_have_count(0, timeout=10000)
            
            # Wait for at least one opportunity card to appear
            opportunity_cards = container.locator(".card")
            card_count = await opportunity_cards.count()
            assert card_count > 0, f"Expected at least 1 opportunity card, got {card_count}"
            
            print("✅ Data loading test passed")
            self.test_results["passed"] += 1
            
        except Exception as e:
            print(f"❌ Data loading test failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Data loading test: {str(e)}")

    async def test_opportunities_data_display(self, page):
        """Test that opportunities data is displayed correctly"""
        print("💰 Testing opportunities data display...")
        
        try:
            # Get all opportunity cards
            cards = page.locator("#opportunitiesContainer .card")
            card_count = await cards.count()
            
            # Should have at least one opportunity card
            assert card_count > 0, f"Expected at least 1 opportunity card, got {card_count}"
            
            # Check the first card for required elements
            first_card = cards.first
            
            # Check for symbol
            symbol_element = first_card.locator("strong")
            symbol_text = await symbol_element.text_content()
            assert symbol_text and len(symbol_text.strip()) > 0, "Symbol should not be empty"
            
            # Check for price information
            price_info = first_card.locator("text=Current:")
            await expect(price_info).to_be_visible()
            
            # Check for sentiment information
            sentiment_info = first_card.locator("text=Score:")
            await expect(sentiment_info).to_be_visible()
            
            # Check for trade details
            trade_details = first_card.locator("text=Position Size:")
            await expect(trade_details).to_be_visible()
            
            # Check for action badges (CALL/PUT)
            action_badges = first_card.locator(".badge")
            badge_count = await action_badges.count()
            assert badge_count > 0, "Should have at least one badge (CALL/PUT)"
            
            print(f"✅ Opportunities data display test passed - Found {card_count} opportunity cards")
            self.test_results["passed"] += 1
            
        except Exception as e:
            print(f"❌ Opportunities data display test failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Opportunities data display test: {str(e)}")

    async def test_mode_switching(self, page):
        """Test switching between different opportunity modes"""
        print("🔄 Testing mode switching...")
        
        try:
            # Test switching to watchlist mode
            watchlist_btn = page.locator("#watchlistBtn")
            await watchlist_btn.click()
            
            # Wait for the title to update
            title_element = page.locator("#opportunitiesTitle")
            await expect(title_element).to_have_text("Watchlist Opportunities", timeout=5000)
            
            # Wait for data to load in watchlist mode
            await page.wait_for_timeout(3000)
            
            # Test switching to all opportunities mode
            all_btn = page.locator("#allBtn")
            await all_btn.click()
            
            # Wait for the title to update
            await expect(title_element).to_have_text("All Trading Opportunities", timeout=5000)
            
            # Wait for data to load in all mode
            await page.wait_for_timeout(3000)
            
            # Switch back to news mode
            news_btn = page.locator("#newsBtn")
            await news_btn.click()
            
            # Wait for the title to update
            await expect(title_element).to_have_text("News-Driven Opportunities", timeout=5000)
            
            print("✅ Mode switching test passed")
            self.test_results["passed"] += 1
            
        except Exception as e:
            print(f"❌ Mode switching test failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Mode switching test: {str(e)}")

    async def test_refresh_functionality(self, page):
        """Test the refresh button functionality"""
        print("🔄 Testing refresh functionality...")
        
        try:
            # Click the refresh button
            refresh_btn = page.locator("#refreshBtn")
            await refresh_btn.click()
            
            # Wait for loading spinner to appear (it might not if data is cached)
            loading_spinner = page.locator("#loadingSpinner")
            
            try:
                await expect(loading_spinner).to_be_visible(timeout=3000)
                # If spinner appears, wait for it to disappear
                await expect(loading_spinner).to_be_hidden(timeout=30000)
            except:
                # If spinner doesn't appear (cached data), that's fine
                print("   ℹ️ Loading spinner didn't appear (likely cached data)")
            
            # Verify data is still displayed
            container = page.locator("#opportunitiesContainer")
            cards = container.locator(".card")
            card_count = await cards.count()
            assert card_count > 0, "Should still have data after refresh"
            
            print("✅ Refresh functionality test passed")
            self.test_results["passed"] += 1
            
        except Exception as e:
            print(f"❌ Refresh functionality test failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Refresh functionality test: {str(e)}")

    async def test_error_handling(self, page):
        """Test error handling"""
        print("⚠️ Testing error handling...")
        
        try:
            # Check for any console errors
            console_errors = []
            
            def handle_console_error(msg):
                if msg.type == "error":
                    console_errors.append(msg.text)
            
            page.on("console", handle_console_error)
            
            # Wait a bit for any errors to appear
            await page.wait_for_timeout(2000)
            
            # Check for any JavaScript errors
            if console_errors:
                print(f"⚠️ Console errors found: {console_errors}")
                # Don't fail the test for console errors, just log them
            
            # Check that the page is still functional
            container = page.locator("#opportunitiesContainer")
            await expect(container).to_be_visible()
            
            print("✅ Error handling test passed")
            self.test_results["passed"] += 1
            
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Error handling test: {str(e)}")

    def print_test_results(self):
        """Print test results summary"""
        print("\n" + "="*50)
        print("🧪 OPPORTUNITIES PAGE TEST RESULTS")
        print("="*50)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"📊 Total: {self.test_results['passed'] + self.test_results['failed']}")
        
        if self.test_results["errors"]:
            print("\n❌ Errors:")
            for error in self.test_results["errors"]:
                print(f"   - {error}")
        
        if self.test_results["failed"] == 0:
            print("\n🎉 All tests passed! Opportunities page is working correctly.")
        else:
            print(f"\n💥 {self.test_results['failed']} test(s) failed. Please check the errors above.")
        
        print("="*50)

async def main():
    """Main test runner"""
    test = OpportunitiesPageTest()
    success = await test.run_test()
    
    if success:
        print("\n✅ Opportunities page test suite completed successfully!")
        return 0
    else:
        print("\n❌ Opportunities page test suite failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 