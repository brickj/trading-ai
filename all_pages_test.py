import asyncio
import json
import time
from datetime import datetime
from playwright.async_api import async_playwright

# List all routes/pages you want to test
ROUTES = [
    "http://localhost:5001/",
    "http://localhost:5001/stocks",
    "http://localhost:5001/crypto",
    "http://localhost:5001/portfolio_page",
    "http://localhost:5001/backtest_page",
    "http://localhost:5001/opportunities",
    "http://localhost:5001/recommendations",
    "http://localhost:5001/logs",
    "http://localhost:5001/system_status",
    # Add more as needed
]

DESTRUCTIVE_KEYWORDS = [
    "delete", "remove", "reset", "shutdown", "deactivate", "account"
]
WHITELIST = [
    "send telegram"
]

LOG_FILE = "test_results/ui_walkthrough_log.json"

async def inject_overlay(page):
    await page.evaluate("""
        if (!window.__testOverlay) {
            const overlay = document.createElement('div');
            overlay.id = '__testOverlay';
            overlay.style.position = 'fixed';
            overlay.style.top = '20px';
            overlay.style.right = '20px';
            overlay.style.zIndex = '99999';
            overlay.style.background = 'rgba(0,0,0,0.85)';
            overlay.style.color = '#fff';
            overlay.style.padding = '18px 28px';
            overlay.style.borderRadius = '10px';
            overlay.style.fontSize = '1.3em';
            overlay.style.fontFamily = 'monospace';
            overlay.style.boxShadow = '0 2px 12px #0008';
            overlay.style.transition = 'opacity 0.3s';
            overlay.innerText = 'UI Test Starting...';
            document.body.appendChild(overlay);
            window.__testOverlay = overlay;
        }
    """)

async def update_overlay(page, text):
    await page.evaluate(f"""
        if (window.__testOverlay) {{
            window.__testOverlay.innerText = `{text}`;
        }}
    """)

async def main():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context()
        page = await context.new_page()

        # Wait for user to start screen recording
        print("Waiting 3 seconds before starting test for screen recording...")
        await page.goto(ROUTES[0])
        await inject_overlay(page)
        await update_overlay(page, "UI Test Starting in 3 seconds...")
        await page.wait_for_timeout(3000)

        for route in ROUTES:
            await page.goto(route)
            await inject_overlay(page)
            await update_overlay(page, f"Visiting: {route}")
            await page.wait_for_timeout(1200)

            # Find all visible buttons
            buttons = await page.query_selector_all("button")
            for btn in buttons:
                try:
                    text = (await btn.inner_text()).strip().lower()
                except Exception:
                    continue
                # Skip destructive buttons unless whitelisted
                if any(kw in text for kw in DESTRUCTIVE_KEYWORDS) and not any(wl in text for wl in WHITELIST):
                    continue

                # Only click visible, enabled buttons
                visible = await btn.is_visible()
                enabled = await btn.is_enabled()
                if not visible or not enabled:
                    continue

                # Click and measure response time
                start = time.time()
                await update_overlay(page, f"Clicking: {text} ...")
                try:
                    await btn.click(timeout=5000)
                except Exception as e:
                    await update_overlay(page, f"Error clicking: {text}")
                    results.append({
                        "timestamp": datetime.now().isoformat(),
                        "route": route,
                        "button": text,
                        "error": str(e)
                    })
                    await page.wait_for_timeout(1200)
                    continue

                # Wait for network idle or a short delay
                try:
                    await page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass
                await page.wait_for_timeout(800)

                elapsed = time.time() - start
                await update_overlay(page, f"Clicked: {text}\nTime: {elapsed:.2f}s")
                results.append({
                    "timestamp": datetime.now().isoformat(),
                    "route": route,
                    "button": text,
                    "response_time": elapsed
                })
                await page.wait_for_timeout(1200)

        await update_overlay(page, "✅ UI Test Complete!")
        await page.wait_for_timeout(3000)
        await browser.close()

    # Write log
    with open(LOG_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Test log written to {LOG_FILE}")

if __name__ == "__main__":
    asyncio.run(main()) 