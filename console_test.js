// Simple test script to verify standard analysis functionality
// Copy and paste this into the browser console

async function testStandardAnalysis() {
  console.log('🔍 Starting Standard Analysis test...');
  
  // Set stock symbol
  const symbolInput = document.getElementById('stockSymbol');
  symbolInput.value = 'AAPL';
  console.log('✅ Set stock symbol to AAPL');
  
  // Make direct API call to verify data
  console.log('🔍 Making direct API call to verify data...');
  const apiResponse = await fetch('/api/analyze_stock', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol: 'AAPL', ai_provider: 'ollama' })
  }).then(r => r.json());
  
  console.log('📊 API Response:', apiResponse);
  
  // Check if API response has required data
  const data = apiResponse.data;
  const checks = {
    hasPositionRecommendations: !!data.position_recommendations && 
                               typeof data.position_recommendations === 'object' && 
                               Object.keys(data.position_recommendations).length > 0,
    
    hasTradingNotes: Array.isArray(data.day_trading_notes) && 
                    data.day_trading_notes.length > 0,
    
    hasOptionsData: !!data.option_type && !!data.strike_price && !!data.option_price,
    
    noTemplateVariables: !JSON.stringify(data).includes('${') && 
                        !JSON.stringify(data).includes('{strategy_type}')
  };
  
  console.log('✅ API Data Checks:', checks);
  
  // Now trigger the UI update
  console.log('🔍 Triggering standard analysis button click...');
  const standardBtn = document.getElementById('standardAnalysisBtn');
  standardBtn.click();
  
  // Wait for UI to update
  return new Promise(resolve => {
    setTimeout(() => {
      // Check UI elements
      console.log('🔍 Checking UI elements...');
      
      const uiChecks = {
        // Position recommendations
        positionSizeDisplayed: document.body.innerHTML.includes('Position Size') && 
                              !document.body.innerHTML.includes('No position recommendations available'),
        
        // Trading notes
        tradingNotesDisplayed: document.body.innerHTML.includes('Trading Notes') && 
                              !document.body.innerHTML.includes('No trading notes available'),
        
        // Options data
        optionsDataDisplayed: document.body.innerHTML.includes('Options Trading') && 
                            document.body.innerHTML.includes('Option Type') &&
                            !document.body.innerHTML.includes('No options trading recommended')
      };
      
      console.log('✅ UI Checks:', uiChecks);
      
      const allApiChecksPass = Object.values(checks).every(v => v);
      const allUiChecksPass = Object.values(uiChecks).every(v => v);
      
      if (allApiChecksPass && allUiChecksPass) {
        console.log('✅ ALL TESTS PASSED! Standard Analysis is working correctly.');
      } else {
        console.log('❌ TESTS FAILED! Standard Analysis has issues.');
        
        if (!allApiChecksPass) {
          console.log('❌ API data issues:');
          Object.entries(checks).filter(([k,v]) => !v).forEach(([k]) => {
            console.log(`  - ${k} check failed`);
          });
        }
        
        if (!allUiChecksPass) {
          console.log('❌ UI display issues:');
          Object.entries(uiChecks).filter(([k,v]) => !v).forEach(([k]) => {
            console.log(`  - ${k} check failed`);
          });
        }
      }
      
      resolve({
        apiChecks: checks,
        uiChecks: uiChecks,
        allPassed: allApiChecksPass && allUiChecksPass
      });
    }, 3000); // Wait 3 seconds for UI to update
  });
}

// Run the test
testStandardAnalysis().then(results => {
  console.log('Test completed!', results);
});
