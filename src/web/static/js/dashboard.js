/* Ultra-Simple Dashboard JavaScript */

console.log('Dashboard JS loaded');

// Set up fetch interceptor to capture all API requests/responses
(function() {
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
        // Only intercept API calls
        if (typeof url === 'string' && url.includes('/api/')) {
            const requestStartTime = new Date();
            
            // Extract request details
            let requestBody = {};
            if (options && options.body) {
                try {
                    requestBody = JSON.parse(options.body);
                } catch (e) {
                    console.error('Error parsing request body:', e);
                }
            }
            
            // Update debug panel with request info
            updateDebugPanel('request', {
                method: options?.method || 'GET',
                url: url,
                symbol: requestBody.symbol || 'N/A',
                ai_provider: requestBody.ai_provider || 'default',
                timestamp: requestStartTime.toISOString()
            });
            
            // Call original fetch
            return originalFetch(url, options).then(async response => {
                // Clone the response so we can read the body
                const clonedResponse = response.clone();
                let data;
                try {
                    data = await clonedResponse.json();
                } catch (error) {
                    data = null;
                    console.error('Error parsing response:', error);
                }
                // Update debug panel with response status
                updateDebugPanel('response', {
                    status: response.status,
                    statusText: response.statusText,
                    headers: Object.fromEntries(response.headers.entries()),
                    timestamp: new Date().toISOString()
                });
                updateDebugPanel('responseData', data);
                // Reconstruct a new response so downstream code can read it again
                const body = data !== null ? JSON.stringify(data) : null;
                return new Response(body, {
                    status: response.status,
                    statusText: response.statusText,
                    headers: response.headers
                });
            }).catch(error => {
                // Update debug panel with error
                updateDebugPanel('error', {
                    error: error.message,
                    timestamp: new Date().toISOString()
                });
                throw error;
            });
        }
        // Pass through non-API calls
        return originalFetch(url, options);
    };
})();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard DOM loaded, initializing...');
    
    // Add event listeners
    if (document.getElementById('stockSymbol')) {
        document.getElementById('stockSymbol').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                doStandardAnalysis();
            }
        });
    }
    
    // Make sure debug panel is visible by default
    const debugPanel = document.getElementById('debugPanelBody');
    if (debugPanel) {
        debugPanel.style.display = 'block';
    }
});

function doStandardAnalysis() {
    console.log('[DEBUG] doStandardAnalysis called');
    const symbol = document.getElementById('stockSymbol').value.trim().toUpperCase();
    if (!symbol) {
        alert('Please enter a stock symbol');
        return;
    }
    
    console.log('Standard analysis for:', symbol);
    showResults('Analyzing ' + symbol + '...');
    
    // Show loading state
    const standardBtn = document.getElementById('standardAnalysisBtn');
    const standardBtnContent = document.getElementById('standardBtnContent');
    const standardBtnLoading = document.getElementById('standardBtnLoading');
    
    standardBtnContent.style.display = 'none';
    standardBtnLoading.style.display = 'inline';
    
    const requestBody = { symbol: symbol, ai_provider: 'ollama' };
    // Debug: capture request
    if (typeof captureDebug === 'function') {
        captureDebug({
            method: 'POST',
            url: '/api/analyze_stock',
            body: requestBody,
            headers: { 'Content-Type': 'application/json' }
        }, null);
    }
    
    fetch('/api/analyze_stock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
    })
    .then(response => response.json())
    .then(data => {
        // Debug: capture response
        if (typeof captureDebug === 'function') {
            captureDebug({
                method: 'POST',
                url: '/api/analyze_stock',
                body: requestBody,
                headers: { 'Content-Type': 'application/json' }
            }, data);
        }
        console.log('Analysis complete:', data);
        
        // Hide loading state
        standardBtnContent.style.display = 'inline';
        standardBtnLoading.style.display = 'none';
        
        if (data.status === 'error') {
            showResults('Error: ' + data.error);
        } else {
            const result = data.data;
            const trading = result && result.trading_recommendation ? result.trading_recommendation : null;
            const options = result && result.options_recommendation ? result.options_recommendation : null;
            
            let resultHtml = `
                <div class="row">
                    <!-- Stock Analysis -->
                    <div class="col-md-6">
                        <div class="card border-primary">
                            <div class="card-header bg-primary text-white">
                                <h5><i class="fas fa-chart-line"></i> Stock Analysis</h5>
                            </div>
                            <div class="card-body">
                                <p><strong>Symbol:</strong> ${symbol}</p>
                                <p><strong>Current Price:</strong> $${result && result.price_data && result.price_data.current_price ? result.price_data.current_price.toFixed(2) : 'N/A'}</p>
                                <p><strong>News Sources:</strong> ${result && result.news_sources ? Object.entries(result.news_sources).map(([source, count]) => `${source}: ${count}`).join(', ') : 'N/A'}</p>
                                <p><strong>Sentiment:</strong> ${result && result.sentiment_analysis && result.sentiment_analysis.overall_sentiment ? result.sentiment_analysis.overall_sentiment : 'Neutral'}</p>
                                <p><strong>Confidence:</strong> ${result && result.sentiment_analysis && result.sentiment_analysis.confidence ? ((result.sentiment_analysis.confidence || 0) * 100).toFixed(1) : 'N/A'}%</p>
                                <p><strong>Action:</strong> <span class="badge ${trading && trading.action === 'CALL' ? 'bg-success' : trading && trading.action === 'PUT' ? 'bg-danger' : 'bg-secondary'}">${trading && trading.action ? trading.action : 'HOLD'}</span></p>
                            </div>
                        </div>
                    </div>
                    <!-- Options Trading Recommendation -->
                    <div class="col-md-6">
                        <div class="card border-warning">
                            <div class="card-header bg-warning text-dark">
                                <h5><i class="fas fa-chart-line"></i> Options Trading</h5>
                            </div>
                            <div class="card-body">
                                ${options && options.action && options.action !== 'HOLD' ? 
                                    `<p><strong>Strategy:</strong> ${options.strategy_type || 'Standard'}</p>
                                    <p><strong>Option Type:</strong> <span class="badge ${options.option_type === 'call' ? 'bg-success' : 'bg-danger'}">${options.option_type ? options.option_type.toUpperCase() : 'N/A'}</span></p>
                                    <p><strong>Strike Price:</strong> $${options.strike_price ? options.strike_price.toFixed(2) : 'N/A'}</p>
                                    <p><strong>Option Price:</strong> $${options.option_price ? options.option_price.toFixed(2) : 'N/A'}</p>
                                    <p><strong>Days to Expiry:</strong> ${options.days_to_expiry || 'N/A'}</p>
                                    <p><strong>Target Gain:</strong> ${options.target_gain || 'N/A'}</p>
                                    <p><strong>Stop Loss:</strong> ${options.stop_loss || 'N/A'}</p>
                                    <p><strong>Position Size:</strong> ${options.position_size || 'N/A'} contracts</p>
                                    <p><strong>Confidence:</strong> ${options.confidence ? ((options.confidence || 0) * 100).toFixed(1) : 'N/A'}%</p>
                                    <p><strong>Reasoning:</strong> ${options.reasoning || 'N/A'}</p>` : 
                                    '<p class="text-warning mt-3"><i class="fas fa-info-circle"></i> No options recommendation - wait for clearer signals</p>'
                                }
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row mt-3">
                    <!-- Position Recommendations -->
                    <div class="col-md-6">
                        <div class="card border-info">
                            <div class="card-header bg-info text-white">
                                <h6><i class="fas fa-dollar-sign"></i> Position Sizes</h6>
                            </div>
                            <div class="card-body">
                                ${options && options.action && options.action !== 'HOLD' && options.position_recommendations ? 
                                    `<div class="mb-2">
                                        <strong>Conservative Account:</strong><br>
                                        <small>
                                            Contracts: ${options.position_recommendations['$500']?.contracts || 'N/A'}<br>
                                            Cost: $${options.position_recommendations['$500']?.total_cost?.toFixed(2) || 'N/A'}<br>
                                            Risk: ${options.position_recommendations['$500']?.risk_percent || 'N/A'}%<br>
                                            R/R Ratio: ${options.position_recommendations['$500']?.risk_reward_ratio?.toFixed(2) || 'N/A'}
                                        </small>
                                    </div>
                                    <div class="mb-2">
                                        <strong>Moderate Account:</strong><br>
                                        <small>
                                            Contracts: ${options.position_recommendations['$1000']?.contracts || 'N/A'}<br>
                                            Cost: $${options.position_recommendations['$1000']?.total_cost?.toFixed(2) || 'N/A'}<br>
                                            Risk: ${options.position_recommendations['$1000']?.risk_percent || 'N/A'}%<br>
                                            R/R Ratio: ${options.position_recommendations['$1000']?.risk_reward_ratio?.toFixed(2) || 'N/A'}
                                        </small>
                                    </div>
                                    <div class="mb-2">
                                        <strong>Aggressive Account:</strong><br>
                                        <small>
                                            Contracts: ${options.position_recommendations['$2000']?.contracts || 'N/A'}<br>
                                            Cost: $${options.position_recommendations['$2000']?.total_cost?.toFixed(2) || 'N/A'}<br>
                                            Risk: ${options.position_recommendations['$2000']?.risk_percent || 'N/A'}%<br>
                                            R/R Ratio: ${options.position_recommendations['$2000']?.risk_reward_ratio?.toFixed(2) || 'N/A'}
                                        </small>
                                    </div>` :
                                    '<p class="text-muted">No position recommendations available</p>'
                                }
                            </div>
                        </div>
                    </div>
                    <!-- Trading Notes -->
                    <div class="col-md-6">
                        <div class="card border-success">
                            <div class="card-header bg-success text-white">
                                <h6><i class="fas fa-lightbulb"></i> Trading Notes</h6>
                            </div>
                            <div class="card-body">
                                <ul class="list-unstyled">
                                    ${options && options.trading_notes ? options.trading_notes.map(note => `<li><small>${note}</small></li>`).join('') : '<li class="text-muted">No trading notes available</li>'}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-12">
                        <div class="alert alert-secondary">
                            <small class="text-muted">Analysis completed at: ${result && result.timestamp ? new Date(result.timestamp).toLocaleString() : 'N/A'}</small>
                        </div>
                    </div>
                </div>
            `;
            showResults(resultHtml);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Hide loading state
        standardBtnContent.style.display = 'inline';
        standardBtnLoading.style.display = 'none';
        showResults('Error: ' + error.message);
        // Debug: capture error
        if (typeof captureDebug === 'function') {
            captureDebug({
                method: 'POST',
                url: '/api/analyze_stock',
                body: requestBody,
                headers: { 'Content-Type': 'application/json' }
            }, { error: error.message });
        }
    });
}

function doEnhancedAnalysis() {
    console.log('[DEBUG] doEnhancedAnalysis called');
    const symbol = document.getElementById('stockSymbol').value.trim().toUpperCase();
    if (!symbol) {
        alert('Please enter a stock symbol');
        return;
    }
    
    console.log('Enhanced analysis for:', symbol);
    showResults('Enhanced analyzing ' + symbol + '...');
    
    // Show loading state
    const enhancedBtn = document.getElementById('enhancedAnalysisBtn');
    const enhancedBtnContent = document.getElementById('enhancedBtnContent');
    const enhancedBtnLoading = document.getElementById('enhancedBtnLoading');
    
    enhancedBtnContent.style.display = 'none';
    enhancedBtnLoading.style.display = 'inline';
    
    const requestBody = { symbol: symbol };
    // Capture request in debug panel
    if (typeof captureDebug === 'function') {
        captureDebug(requestBody, {});
    } else {
        document.getElementById('requestData').textContent = JSON.stringify(requestBody, null, 2);
        document.getElementById('requestStatus').innerHTML = '<small class="text-success">Request captured</small>';
    }
    
    fetch('/api/enhanced_analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
    })
    .then(response => {
        return response.json();
    })
    .then(data => {
        // Capture response in debug panel
        if (typeof captureDebug === 'function') {
            captureDebug(requestBody, data);
        } else {
            document.getElementById('responseData').textContent = JSON.stringify(data, null, 2);
            document.getElementById('responseStatus').innerHTML = '<small class="text-success">Response received</small>';
        }
        
        console.log('Enhanced analysis complete:', data);
        
        // Hide loading state
        enhancedBtnContent.style.display = 'inline';
        enhancedBtnLoading.style.display = 'none';
        
        if (data.status === 'error') {
            showResults('Error: ' + data.error);
        } else {
            const result = data.data;
            const recommendations = result.recommendations;
            
            console.log('[DEBUG] Enhanced analysis response:', data);
            console.log('[DEBUG] Recommendations object:', recommendations);
            
            // Defensive checks for top recommendation
            let topRec = null;
            if (recommendations) {
                topRec = recommendations.top_recommendation || recommendations.top_stock_recommendation || recommendations.top_options_recommendation;
            }
            if (!topRec) {
                // Try legacy or fallback keys
                topRec = result.top_recommendation || result.top_stock_recommendation || result.top_options_recommendation;
            }
            // Robust null check for topRec
            if (!topRec || typeof topRec !== 'object' || Array.isArray(topRec)) {
                console.error('[DEBUG] Invalid or missing top recommendation:', recommendations, topRec);
                showResults('Error: Invalid response structure - missing or invalid top recommendation data');
                return;
            }
            
            let resultHtml = `
                <div class="row">
                    <div class="col-12">
                        <div class="alert alert-success">
                            <h5><i class="fas fa-rocket"></i> Enhanced Analysis Complete</h5>
                            <p><strong>Symbol:</strong> ${symbol} | <strong>Analysis Type:</strong> Enhanced Multi-Strategy</p>
                            <p><strong>Top Recommendation:</strong> ${topRec.recommendation_type || 'N/A'} - ${topRec.action || 'N/A'}</p>
                        </div>
                    </div>
                </div>
                <!-- Top Recommendation -->
                <div class="row">
                    <div class="col-12">
                        <div class="card border-success mb-4">
                            <div class="card-header bg-success text-white">
                                <h5><i class="fas fa-star"></i> Top Recommendation</h5>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-4">
                                        <p><strong>Type:</strong> ${topRec.recommendation_type || 'N/A'}</p>
                                        <p><strong>Action:</strong> <span class="badge ${getBadgeClass(topRec.action)}">${topRec.action || 'N/A'}</span></p>
                                        <p><strong>Confidence:</strong> ${((topRec.confidence || 0) * 100).toFixed(1)}%</p>
                                    </div>
                                    <div class="col-md-4">
                                        <p><strong>Entry Price:</strong> $${topRec.entry_price?.toFixed(2) || 'N/A'}</p>
                                        <p><strong>Target Price:</strong> $${topRec.target_price?.toFixed(2) || 'N/A'}</p>
                                        <p><strong>Stop Loss:</strong> $${topRec.stop_loss?.toFixed(2) || 'N/A'}</p>
                                    </div>
                                    <div class="col-md-4">
                                        <p><strong>Position Size:</strong> ${topRec.position_size || 'N/A'}</p>
                                        <p><strong>Risk/Reward:</strong> ${topRec.risk_reward_ratio?.toFixed(2) || 'N/A'}</p>
                                        <p><strong>Hold Time:</strong> ${topRec.hold_time || 'N/A'}</p>
                                    </div>
                                </div>
                                <p class="mt-2 mb-0"><small><strong>Reasoning:</strong> ${topRec.reasoning || 'N/A'}</small></p>
                            </div>
                        </div>
                    </div>
                </div>
                <!-- Options Recommendations -->
                <div class="row">
                    <div class="col-12">
                        <h5 class="mb-3">Options Trading Recommendations</h5>
                        ${recommendations.options_recommendations && recommendations.options_recommendations.length > 0 ? recommendations.options_recommendations.map(rec => `
                            <div class="card mb-3 border-warning recommendation-card">
                                <div class="card-body">
                                    <h6 class="recommendation-type">${rec.recommendation_type || 'N/A'}</h6>
                                    <div class="row">
                                        <div class="col-md-4">
                                            <p><strong>Action:</strong> <span class="badge ${getBadgeClass(rec.action)}">${rec.action || 'N/A'}</span></p>
                                            <p><strong>Option Type:</strong> <span class="badge ${rec.option_type === 'call' ? 'bg-success' : 'bg-danger'}">${rec.option_type?.toUpperCase() || 'N/A'}</span></p>
                                            <p><strong>Strike Price:</strong> $${rec.strike_price?.toFixed(2) || 'N/A'}</p>
                                        </div>
                                        <div class="col-md-4">
                                            <p><strong>Option Price:</strong> $${rec.option_price?.toFixed(2) || 'N/A'}</p>
                                            <p><strong>Days to Expiry:</strong> ${rec.days_to_expiry || 'N/A'}</p>
                                            <p><strong>Position Size:</strong> ${rec.position_size || 'N/A'} contracts</p>
                                        </div>
                                        <div class="col-md-4">
                                            <p><strong>Base Confidence:</strong> ${((rec.base_confidence || 0) * 100).toFixed(1)}%</p>
                                            <p><strong>Historical Confidence:</strong> ${((rec.historical_confidence || 0) * 100).toFixed(1)}%</p>
                                            <p><strong>Final Confidence:</strong> ${((rec.confidence || 0) * 100).toFixed(1)}%</p>
                                            <p><strong>Rank:</strong> ${rec.rank || 'N/A'}</p>
                                        </div>
                                    </div>
                                    <p class="mt-2 mb-0"><small><strong>Reasoning:</strong> ${rec.reasoning || 'N/A'}</small></p>
                                </div>
                            </div>
                        `).join('') : '<p>No options recommendations available</p>'}
                    </div>
                </div>
                <!-- Stock Recommendations -->
                <div class="row mt-3">
                    <div class="col-12">
                        <h5 class="mb-3">Stock Trading Recommendations</h5>
                        ${recommendations.stock_recommendations && recommendations.stock_recommendations.length > 0 ? recommendations.stock_recommendations.map(rec => `
                            <div class="card mb-3 border-primary recommendation-card">
                                <div class="card-body">
                                    <h6 class="recommendation-type">${rec.recommendation_type || 'N/A'}</h6>
                                    <div class="row">
                                        <div class="col-md-4">
                                            <p><strong>Action:</strong> <span class="badge ${getBadgeClass(rec.action)}">${rec.action || 'N/A'}</span></p>
                                            <p><strong>Entry Price:</strong> $${rec.entry_price?.toFixed(2) || 'N/A'}</p>
                                            <p><strong>Target Price:</strong> $${rec.target_price?.toFixed(2) || 'N/A'}</p>
                                        </div>
                                        <div class="col-md-4">
                                            <p><strong>Stop Loss:</strong> $${rec.stop_loss?.toFixed(2) || 'N/A'}</p>
                                            <p><strong>Position Size:</strong> ${rec.position_size || 'N/A'} shares</p>
                                            <p><strong>Risk/Reward:</strong> ${rec.risk_reward_ratio?.toFixed(2) || 'N/A'}</p>
                                        </div>
                                        <div class="col-md-4">
                                            <p><strong>Base Confidence:</strong> ${((rec.base_confidence || 0) * 100).toFixed(1)}%</p>
                                            <p><strong>Historical Confidence:</strong> ${((rec.historical_confidence || 0) * 100).toFixed(1)}%</p>
                                            <p><strong>Final Confidence:</strong> ${((rec.confidence || 0) * 100).toFixed(1)}%</p>
                                        </div>
                                    </div>
                                    <p class="mt-2 mb-0"><small><strong>Reasoning:</strong> ${rec.reasoning || 'N/A'}</small></p>
                                </div>
                            </div>
                        `).join('') : '<p>No stock recommendations available</p>'}
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-12">
                        <div class="alert alert-secondary">
                            <small class="text-muted">Analysis completed at: ${new Date(result.timestamp).toLocaleString()}</small>
                        </div>
                    </div>
                </div>
            `;
            showResults(resultHtml);
        }
    })
    .catch(error => {
        console.error('Enhanced analysis error:', error);
        // Hide loading state
        enhancedBtnContent.style.display = 'inline';
        enhancedBtnLoading.style.display = 'none';
        // Capture error in debug panel
        if (typeof captureDebug === 'function') {
            captureDebug(requestBody, { error: error.message || error });
        } else {
            document.getElementById('responseData').textContent = JSON.stringify({ error: error.message || error }, null, 2);
            document.getElementById('responseStatus').innerHTML = '<small class="text-danger">Error</small>';
        }
        // Provide more detailed error information
        let errorMessage = 'Unknown error occurred';
        if (error.message) {
            errorMessage = error.message;
        } else if (error.statusText) {
            errorMessage = `HTTP ${error.status}: ${error.statusText}`;
        }
        showResults(`<div class="alert alert-danger">
            <h5><i class="fas fa-exclamation-triangle"></i> Enhanced Analysis Failed</h5>
            <p><strong>Error:</strong> ${errorMessage}</p>
            <p><small>Please try again or contact support if the problem persists.</small></p>
        </div>`);
    });
}

function getBadgeClass(action) {
    switch(action?.toUpperCase()) {
        case 'CALL':
        case 'BUY':
            return 'bg-success';
        case 'PUT':
        case 'SELL':
        case 'SELL_SHORT':
        case 'SHORT':
            return 'bg-danger';
        case 'HOLD':
            return 'bg-secondary';
        default:
            return 'bg-info';
    }
}

// Debug panel functions
function updateDebugPanel(type, data) {
    console.log('Updating debug panel:', type, data);
    
    // Make sure debug panel is visible by default
    const debugPanel = document.getElementById('debugPanelBody');
    debugPanel.style.display = 'block';
    
    switch(type) {
        case 'request':
            document.getElementById('requestStatus').innerHTML = `
                <strong>Request in progress</strong><br>
                <small>
                    Method: ${data.method}<br>
                    URL: ${data.url}<br>
                    Symbol: ${data.symbol}<br>
                    Timestamp: ${new Date(data.timestamp).toLocaleString()}
                </small>
            `;
            
            // Create a complete request object
            const requestData = {
                method: data.method,
                url: data.url,
                headers: { 'Content-Type': 'application/json' },
                body: { symbol: data.symbol, ai_provider: data.ai_provider },
                timestamp: data.timestamp
            };
            
            document.getElementById('requestData').textContent = JSON.stringify(requestData, null, 2);
            
            // Reset response section when new request starts
            document.getElementById('responseStatus').innerHTML = '<small>Waiting for response...</small>';
            document.getElementById('responseData').textContent = 'Waiting for response...';
            break;
            
        case 'response':
            const statusClass = data.status >= 200 && data.status < 300 ? 'text-success' : 'text-danger';
            document.getElementById('responseStatus').innerHTML = `
                <strong class="${statusClass}">Response received</strong><br>
                <small>
                    Status: ${data.status} ${data.statusText}<br>
                    Timestamp: ${new Date(data.timestamp).toLocaleString()}<br>
                    ${data.error ? `Error: ${data.error}` : ''}
                </small>
            `;
            break;
            
        case 'responseData':
            // Format the response data nicely
            try {
                const formattedData = typeof data === 'string' ? JSON.parse(data) : data;
                document.getElementById('responseData').textContent = JSON.stringify(formattedData, null, 2);
            } catch (e) {
                console.error('Error formatting response data:', e);
                document.getElementById('responseData').textContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
            }
            break;
            
        case 'error':
            document.getElementById('requestStatus').innerHTML = `
                <strong class="text-danger">Error occurred</strong><br>
                <small>
                    Error: ${data.message || data.error || 'Unknown error'}<br>
                    Timestamp: ${new Date(data.timestamp).toLocaleString()}
                </small>
            `;
            document.getElementById('responseData').textContent = JSON.stringify({
                error: data.message || data.error || 'Unknown error',
                timestamp: data.timestamp
            }, null, 2);
            break;
    }
}

function clearDebugPanel() {
    document.getElementById('requestStatus').innerHTML = '<small>No request made yet</small>';
    document.getElementById('requestData').textContent = 'No request data';
    document.getElementById('responseStatus').innerHTML = '<small>No response received yet</small>';
    document.getElementById('responseData').textContent = 'No response data';
}

function toggleDebugPanel() {
    const debugPanel = document.getElementById('debugPanelBody');
    if (debugPanel.style.display === 'none') {
        debugPanel.style.display = 'block';
    } else {
        debugPanel.style.display = 'none';
    }
}

function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    const text = element.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        // Show a temporary success message
        const originalText = element.previousElementSibling.querySelector('button').innerHTML;
        const button = element.previousElementSibling.querySelector('button');
        button.innerHTML = '<i class="fas fa-check"></i> Copied!';
        setTimeout(() => {
            button.innerHTML = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}

function showResults(content) {
    const resultsSection = document.getElementById('resultsSection');
    if (!resultsSection) {
        console.error('Results section not found');
        return;
    }
    
    resultsSection.style.display = 'block';
    resultsSection.innerHTML = `
        <div class="col-12">
            ${content}
        </div>
    `;
}

function toggleHowItWorks() {
    const howItWorksCard = document.getElementById('howItWorksCard');
    if (howItWorksCard) {
        if (howItWorksCard.style.display === 'none') {
            howItWorksCard.style.display = 'block';
        } else {
            howItWorksCard.style.display = 'none';
        }
    }
}

console.log('Dashboard functions ready'); 