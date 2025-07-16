import asyncio
from playwright.async_api import async_playwright, expect

async def test_recommendations_table_populated():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('http://localhost:5001/recommendations')

        # Wait for the table to load
        await page.wait_for_selector('#recommendations-table-body')
        # Wait for loading to disappear
        await page.wait_for_function("!document.querySelector('#recommendations-table-body td.text-center') || !document.querySelector('#recommendations-table-body td.text-center').innerText.includes('Loading')")

        # Check that at least one data row is present
        rows = await page.query_selector_all('#recommendations-table-body tr')
        assert len(rows) > 0, 'No rows found in recommendations table.'

        # Check that the first row is not a 'No recommendations found' message
        first_row_text = await rows[0].inner_text()
        assert 'No recommendations found' not in first_row_text, 'Table is empty.'
        assert 'Loading' not in first_row_text, 'Table is still loading.'

        print('✅ Recommendations table is fully populated.')
        await browser.close()

async def main():
    try:
        await test_recommendations_table_populated()
    except AssertionError as e:
        print(f'❌ Test failed: {e}. Retrying once...')
        await asyncio.sleep(2)
        await test_recommendations_table_populated()

if __name__ == '__main__':
    asyncio.run(main()) 