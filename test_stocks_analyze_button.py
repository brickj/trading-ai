#!/usr/bin/env python3
"""
Playwright test for the Analyze button functionality on the stocks page
"""

import asyncio
from playwright.async_api import async_playwright
import time

async def test_analyze_button():
    """Test the Analyze button functionality using Playwright"""
    
    print("🔍 Testing Analyze button with Playwright...")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Set to True for headless
        page = await browser.new_page()
        
        try:
            # Navigate to stocks page
            print("1️⃣ Navigating to stocks page...")
            await page.goto('http://localhost:5001/stocks')
            await page.wait_for_load_state('networkidle')
            
            # Wait for the table to load
            print("2️⃣ Waiting for table to load...")
            await page.wait_for_selector('#stocksTableBody', timeout=10000)
            
            # Check if we have stock rows
            stock_rows = await page.query_selector_all('#stocksTableBody tr')
            print(f"📊 Found {len(stock_rows)} stock rows")
            
            if len(stock_rows) == 0:
                print("❌ No stock rows found")
                return
            
            # Look for the first Analyze button
            print("3️⃣ Looking for Analyze button...")
            analyze_button = await page.query_selector('button[onclick*="analyzeStock"]')
            
            if not analyze_button:
                print("❌ No Analyze button found")
                # Let's check what buttons exist
                buttons = await page.query_selector_all('button')
                print(f"📊 Found {len(buttons)} buttons on page")
                for i, btn in enumerate(buttons):
                    text = await btn.text_content()
                    onclick = await btn.get_attribute('onclick')
                    print(f"   Button {i}: '{text}' onclick='{onclick}'")
                return
            
            print("✅ Found Analyze button")
            
            # Check if enhanced analysis section exists but is hidden
            enhanced_section = await page.query_selector('#enhancedAnalysisResults')
            if enhanced_section:
                is_visible = await enhanced_section.is_visible()
                print(f"📊 Enhanced analysis section exists, visible: {is_visible}")
            else:
                print("❌ Enhanced analysis section not found")
            
            # Click the Analyze button
            print("4️⃣ Clicking Analyze button...")
            await analyze_button.click()
            
            # Wait a moment for the API call to start
            await page.wait_for_timeout(2000)
            
            # Check if loading state appears
            loading_spinner = await page.query_selector('.spinner-border.text-primary')
            if loading_spinner:
                print("✅ Loading spinner appeared")
            else:
                print("❌ Loading spinner not found")
            
            # Wait for the enhanced analysis section to become visible
            print("5️⃣ Waiting for enhanced analysis results...")
            try:
                await page.wait_for_selector('#enhancedAnalysisResults:visible', timeout=30000)
                print("✅ Enhanced analysis section became visible")
                
                # Check if content was loaded
                container = await page.query_selector('#enhancedAnalysisContainer')
                if container:
                    content = await container.text_content()
                    if content:
                        print(f"📊 Container content length: {len(content)}")
                        print(f"📊 Content preview: {content[:200]}...")
                        
                        # Check for specific content
                        has_price = "Current Price" in content
                        has_recommendations = "Trading Recommendations" in content
                        print(f"📊 Has price data: {has_price}")
                        print(f"📊 Has recommendations: {has_recommendations}")
                    else:
                        print("📊 Container is empty")
                    
                else:
                    print("❌ Enhanced analysis container not found")
                    
            except Exception as e:
                print(f"❌ Enhanced analysis section did not become visible: {e}")
                
                # Check what's in the container anyway
                container = await page.query_selector('#enhancedAnalysisContainer')
                if container:
                    content = await container.text_content()
                    if content:
                        print(f"📊 Container content: {content}")
                    else:
                        print("📊 Container is empty")
                else:
                    print("❌ Container not found")
            
            # Wait a bit more to see if anything changes
            await page.wait_for_timeout(5000)
            
            # Take a screenshot for debugging
            await page.screenshot(path='test_analyze_button_result.png')
            print("📸 Screenshot saved as test_analyze_button_result.png")
            
        except Exception as e:
            print(f"❌ Error during test: {e}")
            await page.screenshot(path='test_analyze_button_error.png')
            print("📸 Error screenshot saved as test_analyze_button_error.png")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_analyze_button()) 