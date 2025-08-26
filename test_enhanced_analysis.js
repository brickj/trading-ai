const { test, expect } = require('@playwright/test');

test('Verify Enhanced Analysis Display', async ({ page }) => {
  // Navigate to the dashboard
  await page.goto('http://localhost:5001');
  
  // Wait for the page to load
  await page.waitForSelector('#symbol', { state: 'visible' });
  
  // Enter a stock symbol
  await page.fill('#symbol', 'AAPL');
  
  // Click the Enhanced Analysis button
  await page.click('#enhanced-analysis-btn');
  
  // Wait for the analysis results to load
  await page.waitForSelector('.enhanced-analysis-container', { state: 'visible', timeout: 30000 });
  
  // Verify the enhanced analysis container is visible
  const enhancedContainer = await page.$('.enhanced-analysis-container');
  expect(enhancedContainer).not.toBeNull();
  
  // Verify multiple strategies are displayed
  const strategies = await page.$$('.strategy-card');
  expect(strategies.length).toBeGreaterThan(0);
  
  // Verify backtest results are displayed
  const backtestResults = await page.$$('.backtest-results');
  expect(backtestResults.length).toBeGreaterThan(0);
  
  // Verify performance metrics are displayed
  const performanceMetrics = await page.$$('.performance-metrics');
  expect(performanceMetrics.length).toBeGreaterThan(0);
  
  // Take a screenshot for verification
  await page.screenshot({ path: 'enhanced-analysis-test.png' });
  
  // Log success
  console.log('Enhanced analysis display test passed successfully!');
});
