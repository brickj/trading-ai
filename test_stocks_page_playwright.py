#!/usr/bin/env python3
"""
Playwright test for stocks page data display (DOM-only check)
"""

import asyncio
from playwright.async_api import async_playwright

async def test_stocks_page_data():
    """Test if the stocks page displays data correctly (DOM-only)"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            print("🚀 Starting stocks page data test...")
            await page.goto("http://localhost:5001/stocks")
            await page.wait_for_load_state("networkidle")
            print("✅ Page loaded")

            # Wait for winners/losers/table to be present
            await page.wait_for_selector("#winnersList", timeout=15000)
            await page.wait_for_selector("#losersList", timeout=15000)
            await page.wait_for_selector("#stocksTableBody", timeout=15000)

            # Wait a bit for JS to populate
            await page.wait_for_timeout(2000)

            # Get winners/losers/table content
            winners_html = await page.inner_html("#winnersList")
            losers_html = await page.inner_html("#losersList")
            table_html = await page.inner_html("#stocksTableBody")

            print("\n--- WINNERS SECTION ---\n", winners_html[:500])
            print("\n--- LOSERS SECTION ---\n", losers_html[:500])
            print("\n--- TABLE SECTION ---\n", table_html[:500])

            # Check for 'No winners data' or 'No losers data' messages
            winners_empty = "No winners data available" in winners_html
            losers_empty = "No losers data available" in losers_html
            table_empty = "Loading stock data" in table_html or len(table_html.strip()) == 0

            # Look for at least one stock symbol in each section
            import re
            symbol_pattern = re.compile(r'>[A-Z]{2,6}<')
            winners_has_symbol = bool(symbol_pattern.search(winners_html))
            losers_has_symbol = bool(symbol_pattern.search(losers_html))
            table_has_symbol = bool(symbol_pattern.search(table_html))

            print(f"\nWinners empty: {winners_empty}, has symbol: {winners_has_symbol}")
            print(f"Losers empty: {losers_empty}, has symbol: {losers_has_symbol}")
            print(f"Table empty: {table_empty}, has symbol: {table_has_symbol}")

            if not winners_empty and winners_has_symbol:
                print("✅ Winners section is populated with data!")
            else:
                print("❌ Winners section is NOT populated with data!")

            if not losers_empty and losers_has_symbol:
                print("✅ Losers section is populated with data!")
            else:
                print("❌ Losers section is NOT populated with data!")

            if not table_empty and table_has_symbol:
                print("✅ Table section is populated with data!")
            else:
                print("❌ Table section is NOT populated with data!")

            await page.screenshot(path="test_artifacts/screenshots/stocks_page_data_test.png")
            print("📸 Screenshot saved")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            await page.screenshot(path="test_artifacts/screenshots/stocks_page_error.png")
            raise
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_stocks_page_data()) 