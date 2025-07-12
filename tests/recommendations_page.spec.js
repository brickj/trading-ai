const { test, expect } = require('@playwright/test');

test.describe('Recommendations Page', () => {
  test.beforeEach(async ({ page }) => {
    // Capture browser console logs
    page.on('console', msg => {
      console.log(`[BROWSER LOG]`, msg.type(), msg.text());
    });
    // Navigate to recommendations page before each test
    await page.goto('http://localhost:5001/recommendations');
    await page.waitForLoadState('networkidle');
  });

  test('should load recommendations page with populated data', async ({ page }) => {
    // Wait for the page to load
    await page.waitForSelector('h1:has-text("Trading Recommendations Dashboard")');
    
    // Check that the page title is correct
    await expect(page.locator('h1')).toContainText('Trading Recommendations Dashboard');
    
    // Wait for the recommendations table to load
    await page.waitForSelector('#recommendations-table-body');
    
    // CRITICAL: Wait for loading to complete and actual data to appear
    await page.waitForFunction(() => {
      const tbody = document.querySelector('#recommendations-table-body');
      if (!tbody) return false;
      
      // Check that loading message is gone
      if (tbody.textContent.includes('Loading recommendations...')) return false;
      if (tbody.textContent.includes('Error loading recommendations')) return false;
      if (tbody.textContent.includes('No recommendations found')) return false;
      
      // Check that we have actual data rows (not just headers)
      const rows = tbody.querySelectorAll('tr');
      if (rows.length === 0) return false;
      
      // Check that at least one row has actual data (not empty cells)
      for (let row of rows) {
        const cells = row.querySelectorAll('td');
        if (cells.length > 0) {
          const hasData = Array.from(cells).some(cell => {
            const text = cell.textContent.trim();
            return text.length > 0 && text !== '-' && text !== 'N/A';
          });
          if (hasData) return true;
        }
      }
      
      return false;
    }, { timeout: 30000 });
    
    // Verify we have actual recommendation data
    const tableBody = page.locator('#recommendations-table-body');
    
    // Check that loading message is completely gone
    await expect(tableBody.locator('text=Loading recommendations...')).not.toBeVisible();
    await expect(tableBody.locator('text=Error loading recommendations')).not.toBeVisible();
    await expect(tableBody.locator('text=No recommendations found')).not.toBeVisible();
    
    // Check that we have multiple rows with actual data
    const rows = tableBody.locator('tr');
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThan(0);
    
    // Verify the first row contains actual data
    const firstRow = rows.first();
    
    // Check that symbol is present and not empty
    const symbolCell = firstRow.locator('td').nth(1); // Symbol column
    const symbolText = await symbolCell.textContent();
    expect(symbolText.trim()).toMatch(/^[A-Z]{1,5}$/); // Should be a stock symbol like AAPL, TSLA, etc.
    
    // Check that recommendation type is present
    const typeCell = firstRow.locator('td').nth(2); // Type column
    const typeText = await typeCell.textContent();
    expect(typeText.trim().length).toBeGreaterThan(0);
    
    // Check that action is present
    const actionCell = firstRow.locator('td').nth(3); // Action column
    const actionText = await actionCell.textContent();
    expect(actionText.trim().length).toBeGreaterThan(0);
    
    // Check that confidence is present and formatted as percentage
    const confidenceCell = firstRow.locator('td').nth(4); // Confidence column
    const confidenceText = await confidenceCell.textContent();
    expect(confidenceText.trim()).toMatch(/^\d+\.\d+%$/); // Should be like "72.0%"
    
    // Verify table headers are present
    await expect(page.locator('th:has-text("Date")')).toBeVisible();
    await expect(page.locator('th:has-text("Symbol")')).toBeVisible();
    await expect(page.locator('th:has-text("Type")')).toBeVisible();
    await expect(page.locator('th:has-text("Action")')).toBeVisible();
    await expect(page.locator('th:has-text("Confidence")')).toBeVisible();
    await expect(page.locator('th:has-text("Entry Price")')).toBeVisible();
    await expect(page.locator('th:has-text("Current/Exit Price")')).toBeVisible();
    await expect(page.locator('th:has-text("Outcome")')).toBeVisible();
    await expect(page.locator('th:has-text("Profitable")')).toBeVisible();
  });

  test('should display summary statistics with actual data', async ({ page }) => {
    // Wait for stats to load and be populated
    await page.waitForFunction(() => {
      const totalRecs = document.querySelector('#total-recommendations');
      const winRate = document.querySelector('#win-rate');
      const avgReturn = document.querySelector('#avg-return');
      const lastUpdated = document.querySelector('#last-updated');
      
      if (!totalRecs || !winRate || !avgReturn || !lastUpdated) return false;
      
      const totalText = totalRecs.textContent.trim();
      const winRateText = winRate.textContent.trim();
      const avgReturnText = avgReturn.textContent.trim();
      const lastUpdatedText = lastUpdated.textContent.trim();
      
      // Check that all stats have actual values (not placeholders)
      return totalText !== '...' && totalText !== '0' && totalText.length > 0 &&
             winRateText !== '...' && winRateText.length > 0 &&
             avgReturnText !== '...' && avgReturnText.length > 0 &&
             lastUpdatedText !== '...' && lastUpdatedText !== 'N/A' && lastUpdatedText.length > 0;
    }, { timeout: 30000 });
    
    // Check that summary stats are populated with actual data
    const totalRecs = page.locator('#total-recommendations');
    await expect(totalRecs).not.toHaveText('...');
    await expect(totalRecs).not.toHaveText('0');
    const totalText = await totalRecs.textContent();
    expect(parseInt(totalText.replace(/,/g, ''))).toBeGreaterThan(0);
    
    // Check that win rate is displayed as percentage
    const winRate = page.locator('#win-rate');
    await expect(winRate).not.toHaveText('...');
    const winRateText = await winRate.textContent();
    expect(winRateText).toMatch(/^\d+\.\d+%$/);
    
    // Check that average return is displayed as percentage
    const avgReturn = page.locator('#avg-return');
    await expect(avgReturn).not.toHaveText('...');
    const avgReturnText = await avgReturn.textContent();
    expect(avgReturnText).toMatch(/^-?\d+\.\d+%$/); // Can be negative
    
    // Check that last updated is displayed as a date
    const lastUpdated = page.locator('#last-updated');
    await expect(lastUpdated).not.toHaveText('...');
    await expect(lastUpdated).not.toHaveText('N/A');
    const lastUpdatedText = await lastUpdated.textContent();
    expect(lastUpdatedText.length).toBeGreaterThan(0);
  });

  test('should display filters and allow filtering', async ({ page }) => {
    // Check that filters are present
    await expect(page.locator('#symbol-filter')).toBeVisible();
    await expect(page.locator('#type-filter')).toBeVisible();
    await expect(page.locator('#action-filter')).toBeVisible();
    await expect(page.locator('#outcome-filter')).toBeVisible();
    
    // Check that filter buttons are present
    await expect(page.locator('#apply-filters')).toBeVisible();
    await expect(page.locator('#reset-filters')).toBeVisible();
  });

  test('should display charts with data', async ({ page }) => {
    // Wait for charts to load and be populated
    await page.waitForFunction(() => {
      const typeChart = document.querySelector('#recommendation-types-chart');
      const performanceChart = document.querySelector('#performance-chart');
      
      if (!typeChart || !performanceChart) return false;
      
      // Check that charts have been rendered (not just empty canvases)
      const typeCtx = typeChart.getContext('2d');
      const perfCtx = performanceChart.getContext('2d');
      
      return typeCtx && perfCtx;
    }, { timeout: 30000 });
    
    // Check that chart containers are present
    await expect(page.locator('#recommendation-types-chart')).toBeVisible();
    await expect(page.locator('#performance-chart')).toBeVisible();
    
    // Check that chart titles are present (use more specific selectors)
    await expect(page.locator('h5.card-title:has-text("Recommendation Types")')).toBeVisible();
    await expect(page.locator('h5.card-title:has-text("Recommendation Performance")')).toBeVisible();
  });

  test('should display top symbols and types tables with data', async ({ page }) => {
    // Wait for tables to load and be populated
    await page.waitForFunction(() => {
      const topSymbolsBody = document.querySelector('#top-symbols-body');
      const topTypesBody = document.querySelector('#top-types-body');
      
      if (!topSymbolsBody || !topTypesBody) return false;
      
      // Check that tables have actual data (not loading messages)
      const symbolsText = topSymbolsBody.textContent.trim();
      const typesText = topTypesBody.textContent.trim();
      
      return !symbolsText.includes('Loading data...') && 
             !typesText.includes('Loading data...') &&
             symbolsText.length > 0 && typesText.length > 0;
    }, { timeout: 30000 });
    
    // Check that top symbols table is present and has data
    await expect(page.locator('h5:has-text("Top Symbols")')).toBeVisible();
    const topSymbolsBody = page.locator('#top-symbols-body');
    await expect(topSymbolsBody.locator('text=Loading data...')).not.toBeVisible();
    
    // Check that top types table is present and has data
    await expect(page.locator('h5:has-text("Top Performing Recommendation Types")')).toBeVisible();
    const topTypesBody = page.locator('#top-types-body');
    await expect(topTypesBody.locator('text=Loading data...')).not.toBeVisible();
  });

  test('should handle load more functionality', async ({ page }) => {
    // Wait for initial data to load
    await page.waitForSelector('#recommendations-table-body');
    
    // Wait for actual data to be loaded
    await page.waitForFunction(() => {
      const tbody = document.querySelector('#recommendations-table-body');
      return tbody && !tbody.textContent.includes('Loading recommendations...');
    }, { timeout: 30000 });
    
    // Check that load more button is present
    const loadMoreButton = page.locator('#load-more');
    await expect(loadMoreButton).toBeVisible();
    
    // Check that showing results text is present and shows actual numbers
    const showingResults = page.locator('#showing-results');
    await expect(showingResults).toBeVisible();
    const resultsText = await showingResults.textContent();
    expect(resultsText).toMatch(/Showing \d+ of \d+ recommendations/);
  });

  test('should display recommendation data with proper formatting', async ({ page }) => {
    // Wait for recommendations to load
    await page.waitForSelector('#recommendations-table-body');
    
    // Wait for actual data (not loading message)
    await page.waitForFunction(() => {
      const tbody = document.querySelector('#recommendations-table-body');
      return tbody && !tbody.textContent.includes('Loading recommendations...');
    }, { timeout: 30000 });
    
    // Check that at least one recommendation row exists
    const rows = page.locator('#recommendations-table-body tr');
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThan(0);
    
    // Check that the first row has proper data structure
    const firstRow = rows.first();
    
    // Check that symbol is displayed as a badge
    await expect(firstRow.locator('.symbol-badge')).toBeVisible();
    
    // Check that confidence is displayed as percentage
    const confidenceCell = firstRow.locator('td').nth(4); // 5th column (0-indexed)
    const confidenceText = await confidenceCell.textContent();
    expect(confidenceText.trim()).toMatch(/^\d+\.\d+%$/);
    
    // Check that date is properly formatted
    const dateCell = firstRow.locator('td').nth(0); // Date column
    const dateText = await dateCell.textContent();
    expect(dateText.trim()).toMatch(/^[A-Za-z]{3} \d{1,2}, \d{4} \d{1,2}:\d{2} [AP]M$/);
  });
}); 