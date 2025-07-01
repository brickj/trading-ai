import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright

ARTIFACTS_DIR = Path("test-artifacts")
SCREENSHOTS_DIR = ARTIFACTS_DIR / "screenshots"
APP_URL = "http://localhost:5001/"

def ensure_dirs():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

async def test_position_sizes():
    ensure_dirs()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1600, "height": 1000})
        page = await context.new_page()

        try:
            # Open index page
            print("Opening index page...")
            await page.goto(APP_URL)
            await page.wait_for_load_state("networkidle")
            
            # Click Standard Analysis
            print("Clicking Standard Analysis...")
            await page.click("#standardAnalysisBtn")
            
            # Wait for results to load
            print("Waiting for results...")
            await page.wait_for_selector("#resultsSection", state="visible", timeout=15000)
            await page.wait_for_timeout(3000)  # Extra wait for content to populate
            
            # Scroll down to see Position Sizes and Trading Notes
            print("Scrolling down to capture Position Sizes and Trading Notes...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            
            # Take full page screenshot
            await page.screenshot(path=str(SCREENSHOTS_DIR / "position_sizes_trading_notes_full.png"), full_page=True)
            print(f"Screenshot saved: {SCREENSHOTS_DIR}/position_sizes_trading_notes_full.png")
            
            # Take screenshot of just the results section
            results_section = await page.query_selector("#resultsSection")
            if results_section:
                await results_section.screenshot(path=str(SCREENSHOTS_DIR / "results_section_position_sizes.png"))
                print(f"Results section screenshot saved: {SCREENSHOTS_DIR}/results_section_position_sizes.png")
            
            # Check if Position Sizes and Trading Notes are visible
            content = await page.text_content("#resultsSection")
            print("\n=== Content Check ===")
            print("Position Sizes found:", "Position Sizes" in (content or ""))
            print("Trading Notes found:", "Trading Notes" in (content or ""))
            print("Position Recommendation found:", "Position Recommendation" in (content or ""))
            
            if content and "Position Recommendation" in content:
                print("✅ Position Sizes are displaying!")
            else:
                print("❌ Position Sizes are NOT displaying")
                
            if content and "Trading Notes" in content and "No trading notes available" not in content:
                print("✅ Trading Notes are displaying!")
            else:
                print("❌ Trading Notes are NOT displaying")
            
        except Exception as e:
            print(f"Error: {e}")
            await page.screenshot(path=str(SCREENSHOTS_DIR / "error_screenshot.png"), full_page=True)
        
        finally:
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_position_sizes()) 