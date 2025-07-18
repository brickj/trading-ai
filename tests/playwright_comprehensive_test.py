#!/usr/bin/env python3
"""
Comprehensive Playwright Test Suite for Trading AI Application
Validates that every page is fully populated with real data
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
        
        # Define all pages to test
        self.pages_to_test = [
            {
                "name": "Homepage",
                "route": "/",
                "expected_elements": [
                    "h1",  # Main heading
                    "#howItWorksCard",  # How it works card
                    "nav"  # Navigation
                ],
                "wait_for_data": False
            },
            {
                "name": "Stocks Page",
                "route": "/stocks",
                "expected_elements": [
                    "#stocksTableBody",  # Stocks table
                    "#winnersList",  # Winners list
                    "#losersList",  # Losers list
                    "#stockAnalysisSection"  # Analysis section
                ],
                "wait_for_data": True,
                "data_timeout": 30000  # 30 seconds for data to load
            },
            {
                "name": "Crypto Page",
                "route": "/crypto",
                "expected_elements": [
                    "#cryptoAnalysisContainer",  # Crypto container
                    "#cryptoCardsRow",  # Crypto cards row
                    "#sentimentChartContainer"  # Sentiment chart
                ],
                "wait_for_data": True,
                "data_timeout": 20000
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
                "verify_function": "verify_opportunities_page"  # Custom verification function
            },
            {
                "name": "System Status Page",
                "route": "/system_status",
                "expected_elements": [
                    ".container",  # Main container
                    ".card",  # Status cards
                    "h1"  # Page heading
                ],
                "wait_for_data": True,
                "data_timeout": 15000
            },
            {
                "name": "Logs Page",
                "route": "/logs",
                "expected_elements": [
                    "#logContainer",  # Log container
                    "#logStats",  # Log statistics
                    ".container"  # Main container
                ],
                "wait_for_data": True,
                "data_timeout": 10000
            },
            {
                "name": "Portfolio Page",
                "route": "/portfolio_page",
                "expected_elements": [
                    "#portfolioContainer",  # Portfolio container
                    "#portfolioSection",  # Portfolio section
                    "#addPositionForm"  # Add position form
                ],
                "wait_for_data": False  # Uses mock data
            },
            {
                "name": "Backtest Page",
                "route": "/backtest_page",
                "expected_elements": [
                    "#backtestForm",  # Backtest form
                    "#daysSelector",  # Days selector
                    "h1"  # Page heading
                ],
                "wait_for_data": False
            },
            {
                "name": "Recommendations Page",
                "route": "/recommendations",
                "expected_elements": [
                    ".container",  # Main container
                    "h1",  # Page heading
                    ".card"  # Recommendation cards
                ],
                "wait_for_data": True,
                "data_timeout": 20000
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
                await self.page.wait_for_timeout(2000)
            
            load_time = (time.time() - start_time) * 1000
            logger.info(f"Page load time: {load_time:.2f}ms")
            return True, load_time
            
        except Exception as e:
            load_time = (time.time() - start_time) * 1000
            logger.error(f"Page load failed: {e}")
            return False, load_time
    
    async def verify_page_population(self, page_config):
        """Verify that page is fully populated with data"""
        try:
            # If there's a custom verification function, use it
            if "verify_function" in page_config and hasattr(self, page_config["verify_function"]):
                verify_func = getattr(self, page_config["verify_function"])
                return await verify_func(page_config)
                
            # Default verification for pages without custom verification
            return await self.verify_default_page_population(page_config)
            
        except Exception as e:
            logger.error(f"Error in verify_page_population: {e}")
            return {
                "is_populated": False,
                "missing_elements": [f"Verification error: {e}"],
                "loading_indicators": 0,
                "error_messages": 0,
                "page_content_length": 0
            }
    
    async def verify_default_page_population(self, page_config):
        """Default page population verification"""
        # Check for expected elements
        missing_elements = []
        for element in page_config["expected_elements"]:
            try:
                # Check if element exists (handle multiple elements)
                element_count = await self.page.locator(element).count()
                if element_count == 0:
                    missing_elements.append(element)
                    continue
                
                # For elements that should have content, check the first one
                if element_count > 0:
                    # Get text content from the first element
                    element_text = await self.page.locator(element).first.text_content()
                    if not element_text or element_text.strip() == "":
                        missing_elements.append(f"{element} (empty)")
                
            except Exception as e:
                missing_elements.append(f"{element} (error: {e})")
        
        # Check for loading indicators (be more lenient - some pages have legitimate loading states)
        loading_indicators = await self.page.locator(".spinner, .loading, [data-loading='true']").count()
        
        # Check for error messages
        error_messages = await self.page.locator(".alert-danger, .error, .error-message").count()
        
        # Determine population status - allow some loading indicators for data-dependent pages
        if page_config.get("wait_for_data", False):
            # For data-dependent pages, allow some loading indicators
            is_populated = len(missing_elements) == 0 and error_messages == 0
        else:
            # For static pages, require no loading indicators
            is_populated = len(missing_elements) == 0 and loading_indicators == 0 and error_messages == 0
        
        return {
            "is_populated": is_populated,
            "missing_elements": missing_elements,
            "loading_indicators": loading_indicators,
            "error_messages": error_messages,
            "page_content_length": len(await self.page.content())
        }
        
    async def take_snapshot(self, name):
        """Take a snapshot of the current page"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            filepath = self.artifacts_dir / filename
            
            # Take a full page screenshot
            await self.page.screenshot(path=str(filepath), full_page=True)
            logger.info(f"Snapshot saved to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error taking snapshot: {e}")
            raise
    
    async def verify_opportunities_page(self, page_config):
        """Custom verification for Opportunities page"""
        result = {
            "is_populated": False,
            "missing_elements": [],
            "loading_indicators": 0,
            "error_messages": 0,
            "page_content_length": 0,
            "opportunities_count": 0,
            "snapshot_path": None,
            "api_response": None,
            "console_errors": []
        }
        
        try:
            # Listen for console messages
            console_errors = []
            
            def handle_console(msg):
                if msg.type == 'error':
                    console_errors.append({
                        'text': msg.text,
                        'url': msg.location['url'] if hasattr(msg, 'location') and msg.location else 'unknown',
                        'line': msg.location['lineNumber'] if hasattr(msg, 'location') and msg.location else 'unknown',
                        'col': msg.location['columnNumber'] if hasattr(msg, 'location') and msg.location else 'unknown'
                    })
            
            # Add console listener
            self.page.on("console", handle_console)
            
            # First, do the default verification
            default_result = await self.verify_default_page_population(page_config)
            result.update(default_result)
            
            if not result["is_populated"]:
                logger.warning("Default page population check failed, but continuing with opportunities check")
                # Continue anyway to check for opportunities
            
            # Check for API response using page.evaluate to access browser context
            try:
                api_response = await self.page.evaluate("""async () => {
                    try {
                        // Get the preloaded data from the global scope
                        if (window.preloadedData) {
                            return {
                                source: 'preloaded_data',
                                news_count: window.preloadedData.news_count || 0,
                                watchlist_count: window.preloadedData.watchlist_count || 0,
                                news_timestamp: window.preloadedData.news_timestamp,
                                watchlist_timestamp: window.preloadedData.watchlist_timestamp
                            };
                        }
                        
                        // If no preloaded data, try to fetch it
                        const response = await fetch('/api/news_opportunities');
                        if (response.ok) {
                            const data = await response.json();
                            return {
                                source: 'api_call',
                                status: response.status,
                                data: data,
                                opportunities_count: data.data?.opportunities?.length || 0
                            };
                        }
                        return { error: `API error: ${response.status} ${response.statusText}` };
                    } catch (e) {
                        return { error: `Error checking API: ${e.message}` };
                    }
                }""")
                
                result["api_response"] = api_response
                logger.info(f"API Response: {api_response}")
                
                if "error" in api_response:
                    result["missing_elements"].append(f"API Error: {api_response['error']}")
                
            except Exception as e:
                logger.error(f"Error checking API: {e}")
                result["missing_elements"].append(f"Error checking API: {e}")
            
            # Check for opportunities with a longer timeout
            try:
                await self.page.wait_for_selector(".opportunity-card", state="attached", timeout=10000)
                opportunities = await self.page.locator(".opportunity-card").all()
                result["opportunities_count"] = len(opportunities)
                logger.info(f"Found {result['opportunities_count']} opportunity cards")
                
                if result["opportunities_count"] == 0:
                    # Check if the no-opportunities message is shown
                    no_opps_visible = await self.page.locator("#noOpportunitiesMessage").is_visible()
                    if no_opps_visible:
                        result["missing_elements"].append("No opportunities message is shown")
                    else:
                        result["missing_elements"].append("No opportunity cards found")
                    
                    # Take a snapshot to help with debugging
                    try:
                        snapshot_path = await self.take_snapshot("opportunities_empty")
                        result["snapshot_path"] = snapshot_path
                        logger.info(f"Snapshot of empty opportunities page saved to {snapshot_path}")
                    except Exception as e:
                        logger.error(f"Failed to take snapshot: {e}")
                    
                    result["is_populated"] = False
                    return result
                
                # Verify each opportunity card has required elements
                for i, card in enumerate(opportunities[:3]):  # Check first 3 cards
                    try:
                        # Check for required elements in each card
                        required_elements = [
                            ".symbol",
                            ".price",
                            ".change",
                            ".sentiment",
                            ".recommendation"
                        ]
                        
                        for elem in required_elements:
                            elem_count = await card.locator(elem).count()
                            if elem_count == 0:
                                result["missing_elements"].append(f"Card {i+1} missing {elem}")
                                result["is_populated"] = False
                                
                                # Log the card HTML for debugging
                                try:
                                    card_html = await card.evaluate('el => el.outerHTML')
                                    logger.warning(f"Card {i+1} HTML (missing {elem}): {card_html[:500]}...")
                                except Exception as e:
                                    logger.error(f"Error getting card HTML: {e}")
                    except Exception as e:
                        error_msg = f"Error checking card {i+1}: {e}"
                        result["missing_elements"].append(error_msg)
                        logger.error(error_msg)
                        result["is_populated"] = False
            except Exception as e:
                error_msg = f"Error finding opportunity cards: {e}"
                result["missing_elements"].append(error_msg)
                logger.error(error_msg)
                result["is_populated"] = False
            
            # Check for console errors
            if console_errors:
                result["console_errors"] = console_errors
                logger.error(f"Found {len(console_errors)} console errors")
                for i, err in enumerate(console_errors[:3]):  # Log first 3 errors
                    logger.error(f"Console Error {i+1}: {err['text']} at {err['url']}:{err['line']}:{err['col']}")
            
            # If we got this far and no missing elements, consider it populated
            if not result["missing_elements"]:
                result["is_populated"] = True
            
            # Take a snapshot if the page is populated or if we have errors
            try:
                status = "verified" if result["is_populated"] else "errors"
                snapshot_path = await self.take_snapshot(f"opportunities_{status}")
                result["snapshot_path"] = snapshot_path
                logger.info(f"Snapshot saved to {snapshot_path}")
            except Exception as e:
                logger.error(f"Failed to take snapshot: {e}")
                result["missing_elements"].append(f"Failed to take snapshot: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in verify_opportunities_page: {e}")
            result["is_populated"] = False
            result["missing_elements"].append(f"Verification error: {e}")
            
            # Try to take a snapshot even if there was an error
            try:
                snapshot_path = await self.take_snapshot("opportunities_error")
                result["snapshot_path"] = snapshot_path
                logger.info(f"Error snapshot saved to {snapshot_path}")
            except Exception as snapshot_error:
                logger.error(f"Failed to take error snapshot: {snapshot_error}")
            
            return result
    
    async def take_screenshot(self, page_name):
        """Take screenshot of the current page"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{page_name.lower().replace(' ', '_')}_{timestamp}.png"
            filepath = self.artifacts_dir / filename
            
            await self.page.screenshot(path=str(filepath), full_page=True)
            logger.info(f"Screenshot saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None
    
    async def test_single_page(self, page_config):
        """Test a single page for full population"""
        page_name = page_config["name"]
        route = page_config["route"]
        
        logger.info(f"Testing page: {page_name} ({route})")
        
        try:
            # Navigate to page
            start_time = time.time()
            await self.page.goto(f"{self.base_url}{route}")
            
            # Wait for page to load
            load_success, load_time = await self.wait_for_page_load(page_config)
            
            # Verify page population
            population_result = await self.verify_page_population(page_config)
            
            # Take screenshot
            screenshot_path = await self.take_screenshot(page_name)
            
            # Wait between pages to mimic user behavior
            await self.page.wait_for_timeout(2000)
            
            test_time = (time.time() - start_time) * 1000
            
            # Record test result
            result = {
                "page_name": page_name,
                "route": route,
                "timestamp": datetime.now().isoformat(),
                "load_success": load_success,
                "load_time_ms": load_time,
                "total_test_time_ms": test_time,
                "population_result": population_result,
                "screenshot_path": screenshot_path,
                "status": "PASS" if load_success and population_result["is_populated"] else "FAIL"
            }
            
            self.test_results.append(result)
            
            if result["status"] == "PASS":
                logger.info(f"✅ {page_name}: PASSED (populated in {load_time:.2f}ms)")
            else:
                logger.error(f"❌ {page_name}: FAILED - {population_result['missing_elements']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing {page_name}: {e}")
            
            result = {
                "page_name": page_name,
                "route": route,
                "timestamp": datetime.now().isoformat(),
                "load_success": False,
                "load_time_ms": 0,
                "total_test_time_ms": 0,
                "population_result": {
                    "is_populated": False,
                    "missing_elements": [f"Test error: {e}"],
                    "loading_indicators": 0,
                    "error_messages": 0,
                    "page_content_length": 0
                },
                "screenshot_path": None,
                "status": "FAIL"
            }
            
            self.test_results.append(result)
            return result
    
    async def run_comprehensive_test(self):
        """Run comprehensive test on all pages"""
        logger.info("🚀 Starting Comprehensive Page Population Test")
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"Artifacts directory: {self.artifacts_dir}")

        try:
            # Setup browser
            await self.setup_browser()

            # Test each page
            for page_config in self.pages_to_test:
                await self.test_single_page(page_config)

            # Generate test report
            await self.generate_test_report()

        except Exception as e:
            logger.error(f"Comprehensive test failed: {e}")
            raise

        finally:
            # Teardown browser
            await self.teardown_browser()

    async def generate_test_report(self):
        """Generate comprehensive test report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Calculate summary statistics
        total_pages = len(self.test_results)
        passed_pages = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_pages = total_pages - passed_pages
        
        avg_load_time = sum(r["load_time_ms"] for r in self.test_results) / total_pages if total_pages > 0 else 0
        
        # Create summary
        summary = {
            "test_run": {
                "timestamp": datetime.now().isoformat(),
                "base_url": self.base_url,
                "total_pages_tested": total_pages,
                "pages_passed": passed_pages,
                "pages_failed": failed_pages,
                "success_rate": f"{(passed_pages/total_pages)*100:.1f}%" if total_pages > 0 else "0%",
                "average_load_time_ms": round(avg_load_time, 2)
            },
            "page_results": self.test_results
        }
        
        # Save JSON report
        json_report_path = self.artifacts_dir / f"test_report_{timestamp}.json"
        with open(json_report_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save text report
        text_report_path = self.artifacts_dir / f"test_report_{timestamp}.txt"
        with open(text_report_path, 'w') as f:
            f.write("COMPREHENSIVE PAGE POPULATION TEST REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Test Run: {summary['test_run']['timestamp']}\n")
            f.write(f"Base URL: {summary['test_run']['base_url']}\n")
            f.write(f"Total Pages Tested: {summary['test_run']['total_pages_tested']}\n")
            f.write(f"Pages Passed: {summary['test_run']['pages_passed']}\n")
            f.write(f"Pages Failed: {summary['test_run']['pages_failed']}\n")
            f.write(f"Success Rate: {summary['test_run']['success_rate']}\n")
            f.write(f"Average Load Time: {summary['test_run']['average_load_time_ms']}ms\n\n")
            
            f.write("DETAILED RESULTS:\n")
            f.write("-" * 30 + "\n")
            
            for result in summary['page_results']:
                f.write(f"\n{result['page_name']} ({result['route']}):\n")
                f.write(f"  Status: {result['status']}\n")
                f.write(f"  Load Time: {result['load_time_ms']:.2f}ms\n")
                f.write(f"  Load Success: {result['load_success']}\n")
                f.write(f"  Is Populated: {result['population_result']['is_populated']}\n")
                
                if result['population_result']['missing_elements']:
                    f.write(f"  Missing Elements: {result['population_result']['missing_elements']}\n")
                
                if result['screenshot_path']:
                    f.write(f"  Screenshot: {result['screenshot_path']}\n")
        
        logger.info(f"Test report saved: {json_report_path}")
        logger.info(f"Text report saved: {text_report_path}")
        
        # Print summary to console
        print("\n" + "=" * 50)
        print("COMPREHENSIVE PAGE POPULATION TEST RESULTS")
        print("=" * 50)
        print(f"Total Pages Tested: {total_pages}")
        print(f"Pages Passed: {passed_pages}")
        print(f"Pages Failed: {failed_pages}")
        print(f"Success Rate: {summary['test_run']['success_rate']}")
        print(f"Average Load Time: {summary['test_run']['average_load_time_ms']}ms")
        print("=" * 50)
        
        if failed_pages > 0:
            print("\nFAILED PAGES:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  ❌ {result['page_name']}: {result['population_result']['missing_elements']}")
        
        return summary

async def main():
    """Main test runner"""
    # Check if server is running
    import requests
    try:
        response = requests.get("http://localhost:5001", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding properly")
            return
    except:
        print("❌ Server is not running. Please start the application first:")
        print("   python start_app.py")
        return
    
    # Run comprehensive test
    tester = ComprehensivePageTest()
    await tester.run_comprehensive_test()

@pytest.mark.asyncio
async def test_opportunities_page():
    """Test the opportunities page specifically with detailed logging"""
    test = ComprehensivePageTest()
    
    # Find the opportunities page config
    opp_config = None
    for page in test.pages_to_test:
        if page.get("name") == "Opportunities Page":
            opp_config = page
            break
    
    if not opp_config:
        logger.error("Opportunities Page config not found in test suite")
        assert False, "Opportunities Page config not found in test suite"
    
    # Run the test
    logger.info("Starting Opportunities Page test...")
    await test.setup_browser()
    try:
        # Navigate to the opportunities page
        url = f"{test.base_url}{opp_config['route']}"
        logger.info(f"Navigating to {url}")
        await test.page.goto(url, wait_until="networkidle")
        
        # Run the custom verification
        logger.info("Running custom verification for Opportunities Page")
        result = await test.verify_opportunities_page(opp_config)
        
        # Log detailed results
        logger.info(f"Verification result: {json.dumps(result, indent=2, default=str)}")
        
        # Assert the page is populated
        assert result["is_populated"], f"Opportunities page not properly populated. Issues: {', '.join(result['missing_elements'])}"
        
        # Take a screenshot on success
        screenshot_path = await test.take_screenshot("opportunities_page_populated")
        logger.info(f"✅ Opportunities Page test passed. Screenshot saved to: {screenshot_path}")
    except Exception as e:
        logger.error(f"❌ Opportunities Page test failed: {e}")
        # Take a screenshot on failure
        try:
            screenshot_path = await test.take_screenshot("opportunities_test_failure")
            logger.info(f"Screenshot saved to: {screenshot_path}")
        except Exception as screenshot_error:
            logger.error(f"Failed to take screenshot: {screenshot_error}")
        raise
    finally:
        await test.teardown_browser()

if __name__ == "__main__":
    asyncio.run(main())