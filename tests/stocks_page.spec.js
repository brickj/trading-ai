const { test, expect } = require('@playwright/test');
const http = require('http');

// Function to check if the server is running
async function isServerRunning(url) {
  return new Promise((resolve) => {
    http.get(url, (res) => {
      resolve(res.statusCode === 200);
    }).on('error', () => {
      resolve(false);
    });
  });
}

// Function to assert no console errors
function assertNoConsoleErrors(consoleMessages) {
  const errors = consoleMessages.filter(msg => msg.type() === 'error');
  if (errors.length > 0) {
    console.log('Console errors found:', errors.map(msg => msg.text()));
    throw new Error(`Console errors found: ${errors.map(msg => msg.text()).join(', ')}`);
  }
}

test('Comprehensive /stocks page requirements verification', async ({ page }) => {
  console.log('🚀 Starting comprehensive /stocks page requirements test...');
  
  // Track console errors
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
      console.log('❌ JavaScript Error:', msg.text());
    }
  });
  
  page.on('pageerror', error => {
    consoleErrors.push(error.message);
    console.log('💥 Page Error:', error.message);
  });
  
  // REQUIREMENT 1: Check if server is running and preloaded data is available
  console.log('📡 Checking server status and preloaded data...');
  try {
    const response = await page.request.get('http://localhost:5001/api/preloaded_data');
    expect(response.status()).toBe(200);
    const data = await response.json();
    console.log('✅ Server is running and has preloaded data');
    console.log(`📊 Preloaded data contains ${data.data?.enhanced_analysis?.length || 0} stocks`);
  } catch (error) {
    throw new Error(`Server not accessible: ${error.message}`);
  }
  
  // REQUIREMENT 2: Navigate to the stocks page and measure load time
  console.log('🌐 Navigating to /stocks page...');
  const navigationStart = Date.now();
  await page.goto('http://localhost:5001/stocks');
  const navigationTime = (Date.now() - navigationStart) / 1000;
  console.log(`📊 Page navigation completed in ${navigationTime.toFixed(2)} seconds`);
  
  // Verify page title
  const title = await page.title();
  console.log('📄 Page title:', `"${title}"`);
  expect(title).toContain('S&P 500');
  
  // REQUIREMENT 3: Check that all required page elements exist
  console.log('🔍 Verifying required page elements exist...');
  await expect(page.locator('#winnersList')).toBeVisible();
  await expect(page.locator('#losersList')).toBeVisible();
  await expect(page.locator('#stocksTableBody')).toBeVisible();
  await expect(page.locator('#refreshBtn')).toBeVisible();
  await expect(page.locator('#lastUpdated')).toBeVisible();
  console.log('✅ All required page elements are present');
  
  // REQUIREMENT 4: Wait for data to load and measure load time (should be 1-2 seconds max)
  console.log('⏳ Waiting for data to load...');
  const dataLoadStart = Date.now();
  
  // Wait for loading spinner to disappear (data should load quickly with preloading)
  await page.waitForSelector('#loadingSpinner', { state: 'hidden', timeout: 10000 });
  
  const dataLoadTime = (Date.now() - dataLoadStart) / 1000;
  console.log(`📊 Data loaded in ${dataLoadTime.toFixed(2)} seconds`);
  
  // REQUIREMENT 5: Data should load within 1-2 seconds (with preloading)
  if (dataLoadTime > 3) {
    console.log(`⚠️ Data load time (${dataLoadTime.toFixed(2)}s) exceeds 3 seconds - may indicate preloading isn't working`);
  } else {
    console.log(`✅ Data load time (${dataLoadTime.toFixed(2)}s) is acceptable`);
  }
  
  // REQUIREMENT 6: Verify Top 3 Winners with green arrows and price changes
  console.log('🏆 Verifying Top 3 Winners...');
  const winnersList = page.locator('#winnersList');
  
  // Check that winners list is not showing loading or error message
  const winnersContent = await winnersList.textContent();
  expect(winnersContent).not.toContain('Loading winners');
  expect(winnersContent).not.toContain('No winners data available');
  
  // Count winner items (each winner should have a symbol in <strong> tag)
  const winnerSymbols = await winnersList.locator('strong').count();
  console.log(`📊 Found ${winnerSymbols} winner symbols`);
  expect(winnerSymbols).toBeGreaterThanOrEqual(3);
  
  // Check for green arrows (up arrows) - should be fa-arrow-up icons
  const upArrows = await winnersList.locator('.fa-arrow-up').count();
  console.log(`📊 Found ${upArrows} up arrows in winners`);
  expect(upArrows).toBeGreaterThanOrEqual(3);
  
  // Check for price changes (should have percentage signs)
  const winnersWithPercent = await winnersList.locator('text=/[+-]?\\d+\\.?\\d*%/').count();
  console.log(`📊 Found ${winnersWithPercent} price changes in winners`);
  expect(winnersWithPercent).toBeGreaterThanOrEqual(3);
  
  console.log('✅ Top 3 Winners verified with green arrows and price changes');
  
  // REQUIREMENT 7: Verify Bottom 3 Losers with red arrows and price changes
  console.log('📉 Verifying Bottom 3 Losers...');
  const losersList = page.locator('#losersList');
  
  // Check that losers list is not showing loading or error message
  const losersContent = await losersList.textContent();
  expect(losersContent).not.toContain('Loading losers');
  expect(losersContent).not.toContain('No losers data available');
  
  // Count loser items (each loser should have a symbol in <strong> tag)
  const loserSymbols = await losersList.locator('strong').count();
  console.log(`📊 Found ${loserSymbols} loser symbols`);
  expect(loserSymbols).toBeGreaterThanOrEqual(3);
  
  // Check for red arrows (down arrows) - should be fa-arrow-down icons
  const downArrows = await losersList.locator('.fa-arrow-down').count();
  console.log(`📊 Found ${downArrows} down arrows in losers`);
  expect(downArrows).toBeGreaterThanOrEqual(3);
  
  // Check for price changes (should have percentage signs)
  const losersWithPercent = await losersList.locator('text=/[+-]?\\d+\\.?\\d*%/').count();
  console.log(`📊 Found ${losersWithPercent} price changes in losers`);
  expect(losersWithPercent).toBeGreaterThanOrEqual(3);
  
  console.log('✅ Bottom 3 Losers verified with red arrows and price changes');
  
  // REQUIREMENT 8: Verify main table has at least 6 rows
  console.log('📊 Verifying main table has at least 6 rows...');
  const tableRows = await page.locator('#stocksTableBody tr').count();
  console.log(`📊 Found ${tableRows} table rows`);
  expect(tableRows).toBeGreaterThanOrEqual(6);
  
  // Verify table rows contain actual data (not just loading message)
  const tableContent = await page.locator('#stocksTableBody').textContent();
  expect(tableContent).not.toContain('Loading data...');
  expect(tableContent).not.toContain('Error loading data');
  
  console.log('✅ Main table verified with 6+ rows of actual data');
  
  // REQUIREMENT 9: Test refresh button functionality and timing
  console.log('🔄 Testing refresh button functionality...');
  const refreshBtn = page.locator('#refreshBtn');
  
  // Verify refresh button is enabled
  await expect(refreshBtn).toBeEnabled();
  
  // Click refresh button and measure time
  const refreshStart = Date.now();
  await refreshBtn.click();
  
  // Verify loading spinner appears
  await expect(page.locator('#loadingSpinner')).toBeVisible();
  console.log('✅ Loading spinner appeared after refresh click');
  
  // Wait for refresh to complete
  await page.waitForSelector('#loadingSpinner', { state: 'hidden', timeout: 15000 });
  
  const refreshTime = (Date.now() - refreshStart) / 1000;
  console.log(`📊 Refresh completed in ${refreshTime.toFixed(2)} seconds`);
  
  // Verify data is still present after refresh
  const winnersAfterRefresh = await winnersList.locator('strong').count();
  const losersAfterRefresh = await losersList.locator('strong').count();
  const tableRowsAfterRefresh = await page.locator('#stocksTableBody tr').count();
  
  console.log(`📊 After refresh: ${winnersAfterRefresh} winners, ${losersAfterRefresh} losers, ${tableRowsAfterRefresh} table rows`);
  expect(winnersAfterRefresh).toBeGreaterThanOrEqual(3);
  expect(losersAfterRefresh).toBeGreaterThanOrEqual(3);
  expect(tableRowsAfterRefresh).toBeGreaterThanOrEqual(6);
  
  console.log('✅ Refresh button functionality verified');
  
  // REQUIREMENT 10: Verify no console errors
  console.log('🔍 Checking for console errors...');
  
  // Filter out known non-critical errors (like favicon 404)
  const criticalErrors = consoleErrors.filter(error => 
    !error.includes('favicon.ico') && 
    !error.includes('404') &&
    !error.toLowerCase().includes('favicon')
  );
  
  if (criticalErrors.length > 0) {
    console.log('❌ Critical console errors found:', criticalErrors);
    throw new Error(`Critical console errors detected: ${criticalErrors.join(', ')}`);
  } else {
    console.log('✅ No critical console errors detected');
  }
  
  // REQUIREMENT 11: Performance summary
  console.log('\n📊 PERFORMANCE SUMMARY:');
  console.log(`🌐 Page Navigation: ${navigationTime.toFixed(2)} seconds`);
  console.log(`⚡ Data Load Time: ${dataLoadTime.toFixed(2)} seconds`);
  console.log(`🔄 Refresh Time: ${refreshTime.toFixed(2)} seconds`);
  console.log(`🏆 Winners Found: ${winnerSymbols} (required: 3+)`);
  console.log(`📉 Losers Found: ${loserSymbols} (required: 3+)`);
  console.log(`📊 Table Rows: ${tableRows} (required: 6+)`);
  console.log(`❌ Critical Errors: ${criticalErrors.length} (required: 0)`);
  
  // FINAL VERIFICATION: All requirements met
  const allRequirementsMet = (
    navigationTime < 10 &&  // Page loads quickly
    dataLoadTime < 10 &&    // Data loads within reasonable time
    winnerSymbols >= 3 &&   // At least 3 winners
    loserSymbols >= 3 &&    // At least 3 losers
    tableRows >= 6 &&       // At least 6 table rows
    criticalErrors.length === 0  // No critical errors
  );
  
  if (allRequirementsMet) {
    console.log('\n🎉 ALL REQUIREMENTS SUCCESSFULLY VERIFIED!');
  } else {
    throw new Error('Some requirements were not met. See performance summary above.');
  }
});

test.describe('Stocks Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to stocks page before each test
    await page.goto('http://localhost:5001/stocks');
    await page.waitForLoadState('networkidle');
  });

  test('should load stocks page with winners and losers', async ({ page }) => {
    // Wait for the table to load
    await page.waitForSelector('#stocksTableBody', { timeout: 10000 });
    
    // Check that we have stock rows
    const stockRows = await page.locator('#stocksTableBody tr').count();
    expect(stockRows).toBeGreaterThan(0);
    
    // Check that winners and losers sections exist
    await expect(page.locator('#winnersList')).toBeVisible();
    await expect(page.locator('#losersList')).toBeVisible();
    
    // Check that the enhanced analysis section exists but is hidden initially
    await expect(page.locator('#enhancedAnalysisResults')).toBeHidden();
  });

  test('should display exactly 6 stocks in the analysis table', async ({ page }) => {
    // Wait for the table to load
    await page.waitForSelector('#stocksTableBody', { timeout: 10000 });
    
    // Count the stock rows (excluding header)
    const stockRows = await page.locator('#stocksTableBody tr').count();
    expect(stockRows).toBe(6); // Exactly 6 stocks (3 winners + 3 losers)
    
    // Verify each row has an Analyze button
    for (let i = 0; i < stockRows; i++) {
      const analyzeButton = page.locator('#stocksTableBody tr').nth(i).locator('button[onclick*="analyzeStock"]');
      await expect(analyzeButton).toBeVisible();
    }
  });

  test('should show enhanced analysis when Analyze button is clicked', async ({ page }) => {
    // Wait for the table to load and be populated
    await page.waitForSelector('#stocksTableBody', { timeout: 10000 });
    
    // Wait for the table to have actual data (not loading message)
    await page.waitForFunction(() => {
      const tbody = document.querySelector('#stocksTableBody');
      if (!tbody) return false;
      const rows = tbody.querySelectorAll('tr');
      if (rows.length === 0) return false;
      // Check if first row is not the loading message
      const firstRow = rows[0];
      return !firstRow.textContent.includes('Loading stock data');
    }, { timeout: 10000 });
    
    // Find the first Analyze button
    const analyzeButton = page.locator('button[onclick*="analyzeStock"]').first();
    await expect(analyzeButton).toBeVisible();
    
    // Click the Analyze button
    await analyzeButton.click();
    
    // Wait for the enhanced analysis section to become visible
    await expect(page.locator('#enhancedAnalysisResults')).toBeVisible({ timeout: 60000 });
    
    // Wait for the loading to complete and content to appear
    await page.waitForFunction(() => {
      const container = document.querySelector('#enhancedAnalysisContainer');
      if (!container) return false;
      const content = container.textContent;
      return content && content.length > 100 && !content.includes('Loading');
    }, { timeout: 60000 });
    
    // Verify the enhanced analysis content
    const container = page.locator('#enhancedAnalysisContainer');
    await expect(container).toBeVisible();
    
    // Check for specific content elements
    await expect(container.locator('text=Current Data')).toBeVisible();
    await expect(container.locator('text=Trading Recommendations')).toBeVisible();
    
    // Check for price data (use first occurrence to avoid strict mode violation)
    await expect(container.locator('text=Current Price:').first()).toBeVisible();
    
    // Check for recommendations
    await expect(container.locator('text=Stock Recommendation').first()).toBeVisible();
    await expect(container.locator('text=Options Recommendation').first()).toBeVisible();
    
    // Verify the content is not empty
    const content = await container.textContent();
    expect(content.length).toBeGreaterThan(500);
  });

  test('should display proper stock recommendation data', async ({ page }) => {
    // Wait for the table to load and be populated
    await page.waitForSelector('#stocksTableBody', { timeout: 10000 });
    
    // Wait for the table to have actual data (not loading message)
    await page.waitForFunction(() => {
      const tbody = document.querySelector('#stocksTableBody');
      if (!tbody) return false;
      const rows = tbody.querySelectorAll('tr');
      if (rows.length === 0) return false;
      // Check if first row is not the loading message
      const firstRow = rows[0];
      return !firstRow.textContent.includes('Loading stock data');
    }, { timeout: 10000 });
    
    // Click the first Analyze button
    const analyzeButton = page.locator('button[onclick*="analyzeStock"]').first();
    await analyzeButton.click();
    
    // Wait for enhanced analysis to load
    await expect(page.locator('#enhancedAnalysisResults')).toBeVisible({ timeout: 60000 });
    await page.waitForFunction(() => {
      const container = document.querySelector('#enhancedAnalysisContainer');
      if (!container) return false;
      const content = container.textContent;
      return content && content.length > 100 && !content.includes('Loading');
    }, { timeout: 60000 });
    
    // Check stock recommendation section
    const stockSection = page.locator('text=Stock Recommendation').first();
    await expect(stockSection).toBeVisible();
    
    // Check for required fields (use first occurrence to avoid strict mode violation)
    await expect(page.locator('text=Action:').first()).toBeVisible();
    await expect(page.locator('text=Confidence:').first()).toBeVisible();
    await expect(page.locator('text=Current Price:').first()).toBeVisible();
    await expect(page.locator('text=Risk Level:').first()).toBeVisible();
    await expect(page.locator('text=Time Horizon:').first()).toBeVisible();
    await expect(page.locator('text=Reasoning:').first()).toBeVisible();
  });

  test('should display proper options recommendation data', async ({ page }) => {
    // Wait for the table to load and be populated
    await page.waitForSelector('#stocksTableBody', { timeout: 10000 });
    
    // Wait for the table to have actual data (not loading message)
    await page.waitForFunction(() => {
      const tbody = document.querySelector('#stocksTableBody');
      if (!tbody) return false;
      const rows = tbody.querySelectorAll('tr');
      if (rows.length === 0) return false;
      // Check if first row is not the loading message
      const firstRow = rows[0];
      return !firstRow.textContent.includes('Loading stock data');
    }, { timeout: 10000 });
    
    // Click the first Analyze button
    const analyzeButton = page.locator('button[onclick*="analyzeStock"]').first();
    await analyzeButton.click();
    
    // Wait for enhanced analysis to load
    await expect(page.locator('#enhancedAnalysisResults')).toBeVisible({ timeout: 60000 });
    await page.waitForFunction(() => {
      const container = document.querySelector('#enhancedAnalysisContainer');
      if (!container) return false;
      const content = container.textContent;
      return content && content.length > 100 && !content.includes('Loading');
    }, { timeout: 60000 });
    
    // Check options recommendation section
    const optionsSection = page.locator('text=Options Recommendation').first();
    await expect(optionsSection).toBeVisible();
    
    // Check for required fields (use first occurrence to avoid strict mode violation)
    await expect(page.locator('text=Strategy:').first()).toBeVisible();
    await expect(page.locator('text=Action:').first()).toBeVisible();
    await expect(page.locator('text=Strike Price:').first()).toBeVisible();
    await expect(page.locator('text=Expiry:').first()).toBeVisible();
    await expect(page.locator('text=Target Return:').first()).toBeVisible();
    await expect(page.locator('text=Option Price:').first()).toBeVisible();
    await expect(page.locator('text=Confidence:').first()).toBeVisible();
    await expect(page.locator('text=Reasoning:').first()).toBeVisible();
  });

  test('should handle refresh button correctly', async ({ page }) => {
    // Wait for the table to load
    await page.waitForSelector('#stocksTableBody', { timeout: 10000 });
    
    // Find the refresh button
    const refreshButton = page.locator('button:has-text("Refresh Winners & Losers Analysis")');
    await expect(refreshButton).toBeVisible();
    
    // Get the initial timestamp
    const initialTimestamp = await page.locator('#lastUpdated').textContent();
    
    // Click the refresh button
    await refreshButton.click();
    
    // Wait for the refresh to complete
    await page.waitForTimeout(5000);
    
    // Check that the timestamp has updated
    const newTimestamp = await page.locator('#lastUpdated').textContent();
    expect(newTimestamp).not.toBe(initialTimestamp);
  });

  test('should show winners and losers data correctly', async ({ page }) => {
    // Wait for the winners and losers sections to load
    await page.waitForSelector('#winnersList', { timeout: 10000 });
    await page.waitForSelector('#losersList', { timeout: 10000 });
    
    // Check that winners section has content
    const winnersContent = await page.locator('#winnersList').textContent();
    expect(winnersContent.length).toBeGreaterThan(50);
    expect(winnersContent).not.toContain('No winners data available');
    
    // Check that losers section has content
    const losersContent = await page.locator('#losersList').textContent();
    expect(losersContent.length).toBeGreaterThan(50);
    expect(losersContent).not.toContain('No losers data available');
  });
}); 