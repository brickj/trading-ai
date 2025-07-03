#!/usr/bin/env python3
"""
Detailed Playwright test for the Analyze button functionality with console logging
"""

import asyncio
from playwright.async_api import async_playwright
import time

async def test_analyze_button_debug():
    """Test the Analyze button functionality with detailed debugging"""
    
    print("🔍 Testing Analyze button with detailed debugging...")
    
    async with async_playwright() as p:
        # Launch browser with console logging
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Listen to console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append(msg.text))
        
        # Listen to network requests
        network_requests = []
        page.on("request", lambda req: network_requests.append(f"REQUEST: {req.method} {req.url}"))
        page.on("response", lambda res: network_requests.append(f"RESPONSE: {res.status} {res.url}"))
        
        try:
            # Navigate to stocks page
            print("1️⃣ Navigating to stocks page...")
            await page.goto('http://localhost:5001/stocks')
            await page.wait_for_load_state('networkidle')
            
            # Wait for the table to load
            print("2️⃣ Waiting for table to load...")
            await page.wait_for_selector('#stocksTableBody', timeout=10000)
            
            # Clear console messages from page load
            console_messages.clear()
            network_requests.clear()
            
            # Look for the first Analyze button
            print("3️⃣ Looking for Analyze button...")
            analyze_button = await page.query_selector('button[onclick*="analyzeStock"]')
            
            if not analyze_button:
                print("❌ No Analyze button found")
                return
            
            print("✅ Found Analyze button")
            
            # Click the Analyze button
            print("4️⃣ Clicking Analyze button...")
            await analyze_button.click()
            
            # Wait for the API call to complete (up to 60 seconds)
            print("5️⃣ Waiting for API response...")
            await page.wait_for_timeout(60000)  # Wait up to 60 seconds
            
            # Print console messages
            print("\n📋 Console messages:")
            for msg in console_messages:
                print(f"   {msg}")
            
            # Print network requests
            print("\n🌐 Network requests:")
            for req in network_requests:
                print(f"   {req}")
            
            # Check the final state
            print("\n6️⃣ Checking final state...")
            
            # Check if enhanced analysis section is visible
            enhanced_section = await page.query_selector('#enhancedAnalysisResults')
            if enhanced_section:
                is_visible = await enhanced_section.is_visible()
                print(f"📊 Enhanced analysis section visible: {is_visible}")
            else:
                print("❌ Enhanced analysis section not found")
            
            # Check container content
            container = await page.query_selector('#enhancedAnalysisContainer')
            if container:
                content = await container.text_content()
                if content:
                    print(f"📊 Container content length: {len(content)}")
                    print(f"📊 Content preview: {content[:500]}...")
                    
                    # Check for specific content
                    has_price = "Current Price" in content
                    has_recommendations = "Trading Recommendations" in content
                    has_loading = "Loading" in content
                    has_error = "Error" in content
                    
                    print(f"📊 Has price data: {has_price}")
                    print(f"📊 Has recommendations: {has_recommendations}")
                    print(f"📊 Still showing loading: {has_loading}")
                    print(f"📊 Shows error: {has_error}")
                else:
                    print("📊 Container is empty")
            else:
                print("❌ Container not found")
            
            # Take a screenshot
            await page.screenshot(path='test_analyze_button_debug_result.png')
            print("📸 Screenshot saved as test_analyze_button_debug_result.png")
            
        except Exception as e:
            print(f"❌ Error during test: {e}")
            await page.screenshot(path='test_analyze_button_debug_error.png')
            print("📸 Error screenshot saved as test_analyze_button_debug_error.png")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_analyze_button_debug()) 