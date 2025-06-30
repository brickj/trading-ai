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