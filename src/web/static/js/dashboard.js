/* Ultra-Simple Dashboard JavaScript */

console.log('Dashboard JS loaded');

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
    
    // Update debug panel with request info
    updateDebugPanel('request', {
        method: 'POST',
        url: '/api/analyze_stock',
        symbol: symbol,
        ai_provider: 'ollama',
        timestamp: new Date().toISOString()
    });
    
    const requestBody = { symbol: symbol, ai_provider: 'ollama' };
    
    fetch('/api/analyze_stock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
    })
    .then(response => {
        // Update debug panel with response status
        updateDebugPanel('response', {
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries()),
            timestamp: new Date().toISOString()
        });
        return response.json();
    })
    .then(data => {
        console.log('Analysis complete:', data);
        
        // Update debug panel with response data
        updateDebugPanel('responseData', data);
        
        // Hide loading state
        standardBtnContent.style.display = 'inline';
        standardBtnLoading.style.display = 'none';
        
        if (data.status === 'error') {
            showResults('Error: ' + data.error);
        } else {
            const result = data.data;
            const trading = result.trading_recommendation;
            
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
                                <p><strong>Current Price:</strong> $${result.price_data.current_price.toFixed(2)}</p>
                                <p><strong>News Sources:</strong> ${Object.entries(result.news_sources).map(([source, count]) => 
                                    `${source}: ${count}`).join(', ')}</p>
                                <p><strong>Sentiment:</strong> ${result.sentiment_analysis.overall_sentiment || 'Neutral'}</p>
                                <p><strong>Confidence:</strong> ${((result.sentiment_analysis.confidence || 0) * 100).toFixed(1)}%</p>
                                <p><strong>Action:</strong> <span class="badge ${trading.action === 'CALL' ? 'bg-success' : trading.action === 'PUT' ? 'bg-danger' : 'bg-secondary'}">${trading.action || 'HOLD'}</span></p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Options Trading Recommendation -->
                    <div class="col-md-6">
                        <div class="card border-warning">
                            <div class="card-header bg-warning text-dark">
                                <h5><i class="fas fa-options"></i> Options Trading</h5>
                            </div>
                            <div class="card-body">
                                <p><strong>Strategy:</strong> ${trading.strategy_type || 'Standard'}</p>
                                <p><strong>Option Type:</strong> <span class="badge ${trading.option_type === 'call' ? 'bg-success' : trading.option_type === 'put' ? 'bg-danger' : 'bg-secondary'}">${trading.option_type?.toUpperCase() || 'N/A'}</span></p>
                                <p><strong>Strike Price:</strong> ${trading.strike_price ? '$' + trading.strike_price : 'N/A'}</p>
                                <p><strong>Option Price:</strong> ${trading.option_price ? '$' + trading.option_price : 'N/A'}</p>
                                <p><strong>Days to Expiry:</strong> ${trading.days_to_expiry || 'N/A'}</p>
                                <p><strong>Hold Time:</strong> ${trading.hold_time || 'N/A'}</p>
                                <p><strong>Target Gain:</strong> ${trading.target_gain_percent ? trading.target_gain_percent + '%' : 'N/A'}</p>
                                <p><strong>Stop Loss:</strong> ${trading.stop_loss_percent ? trading.stop_loss_percent + '%' : 'N/A'}</p>
                                <p><strong>Position Size:</strong> ${trading.position_size || 'N/A'} contracts</p>
                                ${trading.action === 'HOLD' ? '<p class="text-warning mt-3"><i class="fas fa-info-circle"></i> Currently holding - waiting for clearer market signals</p>' : ''}
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
                                ${Object.entries(trading.position_recommendations || {}).map(([account, details]) => `
                                    <div class="mb-2">
                                        <strong>${account} Account:</strong><br>
                                        <small>
                                            Contracts: ${details.contracts || 'N/A'}<br>
                                            Cost: $${details.total_cost || 'N/A'}<br>
                                            Risk: ${details.risk_percent || 'N/A'}%<br>
                                            R/R Ratio: ${details.risk_reward_ratio || 'N/A'}
                                        </small>
                                    </div>
                                `).join('') || '<p class="text-muted">No position recommendations available</p>'}
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
                                    ${(trading.day_trading_notes || []).map(note => `<li><small>${note}</small></li>`).join('') || '<li class="text-muted">No trading notes available</li>'}
                                </ul>
                            </div>
                        </div>
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
        console.error('Error:', error);
        
        // Hide loading state
        standardBtnContent.style.display = 'inline';
        standardBtnLoading.style.display = 'none';
        
        updateDebugPanel('error', {
            error: error.message,
            timestamp: new Date().toISOString()
        });
        showResults('Error: ' + error.message);
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
    
    // Update debug panel with request info
    updateDebugPanel('request', {
        method: 'POST',
        url: '/api/enhanced_analysis',
        symbol: symbol,
        timestamp: new Date().toISOString()
    });
    
    const requestBody = { symbol: symbol };
    
    fetch('/api/enhanced_analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
    })
    .then(response => {
        // Update debug panel with response status
        updateDebugPanel('response', {
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries()),
            timestamp: new Date().toISOString()
        });
        return response.json();
    })
    .then(data => {
        console.log('Enhanced analysis complete:', data);
        
        // Update debug panel with response data
        updateDebugPanel('responseData', data);
        
        // Hide loading state
        enhancedBtnContent.style.display = 'inline';
        enhancedBtnLoading.style.display = 'none';
        
        if (data.status === 'error') {
            showResults('Error: ' + data.error);
        } else {
            const result = data.data;
            const recommendations = result.recommendations;
            
            let resultHtml = `
                <div class="row">
                    <div class="col-12">
                        <div class="alert alert-success">
                            <h5><i class="fas fa-rocket"></i> Enhanced Analysis Complete</h5>
                            <p><strong>Symbol:</strong> ${symbol} | <strong>Analysis Type:</strong> Enhanced Multi-Strategy</p>
                            <p><strong>Top Recommendation:</strong> ${recommendations.top_recommendation.recommendation_type} - ${recommendations.top_recommendation.action}</p>
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
                                        <p><strong>Type:</strong> ${recommendations.top_recommendation.recommendation_type}</p>
                                        <p><strong>Action:</strong> <span class="badge ${getBadgeClass(recommendations.top_recommendation.action)}">${recommendations.top_recommendation.action}</span></p>
                                        <p><strong>Confidence:</strong> ${(recommendations.top_recommendation.confidence * 100).toFixed(1)}%</p>
                                    </div>
                                    <div class="col-md-4">
                                        <p><strong>Entry Price:</strong> $${recommendations.top_recommendation.entry_price?.toFixed(2) || 'N/A'}</p>
                                        <p><strong>Target Price:</strong> $${recommendations.top_recommendation.target_price?.toFixed(2) || 'N/A'}</p>
                                        <p><strong>Stop Loss:</strong> $${recommendations.top_recommendation.stop_loss?.toFixed(2) || 'N/A'}</p>
                                    </div>
                                    <div class="col-md-4">
                                        <p><strong>Position Size:</strong> ${recommendations.top_recommendation.position_size || 'N/A'}</p>
                                        <p><strong>Risk/Reward:</strong> ${recommendations.top_recommendation.risk_reward_ratio?.toFixed(2) || 'N/A'}</p>
                                        <p><strong>Hold Time:</strong> ${recommendations.top_recommendation.hold_time || 'N/A'}</p>
                                    </div>
                                </div>
                                <p class="mt-2 mb-0"><small><strong>Reasoning:</strong> ${recommendations.top_recommendation.reasoning}</small></p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Options Recommendations -->
                <div class="row">
                    <div class="col-12">
                        <h5 class="mb-3">Options Trading Recommendations</h5>
                        ${recommendations.options_recommendations ? recommendations.options_recommendations.map(rec => `
                            <div class="card mb-3 border-warning recommendation-card">
                                <div class="card-body">
                                    <h6 class="recommendation-type">${rec.recommendation_type}</h6>
                                    <div class="row">
                                        <div class="col-md-4">
                                            <p><strong>Action:</strong> <span class="badge ${getBadgeClass(rec.action)}">${rec.action}</span></p>
                                            <p><strong>Option Type:</strong> <span class="badge ${rec.option_type === 'call' ? 'bg-success' : 'bg-danger'}">${rec.option_type?.toUpperCase() || 'N/A'}</span></p>
                                            <p><strong>Strike Price:</strong> $${rec.strike_price?.toFixed(2) || 'N/A'}</p>
                                        </div>
                                        <div class="col-md-4">
                                            <p><strong>Option Price:</strong> $${rec.option_price?.toFixed(2) || 'N/A'}</p>
                                            <p><strong>Days to Expiry:</strong> ${rec.days_to_expiry || 'N/A'}</p>
                                            <p><strong>Position Size:</strong> ${rec.position_size || 'N/A'} contracts</p>
                                        </div>
                                        <div class="col-md-4">
                                            <p><strong>Base Confidence:</strong> ${(rec.base_confidence * 100).toFixed(1)}%</p>
                                            <p><strong>Historical Confidence:</strong> ${(rec.historical_confidence * 100).toFixed(1)}%</p>
                                            <p><strong>Final Confidence:</strong> ${(rec.confidence * 100).toFixed(1)}%</p>
                                            <p><strong>Rank:</strong> ${rec.rank || 'N/A'}</p>
                                        </div>
                                    </div>
                                    <p class="mt-2 mb-0"><small><strong>Reasoning:</strong> ${rec.reasoning}</small></p>
                                </div>
                            </div>
                        `).join('') : '<p>No options recommendations available</p>'}
                    </div>
                </div>
                
                <!-- Stock Recommendations -->
                <div class="row mt-3">
                    <div class="col-12">
                        <h5 class="mb-3">Stock Trading Recommendations</h5>
                        ${recommendations.stock_recommendations ? recommendations.stock_recommendations.map(rec => `
                            <div class="card mb-3 border-primary recommendation-card">
                                <div class="card-body">
                                    <h6 class="recommendation-type">${rec.recommendation_type}</h6>
                                    <div class="row">
                                        <div class="col-md-4">
                                            <p><strong>Action:</strong> <span class="badge ${getBadgeClass(rec.action)}">${rec.action}</span></p>
                                            <p><strong>Entry Price:</strong> $${rec.entry_price?.toFixed(2) || 'N/A'}</p>
                                            <p><strong>Target Price:</strong> $${rec.target_price?.toFixed(2) || 'N/A'}</p>
                                        </div>
                                        <div class="col-md-4">
                                            <p><strong>Stop Loss:</strong> $${rec.stop_loss?.toFixed(2) || 'N/A'}</p>
                                            <p><strong>Position Size:</strong> ${rec.position_size || 'N/A'} shares</p>
                                            <p><strong>Risk/Reward:</strong> ${rec.risk_reward_ratio?.toFixed(2) || 'N/A'}</p>
                                        </div>
                                        <div class="col-md-4">
                                            <p><strong>Base Confidence:</strong> ${(rec.base_confidence * 100).toFixed(1)}%</p>
                                            <p><strong>Historical Confidence:</strong> ${(rec.historical_confidence * 100).toFixed(1)}%</p>
                                            <p><strong>Final Confidence:</strong> ${(rec.confidence * 100).toFixed(1)}%</p>
                                        </div>
                                    </div>
                                    <p class="mt-2 mb-0"><small><strong>Reasoning:</strong> ${rec.reasoning}</small></p>
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
        console.error('Error:', error);
        
        // Hide loading state
        enhancedBtnContent.style.display = 'inline';
        enhancedBtnLoading.style.display = 'none';
        
        updateDebugPanel('error', {
            error: error.message,
            timestamp: new Date().toISOString()
        });
        showResults('Error: ' + error.message);
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

console.log('Dashboard functions ready'); 