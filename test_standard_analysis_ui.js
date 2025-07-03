// Test script to verify standard analysis UI elements are populated correctly
// This runs in the browser console to check that all UI elements are properly populated

function testStandardAnalysisUI() {
  console.log('Starting Standard Analysis UI test...');
  
  // 1. Get the stock symbol input and set a value
  const symbolInput = document.getElementById('stockSymbol');
  if (!symbolInput) {
    console.error('❌ Stock symbol input not found');
    return false;
  }
  symbolInput.value = 'AAPL';
  
  // 2. Track the fetch request to capture the response
  let originalFetch = window.fetch;
  let responseData = null;
  
  window.fetch = async function(url, options) {
    const response = await originalFetch(url, options);
    
    // Clone the response so we can read it twice
    const clone = response.clone();
    
    if (url === '/api/analyze_stock' && options.method === 'POST') {
      try {
        const data = await clone.json();
        responseData = data;
        console.log('✅ Intercepted /api/analyze_stock response:', data);
      } catch (e) {
        console.error('❌ Error parsing response:', e);
      }
    }
    
    return response;
  };
  
  // 3. Create a promise to wait for the analysis to complete
  const testPromise = new Promise((resolve) => {
    // Store original function
    const originalDoStandardAnalysis = window.doStandardAnalysis;
    
    // Override the function to detect when it completes
    window.doStandardAnalysis = function() {
      // Call original function
      originalDoStandardAnalysis.apply(this);
      
      // Wait for the UI to update
      setTimeout(() => {
        // Restore original function
        window.doStandardAnalysis = originalDoStandardAnalysis;
        window.fetch = originalFetch;
        
        // Check UI elements
        const results = checkUIElements();
        resolve(results);
      }, 3000); // Wait 3 seconds for UI to update
    };
  });
  
  // 4. Click the standard analysis button
  const standardBtn = document.getElementById('standardAnalysisBtn');
  if (!standardBtn) {
    console.error('❌ Standard analysis button not found');
    return false;
  }
  standardBtn.click();
  
  // 5. Return the promise
  return testPromise;
}

function checkUIElements() {
  console.log('Checking UI elements...');
  const results = {
    success: true,
    checks: []
  };
  
  // Helper function to add check results
  function addCheck(name, passed, element, value) {
    results.checks.push({
      name,
      passed,
      element: element ? element.outerHTML : null,
      value
    });
    
    if (!passed) {
      results.success = false;
    }
  }
  
  // 1. Check for current price
  const priceElement = document.querySelector('.card-body p:contains("Current Price:")');
  const priceText = priceElement ? priceElement.textContent : '';
  const hasPrice = priceText && !priceText.includes('N/A');
  addCheck('Current Price', hasPrice, priceElement, priceText);
  
  // 2. Check for sentiment
  const sentimentElement = document.querySelector('.card-body p:contains("Sentiment:")');
  const sentimentText = sentimentElement ? sentimentElement.textContent : '';
  const hasSentiment = sentimentText && !sentimentText.includes('N/A');
  addCheck('Sentiment', hasSentiment, sentimentElement, sentimentText);
  
  // 3. Check for action badge
  const actionElement = document.querySelector('.card-body p:contains("Action:")');
  const actionBadge = actionElement ? actionElement.querySelector('.badge') : null;
  const actionText = actionBadge ? actionBadge.textContent : '';
  const hasAction = actionText && actionText !== 'N/A';
  addCheck('Action', hasAction, actionElement, actionText);
  
  // 4. Check for options trading data
  const optionsCard = document.querySelector('.card.border-warning');
  const optionsContent = optionsCard ? optionsCard.textContent : '';
  const hasOptions = optionsContent && !optionsContent.includes('No options trading recommended');
  addCheck('Options Trading', hasOptions, optionsCard, optionsContent);
  
  // 5. Check for position recommendations
  const positionCard = document.querySelector('.card.border-info');
  const positionContent = positionCard ? positionCard.textContent : '';
  const hasPositions = positionContent && !positionContent.includes('No position recommendations available');
  addCheck('Position Recommendations', hasPositions, positionCard, positionContent);
  
  // 6. Check for trading notes
  const notesCard = document.querySelector('.card.border-success');
  const notesList = notesCard ? notesCard.querySelector('ul') : null;
  const notesItems = notesList ? notesList.querySelectorAll('li') : [];
  const hasNotes = notesItems.length > 0 && !notesCard.textContent.includes('No trading notes available');
  addCheck('Trading Notes', hasNotes, notesCard, notesItems.length + ' notes found');
  
  // 7. Check for template variables in trading notes
  let hasTemplateVars = false;
  if (notesList) {
    const notesText = notesList.textContent;
    hasTemplateVars = notesText.includes('{') || notesText.includes('}');
  }
  addCheck('No Template Variables', !hasTemplateVars, notesList, hasTemplateVars ? 'Template variables found' : 'No template variables');
  
  // Log results
  console.log('UI Check Results:', results);
  
  if (results.success) {
    console.log('✅ All UI elements are populated correctly!');
  } else {
    console.error('❌ Some UI elements are not populated correctly!');
    results.checks.filter(check => !check.passed).forEach(check => {
      console.error(`❌ ${check.name} check failed:`, check.value);
    });
  }
  
  return results;
}

// Add jQuery-like contains selector
if (!Element.prototype.matches) {
  Element.prototype.matches = Element.prototype.msMatchesSelector || Element.prototype.webkitMatchesSelector;
}
if (!document.querySelector(':contains')) {
  document.querySelectorAll = (function(originalQSA) {
    return function(selector) {
      if (selector.includes(':contains')) {
        const parts = selector.split(':contains');
        const baseSelector = parts[0];
        const searchText = parts[1].slice(1, -1);
        
        const elements = originalQSA.call(this, baseSelector);
        const results = [];
        
        for (let i = 0; i < elements.length; i++) {
          if (elements[i].textContent.includes(searchText)) {
            results.push(elements[i]);
          }
        }
        
        return results;
      } else {
        return originalQSA.call(this, selector);
      }
    };
  })(document.querySelectorAll);
}

// Run the test
testStandardAnalysisUI().then(results => {
  console.log('Test completed with result:', results.success ? 'PASS' : 'FAIL');
});
