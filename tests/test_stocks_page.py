import time
import pytest
from playwright.sync_api import sync_playwright, expect

# Fail test if there are any console errors
def assert_no_console_errors(console_messages):
    errors = [msg for msg in console_messages if msg.type == "error"]
    assert not errors, f"Console errors found: {[msg.text for msg in errors]}"

@pytest.mark.parametrize("browser_name", ["chromium", "firefox", "webkit"])
def test_stocks_page_load_and_refresh(browser_name):
    with sync_playwright() as p:
        browser = getattr(p, browser_name).launch()
        page = browser.new_page()
        console_messages = []
        page.on("console", lambda msg: console_messages.append(msg))

        print(f"\n🚀 Navigating to /stocks page with {browser_name}...")
        start_time = time.time()
        page.goto("http://localhost:5001/stocks")  # Update to your actual local URL
        page.wait_for_load_state("networkidle")

        # Wait for main table to appear
        page.wait_for_selector("table.stocks-table >> tr", timeout=10000)
        load_duration = time.time() - start_time
        print(f"✅ Initial data loaded in {load_duration:.2f} seconds")

        # Check Top 3 Winners
        winners = page.locator("#top-winners .stock-card")
        expect(winners).to_have_count(3)
        for i in range(3):
            card = winners.nth(i)
            expect(card).to_contain_text("↑")
            expect(card.locator(".price")).not_to_be_empty()

        # Check Bottom 3 Losers
        losers = page.locator("#bottom-losers .stock-card")
        expect(losers).to_have_count(3)
        for i in range(3):
            card = losers.nth(i)
            expect(card).to_contain_text("↓")
            expect(card.locator(".price")).not_to_be_empty()

        # Check full table has at least 6 rows
        rows = page.locator("table.stocks-table >> tr")
        assert rows.count() >= 6, "Table should have at least 6 rows"

        # Click Refresh Button
        print("🔄 Refreshing stock data...")
        refresh_start = time.time()
        page.click("button#refresh-data")
        page.wait_for_selector(".loading-spinner", state="visible", timeout=5000)
        page.wait_for_selector(".loading-spinner", state="hidden", timeout=10000)

        # Wait for updated data (you may also check for a change in timestamp or row values)
        page.wait_for_selector("table.stocks-table >> tr", timeout=10000)
        refresh_duration = time.time() - refresh_start
        print(f"✅ Data refreshed in {refresh_duration:.2f} seconds")

        # Final error check
        assert_no_console_errors(console_messages)
        print("✅ No console errors found.")

        browser.close() 