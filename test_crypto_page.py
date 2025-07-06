#!/usr/bin/env python3
"""
Comprehensive Playwright test for the crypto page functionality
Tests that the /crypto page loads and displays crypto data correctly with ALL fields validated
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright, expect
import sys
import os
import re

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class CryptoPageTest:
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        # Expected cryptos based on the watchlist
        self.expected_cryptos = ["ADAUSD", "BTCUSD", "ETHUSD", "SOLUSD"]
        self.required_fields = [
            "symbol", "current_price", "strike_price", "option_price",
            "sentiment_score", "confidence", "news_count", "signal_strength",
            "action", "reasoning"
        ]

    async def run_test(self):
        """Run the complete crypto page test suite"""
        print("🧪 Starting Comprehensive Crypto Page Test Suite...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Test 1: Navigation
                await self.test_navigation(page)
                
                # Test 2: Initial page state
                await self.test_initial_page_state(page)
                
                # Test 3: Data loading
                await self.test_data_loading(page)
                
                # Test 4: Comprehensive data validation
                await self.test_comprehensive_data(page)
                
                # Test 5: Refresh functionality
                await self.test_refresh_functionality(page)
                
                # Test 6: Error handling
                await self.test_error_handling(page)
                
                # Test 7: Sentiment chart
                await self.test_sentiment_chart(page)
                
                # Test 8: Summary statistics
                await self.test_summary_statistics(page)
                
                # Test 9: Crypto market summary
                await self.test_crypto_market_summary(page)
                
            except Exception as e:
                self.test_results["failed"] += 1
                self.test_results["errors"].append(f"Test execution error: {str(e)}")
                print(f"❌ Test execution error: {e}")
            finally:
                await browser.close()
        
        # Print final results
        self.print_results()
        
        # Return success/failure
        return self.test_results["failed"] == 0

    async def test_navigation(self, page):
        """Test navigation to the crypto page"""
        print("📱 Testing navigation to crypto page...")
        try:
            await page.goto(f"{self.base_url}/crypto")
            await page.wait_for_load_state("networkidle")
            
            # Verify we're on the crypto page
            title = await page.title()
            if "Crypto" not in title:
                raise Exception(f"Expected crypto page, got: {title}")
            
            print("✅ Navigation test passed")
            self.test_results["passed"] += 1
        except Exception as e:
            print(f"❌ Navigation test failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Navigation: {str(e)}")

    async def test_initial_page_state(self, page):
        """Test initial page state and loading"""
        print("🔍 Testing initial page state...")
        try:
            # Wait for the page to load
            await page.wait_for_timeout(2000)
            
            # Check if loading spinner is hidden (data should be loaded)
            loading_spinner = page.locator(".loading-spinner")
            spinner_count = await loading_spinner.count()
            if spinner_count > 0:
                print("   ℹ️ Loading spinner is visible")
            else:
                print("   ℹ️ Loading spinner is hidden (data already loaded)")
            
            print("✅ Initial page state test passed")
            self.test_results["passed"] += 1
        except Exception as e:
            print(f"❌ Initial page state test failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Initial state: {str(e)}")

    async def test_data_loading(self, page):
        """Test that crypto data is loaded"""
        print("📊 Testing data loading...")
        try:
            # Wait for crypto cards to appear - use the correct CSS selector
            await page.wait_for_selector("#cryptoContainer .card", timeout=10000)
            
            # Count crypto cards - look for cards inside the crypto container
            crypto_cards = page.locator("#cryptoCardsRow .card")
            card_count = await crypto_cards.count()
            print(f"   ✅ Found {card_count} crypto cards")
            
            # CRITICAL: Must have at least the expected number of cryptos
            if card_count < len(self.expected_cryptos):
                raise Exception(f"Expected at least {len(self.expected_cryptos)} crypto cards, found {card_count}")
            
            print("✅ Data loading test passed")
            self.test_results["passed"] += 1
        except Exception as e:
            print(f"❌ Data loading test failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Data loading: {str(e)}")

    async def test_comprehensive_data(self, page):
        """Test comprehensive crypto data display with strict validation"""
        print("💰 Testing comprehensive crypto data display...")
        try:
            # Get all crypto cards - use the correct CSS selector
            crypto_cards = page.locator("#cryptoCardsRow .card")
            card_count = await crypto_cards.count()
            print(f"   📊 Found {card_count} crypto cards")
            
            # CRITICAL: Must have all expected cryptos
            if card_count < len(self.expected_cryptos):
                raise Exception(f"CRITICAL: Expected {len(self.expected_cryptos)} cryptos, found {card_count}")
            
            # Get all crypto symbols to verify we have the expected ones
            found_symbols = []
            for i in range(card_count):
                card = crypto_cards.nth(i)
                if i == 0:
                    # Debug: print the inner HTML of the first card
                    html = await card.inner_html()
                    print(f"      [DEBUG] First card inner HTML:\n{html}")
                    # Print all <strong> elements and their classes
                    strongs = card.locator('strong')
                    count = await strongs.count()
                    for j in range(count):
                        s = strongs.nth(j)
                        s_class = await s.get_attribute('class')
                        s_text = await s.text_content()
                        print(f"      [DEBUG] <strong> #{j}: class={s_class}, text={s_text}")
                symbol_element = card.locator('strong.crypto-symbol')
                symbol_text = await symbol_element.text_content()
                if symbol_text:
                    symbol = symbol_text.strip()
                    found_symbols.append(symbol)
            
            print(f"   ℹ️ Found cryptos: {', '.join(found_symbols)}")
            
            # Check for missing cryptos
            missing_cryptos = [crypto for crypto in self.expected_cryptos if crypto not in found_symbols]
            if missing_cryptos:
                print(f"   ⚠️ Missing cryptos: {', '.join(missing_cryptos)}")
                raise Exception(f"CRITICAL: Missing expected cryptos: {missing_cryptos}")
            
            # Test each crypto card comprehensively
            for i in range(card_count):
                card = crypto_cards.nth(i)
                symbol_element = card.locator('strong.crypto-symbol')
                symbol_text = await symbol_element.text_content()
                symbol = symbol_text.strip() if symbol_text else f"Card_{i}"
                
                print(f"   🔍 Testing card {i+1}: {symbol}")
                
                # Test all required sections and fields
                await self.test_crypto_card_fields(card, symbol)
            
            print("✅ Comprehensive data test passed")
            self.test_results["passed"] += 1
        except Exception as e:
            print(f"❌ Comprehensive data test failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Comprehensive data: {str(e)}")

    async def test_crypto_card_fields(self, card, symbol):
        """Test all required fields in a crypto card and ensure they are populated with data"""
        print(f"      📋 Testing sections for {symbol}...")
        
        # Test all required sections exist and have data
        sections_to_test = [
            ("Symbol/Title", "strong.crypto-symbol"),
            ("Execute Button", "button:has-text('Execute')"),
            ("Price Info Section", "h6:has-text('Price Info')"),
            ("Current Price", "p:has-text('Current:')"),
            ("Sentiment Section", "h6:has-text('Sentiment')"),
            ("Sentiment Score", "p:has-text('Score:')"),
            ("Confidence", "p:has-text('Confidence:')"),
            ("News Count", "p:has-text('News Count:')"),
            ("Trade Details Section", "h6:has-text('Trade Details')"),
            ("Signal Strength", "p:has-text('Signal Strength:')"),
            ("Strategy Section", "h6:has-text('Strategy')"),
            ("Reasoning", "p.small"),
        ]
        
        for section_name, selector in sections_to_test:
            count = await card.locator(selector).count()
            if count > 0:
                print(f"         ✅ {section_name}: {selector} found")
                
                # For data fields, check they have actual values
                if section_name in ["Current Price", "Sentiment Score", "Confidence", "News Count", "Signal Strength"]:
                    # Get the element that contains the value
                    element = card.locator(selector).first
                    element_text = await element.text_content()
                    
                    # Look for the actual value (should be after the label)
                    if ":" in element_text:
                        value_part = element_text.split(":", 1)[1].strip()
                        # Remove any HTML tags and get just the text
                        value_part = re.sub(r'<[^>]+>', '', value_part).strip()
                        
                        if value_part and value_part not in ["N/A", "null", "undefined", ""]:
                            print(f"         ✅ {section_name} has data: {value_part}")
                        else:
                            print(f"         ❌ {section_name} has no data: '{value_part}'")
                            raise Exception(f"Field {section_name} has no data for {symbol}: '{value_part}'")
                    else:
                        print(f"         ⚠️ {section_name} format unclear: '{element_text}'")
            else:
                print(f"         ❌ {section_name}: {selector} not found")
                raise Exception(f"Missing section: {section_name} ({selector}) for {symbol}")

        # Ensure options-specific fields are NOT present
        forbidden_fields = [
            "Strike Price", "Option Price", "Days to Expiry", "contracts", "Target Gain", "Stop Loss", "Option Type"
        ]
        for forbidden in forbidden_fields:
            forbidden_selector = f"text={forbidden}"
            count = await card.locator(forbidden_selector).count()
            if count > 0:
                raise Exception(f"Options-specific field '{forbidden}' found in crypto card for {symbol}")

        # Ensure reasoning does not mention options or contracts
        reasoning_text = await card.locator("p.small").text_content()
        if reasoning_text:
            forbidden_words = ["option", "contract", "expiry", "strike", "premium"]
            for word in forbidden_words:
                if word in reasoning_text.lower():
                    raise Exception(f"Options-related word '{word}' found in reasoning for {symbol}: {reasoning_text}")
        print(f"         ✅ No options-specific fields or advice for {symbol}")

    async def test_refresh_functionality(self, page):
        """Test refresh functionality"""
        print("🔄 Testing refresh functionality...")
        try:
            # Find and click refresh button
            refresh_button = page.locator("button:has-text('Refresh'), .refresh-btn, #refreshBtn")
            if await refresh_button.count() > 0:
                await refresh_button.click()
                await page.wait_for_timeout(2000)
                print("   ℹ️ Refresh button clicked")
            else:
                print("   ℹ️ No refresh button found, testing manual refresh")
                await page.reload()
                await page.wait_for_load_state("networkidle")
            
            # Check if loading spinner appears briefly
            loading_spinner = page.locator(".loading-spinner")
            spinner_count = await loading_spinner.count()
            if spinner_count > 0:
                print("   ℹ️ Loading spinner appeared after refresh")
            else:
                print("   ℹ️ Loading spinner didn't appear (likely cached data)")
            
            print("✅ Refresh functionality test passed")
            self.test_results["passed"] += 1
        except Exception as e:
            print(f"❌ Refresh functionality test failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Refresh: {str(e)}")

    async def test_error_handling(self, page):
        """Test error handling"""
        print("⚠️ Testing error handling...")
        try:
            # Check for error messages
            error_messages = page.locator(".error, .alert-danger, .error-message")
            error_count = await error_messages.count()
            
            if error_count > 0:
                print(f"   ⚠️ Found {error_count} error/warning messages")
                for i in range(error_count):
                    error_text = await error_messages.nth(i).text_content()
                    print(f"   Error {i+1}: {error_text[:100]}...")
            else:
                print("   ✅ No error messages found")
            
            # Check console for errors
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            
            # Wait a bit to catch any console errors
            await page.wait_for_timeout(1000)
            
            if console_errors:
                print(f"   ⚠️ Found {len(console_errors)} console errors")
                for error in console_errors[:3]:  # Show first 3 errors
                    print(f"   Console error: {error[:100]}...")
            else:
                print("   ✅ No console errors found")
            
            print("✅ Error handling test passed")
            self.test_results["passed"] += 1
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Error handling: {str(e)}")

    async def test_sentiment_chart(self, page):
        """Test sentiment chart if present and populated with data"""
        print("📈 Testing sentiment chart...")
        try:
            # Wait for charts to be created and populated
            await page.wait_for_timeout(3000)  # Wait for JavaScript to execute
            
            # Check specifically for the sentiment distribution chart (id="sentimentDistributionChart")
            sentiment_chart = page.locator("#sentimentDistributionChart")
            if await sentiment_chart.count() == 0:
                print("   ❌ Sentiment Distribution chart not found (id='sentimentDistributionChart')")
                raise Exception("Sentiment Distribution chart not found")
            else:
                print("   ✅ Found Sentiment Distribution chart element")
            
            # Check specifically for the signal chart (id="signalChart")
            signal_chart = page.locator("#signalChart")
            if await signal_chart.count() == 0:
                print("   ❌ Signal Distribution chart not found (id='signalChart')")
                raise Exception("Signal Distribution chart not found")
            else:
                print("   ✅ Found Signal Distribution chart element")
            
            # Check if charts have data by looking for Chart.js data
            chart_elements = [sentiment_chart, signal_chart]
            chart_names = ["Sentiment Distribution", "Signal Distribution"]
            
            for i, chart in enumerate(chart_elements):
                # Check if chart has data by looking for Chart.js context
                # Determine which chart ID to use
                chart_id = "sentimentDistributionChart" if chart_names[i] == "Sentiment Distribution" else "signalChart"
                
                chart_data = await page.evaluate("""
                    (chartId) => {
                        const chartElement = document.getElementById(chartId);
                        if (chartElement) {
                            const chart = Chart.getChart(chartElement);
                            if (chart && chart.data && chart.data.datasets) {
                                return {
                                    hasData: chart.data.datasets.some(dataset => dataset.data && dataset.data.length > 0 && 
                                        dataset.data.some(value => value > 0)), // Check if any data points are non-zero
                                    datasetCount: chart.data.datasets.length,
                                    totalDataPoints: chart.data.datasets.reduce((sum, dataset) => sum + (dataset.data ? dataset.data.length : 0), 0),
                                    actualData: chart.data.datasets.map(dataset => dataset.data)
                                };
                            }
                        }
                        return { hasData: false, datasetCount: 0, totalDataPoints: 0, actualData: [] };
                    }
                """, chart_id)
                
                if chart_data['hasData']:
                    print(f"   ✅ {chart_names[i]} chart has data: {chart_data['datasetCount']} datasets, {chart_data['totalDataPoints']} data points")
                    print(f"   ✅ {chart_names[i]} chart actual data: {chart_data['actualData']}")
                else:
                    print(f"   ❌ {chart_names[i]} chart is empty or contains only zero values")
                    raise Exception(f"{chart_names[i]} chart exists but has no meaningful data")
            
            print("✅ Sentiment chart test passed")
            self.test_results["passed"] += 1
        except Exception as e:
            print(f"❌ Sentiment chart test failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Sentiment chart: {str(e)}")

    async def test_summary_statistics(self, page):
        """Test summary statistics are populated with data"""
        print("📊 Testing summary statistics...")
        try:
            # Check for the summary statistics section
            summary_stats = page.locator("#summaryStats")
            if await summary_stats.count() == 0:
                print("   ❌ Summary statistics section not found")
                raise Exception("Summary statistics section not found")
            
            print("   ✅ Summary statistics section found")
            
            # Check specific elements that should contain data
            stats_ids = ["bullishCount", "bearishCount", "neutralCount", "avgSentiment"]
            stats_names = ["Bullish Count", "Bearish Count", "Neutral Count", "Average Sentiment"]
            
            for i, stat_id in enumerate(stats_ids):
                stat_element = page.locator(f"#{stat_id}")
                if await stat_element.count() == 0:
                    print(f"   ❌ {stats_names[i]} element not found (id='{stat_id}')")
                    raise Exception(f"{stats_names[i]} element not found")
                
                # Get the content and check if it contains real data (not just placeholder or dash)
                stat_text = await stat_element.text_content()
                if stat_text and stat_text.strip() and stat_text.strip() != "-":
                    print(f"   ✅ {stats_names[i]} has data: '{stat_text.strip()}'")
                else:
                    print(f"   ❌ {stats_names[i]} has no data or just placeholder: '{stat_text}'")
                    raise Exception(f"{stats_names[i]} has no data or just placeholder")
            
            print("✅ Summary statistics test passed")
            self.test_results["passed"] += 1
        except Exception as e:
            print(f"❌ Summary statistics test failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Summary statistics: {str(e)}")

    async def test_crypto_market_summary(self, page):
        """Test crypto market summary section"""
        print("📊 Testing crypto market summary...")
        try:
            # Wait for summary to be populated
            await page.wait_for_timeout(2000)
            
            # Look for crypto market summary section heading
            market_summary_heading = page.locator("h5:has-text('Crypto Market Summary')")
            if await market_summary_heading.count() == 0:
                print("   ❌ Crypto Market Summary heading not found")
                raise Exception("Crypto Market Summary heading not found")
                
            print("   ✅ Crypto Market Summary heading found")
            
            # Verify that the summary stats div has actual data by checking for specific elements
            summary_section = page.locator("#summaryStats")
            if await summary_section.count() == 0:
                print("   ❌ Summary stats container not found")
                raise Exception("Summary stats container not found")
            
            # Check if the summary contains text indicating real data (numbers, not just labels)
            summary_text = await summary_section.text_content()
            
            # Look for numeric content in the summary text
            import re
            numeric_content = re.findall(r'\d+\.?\d*', summary_text)
            
            if numeric_content and len(numeric_content) >= 2:  # Should have at least a couple numbers
                print(f"   ✅ Crypto market summary has numeric data: {numeric_content[:5]}...")
            else:
                print(f"   ❌ Crypto market summary lacks numeric data: '{summary_text[:100]}'")
                raise Exception("Crypto market summary lacks actual numeric data")
            
            print("✅ Crypto market summary test passed")
            self.test_results["passed"] += 1
        except Exception as e:
            print(f"❌ Crypto market summary test failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Crypto market summary: {str(e)}")

    def print_results(self):
        """Print test results"""
        print("\n" + "=" * 60)
        print("🧪 COMPREHENSIVE CRYPTO PAGE TEST RESULTS")
        print("=" * 60)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"📊 Total: {self.test_results['passed'] + self.test_results['failed']}")
        print("=" * 60)
        
        if self.test_results["errors"]:
            print("\n❌ ERRORS FOUND:")
            for error in self.test_results["errors"]:
                print(f"   • {error}")
        
        if self.test_results["failed"] == 0:
            print("\n🎉 All tests passed!")
            print("=" * 60)
            print("✅ Crypto page test suite passed!")
        else:
            print(f"\n❌ {self.test_results['failed']} test(s) failed!")
            print("=" * 60)
            print("❌ Crypto page test suite FAILED!")

async def main():
    """Main test runner"""
    test = CryptoPageTest()
    success = await test.run_test()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 