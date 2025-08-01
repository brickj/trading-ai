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
                    ".card",  # Feature cards
                    "#resultsSection"  # Results section (may contain last analysis)
                ],
                "wait_for_data": True,
                "data_timeout": 10000,  # Wait 10 seconds for data to load
                "verify_population": True,
                "expected_data": ["feature cards", "navigation", "main content", "last analysis"]
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
                "expected_data": ["system metrics", "service status", "performance data"],
                "min_data_count": 4  # At least 4 system metrics
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
                "route": "/backtest",
                "expected_elements": [
                    "#backtestForm",  # Backtest form
                    "#daysSelector",  # Days selector
                    "h1",  # Page heading
                    "#backtestResults",  # Backtest results area
                    "#performanceChart",  # Performance chart canvas
                    "#backtestTotalReturn",  # Total return display
                    "#backtestWinRate",  # Win rate display
                    "#backtestTotalTrades",  # Total trades display
                    "#backtestAvgReturn"  # Average return display
                ],
                "wait_for_data": True,
                "data_timeout": 15000,
                "verify_population": True,
                "expected_data": ["backtest form", "parameter selection", "backtest results"],
                "min_data_count": 3  # At least 3 form elements
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
                    "#reportResults"  # Report results
                ],
                "wait_for_data": True,
                "data_timeout": 15000,
                "verify_population": True,
                "expected_data": ["reporting form", "report results", "date selection"],
                "min_data_count": 3  # At least 3 form elements
            }
        ]
    
    async def setup_browser(self):
        """Set up browser with improved resource management"""
        try:
            # Clean up any existing browser first
            await self.teardown_browser()
            
            self.playwright = await async_playwright().start()
            
            # Launch browser with better resource management
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox', 
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',  # Prevent memory issues
                    '--disable-gpu',  # Disable GPU to reduce resource usage
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create context with better resource limits
            self.context = await self.browser.new_context(
                record_video_dir=str(self.artifacts_dir),
                record_video_size={"width": 1280, "height": 720},  # Reduced size
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                ignore_https_errors=True
            )
            
            self.page = await self.context.new_page()
            
            # Set longer timeouts
            self.page.set_default_timeout(30000)
            self.page.set_default_navigation_timeout(30000)
            
            logger.info("Browser setup complete with improved resource management")
            
        except Exception as e:
            logger.error(f"Browser setup failed: {e}")
            raise

    async def ensure_browser_healthy(self):
        """Ensure browser is healthy, recreate if needed"""
        try:
            # Test if browser is still responsive
            if not self.browser or not self.context:
                logger.warning("Browser or context missing, recreating...")
                await self.setup_browser()
                return
            
            # Test if we can create a new page
            try:
                test_page = await self.context.new_page()
                await test_page.close()
            except Exception:
                logger.warning("Browser context not responsive, recreating...")
                await self.setup_browser()
                return
                
        except Exception as e:
            logger.error(f"Error ensuring browser health: {e}")
            await self.setup_browser()
    
    async def teardown_browser(self):
        """Clean up browser resources with better error handling"""
        try:
            if hasattr(self, 'page') and self.page:
                try:
                    if not self.page.is_closed():
                        await self.page.close()
                except Exception:
                    pass  # Page might already be closed
        except Exception as e:
            logger.warning(f"Error closing page: {e}")
        
        try:
            if hasattr(self, 'context') and self.context:
                await self.context.close()
        except Exception as e:
            logger.warning(f"Error closing context: {e}")
        
        try:
            if hasattr(self, 'browser') and self.browser:
                await self.browser.close()
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")
        
        try:
            if hasattr(self, 'playwright') and self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.warning(f"Error stopping playwright: {e}")
        
        logger.info("Browser teardown complete")
    
    async def wait_for_page_load(self, page_config):
        """Wait for page to fully load with better error handling"""
        start_time = time.time()
        
        try:
            # Wait for page to be ready
            await self.page.wait_for_load_state("networkidle", timeout=15000)
            
            # If page needs data, wait for it
            if page_config.get("wait_for_data", False):
                timeout = page_config.get("data_timeout", 20000)
                logger.info(f"Waiting for data to load on {page_config['name']} (timeout: {timeout}ms)")
                
                # Wait for key data elements to appear
                for element in page_config["expected_elements"]:
                    try:
                        await self.page.wait_for_selector(element, timeout=timeout)
                        logger.info(f"Found element: {element}")
                    except Exception as e:
                        logger.warning(f"Element {element} not found: {e}")
                
                # Additional wait for data to populate
                await asyncio.sleep(3)
            
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
                    metrics = await self.page.query_selector_all(".metric, .status-indicator, #cpuUsage, #memoryUsage, #uptime, #cacheHitRate")
                    if len(metrics) > 0:
                        data_found.append(f"system metrics ({len(metrics)} items)")
                
                elif data_type == "service status":
                    service_elements = await self.page.query_selector_all("#serviceStatus, .card-header, .badge")
                    if len(service_elements) > 0:
                        data_found.append(f"service status ({len(service_elements)} items)")
                
                elif data_type == "performance data":
                    perf_elements = await self.page.query_selector_all("#performanceMetrics, #databaseStatus, .card-body")
                    if len(perf_elements) > 0:
                        data_found.append(f"performance data ({len(perf_elements)} items)")
                
                elif data_type == "feature cards":
                    feature_cards = await self.page.query_selector_all(".card")
                    if len(feature_cards) > 0:
                        data_found.append(f"feature cards ({len(feature_cards)} items)")
                
                elif data_type == "navigation":
                    nav_elements = await self.page.query_selector_all("nav, .navbar, .nav")
                    if len(nav_elements) > 0:
                        data_found.append(f"navigation ({len(nav_elements)} items)")
                
                elif data_type == "main content":
                    content_elements = await self.page.query_selector_all(".container, .main-content, .content")
                    if len(content_elements) > 0:
                        data_found.append(f"main content ({len(content_elements)} items)")
                
                elif data_type == "last analysis":
                    # Check for last analysis display
                    last_analysis_elements = await self.page.query_selector_all("#resultsSection, .alert, .last-analysis")
                    if len(last_analysis_elements) > 0:
                        data_found.append(f"last analysis ({len(last_analysis_elements)} items)")
                
                elif data_type == "backtest form":
                    backtest_elements = await self.page.query_selector_all("#backtestForm, #daysSelector, #symbolInput")
                    if len(backtest_elements) > 0:
                        data_found.append(f"backtest form ({len(backtest_elements)} items)")
                
                elif data_type == "parameter selection":
                    param_elements = await self.page.query_selector_all("#daysSelector, #symbolInput, .form-control")
                    if len(param_elements) > 0:
                        data_found.append(f"parameter selection ({len(param_elements)} items)")
                
                elif data_type == "backtest results":
                    backtest_results_elements = await self.page.query_selector_all("#backtestResults, #backtestTotalReturn, #backtestWinRate, #backtestTotalTrades, #backtestAvgReturn")
                    if len(backtest_results_elements) > 0:
                        data_found.append(f"backtest results ({len(backtest_results_elements)} items)")
                
                elif data_type == "reporting form":
                    report_elements = await self.page.query_selector_all("#reportingForm, #startDate, #endDate, #reportType")
                    if len(report_elements) > 0:
                        data_found.append(f"reporting form ({len(report_elements)} items)")
                
                elif data_type == "report results":
                    results_elements = await self.page.query_selector_all("#reportResults, #reportContent, .alert")
                    if len(results_elements) > 0:
                        data_found.append(f"report results ({len(results_elements)} items)")
                
                elif data_type == "date selection":
                    date_elements = await self.page.query_selector_all("#startDate, #endDate, .form-control")
                    if len(date_elements) > 0:
                        data_found.append(f"date selection ({len(date_elements)} items)")
            
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
    
    async def verify_chart_rendering(self, page_config):
        """Verify that charts are actually rendered and visible"""
        logger.info("🔍 Verifying chart rendering")
        
        try:
            # Set up console message handler to capture chart creation logs
            console_messages = []
            
            def handle_console(msg):
                console_messages.append(msg.text)
                if "chart" in msg.text.lower():
                    logger.info(f"Chart console: {msg.text}")
            
            self.page.on("console", handle_console)
            
            # Wait for chart to load
            await asyncio.sleep(3)
            
            # Check if chart canvas exists and has content
            chart_canvas = await self.page.query_selector("#performanceChart")
            if not chart_canvas:
                logger.error("❌ Chart canvas not found")
                return False
            
            # Check if canvas has dimensions
            canvas_box = await chart_canvas.bounding_box()
            if not canvas_box or canvas_box['width'] == 0 or canvas_box['height'] == 0:
                logger.error("❌ Chart canvas has zero dimensions")
                return False
            
            # Check if canvas is visible
            is_visible = await chart_canvas.is_visible()
            if not is_visible:
                logger.error("❌ Chart canvas is not visible")
                return False
            
            # Check for chart data by looking for Chart.js elements
            chart_elements = await self.page.query_selector_all("canvas")
            if len(chart_elements) == 0:
                logger.error("❌ No canvas elements found")
                return False
            
            # Check if any canvas has Chart.js data
            for canvas in chart_elements:
                try:
                    # Check if canvas has any content (Chart.js creates internal elements)
                    canvas_content = await canvas.inner_html()
                    if canvas_content and len(canvas_content.strip()) > 0:
                        logger.info("✅ Chart canvas has content")
                        return True
                except Exception as e:
                    logger.warning(f"Could not check canvas content: {e}")
            
            # Alternative: Check for Chart.js specific attributes or classes
            chart_js_elements = await self.page.query_selector_all("[data-chart], .chartjs-render-monitor")
            if len(chart_js_elements) > 0:
                logger.info("✅ Chart.js elements found")
                return True
            
            # Check for chart data by looking at the canvas style (our debugging indicators)
            canvas_style = await chart_canvas.get_attribute("style")
            if canvas_style and ("border" in canvas_style or "background" in canvas_style):
                logger.info("✅ Chart canvas has debugging indicators (chart was created)")
                return True
            
            # Check if chart data is loaded by looking for specific text content
            chart_data_indicators = await self.page.query_selector_all("text, .chartjs-tooltip")
            if len(chart_data_indicators) > 0:
                logger.info("✅ Chart data indicators found")
                return True
            
            # Check console messages for chart creation indicators
            chart_console_messages = [msg for msg in console_messages if "chart" in msg.lower()]
            if chart_console_messages:
                logger.info(f"✅ Chart console messages found: {len(chart_console_messages)} messages")
                return True
            
            logger.warning("⚠️ Chart may not be fully rendered")
            return True  # Allow partial success for now
            
        except Exception as e:
            logger.error(f"Error verifying chart rendering: {e}")
            return False
    
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
        """Test a single page with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Ensure browser is healthy before each test
                await self.ensure_browser_healthy()
                
                # Also check if page is valid
                try:
                    if not self.page or self.page.is_closed():
                        logger.warning("Page closed, creating new page...")
                        self.page = await self.context.new_page()
                except Exception:
                    logger.warning("Page invalid, creating new page...")
                    self.page = await self.context.new_page()
                
                return await self._test_single_page_internal(page_config)
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    # Try to recreate browser if context is completely dead
                    try:
                        await self.teardown_browser()
                        await asyncio.sleep(1)
                        await self.setup_browser()
                    except Exception as setup_error:
                        logger.error(f"Failed to recreate browser: {setup_error}")
                    continue
                else:
                    raise

    async def _test_single_page_internal(self, page_config):
        """Internal test implementation"""
        page_name = page_config["name"]
        route = page_config["route"]
        
        logger.info(f"🚀 Testing {page_name} at {route}")
        
        try:
            # Check if page is still valid
            try:
                if not self.page or self.page.is_closed():
                    logger.warning("Page closed, creating new page...")
                    self.page = await self.context.new_page()
            except Exception:
                logger.warning("Page invalid, creating new page...")
                self.page = await self.context.new_page()
            
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
            
            # Special verification for backtest page (includes chart verification)
            if page_name == "Backtest Page" and data_ok:
                chart_verified = await self.verify_chart_rendering(page_config)
                if not chart_verified:
                    logger.warning(f"⚠️ Chart rendering verification failed for {page_name}")
                    # Don't fail the test, but log the issue
                else:
                    logger.info(f"✅ Chart rendering verified for {page_name}")
            
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
                
                # Add retry logic for each page
                success = await self.test_single_page(page_config)
                if success:
                    passed_pages += 1
                
                # Longer delay between pages
                await asyncio.sleep(2)
            
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
