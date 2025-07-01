import asyncio
import os
import time
from pathlib import Path
from playwright.async_api import async_playwright, expect

ARTIFACTS_DIR = Path("test-artifacts")
SCREENSHOTS_DIR = ARTIFACTS_DIR / "screenshots"
VIDEOS_DIR = ARTIFACTS_DIR / "videos"
APP_URL = "http://localhost:5001/"

def ensure_dirs():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

async def restart_app():
    os.system("pkill -f start_app.py; sleep 2; nohup python3 start_app.py > app.log 2>&1 &")
    print("Waiting for app to start...")
    time.sleep(5)

async def verify_standard_analysis_results(page):
    """Verify all fields in Standard Analysis results"""
    print("Verifying Standard Analysis results...")
    
    # Wait for results section to be visible
    await page.wait_for_selector("#resultsSection", state="visible", timeout=10000)
    
    # Check that results section contains analysis content
    results_content = await page.text_content("#resultsSection")
    assert results_content and len(results_content.strip()) > 0, "Standard: Results section is empty"
    
    # Verify Stock Analysis section exists
    assert await page.is_visible("text=Stock Analysis"), "Standard: Stock Analysis section not found"
    
    # Verify sentiment analysis fields
    sentiment_text = await page.text_content("#resultsSection")
    assert "Sentiment:" in sentiment_text, "Standard: Sentiment field missing"
    assert "Confidence:" in sentiment_text, "Standard: Confidence field missing"
    
    # Verify Position Sizes and Trading Notes (from the original requirements)
    assert "Position Sizes" in sentiment_text, "Standard: Position Sizes field missing"
    assert "Trading Notes" in sentiment_text, "Standard: Trading Notes field missing"
    
    # Check that these fields are not showing "No data available" or similar
    assert "No position recommendations available" not in sentiment_text, "Standard: No position recommendations"
    assert "No trading notes available" not in sentiment_text, "Standard: No trading notes"
    
    # Verify timestamp is present
    assert "Analysis completed at:" in sentiment_text, "Standard: Analysis timestamp missing"
    
    print("✓ Standard Analysis verification passed")

async def verify_enhanced_analysis_results(page):
    """Verify all fields in Enhanced Analysis results"""
    print("Verifying Enhanced Analysis results...")
    
    # Wait for results section to be visible and updated
    await page.wait_for_selector("#resultsSection", state="visible", timeout=15000)
    
    # Wait for enhanced analysis to complete (look for enhanced-specific content)
    await page.wait_for_selector("text=Enhanced Analysis Complete", timeout=15000)
    
    # Check that results section contains enhanced analysis content
    results_content = await page.text_content("#resultsSection")
    assert results_content and len(results_content.strip()) > 0, "Enhanced: Results section is empty"
    
    # Verify Enhanced Analysis Complete alert
    assert await page.is_visible("text=Enhanced Analysis Complete"), "Enhanced: Analysis complete alert not found"
    assert await page.is_visible("text=Enhanced Multi-Strategy"), "Enhanced: Analysis type not found"
    
    # Verify Top Recommendation Card exists
    assert await page.is_visible("text=Top Recommendation"), "Enhanced: Top Recommendation card not found"
    
    # Verify all Top Recommendation fields
    top_rec_fields = [
        "Type:", "Action:", "Confidence:", "Entry Price:", "Target Price:", 
        "Stop Loss:", "Position Size:", "Risk/Reward:", "Hold Time:", "Reasoning:"
    ]
    
    for field in top_rec_fields:
        assert await page.is_visible(f"text={field}"), f"Enhanced: Top Recommendation field '{field}' not found"
    
    # Verify the actual values are not "N/A" for critical fields
    top_rec_content = await page.text_content("#resultsSection")
    assert "N/A" not in top_rec_content or top_rec_content.count("N/A") < 3, "Enhanced: Too many N/A values in Top Recommendation"
    
    # Verify Options Trading Recommendations section
    if await page.is_visible("text=Options Trading Recommendations"):
        print("Checking Options Trading Recommendations...")
        
        # Check if there are actual recommendations or "No options recommendations available"
        if await page.is_visible("text=No options recommendations available"):
            print("No options recommendations available (this is acceptable)")
        else:
            # Verify options recommendation fields
            options_fields = [
                "Action:", "Option Type:", "Strike Price:", "Option Price:", 
                "Days to Expiry:", "Position Size:", "Base Confidence:", 
                "Historical Confidence:", "Final Confidence:", "Rank:", "Reasoning:"
            ]
            
            for field in options_fields:
                assert await page.is_visible(f"text={field}"), f"Enhanced: Options field '{field}' not found"
    
    # Verify Stock Trading Recommendations section
    if await page.is_visible("text=Stock Trading Recommendations"):
        print("Checking Stock Trading Recommendations...")
        
        # Check if there are actual recommendations or "No stock recommendations available"
        if await page.is_visible("text=No stock recommendations available"):
            print("No stock recommendations available (this is acceptable)")
        else:
            # Verify stock recommendation fields
            stock_fields = [
                "Action:", "Entry Price:", "Target Price:", "Stop Loss:", 
                "Position Size:", "Risk/Reward:", "Base Confidence:", 
                "Historical Confidence:", "Final Confidence:", "Reasoning:"
            ]
            
            for field in stock_fields:
                assert await page.is_visible(f"text={field}"), f"Enhanced: Stock field '{field}' not found"
    
    # Verify Position Sizes and Trading Notes (from the original requirements)
    enhanced_content = await page.text_content("#resultsSection")
    assert "Position Size:" in enhanced_content, "Enhanced: Position Size field missing"
    
    # Check that position sizes are not showing "N/A" for all recommendations
    position_size_count = enhanced_content.count("Position Size:")
    na_count = enhanced_content.count("Position Size: N/A")
    assert na_count < position_size_count, "Enhanced: All Position Sizes are N/A"
    
    # Verify timestamp is present
    assert "Analysis completed at:" in enhanced_content, "Enhanced: Analysis timestamp missing"
    
    print("✓ Enhanced Analysis verification passed")

async def run_test():
    ensure_dirs()
    await restart_app()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            record_video_dir=str(VIDEOS_DIR),
            viewport={"width": 1600, "height": 1000}
        )
        page = await context.new_page()

        step = 1
        async def snap(label):
            nonlocal step
            path = SCREENSHOTS_DIR / f"step{step}_{label}.png"
            await page.screenshot(path=str(path), full_page=True)
            print(f"Screenshot: {path}")
            step += 1

        try:
            # Open index page
            print("Step 1: Opening index page...")
            await page.goto(APP_URL)
            await page.wait_for_load_state("networkidle")
            await snap("index_loaded")

            # Verify page loaded correctly
            assert await page.is_visible("text=Trading Dashboard"), "Dashboard title not found"
            assert await page.is_visible("#standardAnalysisBtn"), "Standard Analysis button not found"
            assert await page.is_visible("#enhancedAnalysisBtn"), "Enhanced Analysis button not found"

            # Click Standard Analysis
            print("Step 2: Clicking Standard Analysis...")
            await page.click("#standardAnalysisBtn")
            await page.wait_for_timeout(4000)
            await snap("standard_analysis_clicked")
            
            # Verify Standard Analysis results
            await verify_standard_analysis_results(page)
            await snap("standard_analysis_results")
            
            # Take a specific screenshot of Position Sizes and Trading Notes sections
            print("Step 2.5: Capturing Position Sizes and Trading Notes...")
            # Scroll down to ensure Position Sizes and Trading Notes are visible
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)  # Wait for scroll to complete
            
            # Take screenshot focused on the Position Sizes and Trading Notes sections
            await page.screenshot(path=str(SCREENSHOTS_DIR / "position_sizes_trading_notes_populated.png"), full_page=True)
            print(f"Screenshot: {SCREENSHOTS_DIR}/position_sizes_trading_notes_populated.png")
            
            # Also take a screenshot of just the results section
            results_section = await page.query_selector("#resultsSection")
            if results_section:
                await results_section.screenshot(path=str(SCREENSHOTS_DIR / "results_section_only.png"))
                print(f"Screenshot: {SCREENSHOTS_DIR}/results_section_only.png")

            # Click Enhanced Analysis
            print("Step 3: Clicking Enhanced Analysis...")
            await page.click("#enhancedAnalysisBtn")
            await page.wait_for_timeout(4000)
            await snap("enhanced_analysis_clicked")
            
            # Verify Enhanced Analysis results
            await verify_enhanced_analysis_results(page)
            await snap("enhanced_analysis_results")

            # Click Help button if present
            print("Step 4: Testing Help button...")
            if await page.is_visible('button:has-text("Help")'):
                await page.click('button:has-text("Help")')
                await page.wait_for_timeout(1000)
                await snap("help_clicked")
                
                # Verify help content is shown
                assert await page.is_visible("text=How It Works"), "Help content not found"
                
                # Close help
                await page.click('button:has-text("×")')
                await page.wait_for_timeout(500)
                await snap("help_closed")

            # Test Debug Panel toggle
            print("Step 5: Testing Debug Panel...")
            if await page.is_visible('button:has-text("Toggle")'):
                await page.click('button:has-text("Toggle")')
                await page.wait_for_timeout(500)
                await snap("debug_panel_toggled")

            # Test Theme Toggle
            print("Step 6: Testing Theme Toggle...")
            if await page.is_visible('.theme-toggle'):
                await page.click('.theme-toggle')
                await page.wait_for_timeout(500)
                await snap("theme_toggled")

            print("✓ All tests passed successfully!")

        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            await snap("test_failed")
            raise

        finally:
            # Save video
            video_path = await page.video.path() if page.video else None
            if video_path:
                print(f"Video saved: {video_path}")

            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test()) 