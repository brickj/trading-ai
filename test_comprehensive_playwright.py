#!/usr/bin/env python3
"""
Comprehensive Playwright Test Suite for Trading AI Application
==============================================================

This script tests all pages and interactive elements of the Trading AI application:
1. Navigates to all available pages
2. Tests every clickable element on each page
3. Captures performance metrics and errors
4. Records screen video and takes screenshots
5. Generates comprehensive test report

Usage:
    python test_comprehensive_playwright.py
"""

import asyncio
import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
import logging

# Test configuration
TEST_CONFIG = {
    "base_url": "http://localhost:5001",
    "pages": [
        {"path": "/", "name": "Dashboard"},
        {"path": "/stocks", "name": "Stocks"},
        {"path": "/crypto", "name": "Crypto"},
        {"path": "/opportunities", "name": "Opportunities"},
        {"path": "/system_status", "name": "System Status"},
        {"path": "/logs", "name": "Logs Viewer"}
    ],
    "wait_timeout": 30000,  # 30 seconds
    "click_delay": 1000,    # 1 second between clicks
    "screenshot_on_error": True,
    "record_video": True,
    "dangerous_selectors": [
        'button[onclick*="delete"]',
        'button[data-action*="delete"]',
        'button[class*="delete"]',
        'a[href*="delete"]',
        'button[onclick*="remove"]',
        'button[data-action*="remove"]',
        'button[class*="remove"]',
        'button[onclick*="clear"]',
        'button[data-action*="clear"]',
        'button[class*="clear"]'
    ]
}

class TestResults:
    """Class to track test results and statistics"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.pages_visited = []
        self.buttons_clicked = []
        self.errors = []
        self.response_times = []
        self.screenshots = []
        self.performance_data = {}
        
    def add_page_visit(self, page_name, url, success=True, error=None):
        self.pages_visited.append({
            "page": page_name,
            "url": url,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        
    def add_button_click(self, page_name, button_text, selector, response_time, success=True, error=None):
        self.buttons_clicked.append({
            "page": page_name,
            "button_text": button_text,
            "selector": selector,
            "response_time_ms": response_time,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        self.response_times.append(response_time)
        
    def add_error(self, page_name, error_type, message, details=None):
        self.errors.append({
            "page": page_name,
            "error_type": error_type,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    def add_screenshot(self, page_name, filepath, reason):
        self.screenshots.append({
            "page": page_name,
            "filepath": filepath,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        
    def get_summary(self):
        total_pages = len(self.pages_visited)
        successful_pages = len([p for p in self.pages_visited if p["success"]])
        total_clicks = len(self.buttons_clicked)
        successful_clicks = len([c for c in self.buttons_clicked if c["success"]])
        total_errors = len(self.errors)
        
        response_stats = {}
        if self.response_times:
            response_stats = {
                "min_ms": min(self.response_times),
                "max_ms": max(self.response_times),
                "avg_ms": sum(self.response_times) / len(self.response_times),
                "total_samples": len(self.response_times)
            }
            
        return {
            "test_duration": str(datetime.now() - self.start_time),
            "pages": {
                "total": total_pages,
                "successful": successful_pages,
                "failed": total_pages - successful_pages
            },
            "interactions": {
                "total_clicks": total_clicks,
                "successful_clicks": successful_clicks,
                "failed_clicks": total_clicks - successful_clicks
            },
            "errors": {
                "total": total_errors,
                "by_page": {}
            },
            "response_times": response_stats,
            "screenshots_taken": len(self.screenshots)
        }

class ComprehensivePlaywrightTester:
    """Main test class"""
    
    def __init__(self):
        self.results = TestResults()
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging for the test"""
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Setup logger
        logger = logging.getLogger("PlaywrightTester")
        logger.setLevel(logging.INFO)
        
        # Create file handler
        log_filename = f"logs/playwright_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    async def check_app_running(self):
        """Check if the Flask app is running"""
        try:
            import requests
            response = requests.get(TEST_CONFIG["base_url"], timeout=5)
            self.logger.info(f"✅ Flask app is running (status: {response.status_code})")
            return True
        except Exception as e:
            self.logger.error(f"❌ Flask app is not running: {e}")
            self.logger.error("Please start the app with: python start_app.py")
            return False
            
    async def wait_for_page_load(self, page, page_name):
        """Wait for page to fully load with comprehensive checks"""
        try:
            # Wait for network to be idle
            await page.wait_for_load_state("networkidle", timeout=TEST_CONFIG["wait_timeout"])
            
            # Wait for any loading spinners to disappear
            loading_selectors = [
                "#loadingSpinner",
                ".loading-spinner", 
                ".spinner",
                "[class*='loading']",
                "[id*='loading']"
            ]
            
            for selector in loading_selectors:
                try:
                    loading_element = page.locator(selector)
                    if await loading_element.is_visible():
                        self.logger.info(f"🔄 Waiting for loading element to disappear: {selector}")
                        await loading_element.wait_for(state="hidden", timeout=10000)
                except:
                    pass  # Loading element might not exist
                    
            # Wait a bit for dynamic content
            await page.wait_for_timeout(2000)
            
            self.logger.info(f"✅ Page {page_name} loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to wait for page load: {e}")
            return False
            
    async def capture_page_errors(self, page, page_name):
        """Capture any visible error messages on the page"""
        errors_found = []
        
        try:
            # Check for error alerts
            error_selectors = [
                ".alert-danger",
                ".alert-warning", 
                ".error",
                ".error-message",
                "[class*='error']",
                "[role='alert']"
            ]
            
            for selector in error_selectors:
                try:
                    error_elements = page.locator(selector)
                    count = await error_elements.count()
                    
                    for i in range(count):
                        error_element = error_elements.nth(i)
                        if await error_element.is_visible():
                            error_text = await error_element.text_content()
                            if error_text and error_text.strip():
                                # Skip disclaimers and educational messages
                                if not any(keyword in error_text.lower() for keyword in 
                                         ["disclaimer", "educational purposes", "important disclaimer"]):
                                    errors_found.append({
                                        "selector": selector,
                                        "text": error_text.strip()
                                    })
                                    self.logger.warning(f"⚠️ Error found on {page_name}: {error_text[:100]}...")
                except:
                    pass  # Element might not exist
                    
        except Exception as e:
            self.logger.error(f"Error while checking for page errors: {e}")
            
        return errors_found
        
    async def check_key_content(self, page, page_name):
        """Check that key content fields are populated on the page"""
        content_issues = []
        
        try:
            # Define key content selectors for each page
            key_selectors = {
                "Dashboard": [
                    ".card-body",
                    ".dashboard-content",
                    "#main-content",
                    "[class*='widget']"
                ],
                "Stocks": [
                    "#winnersList",
                    "#losersList", 
                    "#stocksTableBody",
                    ".stock-item"
                ],
                "Crypto": [
                    ".crypto-data",
                    ".crypto-table",
                    "[class*='crypto']"
                ],
                "Opportunities": [
                    ".opportunities-content",
                    ".opportunity-item",
                    "[class*='opportunity']"
                ],
                "System Status": [
                    ".system-status",
                    ".status-indicator",
                    "[class*='status']"
                ],
                "Logs Viewer": [
                    ".log-content",
                    ".log-entry",
                    "[class*='log']"
                ]
            }
            
            selectors_to_check = key_selectors.get(page_name, [".main-content", "#content", ".container"])
            
            for selector in selectors_to_check:
                try:
                    element = page.locator(selector)
                    if await element.is_visible():
                        content = await element.text_content()
                        if not content or content.strip() == "" or "Loading" in content:
                            content_issues.append(f"Empty or loading content in: {selector}")
                            self.logger.warning(f"⚠️ {page_name}: Empty content in {selector}")
                except:
                    pass  # Element might not exist
                    
        except Exception as e:
            self.logger.error(f"Error while checking key content: {e}")
            
        return content_issues
        
    async def take_screenshot(self, page, page_name, reason="error"):
        """Take a screenshot of the current page"""
        try:
            # Create screenshots directory
            screenshots_dir = Path("test-results/screenshots")
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{page_name.lower().replace(' ', '_')}_{reason}_{timestamp}.png"
            filepath = screenshots_dir / filename
            
            # Take screenshot
            await page.screenshot(path=str(filepath), full_page=True)
            
            self.results.add_screenshot(page_name, str(filepath), reason)
            self.logger.info(f"📸 Screenshot saved: {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return None
            
    async def find_clickable_elements(self, page, page_name):
        """Find all clickable elements on the page"""
        clickable_elements = []
        
        try:
            # Define selectors for clickable elements
            clickable_selectors = [
                "button:visible",
                "a:visible",
                "[onclick]:visible",
                "[role='button']:visible",
                "input[type='submit']:visible",
                "input[type='button']:visible",
                ".btn:visible",
                "[class*='clickable']:visible",
                "[data-toggle]:visible",
                "[data-action]:visible"
            ]
            
            for selector in clickable_selectors:
                try:
                    elements = page.locator(selector)
                    count = await elements.count()
                    
                    for i in range(count):
                        element = elements.nth(i)
                        
                        # Check if element is actually visible and enabled
                        if await element.is_visible() and await element.is_enabled():
                            # Get element info
                            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                            text_content = await element.text_content()
                            class_name = await element.get_attribute("class") or ""
                            onclick = await element.get_attribute("onclick") or ""
                            data_action = await element.get_attribute("data-action") or ""
                            
                            # Skip dangerous elements
                            element_info = f"{tag_name} {class_name} {onclick} {data_action} {text_content}".lower()
                            is_dangerous = any(danger in element_info for danger in 
                                             ["delete", "remove", "clear", "reset", "destroy"])
                            
                            if not is_dangerous:
                                clickable_elements.append({
                                    "element": element,
                                    "selector": f"{selector}:nth-child({i+1})",
                                    "text": (text_content or "").strip()[:50],
                                    "tag": tag_name,
                                    "class": class_name
                                })
                                
                except Exception as e:
                    self.logger.debug(f"Error finding elements with selector {selector}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error finding clickable elements: {e}")
            
        self.logger.info(f"🔍 Found {len(clickable_elements)} safe clickable elements on {page_name}")
        return clickable_elements
        
    async def click_element_safely(self, page, element_info, page_name):
        """Click an element safely with error handling and timing"""
        start_time = time.time()
        
        try:
            element = element_info["element"]
            selector = element_info["selector"]
            text = element_info["text"]
            
            self.logger.info(f"🖱️  Clicking: {text} ({selector})")
            
            # Scroll element into view
            await element.scroll_into_view_if_needed()
            await page.wait_for_timeout(500)  # Brief pause after scrolling
            
            # Click the element
            await element.click(timeout=5000)
            
            # Wait for any response
            await page.wait_for_timeout(TEST_CONFIG["click_delay"])
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            self.results.add_button_click(page_name, text, selector, response_time, success=True)
            self.logger.info(f"✅ Clicked successfully (response time: {response_time:.0f}ms)")
            
            return True, response_time
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            self.results.add_button_click(
                page_name, element_info.get("text", ""), 
                element_info.get("selector", ""), 
                response_time, success=False, error=error_msg
            )
            
            self.logger.error(f"❌ Click failed: {error_msg}")
            return False, response_time
            
    async def test_page(self, page, page_config):
        """Test a single page comprehensively"""
        page_name = page_config["name"]
        page_path = page_config["path"]
        page_url = f"{TEST_CONFIG['base_url']}{page_path}"
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"🧪 Testing page: {page_name} ({page_url})")
        self.logger.info(f"{'='*60}")
        
        try:
            # Navigate to page
            self.logger.info(f"📱 Navigating to {page_url}...")
            await page.goto(page_url)
            
            # Wait for page to load
            if not await self.wait_for_page_load(page, page_name):
                self.results.add_page_visit(page_name, page_url, success=False, 
                                          error="Page failed to load")
                return
                
            # Check for errors on page load
            page_errors = await self.capture_page_errors(page, page_name)
            for error in page_errors:
                self.results.add_error(page_name, "Page Error", error["text"], error["selector"])
                
            # Check key content
            content_issues = await self.check_key_content(page, page_name)
            for issue in content_issues:
                self.results.add_error(page_name, "Content Issue", issue)
                
            # Take screenshot if there are errors or content issues
            if page_errors or content_issues:
                await self.take_screenshot(page, page_name, "errors_detected")
                
            # Find clickable elements
            clickable_elements = await self.find_clickable_elements(page, page_name)
            
            # Click each element
            for i, element_info in enumerate(clickable_elements):
                self.logger.info(f"📊 Testing element {i+1}/{len(clickable_elements)}")
                
                success, response_time = await self.click_element_safely(page, element_info, page_name)
                
                # Check for new errors after click
                if success:
                    post_click_errors = await self.capture_page_errors(page, page_name)
                    new_errors = [e for e in post_click_errors if e not in page_errors]
                    
                    for error in new_errors:
                        self.results.add_error(page_name, "Post-Click Error", 
                                             error["text"], error["selector"])
                        await self.take_screenshot(page, page_name, "post_click_error")
                        
                # Brief pause between clicks
                await page.wait_for_timeout(500)
                
            # Custom check for index page enhanced analysis
            if page_path == "/":
                self.logger.info("🧪 Triggering enhanced analysis on index page...")
                enhanced_btn = page.locator("#enhancedAnalysisBtn")
                await enhanced_btn.click()
                await page.wait_for_timeout(4000)
                # Check for Position Sizes and Trading Notes
                content = await page.content()
                if ("Position Sizes" in content and "Trading Notes" in content and
                    ("No position recommendations available" not in content) and
                    ("No trading notes available" not in content)):
                    self.logger.info("✅ Position Sizes and Trading Notes are populated on index page!")
                else:
                    self.logger.error("❌ FAILURE: Position Sizes or Trading Notes are missing or empty on index page!")
                    self.results.add_error(page_name, "Content Issue", "Position Sizes or Trading Notes missing/empty after enhanced analysis")
                    await self.take_screenshot(page, page_name, "missing_position_or_notes")
                    return
                
            self.results.add_page_visit(page_name, page_url, success=True)
            self.logger.info(f"✅ Completed testing {page_name}")
            
        except Exception as e:
            error_msg = f"Page test failed: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            self.results.add_page_visit(page_name, page_url, success=False, error=error_msg)
            self.results.add_error(page_name, "Test Exception", error_msg, traceback.format_exc())
            await self.take_screenshot(page, page_name, "test_exception")
            
    async def run_comprehensive_test(self):
        """Run the comprehensive test suite"""
        self.logger.info("🚀 Starting Comprehensive Playwright Test Suite")
        self.logger.info("=" * 80)
        
        # Check if app is running
        if not await self.check_app_running():
            return False
            
        async with async_playwright() as p:
            # Launch browser
            self.logger.info("🌐 Launching browser...")
            browser = await p.chromium.launch(
                headless=False,  # Set to True for headless mode
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            
            # Create context with video recording
            record_video_dir = None
            if TEST_CONFIG["record_video"]:
                video_dir = Path("test-results/videos")
                video_dir.mkdir(parents=True, exist_ok=True)
                record_video_dir = str(video_dir)
            context = await browser.new_context(viewport={"width": 1920, "height": 1080}, record_video_dir=record_video_dir)
            page = await context.new_page()
            
            # Setup page event listeners
            page.on("console", lambda msg: self.logger.debug(f"CONSOLE [{msg.type}]: {msg.text}"))
            page.on("pageerror", lambda err: self.logger.error(f"PAGE ERROR: {err}"))
            page.on("requestfailed", lambda req: self.logger.warning(f"REQUEST FAILED: {req.url}"))
            
            try:
                # Test each page
                for page_config in TEST_CONFIG["pages"]:
                    await self.test_page(page, page_config)
                    
                self.logger.info("\n🎉 Test suite completed successfully!")
                return True
                
            except Exception as e:
                self.logger.error(f"❌ Test suite failed: {e}")
                return False
                
            finally:
                # Save video if recording
                if TEST_CONFIG["record_video"]:
                    try:
                        if page.video:
                            video_path = await page.video.path()
                            self.logger.info(f"🎥 Video recording saved: {video_path}")
                    except Exception:
                        pass
                        
                await context.close()
                await browser.close()
                
    def save_test_report(self):
        """Save comprehensive test report"""
        try:
            # Create test results directory
            results_dir = Path("test-results")
            results_dir.mkdir(exist_ok=True)
            
            # Generate report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"comprehensive_test_report_{timestamp}.json"
            report_filepath = results_dir / report_filename
            
            # Compile full report
            full_report = {
                "test_info": {
                    "test_name": "Comprehensive Playwright Test Suite",
                    "timestamp": datetime.now().isoformat(),
                    "configuration": TEST_CONFIG
                },
                "summary": self.results.get_summary(),
                "detailed_results": {
                    "pages_visited": self.results.pages_visited,
                    "buttons_clicked": self.results.buttons_clicked,
                    "errors": self.results.errors,
                    "screenshots": self.results.screenshots
                }
            }
            
            # Save report
            with open(report_filepath, 'w') as f:
                json.dump(full_report, f, indent=2, default=str)
                
            self.logger.info(f"📊 Test report saved: {report_filepath}")
            
            # Print summary to console
            self.print_test_summary()
            
            return str(report_filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to save test report: {e}")
            return None
            
    def print_test_summary(self):
        """Print a formatted test summary"""
        summary = self.results.get_summary()
        
        print("\n" + "="*80)
        print("🏁 COMPREHENSIVE TEST SUMMARY")
        print("="*80)
        
        print(f"⏱️  Test Duration: {summary['test_duration']}")
        print(f"📄 Pages Tested: {summary['pages']['successful']}/{summary['pages']['total']}")
        print(f"🖱️  Elements Clicked: {summary['interactions']['successful_clicks']}/{summary['interactions']['total_clicks']}")
        print(f"❌ Total Errors: {summary['errors']['total']}")
        print(f"📸 Screenshots: {summary['screenshots_taken']}")
        
        if summary['response_times']:
            rt = summary['response_times']
            print(f"\n📈 Response Time Statistics:")
            print(f"   Min: {rt['min_ms']:.0f}ms")
            print(f"   Avg: {rt['avg_ms']:.0f}ms") 
            print(f"   Max: {rt['max_ms']:.0f}ms")
            print(f"   Samples: {rt['total_samples']}")
            
        print(f"\n📋 Pages Visited:")
        for page in self.results.pages_visited:
            status = "✅" if page["success"] else "❌"
            print(f"   {status} {page['page']}")
            
        if self.results.errors:
            print(f"\n⚠️  Errors Found:")
            for error in self.results.errors[:10]:  # Show first 10 errors
                print(f"   • {error['page']}: {error['message'][:80]}...")
                
        print("="*80)

async def main():
    """Main function to run the comprehensive test"""
    tester = ComprehensivePlaywrightTester()
    
    try:
        # Run the test suite
        success = await tester.run_comprehensive_test()
        
        # Save test report
        report_path = tester.save_test_report()
        
        if success:
            print("\n🎉 ALL TESTS COMPLETED!")
            print("Check the test report and video recording for detailed results.")
        else:
            print("\n❌ SOME TESTS FAILED!")
            print("Check the test report for detailed error information.")
            
        if report_path:
            print(f"📊 Detailed report: {report_path}")
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        tester.logger.error(f"Test suite crashed: {e}")
        tester.logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
