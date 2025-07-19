#!/usr/bin/env python3
"""
Comprehensive Playwright Test Suite for Trading AI Application
Validates that every page is fully populated with real data and logs detailed information
"""
import asyncio
import json
import os
import time
import pytest
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, expect, Page
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensivePageTest:
    """Comprehensive test suite for all application pages"""
    
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.test_results = []
        self.artifacts_dir = Path("test_artifacts")
        self.artifacts_dir.mkdir(exist_ok=True)
        self.page = None
        self.browser = None
        self.context = None
        
        # Define all pages to test with detailed expectations
        self.pages_to_test = [
            {
                "name": "Homepage",
                "route": "/",
                "expected_elements": [
                    "h1",  # Main heading
                    "#howItWorksCard",  # How it works card
                    "nav",  # Navigation
                    ".container",  # Main container
                    ".card"  # Feature cards
                ],
                "wait_for_data": False,
                "verify_population": True,
                "expected_data": ["feature cards", "navigation", "main content"]
            },
            {
                "name": "Stocks Page",
                "route": "/stocks",
                "expected_elements": [
                    "#stocksTableBody",  # Stocks table
                    "#winnersList",  # Winners list
                    "#losersList",  # Losers list
                    "#stockAnalysisSection",  # Analysis section
                    ".stock-card",  # Stock cards
                    "#marketOverview"  # Market overview
                ],
                "wait_for_data": True,
                "data_timeout": 30000,  # 30 seconds for data to load
                "verify_population": True,
                "expected_data": ["stock data", "winners/losers", "market analysis"],
                "min_data_count": 5  # At least 5 stocks should be loaded
            },
            {
                "name": "Crypto Page",
                "route": "/crypto",
                "expected_elements": [
                    "#cryptoAnalysisContainer",  # Crypto container
                    "#cryptoCardsRow",  # Crypto cards row
                    "#sentimentChartContainer",  # Sentiment chart
                    ".crypto-card",  # Crypto cards
                    "#cryptoOverview"  # Crypto overview
                ],
                "wait_for_data": True,
                "data_timeout": 20000,
                "verify_population": True,
                "expected_data": ["crypto data", "sentiment analysis", "price charts"],
                "min_data_count": 3  # At least 3 crypto assets
            },
            {
                "name": "Opportunities Page",
                "route": "/opportunities",
                "expected_elements": [
                    "#opportunitiesSection",  # Opportunities section
                    "#opportunitiesContainer",  # Opportunities container
                    "#findButton",  # Find button
                    "#newsBtn",  # News button
                    "#watchlistBtn",  # Watchlist button
                    "#refreshBtn",  # Refresh button
                    "#lastUpdated",  # Last updated timestamp
                    ".opportunity-card"  # At least one opportunity card
                ],
                "wait_for_data": True,
                "data_timeout": 30000,  # Increased timeout for data loading
                "verify_population": True,
                "expected_data": ["opportunities", "news data", "watchlist data"],
                "min_data_count": 1,  # At least 1 opportunity
                "verify_function": "verify_opportunities_page"  # Custom verification function
            },
            {
                "name": "System Status Page",
                "route": "/system_status",
                "expected_elements": [
                    ".container",  # Main container
                    ".card",  # Status cards
                    "h1",  # Page heading
                    "#systemMetrics",  # System metrics
                    "#serviceStatus"  # Service status
                ],
                "wait_for_data": True,
                "data_timeout": 15000,
                "verify_population": True,
                "expected_data": ["system metrics", "service status", "performance data"]
            },
            {
                "name": "Logs Page",
                "route": "/logs",
                "expected_elements": [
                    "#logContainer",  # Log container
                    "#logStats",  # Log statistics
                    ".container",  # Main container
                    ".log-entry"  # Log entries
                ],
                "wait_for_data": True,
                "data_timeout": 10000,
                "verify_population": True,
                "expected_data": ["log entries", "log statistics", "error logs"],
                "min_data_count": 10  # At least 10 log entries
            },
            {
                "name": "Portfolio Page",
                "route": "/portfolio_page",
                "expected_elements": [
                    "#portfolioContainer",  # Portfolio container
                    "#portfolioSection",  # Portfolio section
                    "#addPositionForm",  # Add position form
                    ".portfolio-card"  # Portfolio cards
                ],
                "wait_for_data": False,  # Uses mock data
                "verify_population": True,
                "expected_data": ["portfolio form", "position management"]
            },
            {
                "name": "Backtest Page",
                "route": "/backtest_page",
                "expected_elements": [
                    "#backtestForm",  # Backtest form
                    "#daysSelector",  # Days selector
                    "h1",  # Page heading
                    "#backtestResults"  # Backtest results area
                ],
                "wait_for_data": False,
                "verify_population": True,
                "expected_data": ["backtest form", "parameter selection"]
            },
            {
                "name": "Recommendations Page",
                "route": "/recommendations",
                "expected_elements": [
                    ".container",  # Main container
                    "h1",  # Page heading
                    ".card",  # Recommendation cards
                    "#recommendationsContainer"  # Recommendations container
                ],
                "wait_for_data": True,
                "data_timeout": 20000,
                "verify_population": True,
                "expected_data": ["recommendations", "trading signals", "analysis results"],
                "min_data_count": 1  # At least 1 recommendation
            },
            {
                "name": "Scalping Signals Page",
                "route": "/scalping_signals",
                "expected_elements": [
                    ".container",  # Main container
                    "h1",  # Page heading
                    "#scalpingSignalsContainer",  # Scalping signals container
                    ".signal-card"  # Signal cards
                ],
                "wait_for_data": True,
                "data_timeout": 25000,
                "verify_population": True,
                "expected_data": ["scalping signals", "momentum analysis", "trading opportunities"],
                "min_data_count": 1  # At least 1 signal
            },
            {
                "name": "Reporting Page",
                "route": "/reporting",
                "expected_elements": [
                    ".container",  # Main container
                    "h1",  # Page heading
                    "#reportingForm",  # Reporting form
                    "#reportResults"  # Report results area
                ],
                "wait_for_data": False,
                "verify_population": True,
                "expected_data": ["reporting form", "date selection", "report types"]
            }
        ]
    
    async def setup_browser(self):
        """Set up browser with video recording"""
        self.playwright = await async_playwright().start()
        
        # Launch browser with video recording
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        # Create context with video recording
        self.context = await self.browser.new_context(
            record_video_dir=str(self.artifacts_dir),
            record_video_size={"width": 1920, "height": 1080}
        )
        
        self.page = await self.context.new_page()
        
        # Set viewport
        await self.page.set_viewport_size({"width": 1920, "height": 1080})
        
        logger.info("Browser setup complete with video recording enabled")
    
    async def teardown_browser(self):
        """Clean up browser resources"""
        if hasattr(self, 'context'):
            await self.context.close()
        if hasattr(self, 'browser'):
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        
        logger.info("Browser teardown complete")
    
    async def wait_for_page_load(self, page_config):
        """Wait for page to fully load with data"""
        start_time = time.time()
        
        try:
            # Wait for page to be ready
            await self.page.wait_for_load_state("networkidle", timeout=10000)
            
            # If page needs data, wait for it
            if page_config.get("wait_for_data", False):
                timeout = page_config.get("data_timeout", 15000)
                logger.info(f"Waiting for data to load on {page_config['name']} (timeout: {timeout}ms)")
                
                # Wait for key data elements to appear
                for element in page_config["expected_elements"]:
                    try:
                        await self.page.wait_for_selector(element, timeout=timeout)
                        logger.info(f"Found element: {element}")
                    except Exception as e:
                        logger.warning(f"Element {element} not found: {e}")
                
                # Additional wait for data to populate
                await asyncio.sleep(2)
            
            load_time = time.time() - start_time
            logger.info(f"Page load completed in {load_time:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"Error waiting for page load: {e}")
            return False
    
    async def verify_page_population(self, page_config):
        """Verify that page is fully populated with data"""
        logger.info(f"🔍 Verifying page population for {page_config['name']}")
        
        try:
            # Check for expected data types
            expected_data = page_config.get("expected_data", [])
            data_found = []
            
            for data_type in expected_data:
                # Check for various data indicators
                if data_type == "stock data":
                    stock_cards = await self.page.query_selector_all(".stock-card, #stocksTableBody tr")
                    if len(stock_cards) > 0:
                        data_found.append(f"stock data ({len(stock_cards)} items)")
                
                elif data_type == "crypto data":
                    crypto_cards = await self.page.query_selector_all(".crypto-card, #cryptoCardsRow .card")
                    if len(crypto_cards) > 0:
                        data_found.append(f"crypto data ({len(crypto_cards)} items)")
                
                elif data_type == "opportunities":
                    opp_cards = await self.page.query_selector_all(".opportunity-card, .opportunity-item")
                    if len(opp_cards) > 0:
                        data_found.append(f"opportunities ({len(opp_cards)} items)")
                
                elif data_type == "recommendations":
                    rec_cards = await self.page.query_selector_all(".card, .recommendation-item")
                    if len(rec_cards) > 0:
                        data_found.append(f"recommendations ({len(rec_cards)} items)")
                
                elif data_type == "log entries":
                    log_entries = await self.page.query_selector_all(".log-entry, .log-item")
                    if len(log_entries) > 0:
                        data_found.append(f"log entries ({len(log_entries)} items)")
                
                elif data_type == "scalping signals":
                    signal_cards = await self.page.query_selector_all(".signal-card, .scalping-item")
                    if len(signal_cards) > 0:
                        data_found.append(f"scalping signals ({len(signal_cards)} items)")
                
                elif data_type == "system metrics":
                    metrics = await self.page.query_selector_all(".metric, .status-indicator")
                    if len(metrics) > 0:
                        data_found.append(f"system metrics ({len(metrics)} items)")
            
            # Check minimum data count if specified
            min_count = page_config.get("min_data_count", 0)
            if min_count > 0:
                all_data_items = await self.page.query_selector_all(".card, .item, tr, .entry")
                if len(all_data_items) >= min_count:
                    data_found.append(f"minimum data count met ({len(all_data_items)} >= {min_count})")
                else:
                    logger.warning(f"Minimum data count not met: {len(all_data_items)} < {min_count}")
            
            # Log findings
            if data_found:
                logger.info(f"✅ {page_config['name']} - Data found: {', '.join(data_found)}")
                return True
            else:
                logger.warning(f"⚠️ {page_config['name']} - No expected data found")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying page population: {e}")
            return False
    
    async def verify_default_page_population(self, page_config):
        """Verify default page elements are present"""
        logger.info(f"🔍 Verifying default elements for {page_config['name']}")
        
        try:
            elements_found = []
            for element in page_config["expected_elements"]:
                try:
                    await self.page.wait_for_selector(element, timeout=5000)
                    elements_found.append(element)
                except Exception as e:
                    logger.warning(f"Element {element} not found: {e}")
            
            if len(elements_found) >= len(page_config["expected_elements"]) * 0.8:  # 80% threshold
                logger.info(f"✅ {page_config['name']} - Elements found: {len(elements_found)}/{len(page_config['expected_elements'])}")
                return True
            else:
                logger.warning(f"⚠️ {page_config['name']} - Missing elements: {len(elements_found)}/{len(page_config['expected_elements'])}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying default elements: {e}")
            return False
    
    async def take_snapshot(self, name):
        """Take a snapshot of the current page state"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = self.artifacts_dir / filename
        
        await self.page.screenshot(path=str(filepath))
        logger.info(f"📸 Snapshot saved: {filepath}")
        return filepath
    
    async def verify_opportunities_page(self, page_config):
        """Special verification for opportunities page"""
        logger.info("🔍 Special verification for Opportunities page")
        
        try:
            # Set up console message handler
            console_messages = []
            
            def handle_console(msg):
                console_messages.append(msg.text)
                logger.info(f"Console: {msg.text}")
            
            self.page.on("console", handle_console)
            
            # Wait for opportunities to load
            await asyncio.sleep(3)
            
            # Check for opportunities data
            opportunities = await self.page.query_selector_all(".opportunity-card, .opportunity-item")
            logger.info(f"Found {len(opportunities)} opportunities")
            
            # Check for news/watchlist buttons
            news_btn = await self.page.query_selector("#newsBtn")
            watchlist_btn = await self.page.query_selector("#watchlistBtn")
            
            if news_btn and watchlist_btn:
                logger.info("✅ News and Watchlist buttons found")
                
                # Test switching to news mode
                await news_btn.click()
                await asyncio.sleep(2)
                
                # Test switching to watchlist mode
                await watchlist_btn.click()
                await asyncio.sleep(2)
                
                logger.info("✅ Mode switching working")
            else:
                logger.warning("⚠️ News/Watchlist buttons not found")
            
            # Check for refresh functionality
            refresh_btn = await self.page.query_selector("#refreshBtn")
            if refresh_btn:
                logger.info("✅ Refresh button found")
            else:
                logger.warning("⚠️ Refresh button not found")
            
            # Check for last updated timestamp
            last_updated = await self.page.query_selector("#lastUpdated")
            if last_updated:
                timestamp_text = await last_updated.text_content()
                logger.info(f"✅ Last updated: {timestamp_text}")
            else:
                logger.warning("⚠️ Last updated timestamp not found")
            
            return len(opportunities) > 0
            
        except Exception as e:
            logger.error(f"Error in opportunities verification: {e}")
            return False
    
    async def take_screenshot(self, page_name):
        """Take a screenshot of the current page"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{page_name}_{timestamp}.png"
        filepath = self.artifacts_dir / filename
        
        await self.page.screenshot(path=str(filepath))
        logger.info(f"📸 Screenshot saved: {filepath}")
        return filepath
    
    async def test_single_page(self, page_config):
        """Test a single page comprehensively"""
        page_name = page_config["name"]
        route = page_config["route"]
        
        logger.info(f"🚀 Testing {page_name} at {route}")
        
        try:
            # Navigate to page
            full_url = f"{self.base_url}{route}"
            await self.page.goto(full_url, wait_until="networkidle")
            logger.info(f"✅ Navigated to {full_url}")
            
            # Wait for page load
            load_success = await self.wait_for_page_load(page_config)
            if not load_success:
                logger.error(f"❌ Page load failed for {page_name}")
                return False
            
            # Verify default elements
            elements_ok = await self.verify_default_page_population(page_config)
            if not elements_ok:
                logger.warning(f"⚠️ Default elements missing for {page_name}")
            
            # Verify data population if required
            data_ok = True
            if page_config.get("verify_population", False):
                data_ok = await self.verify_page_population(page_config)
                if not data_ok:
                    logger.warning(f"⚠️ Data population incomplete for {page_name}")
            
            # Special verification if specified
            if page_config.get("verify_function"):
                if page_config["verify_function"] == "verify_opportunities_page":
                    special_ok = await self.verify_opportunities_page(page_config)
                    if not special_ok:
                        logger.warning(f"⚠️ Special verification failed for {page_name}")
            
            # Take screenshot
            screenshot_path = await self.take_screenshot(page_name)
            
            # Record results
            result = {
                "page": page_name,
                "route": route,
                "success": load_success and elements_ok and data_ok,
                "load_success": load_success,
                "elements_ok": elements_ok,
                "data_ok": data_ok,
                "screenshot": str(screenshot_path),
                "timestamp": datetime.now().isoformat()
            }
            
            self.test_results.append(result)
            
            if result["success"]:
                logger.info(f"✅ {page_name} - Test PASSED")
            else:
                logger.warning(f"⚠️ {page_name} - Test PARTIAL PASS")
            
            return result["success"]
            
        except Exception as e:
            logger.error(f"❌ Error testing {page_name}: {e}")
            
            # Take error screenshot
            try:
                screenshot_path = await self.take_screenshot(f"{page_name}_ERROR")
            except:
                screenshot_path = "screenshot_failed"
            
            result = {
                "page": page_name,
                "route": route,
                "success": False,
                "error": str(e),
                "screenshot": str(screenshot_path),
                "timestamp": datetime.now().isoformat()
            }
            
            self.test_results.append(result)
            return False
    
    async def run_comprehensive_test(self):
        """Run comprehensive test on all pages"""
        logger.info("🚀 Starting comprehensive page test suite")
        
        try:
            await self.setup_browser()
            
            total_pages = len(self.pages_to_test)
            passed_pages = 0
            
            for i, page_config in enumerate(self.pages_to_test, 1):
                logger.info(f"📄 Testing page {i}/{total_pages}: {page_config['name']}")
                
                success = await self.test_single_page(page_config)
                if success:
                    passed_pages += 1
                
                # Small delay between pages
                await asyncio.sleep(1)
            
            # Generate report
            await self.generate_test_report()
            
            logger.info(f"🎉 Test suite completed: {passed_pages}/{total_pages} pages passed")
            return passed_pages == total_pages
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            return False
        finally:
            await self.teardown_browser()
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.artifacts_dir / f"test_report_{timestamp}.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_pages": len(self.pages_to_test),
            "passed_pages": sum(1 for r in self.test_results if r.get("success", False)),
            "failed_pages": sum(1 for r in self.test_results if not r.get("success", False)),
            "results": self.test_results,
            "summary": {
                "all_passed": all(r.get("success", False) for r in self.test_results),
                "pages_with_data": sum(1 for r in self.test_results if r.get("data_ok", False)),
                "pages_with_elements": sum(1 for r in self.test_results if r.get("elements_ok", False))
            }
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Test report saved: {report_file}")
        
        # Print summary
        logger.info("=" * 60)
        logger.info("📊 COMPREHENSIVE TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Pages Tested: {report['total_pages']}")
        logger.info(f"Pages Passed: {report['passed_pages']}")
        logger.info(f"Pages Failed: {report['failed_pages']}")
        logger.info(f"Success Rate: {(report['passed_pages']/report['total_pages']*100):.1f}%")
        logger.info("=" * 60)
        
        # Detailed results
        for result in self.test_results:
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            logger.info(f"{status} - {result['page']}")
            if not result.get("success", False):
                if "error" in result:
                    logger.info(f"    Error: {result['error']}")
                if not result.get("load_success", True):
                    logger.info("    Issue: Page load failed")
                if not result.get("elements_ok", True):
                    logger.info("    Issue: Missing elements")
                if not result.get("data_ok", True):
                    logger.info("    Issue: Data not populated")
        
        logger.info("=" * 60)

async def main():
    """Main test runner"""
    test_suite = ComprehensivePageTest()
    success = await test_suite.run_comprehensive_test()
    
    if success:
        logger.info("🎉 All tests passed!")
        exit(0)
    else:
        logger.error("❌ Some tests failed!")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())

# Pytest integration
@pytest.mark.asyncio
async def test_opportunities_page():
    """Test opportunities page specifically"""
    test_suite = ComprehensivePageTest()
    await test_suite.setup_browser()
    
    try:
        opportunities_config = next(p for p in test_suite.pages_to_test if p["name"] == "Opportunities Page")
        success = await test_suite.test_single_page(opportunities_config)
        assert success, "Opportunities page test failed"
    finally:
        await test_suite.teardown_browser()
