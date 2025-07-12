#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

async def test_scalping_page_fully_populated():
    print("Starting scalping signals Playwright test...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await page.goto("http://localhost:5001/scalping_signals", timeout=20000)
            print("Navigated to scalping signals page")

            # Click Run Analysis to ensure data is loaded
            await page.click("button:has-text('Run Analysis')")
            print("Clicked Run Analysis")

            # Wait for stats to update (should be > 0)
            await page.wait_for_selector("#totalSignals:not(:empty)", timeout=30000)
            await page.wait_for_selector("#totalOpportunities:not(:empty)", timeout=30000)
            await page.wait_for_selector("#stockCount:not(:empty)", timeout=30000)
            await page.wait_for_selector("#cryptoCount:not(:empty)", timeout=30000)
            print("Stats loaded")

            # Check stats values
            total_signals = int(await page.inner_text("#totalSignals"))
            total_opps = int(await page.inner_text("#totalOpportunities"))
            stock_count = int(await page.inner_text("#stockCount"))
            crypto_count = int(await page.inner_text("#cryptoCount"))
            assert total_signals > 0, "Total Signals should be > 0"
            assert stock_count > 0, "Stocks should be > 0"
            assert crypto_count > 0, "Cryptos should be > 0"
            print(f"Stats: Total={total_signals}, Opps={total_opps}, Stocks={stock_count}, Cryptos={crypto_count}")

            # Wait for at least one opportunity card
            await page.wait_for_selector(".opportunity-card", timeout=30000)
            cards = await page.query_selector_all(".opportunity-card")
            assert len(cards) > 0, "No opportunity cards found"
            print(f"Found {len(cards)} opportunity cards")

            # Check each card for required fields
            for idx, card in enumerate(cards):
                card_html = await card.inner_html()
                assert any(x in card_html for x in ["fa-chart-bar", "fa-coins"]), f"Card {idx} missing asset icon"
                assert "$" in card_html, f"Card {idx} missing price"
                assert "Volume Ratio" in card_html, f"Card {idx} missing volume ratio"
                assert "Sentiment" in card_html, f"Card {idx} missing sentiment"
                assert "Recommendation" in card_html, f"Card {idx} missing recommendation"
                assert "headline-item" in card_html, f"Card {idx} missing headlines"
            print("All cards have required fields")

            # Take screenshot
            await page.screenshot(path="scalping_signals_playwright.png")
            print("Screenshot saved to scalping_signals_playwright.png")
            print("\n✅ TEST PASSED: Scalping signals page is fully populated and displays all required data.")
            return True
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            await page.screenshot(path="scalping_signals_playwright_failed.png")
            print("Screenshot saved to scalping_signals_playwright_failed.png")
            return False
        finally:
            await browser.close()
            print("Browser closed")

async def main():
    result = await test_scalping_page_fully_populated()
    return 0 if result else 1

if __name__ == "__main__":
    asyncio.run(main()) 