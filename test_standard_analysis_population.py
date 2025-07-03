#!/usr/bin/env python3
"""
Test script to verify that target_gain and stop_loss values are populated
in the frontend when the standard analysis button is clicked.
"""
import asyncio
from playwright.async_api import async_playwright

async def test_standard_analysis_population():
    """Test if target_gain and stop_loss values are populated in the frontend"""
    print("Starting test to verify target_gain and stop_loss population...")
    
    async with async_playwright() as p:
        # Launch the browser (not headless so we can see what's happening)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Navigate to the index page
            await page.goto("http://localhost:5001")
            print("Navigated to index page")
            
            # Wait for the page to load
            await page.wait_for_selector("#stockSymbol", state="visible", timeout=10000)
            print("Page loaded successfully")
            
            # Enter a stock symbol
            await page.fill("#stockSymbol", "AAPL")
            print("Entered stock symbol: AAPL")
            
            # Click the standard analysis button
            standard_btn = await page.query_selector("#standardAnalysisBtn")
            if not standard_btn:
                print("Could not find standard analysis button")
                return False
            
            await standard_btn.click()
            print("Clicked standard analysis button")
            
            # Wait for the analysis results to load
            try:
                # Wait for the loading state in the button
                await page.wait_for_selector("#standardBtnLoading:visible", timeout=5000)
                print("Loading indicator appeared")
                
                # Then wait for it to disappear
                await page.wait_for_selector("#standardBtnContent:visible", timeout=30000)
                print("Loading indicator disappeared")
                
                # Wait for results to appear in the resultsSection
                await page.wait_for_selector("#resultsSection:visible", timeout=10000)
                print("Analysis results appeared")
                
                # Take a screenshot of the results
                await page.screenshot(path="standard_analysis_results.png")
                print("Screenshot saved to standard_analysis_results.png")
                
                # Check if target_gain and stop_loss values are present and not empty
                html_content = await page.content()
                
                # Save the HTML content for debugging
                with open("analysis_results.html", "w") as f:
                    f.write(html_content)
                print("Saved HTML content to analysis_results.html")
                
                # Check for target_gain and stop_loss in the content
                target_gain_present = "Target Gain:" in html_content
                stop_loss_present = "Stop Loss:" in html_content
                
                # Extract the values using JavaScript
                target_gain = await page.evaluate("""
                    () => {
                        const elements = document.querySelectorAll('p');
                        for (const el of elements) {
                            if (el.textContent.includes('Target Gain:')) {
                                const value = el.textContent.split('Target Gain:')[1].trim();
                                return value;
                            }
                        }
                        return null;
                    }
                """)
                
                stop_loss = await page.evaluate("""
                    () => {
                        const elements = document.querySelectorAll('p');
                        for (const el of elements) {
                            if (el.textContent.includes('Stop Loss:')) {
                                const value = el.textContent.split('Stop Loss:')[1].trim();
                                return value;
                            }
                        }
                        return null;
                    }
                """)
                
                print(f"Target Gain value: {target_gain}")
                print(f"Stop Loss value: {stop_loss}")
                
                # Check if the values are properly populated (not empty or N/A)
                target_gain_populated = target_gain_present and target_gain and target_gain != "N/A"
                stop_loss_populated = stop_loss_present and stop_loss and stop_loss != "N/A"
                
                # Print the test results
                print("\nTest Results:")
                print(f"Target Gain field present: {target_gain_present}")
                print(f"Target Gain populated: {target_gain_populated}")
                print(f"Stop Loss field present: {stop_loss_present}")
                print(f"Stop Loss populated: {stop_loss_populated}")
                
                # Overall test result
                if target_gain_populated and stop_loss_populated:
                    print("\n✅ TEST PASSED: Frontend correctly displays populated target_gain and stop_loss values")
                    return True
                else:
                    print("\n❌ TEST FAILED: Frontend does not correctly display populated target_gain and stop_loss values")
                    return False
                    
            except Exception as e:
                print(f"Error waiting for results: {str(e)}")
                await page.screenshot(path="error_state.png")
                print("Error state screenshot saved to error_state.png")
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
    result = await test_standard_analysis_population()
    return 0 if result else 1

if __name__ == "__main__":
    asyncio.run(main())
