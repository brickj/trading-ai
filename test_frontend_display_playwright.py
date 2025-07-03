#!/usr/bin/env python3
"""
Test script to verify that the frontend correctly displays target_gain and stop_loss values
from the standard analysis endpoint using Playwright.
"""
import asyncio
import json
import os
from playwright.async_api import async_playwright

async def test_frontend_display():
    """Test if the frontend correctly displays target_gain and stop_loss values"""
    print("Starting frontend display test with Playwright...")
    
    async with async_playwright() as p:
        # Launch the browser in headless mode
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to the dashboard page
            await page.goto("http://localhost:5001")
            print("Navigated to dashboard page")
            
            # Wait for the page to load
            await page.wait_for_selector("#stockSymbol", timeout=10000)
            print("Page loaded successfully")
            
            # Enter a stock symbol
            await page.fill("#stockSymbol", "AAPL")
            print("Entered stock symbol: AAPL")
            
            # Click the standard analysis button
            await page.click("#standardAnalysisBtn")
            print("Clicked standard analysis button")
            
            # Wait for the analysis to complete and results to display
            await page.wait_for_selector("#analysisResults", timeout=30000)
            print("Analysis results loaded")
            
            # Wait a bit more for the results to fully render
            await page.wait_for_timeout(2000)
            
            # Take a screenshot of the results
            await page.screenshot(path="analysis_results_playwright.png")
            print(f"Screenshot saved to analysis_results_playwright.png")
            
            # Check if target_gain and stop_loss are displayed and extract their values
            target_gain_element = await page.query_selector("text=Target Gain:")
            stop_loss_element = await page.query_selector("text=Stop Loss:")
            
            target_gain_present = target_gain_element is not None
            stop_loss_present = stop_loss_element is not None
            
            # Extract the values using JavaScript
            if target_gain_present:
                target_gain = await page.evaluate("""
                    () => {
                        const elements = document.querySelectorAll('p');
                        for (const el of elements) {
                            if (el.textContent.includes('Target Gain:')) {
                                return el.textContent.split('Target Gain:')[1].trim();
                            }
                        }
                        return 'Not found';
                    }
                """)
                print(f"Target Gain value: {target_gain}")
            else:
                target_gain = "Not found"
                print("Target Gain field not found in the results")
            
            if stop_loss_present:
                stop_loss = await page.evaluate("""
                    () => {
                        const elements = document.querySelectorAll('p');
                        for (const el of elements) {
                            if (el.textContent.includes('Stop Loss:')) {
                                return el.textContent.split('Stop Loss:')[1].trim();
                            }
                        }
                        return 'Not found';
                    }
                """)
                print(f"Stop Loss value: {stop_loss}")
            else:
                stop_loss = "Not found"
                print("Stop Loss field not found in the results")
            
            # Check if the values are properly displayed (not empty or N/A)
            target_gain_valid = target_gain_present and "N/A" not in target_gain and target_gain != "Not found"
            stop_loss_valid = stop_loss_present and "N/A" not in stop_loss and stop_loss != "Not found"
            
            # Print the test results
            print("\nTest Results:")
            print(f"Target Gain field present: {target_gain_present}")
            print(f"Target Gain value valid: {target_gain_valid}")
            print(f"Stop Loss field present: {stop_loss_present}")
            print(f"Stop Loss value valid: {stop_loss_valid}")
            
            # Get the raw HTML for debugging
            results_html = await page.inner_html("#analysisResults")
            with open("analysis_results.html", "w") as f:
                f.write(results_html)
            print("Saved results HTML to analysis_results.html")
            
            # Overall test result
            if target_gain_valid and stop_loss_valid:
                print("\n✅ TEST PASSED: Frontend correctly displays target_gain and stop_loss values")
                return True
            else:
                print("\n❌ TEST FAILED: Frontend does not correctly display target_gain and stop_loss values")
                return False
                
        except Exception as e:
            print(f"Error during test: {str(e)}")
            return False
        finally:
            # Close the browser
            await browser.close()
            print("Browser closed")

async def main():
    """Main function to run the test"""
    result = await test_frontend_display()
    return 0 if result else 1

if __name__ == "__main__":
    asyncio.run(main())
