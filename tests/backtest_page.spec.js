// Playwright test for the Backtest page
const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:5001';
const BACKTEST_URL = `${BASE_URL}/backtest_page`;
const API_URL = `${BASE_URL}/api/backtest`;

// Helper to wait for results to be populated
async function waitForResults(page) {
  await page.waitForSelector('#resultsSection', { state: 'visible', timeout: 15000 });
  // Spinner should be hidden
  await expect(page.locator('#backtestLoading')).toBeHidden();
  // Summary cards should not be N/A or '-'
  for (const id of ['#initialCapital', '#finalCapital', '#totalReturn', '#winRate']) {
    const text = await page.textContent(id);
    expect(text).not.toMatch(/N\/A|^\s*-\s*$/);
  }
  // Chart canvas should be visible
  await expect(page.locator('#performanceChart')).toBeVisible();
  // Trades table should have at least one real row (not just the 'No trades executed' row)
  const tradeRows = await page.locator('#tradesTableBody tr').count();
  expect(tradeRows).toBeGreaterThan(0);
  const firstRowText = await page.textContent('#tradesTableBody tr:first-child');
  expect(firstRowText).not.toMatch(/No trades executed/);
  // Strategy statistics should not be N/A or '-'
  for (const id of ['#totalTrades', '#winningTrades', '#losingTrades', '#avgTrade', '#bestTrade', '#worstTrade']) {
    const text = await page.textContent(id);
    expect(text).not.toMatch(/N\/A|^\s*-\s*$/);
  }
}

test.describe('Backtest Page', () => {
  test('loads with saved results and displays all fields', async ({ page }) => {
    await page.goto(BACKTEST_URL);
    // Use default symbol and period (should be prepopulated)
    await waitForResults(page);
    // Screenshot for proof
    await page.screenshot({ path: 'test-artifacts/backtest_page_initial.png', fullPage: true });
  });

  test('runs new backtest and updates all fields', async ({ page }) => {
    await page.goto(BACKTEST_URL);
    // Fill form with a symbol and period
    await page.fill('#symbol', 'AAPL');
    await page.selectOption('#daysBack', '730');
    await page.click('button[type="submit"]');
    // Wait for spinner to disappear and results to show
    await waitForResults(page);
    // Screenshot for proof
    await page.screenshot({ path: 'test-artifacts/backtest_page_after_rerun.png', fullPage: true });
    // Check that summary fields are updated
    const finalCapital = await page.textContent('#finalCapital');
    expect(finalCapital).not.toBe('-');
    const totalReturn = await page.textContent('#totalReturn');
    expect(totalReturn).not.toBe('-');
    const winRate = await page.textContent('#winRate');
    expect(winRate).not.toBe('-');
    const totalTrades = await page.textContent('#totalTrades');
    expect(Number(totalTrades)).toBeGreaterThan(0);
  });
}); 