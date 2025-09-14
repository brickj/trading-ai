"""
Test script for the Opportunities Page
"""
import asyncio
import json
import logging
import os
import pytest
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, expect, Page

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_opportunities.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OpportunitiesPageTest:
    """Test suite for the Opportunities page"""
    
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.artifacts_dir = Path("test_artifacts/opportunities")
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.page = None
        self.browser = None
        self.context = None
        self.playwright = None
    
    async def _log_console(self, msg):
        """Log browser console messages"""
        try:
            location = await msg.location()
            log_entry = {
                'type': msg.type,
                'text': msg.text,
                'url': location.get('url', '') if location else '',
                'line': location.get('lineNumber', '') if location else '',
                'column': location.get('columnNumber', '') if location else '',
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"CONSOLE {msg.type.upper()}: {msg.text}")
            if hasattr(self, 'console_logs'):
                self.console_logs.append(log_entry)
        except Exception as e:
            logger.error(f"Error logging console message: {e}")
    
    async def _handle_page_error(self, error):
        """Handle page errors"""
        try:
            error_info = {
                'error': str(error),
                'stack': str(error.stack) if hasattr(error, 'stack') else '',
                'timestamp': datetime.now().isoformat()
            }
            logger.error(f"PAGE ERROR: {error_info}")
            if hasattr(self, 'page_errors'):
                self.page_errors.append(error_info)
        except Exception as e:
            logger.error(f"Error handling page error: {e}")
    
    async def setup(self):
        """Set up the test environment"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=False)  # Set to False to see the browser
            
            # Initialize storage for logs and errors
            self.console_logs = []
            self.page_errors = []
            self.requests = []
            self.responses = []
            
            # Create a new context with viewport settings
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                record_video_dir='test_artifacts/videos',
                record_video_size={'width': 1920, 'height': 1080}
            )
            
            # Create a new page with default timeout settings
            self.page = await self.context.new_page()
            
            # Set up console logging and error handling after page is created
            self.page.on("console", lambda msg: asyncio.create_task(self._log_console(msg)))
            self.page.on("pageerror", lambda error: asyncio.create_task(self._handle_page_error(error)))
            
            # Increase default timeouts
            self.page.set_default_timeout(60000)  # 60 seconds
            
            # Set up request/response logging
            async def log_request(request):
                try:
                    self.requests.append({
                        'url': request.url,
                        'method': request.method,
                        'headers': dict(request.headers),
                        'post_data': request.post_data,
                        'timestamp': datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.error(f"Error logging request: {e}")
            
            async def log_response(response):
                try:
                    body = await response.body()
                    try:
                        # Try to parse as JSON
                        body = body.decode('utf-8')
                        json_body = json.loads(body)
                        body = json.dumps(json_body, indent=2)
                    except Exception as json_err:
                        # If not JSON, use as is
                        logger.debug(f"Response is not JSON: {json_err}")
                    
                    self.responses.append({
                        'url': response.url,
                        'status': response.status,
                        'status_text': response.status_text,
                        'headers': dict(response.headers),
                        'body': body,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Log API responses for debugging
                    if '/api/' in response.url and response.status == 200:
                        logger.info(f"API Response from {response.url}: {body[:500]}...")
                        
                except Exception as e:
                    logger.error(f"Error logging response: {e}")
            
            self.page.on("request", lambda req: asyncio.create_task(log_request(req)))
            self.page.on("response", lambda res: asyncio.create_task(log_response(res)))
            
            logger.info("Test setup completed successfully")
            
        except Exception as e:
            logger.error(f"Error during test setup: {e}")
            await self.teardown()
            raise
        
        # Log all requests and responses
        async def log_request(request):
            try:
                self.requests.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'post_data': request.post_data,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error logging request: {e}")
            
        async def log_response(response):
            try:
                body = await response.body()
                try:
                    # Try to parse as JSON
                    body = body.decode('utf-8')
                    json_body = json.loads(body)
                    body = json.dumps(json_body, indent=2)
                except Exception as json_err:
                    # If not JSON, use as is
                    logger.debug(f"Response is not JSON: {json_err}")
                
                self.responses.append({
                    'url': response.url,
                    'status': response.status,
                    'status_text': response.status_text,
                    'headers': dict(response.headers),
                    'body': body,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Log API responses for debugging
                if '/api/' in response.url and response.status == 200:
                    logger.info(f"API Response from {response.url}: {body[:500]}...")
                    
            except Exception as e:
                logger.error(f"Error logging response: {e}")
        
        self.page.on("request", lambda req: asyncio.create_task(log_request(req)))
        self.page.on("response", lambda res: asyncio.create_task(log_response(res)))
        
        # Setup response handler for API calls
        async def handle_response(response):
            if '/api/' in response.url:
                try:
                    response_data = {
                        'url': response.url,
                        'status': response.status,
                        'headers': dict(response.headers)
                    }
                    
                    # Only try to parse JSON if the response is OK
                    if response.ok:
                        try:
                            response_data['json'] = await response.json()
                        except:
                            response_data['text'] = await response.text()
                    
                    self.responses.append(response_data)
                    logger.info(f"API Response - {response.url} ({response.status})")
                    
                except Exception as e:
                    logger.error(f"Error processing response: {e}")
        
        # Setup request handler for logging
        async def handle_request(request):
            self.requests.append({
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers)
            })
            await request.continue_()
        
        # Setup console error handler
        console_errors = []
        
        def handle_console(msg):
            if msg.type == 'error':
                error_info = {
                    'text': msg.text,
                    'url': msg.location['url'] if hasattr(msg, 'location') and msg.location else 'unknown',
                    'line': msg.location.get('lineNumber', 'unknown') if hasattr(msg, 'location') and msg.location else 'unknown',
                    'col': msg.location.get('columnNumber', 'unknown') if hasattr(msg, 'location') and msg.location else 'unknown'
                }
                console_errors.append(error_info)
                logger.error(f"Console Error: {error_info}")
        
        # Attach handlers
        self.page.on('response', handle_response)
        self.page.on('console', handle_console)
        
        # Store console errors for later inspection
        self.console_errors = console_errors
    
    async def teardown(self):
        """Clean up test environment"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def take_screenshot(self, name):
        """Take a screenshot and save it to the artifacts directory"""
        if not self.page:
            return None
            
        screenshot_path = self.artifacts_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await self.page.screenshot(path=str(screenshot_path))
        return str(screenshot_path)
    
    async def check_console_errors(self):
        """Check for console errors on the page"""
        if not self.page:
            return []
            
        console_errors = []
        
        def handle_console(msg):
            if msg.type == 'error':
                console_errors.append({
                    'text': msg.text,
                    'url': msg.location['url'] if hasattr(msg, 'location') and msg.location else 'unknown',
                    'line': msg.location.get('lineNumber', 'unknown') if hasattr(msg, 'location') and msg.location else 'unknown',
                    'col': msg.location.get('columnNumber', 'unknown') if hasattr(msg, 'location') and msg.location else 'unknown'
                })
        
        self.page.on("console", handle_console)
        return console_errors
    
    async def save_page_content(self, name):
        """Save the current page content to a file"""
        content_path = self.artifacts_dir / f"{name}_content.html"
        content = await self.page.content()
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(content_path)
        
    async def verify_opportunities_page(self):
        """Verify the opportunities page is working correctly"""
        result = {
            "is_populated": False,
            "missing_elements": [],
            "opportunities_count": 0,
            "console_errors": [],
            "screenshot_path": None,
            "page_content_path": None,
            "network_requests": [],
            "api_responses": [],
            "preloaded_data": None,
            "page_title": None
        }
        
        try:
            # Navigate to the opportunities page with a longer timeout
            url = f"{self.base_url}/opportunities"
            logger.info(f"Navigating to {url}")
            
            try:
                # First load the page with a basic check
                response = await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
                logger.info(f"Page loaded with status: {response.status if response else 'No response'}")
                
                # Wait for the main container to be present
                await self.page.wait_for_selector("body", state="attached", timeout=10000)
                
                # Get the page title
                result["page_title"] = await self.page.title()
                logger.info(f"Page title: {result['page_title']}")
                
                # Save the initial page content
                result["page_content_path"] = await self.save_page_content("initial_page")
                
                # Wait for network to be idle (but don't fail if it takes too long)
                try:
                    await self.page.wait_for_load_state("networkidle", timeout=10000)
                except Exception as e:
                    logger.warning(f"Network idle check timed out: {e}")
                
                # Check if the opportunities container is present
                try:
                    await self.page.wait_for_selector("#opportunitiesContainer", state="attached", timeout=10000)
                except Exception as e:
                    result["missing_elements"].append(f"Opportunities container not found: {e}")
                    # Continue execution to gather more diagnostic info
                
            except Exception as e:
                result["missing_elements"].append(f"Error loading page: {e}")
                # Save error page content
                try:
                    error_content = await self.page.content()
                    error_path = self.artifacts_dir / "error_page.html"
                    with open(error_path, 'w', encoding='utf-8') as f:
                        f.write(error_content)
                    logger.error(f"Error page content saved to {error_path}")
                except Exception as save_error:
                    logger.error(f"Failed to save error page: {save_error}")
                
                return result
            
            # Check for preloaded data
            preloaded_data = await self.page.evaluate("""() => {
                try {
                    return {
                        has_preloaded_data: !!window.preloadedData,
                        news_count: window.preloadedData?.news_count || 0,
                        watchlist_count: window.preloadedData?.watchlist_count || 0,
                        news_timestamp: window.preloadedData?.news_timestamp,
                        watchlist_timestamp: window.preloadedData?.watchlist_timestamp
                    };
                } catch (e) {
                    return { error: e.toString() };
                }
            }""")
            
            if "error" in preloaded_data:
                result["missing_elements"].append(f"Error checking preloaded data: {preloaded_data['error']}")
            else:
                logger.info(f"Preloaded data: {json.dumps(preloaded_data, indent=2)}")
            
            # Check for console errors from the handler
            if hasattr(self, 'console_errors') and self.console_errors:
                result["console_errors"] = self.console_errors
                logger.error(f"Found {len(self.console_errors)} console errors")
            
            # Check for preloaded data in the page
            try:
                preloaded_data = await self.page.evaluate("""() => {
                    try {
                        return {
                            has_preloaded_data: !!window.preloadedData,
                            has_opportunities_data: !!(window.preloadedData && 
                                (window.preloadedData.news_opportunities || window.preloadedData.watchlist_opportunities)),
                            data_keys: window.preloadedData ? Object.keys(window.preloadedData) : []
                        };
                    } catch (e) {
                        return { error: e.toString() };
                    }
                }""")
                
                result["preloaded_data"] = preloaded_data
                logger.info(f"Preloaded data check: {json.dumps(preloaded_data, indent=2)}")
                
                if preloaded_data.get('error'):
                    result["missing_elements"].append(f"Error checking preloaded data: {preloaded_data['error']}")
                
            except Exception as e:
                error_msg = f"Error checking preloaded data: {e}"
                logger.error(error_msg)
                result["missing_elements"].append(error_msg)
            
            # Save network requests and responses
            result["network_requests"] = self.requests
            result["api_responses"] = self.responses
            
            # Log API responses for debugging
            if not self.responses:
                logger.warning("No API responses were captured")
            else:
                logger.info(f"Captured {len(self.responses)} API responses")
            
            # Check for opportunity cards with a longer timeout
            try:
                # Wait for either opportunity cards or no opportunities message
                try:
                    await self.page.wait_for_selector(".opportunity-card, #noOpportunitiesMessage", state="attached", timeout=15000)
                except Exception as e:
                    logger.warning(f"Neither opportunity cards nor 'no opportunities' message found: {e}")
                    
                # Check which one is visible
                has_cards = await self.page.locator(".opportunity-card").is_visible()
                has_no_opps_msg = await self.page.locator("#noOpportunitiesMessage").is_visible()
                
                if has_cards:
                    opportunities = await self.page.locator(".opportunity-card").all()
                    result["opportunities_count"] = len(opportunities)
                    logger.info(f"Found {result['opportunities_count']} opportunity cards")
                elif has_no_opps_msg:
                    logger.info("Found 'no opportunities' message")
                    result["missing_elements"].append("No opportunities message is shown")
                else:
                    # If we get here, neither is visible - take a screenshot and save HTML
                    logger.warning("Neither opportunity cards nor 'no opportunities' message is visible")
                    await self.take_screenshot("no_opportunities_visible")
                    await self.save_page_content("no_opportunities_visible")
                    result["missing_elements"].append("Neither opportunity cards nor 'no opportunities' message is visible")
                
                if result["opportunities_count"] == 0:
                    # Check if the no-opportunities message is shown
                    no_opps_visible = await self.page.locator("text=No trading opportunities found").is_visible()
                    if no_opps_visible:
                        result["missing_elements"].append("No opportunities message is shown")
                    else:
                        result["missing_elements"].append("No opportunity cards found but no message shown")
                else:
                    # Verify the first card has required elements
                    first_card = opportunities[0]
                    required_elements = [
                        ".symbol",
                        ".price",
                        ".change",
                        ".sentiment",
                        ".recommendation"
                    ]
                    
                    for elem in required_elements:
                        elem_count = await first_card.locator(elem).count()
                        if elem_count == 0:
                            result["missing_elements"].append(f"First card missing {elem}")
                            
                            # Log the card HTML for debugging
                            try:
                                card_html = await first_card.evaluate('el => el.outerHTML')
                                logger.warning(f"First card HTML (missing {elem}): {card_html[:500]}...")
                            except Exception as e:
                                logger.error(f"Error getting card HTML: {e}")
            
            except Exception as e:
                result["missing_elements"].append(f"Error finding opportunity cards: {e}")
            
            # If no missing elements, mark as populated
            if not result["missing_elements"]:
                result["is_populated"] = True
            
            # Take a screenshot for debugging
            try:
                screenshot_path = await self.take_screenshot("opportunities_verified")
                result["screenshot_path"] = screenshot_path
                logger.info(f"Screenshot saved to {screenshot_path}")
            except Exception as e:
                logger.error(f"Failed to take screenshot: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in verify_opportunities_page: {e}")
            result["missing_elements"].append(f"Verification error: {e}")
            
            # Try to take a screenshot on error
            try:
                screenshot_path = await self.take_screenshot("opportunities_error")
                result["screenshot_path"] = screenshot_path
                logger.info(f"Error screenshot saved to {screenshot_path}")
            except Exception as screenshot_error:
                logger.error(f"Failed to take error screenshot: {screenshot_error}")
            
            return result

@pytest.mark.asyncio
async def test_opportunities_page():
    """Test the opportunities page with detailed logging"""
    test = OpportunitiesPageTest()
    
    try:
        # Set up the test environment
        await test.setup()
        
        # Run the verification
        logger.info("Starting Opportunities Page test...")
        result = await test.verify_opportunities_page()
        
        # Log the detailed results
        logger.info(f"Verification result: {json.dumps(result, indent=2, default=str)}")
        
        # Log console errors if any
        if result.get("console_errors"):
            logger.error(f"Found {len(result['console_errors'])} console errors:")
            for i, err in enumerate(result["console_errors"][:5]):  # Log first 5 errors
                logger.error(f"  {i+1}. {err['text']} at {err['url']}:{err['line']}:{err['col']}")
        
        # Assert the page is populated
        assert result["is_populated"], f"Opportunities page not properly populated. Issues: {', '.join(result['missing_elements'])}"
        
        logger.info("✅ Opportunities Page test passed")
        
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
        # Clean up
        await test.teardown()

if __name__ == "__main__":
    asyncio.run(test_opportunities_page())
