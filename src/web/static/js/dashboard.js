// Dashboard JavaScript for Trading AI Analysis
// Handles stock analysis, progress tracking, and debug functionality

// Global variables
let currentAnalysisType = null;
let analysisInProgress = false;

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized');
    initializeDashboard();
});

function initializeDashboard() {
    // Set up event listeners
    setupEventListeners();
    
    // Initialize debug panel
    initializeDebugPanel();
    
    // Show initial state
    updateUIState('idle');
}

function setupEventListeners() {
    // Stock symbol input handling
    const stockSymbolInput = document.getElementById('stockSymbol');
    if (stockSymbolInput) {
        stockSymbolInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                doStandardAnalysis();
            }
        });
    }
}

// Analysis Functions
function doStandardAnalysis() {
    if (analysisInProgress) return;
    
    const symbol = document.getElementById('stockSymbol').value.trim().toUpperCase();
    if (!symbol) {
        showAlert('Please enter a stock symbol', 'warning');
        return;
    }
    
    currentAnalysisType = 'standard';
    startAnalysis(symbol, 'standard');
}

function doEnhancedAnalysis() {
    if (analysisInProgress) return;
    
    const symbol = document.getElementById('stockSymbol').value.trim().toUpperCase();
    if (!symbol) {
        showAlert('Please enter a stock symbol', 'warning');
        return;
    }
    
    currentAnalysisType = 'enhanced';
    startAnalysis(symbol, 'enhanced');
}

function startAnalysis(symbol, analysisType) {
    analysisInProgress = true;
    updateUIState('analyzing');
    
    // Show progress
    showProgress();
    
    // Update debug panel
    updateDebugPanel('request', {
        symbol: symbol,
        analysisType: analysisType,
        timestamp: new Date().toISOString()
    });
    
    // Make API call
    const endpoint = analysisType === 'enhanced' ? '/api/enhanced_analysis' : '/api/comprehensive_analysis';
    
    // Create AbortController for timeout handling
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 45000); // 45 second timeout to match backend
    
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            symbol: symbol,
            analysis_type: analysisType
        }),
        signal: controller.signal
    })
    .then(response => response.json())
    .then(data => {
        clearTimeout(timeoutId); // Clear timeout on success
        updateDebugPanel('response', data);
        handleAnalysisResponse(data, analysisType);
    })
    .catch(error => {
        clearTimeout(timeoutId); // Clear timeout on completion
        console.error('Analysis error:', error);
        
        // Handle timeout specifically
        if (error.name === 'AbortError') {
            updateDebugPanel('response', { error: 'Request timed out after 20 seconds' });
            handleAnalysisError(new Error('Analysis timed out. Ollama may be taking too long to respond.'));
        } else {
            updateDebugPanel('response', { error: error.message });
            handleAnalysisError(error);
        }
    })
    .finally(() => {
        analysisInProgress = false;
        updateUIState('completed');
        hideProgress();
    });
}

function handleAnalysisResponse(data, analysisType) {
    if (data.success || data.status === 'success') {
        showResults(data, analysisType);
        showAlert('Analysis completed successfully!', 'success');
    } else {
        showAlert('Analysis failed: ' + (data.message || 'Unknown error'), 'danger');
    }
}

function handleAnalysisError(error) {
    showAlert('Analysis error: ' + error.message, 'danger');
}

// UI State Management
function updateUIState(state) {
    const standardBtn = document.getElementById('standardAnalysisBtn');
    const enhancedBtn = document.getElementById('enhancedAnalysisBtn');
    const badge = document.getElementById('analysisTypeBadge');
    
    switch (state) {
        case 'idle':
            if (standardBtn) standardBtn.disabled = false;
            if (enhancedBtn) enhancedBtn.disabled = false;
            if (badge) badge.style.display = 'none';
            break;
            
        case 'analyzing':
            if (standardBtn) standardBtn.disabled = true;
            if (enhancedBtn) enhancedBtn.disabled = true;
            if (badge) {
                badge.textContent = currentAnalysisType === 'enhanced' ? 'Enhanced' : 'Standard';
                badge.style.display = 'inline';
            }
            break;
            
        case 'completed':
            if (standardBtn) standardBtn.disabled = false;
            if (enhancedBtn) enhancedBtn.disabled = false;
            break;
    }
}

// Progress Management
function showProgress() {
    const progress = document.getElementById('analysisProgress');
    const progressText = document.getElementById('progressText');
    const progressBar = document.getElementById('progressBar');
    
    if (progress) progress.style.display = 'block';
    if (progressText) progressText.style.display = 'block';
    
    // Animate progress bar
    let width = 0;
    const interval = setInterval(() => {
        if (width >= 90) {
            clearInterval(interval);
        } else {
            width++;
            if (progressBar) progressBar.style.width = width + '%';
        }
    }, 100);
}

function hideProgress() {
    const progress = document.getElementById('analysisProgress');
    const progressText = document.getElementById('progressText');
    const progressBar = document.getElementById('progressBar');
    
    if (progress) progress.style.display = 'none';
    if (progressText) progressText.style.display = 'none';
    if (progressBar) progressBar.style.width = '0%';
}

// Results Display
function showResults(data, analysisType) {
    const resultsSection = document.getElementById('resultsSection');
    if (!resultsSection) return;
    
    let resultsHTML = '';
    
    if (analysisType === 'enhanced') {
        resultsHTML = generateEnhancedResultsHTML(data);
    } else {
        resultsHTML = generateStandardResultsHTML(data);
    }
    
    resultsSection.innerHTML = resultsHTML;
    resultsSection.style.display = 'block';
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function generateStandardResultsHTML(data) {
    // Extract data from the API response
    const responseData = data.data || data;
    const analysisData = responseData.comprehensive_analysis || responseData.enhanced_analysis || responseData.analysis || {};
    const sentimentData = analysisData.sentiment_data || {};
    const signalData = analysisData.signal_data || {};
    const priceData = analysisData.price_data || analysisData;  // Some data might be at the root
    const newsData = analysisData.news_data || {};
    const recommendation = analysisData.recommendation || {};
    
    return `
        <div class="col-12">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h5><i class="fas fa-chart-line"></i> Standard Analysis Results for ${priceData.symbol || analysisData.symbol || 'N/A'}</h5>
                    <small class="text-light">Single recommendation using basic TradingStrategy</small>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Price Information</h6>
                            <p><strong>Current Price:</strong> $${priceData.current_price !== undefined ? priceData.current_price : 'N/A'}</p>
                            <p><strong>Change:</strong> ${priceData.change !== undefined ? priceData.change : 'N/A'} (${priceData.change_percent || 'N/A'}%)</p>
                            <p><strong>Volume:</strong> ${priceData.volume?.toLocaleString() || 'N/A'}</p>
                        </div>
                        <div class="col-md-6">
                            <h6>Sentiment Analysis</h6>
                            <p><strong>Score:</strong> ${sentimentData.sentiment_score !== undefined ? sentimentData.sentiment_score : 'N/A'}</p>
                            <p><strong>Confidence:</strong> ${sentimentData.confidence !== undefined ? sentimentData.confidence : 'N/A'}</p>
                            <p><strong>Summary:</strong> ${(sentimentData.summary || 'N/A').substring(0, 100)}...</p>
                        </div>
                    </div>
                    <div class="row mt-3">
                        <div class="col-md-6">
                            <h6>Trading Signal</h6>
                            <p><strong>Action:</strong> <span class="badge bg-${getSignalColor(signalData.action || recommendation.action)}">${signalData.action || recommendation.action || 'N/A'}</span></p>
                            <p><strong>Strength:</strong> ${signalData.signal_strength !== undefined ? signalData.signal_strength : 'N/A'}</p>
                            <p><strong>Reasoning:</strong> ${signalData.reasoning || recommendation.reasoning || 'N/A'}</p>
                        </div>
                        <div class="col-md-6">
                            <h6>Recommendation Details</h6>
                            <p><strong>Strategy:</strong> ${recommendation.strategy_type || 'Standard'}</p>
                            <p><strong>Option Type:</strong> ${recommendation.option_type || 'N/A'}</p>
                            <p><strong>Strike Price:</strong> $${recommendation.strike_price || 'N/A'}</p>
                            <p><strong>Days to Expiry:</strong> ${recommendation.days_to_expiry || 'N/A'}</p>
                        </div>
                    </div>
                    <div class="row mt-3">
                        <div class="col-12">
                            <h6>Analysis Summary</h6>
                            <p><strong>Articles Analyzed:</strong> ${newsData.article_count || analysisData.news_count || 'N/A'}</p>
                            <p><strong>AI Provider:</strong> ${data.data?.ai_provider_used || data.ai_provider_used || 'N/A'}</p>
                            <p><strong>Analysis Type:</strong> ${analysisData.analysis_type || 'Standard'}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function generateEnhancedResultsHTML(data) {
    // Extract data from the nested structure
    const analysisData = data.data?.enhanced_analysis || data.data?.comprehensive_analysis || data.enhanced_analysis || data.comprehensive_analysis || {};
    const symbol = analysisData.symbol || 'N/A';
    const priceData = analysisData.price_data || {};
    const sentimentData = analysisData.sentiment_data || {};
    const recommendations = analysisData.recommendations || {};
    
    // Extract different recommendation types
    const allRecommendations = recommendations.all_recommendations || [];
    const stockRecommendations = recommendations.stock_recommendations || [];
    const optionsRecommendations = recommendations.options_recommendations || [];
    const topRecommendation = recommendations.top_recommendation || {};
    const recommendationSummary = recommendations.recommendation_summary || {};
    
    // Generate HTML for all recommendations
    const recommendationsHTML = allRecommendations.map((rec, index) => {
        const confidence = Math.round((rec.confidence || 0) * 100);
        const category = rec.category || 'Unknown';
        const rank = rec.overall_rank || (index + 1);
        
        return `
            <div class="col-md-6 mb-3">
                <div class="card h-100 ${rank === 1 ? 'border-warning' : ''}">
                    <div class="card-header bg-${getSignalColor(rec.action)} text-white">
                        <div class="d-flex justify-content-between align-items-center">
                            <h6 class="mb-0">${rec.strategy_type || 'Strategy ' + rank}</h6>
                            <span class="badge bg-light text-dark">#${rank}</span>
                        </div>
                        <small>${category} | Confidence: ${confidence}%</small>
                    </div>
                    <div class="card-body">
                        <div class="mb-2">
                            <strong>Action:</strong> <span class="badge bg-${getSignalColor(rec.action)}">${rec.action || 'N/A'}</span>
                        </div>
                        
                        ${rec.option_type ? `
                        <div class="mb-2">
                            <strong>${rec.option_type?.toUpperCase()} Option</strong><br>
                            <small>Strike: $${rec.strike_price || 'N/A'} | Premium: $${rec.option_price || 'N/A'}</small><br>
                            <small>Days to Expiry: ${rec.days_to_expiry || 'N/A'}</small>
                        </div>
                        ` : ''}
                        
                        ${rec.backtest_results ? `
                        <div class="mb-2">
                            <strong>Backtest Results</strong>
                            <div class="small">
                                <div>Win Rate: ${rec.backtest_results.win_rate || 0}% (${rec.backtest_results.total_trades || 0} trades)</div>
                                <div>Avg Return: ${rec.backtest_results.avg_return > 0 ? '+' : ''}${rec.backtest_results.avg_return || 0}%</div>
                                <div>Max Gain: ${rec.backtest_results.max_gain || 0}% | Max Loss: ${rec.backtest_results.max_loss || 0}%</div>
                            </div>
                        </div>
                        ` : ''}
                        
                        ${rec.reasoning ? `
                        <div class="alert alert-light p-2 mt-2 mb-0 small">
                            <strong>Strategy:</strong> ${rec.reasoning.substring(0, 150)}${rec.reasoning.length > 150 ? '...' : ''}
                        </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('\n');
    
    // Generate top recommendation summary
    const topRecommendationSummary = topRecommendation ? `
        <div class="col-12 mb-4">
            <div class="card border-warning">
                <div class="card-header bg-warning text-dark">
                    <h6 class="mb-0"><i class="fas fa-trophy"></i> Top Recommendation</h6>
                </div>
                <div class="card-body">
                    <div class="row text-center">
                        <div class="col-md-3">
                            <div class="h5 text-${getSignalColor(topRecommendation.action)}">${topRecommendation.action || 'N/A'}</div>
                            <div class="text-muted small">Action</div>
                        </div>
                        <div class="col-md-3">
                            <div class="h5">${Math.round((topRecommendation.confidence || 0) * 100)}%</div>
                            <div class="text-muted small">Confidence</div>
                        </div>
                        <div class="col-md-3">
                            <div class="h5">${topRecommendation.category || 'N/A'}</div>
                            <div class="text-muted small">Category</div>
                        </div>
                        <div class="col-md-3">
                            <div class="h5">${recommendationSummary.total_strategies || allRecommendations.length}</div>
                            <div class="text-muted small">Total Strategies</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    ` : '';
    
    return `
        <div class="col-12">
            <div class="card mb-4">
                <div class="card-header bg-success text-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h5 class="mb-0"><i class="fas fa-chart-line"></i> ${symbol} - Enhanced Analysis</h5>
                            <small>Multiple strategies with backtesting from EnhancedTradingStrategy</small>
                        </div>
                        <span class="badge bg-light text-dark">${allRecommendations.length} Strategies</span>
                    </div>
                </div>
                <div class="card-body">
                    <div class="row mb-3">
                        <div class="col-md-3">
                            <div class="h5 mb-1">$${priceData.current_price || 'N/A'}</div>
                            <div class="text-muted small">Current Price</div>
                        </div>
                        <div class="col-md-3">
                            <div class="h5 mb-1">${priceData.change || 'N/A'} (${priceData.change_percent || 'N/A'}%)</div>
                            <div class="text-muted small">Today's Change</div>
                        </div>
                        <div class="col-md-3">
                            <div class="h5 mb-1">${priceData.volume ? priceData.volume.toLocaleString() : 'N/A'}</div>
                            <div class="text-muted small">Volume</div>
                        </div>
                        <div class="col-md-3">
                            <div class="h5 mb-1">${Math.round((sentimentData.sentiment_score || 0) * 100) / 100}</div>
                            <div class="text-muted small">Sentiment Score</div>
                        </div>
                    </div>
                    
                    ${topRecommendationSummary}
                    
                    <div class="row">
                        <div class="col-12 mb-3">
                            <h6>All Strategy Recommendations (Ranked by Confidence)</h6>
                        </div>
                        ${recommendationsHTML || '<div class="col-12">No strategy recommendations available</div>'}
                    </div>
                    
                    <div class="row mt-3">
                        <div class="col-md-6">
                            <h6>Strategy Breakdown</h6>
                            <p><strong>Stock Strategies:</strong> ${stockRecommendations.length}</p>
                            <p><strong>Options Strategies:</strong> ${optionsRecommendations.length}</p>
                            <p><strong>Best Category:</strong> ${recommendationSummary.best_category || 'N/A'}</p>
                        </div>
                        <div class="col-md-6">
                            <h6>Analysis Details</h6>
                            <p><strong>Analysis Type:</strong> ${analysisData.analysis_type || 'Enhanced'}</p>
                            <p><strong>Articles Analyzed:</strong> ${analysisData.news_count || 'N/A'}</p>
                            <p><strong>Generated:</strong> ${new Date().toLocaleString()}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function getSignalColor(action) {
    switch (action?.toUpperCase()) {
        case 'BUY': return 'success';
        case 'SELL': return 'danger';
        case 'HOLD': return 'warning';
        default: return 'secondary';
    }
}

// Debug Panel Functions
function initializeDebugPanel() {
    // Debug panel is already visible by default
    console.log('Debug panel initialized');
}

function toggleDebugPanel() {
    const debugBody = document.getElementById('debugPanelBody');
    if (debugBody) {
        debugBody.style.display = debugBody.style.display === 'none' ? 'block' : 'none';
    }
}

function clearDebugPanel() {
    document.getElementById('requestData').textContent = 'No request data';
    document.getElementById('responseData').textContent = 'No response data';
    document.getElementById('requestStatus').innerHTML = '<small>No request made yet</small>';
    document.getElementById('responseStatus').innerHTML = '<small>No response received yet</small>';
}

function updateDebugPanel(type, data) {
    if (type === 'request') {
        document.getElementById('requestData').textContent = JSON.stringify(data, null, 2);
        document.getElementById('requestStatus').innerHTML = '<small class="text-success">Request sent successfully</small>';
    } else if (type === 'response') {
        document.getElementById('responseData').textContent = JSON.stringify(data, null, 2);
        document.getElementById('responseStatus').innerHTML = '<small class="text-success">Response received</small>';
    }
}

// Utility Functions
function showAlert(message, type = 'info') {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at top of container
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

function toggleHowItWorks() {
    const howItWorksCard = document.getElementById('howItWorksCard');
    if (howItWorksCard) {
        howItWorksCard.style.display = howItWorksCard.style.display === 'none' ? 'block' : 'none';
    }
}

function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        navigator.clipboard.writeText(element.textContent).then(() => {
            showAlert('Copied to clipboard!', 'success');
        }).catch(() => {
            showAlert('Failed to copy to clipboard', 'warning');
        });
    }
}

// Export functions for global access
window.doStandardAnalysis = doStandardAnalysis;
window.doEnhancedAnalysis = doEnhancedAnalysis;
window.toggleHowItWorks = toggleHowItWorks;
window.toggleDebugPanel = toggleDebugPanel;
window.clearDebugPanel = clearDebugPanel;
window.copyToClipboard = copyToClipboard;
