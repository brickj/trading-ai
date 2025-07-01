/* S&P 500 Analysis JavaScript */

// Global variables
let sp500Data = [];
let autoRefreshInterval = null;

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    console.log('[DEBUG] DOMContentLoaded event fired');
    
    // Set up refresh button
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            console.log('[DEBUG] Refresh button clicked');
            loadSP500Data();
        });
        console.log('[DEBUG] Refresh button event listener added');
    } else {
        console.error('[DEBUG] refreshBtn element not found');
    }
    
    // Set up auto-refresh toggle
    const autoRefreshToggle = document.getElementById('autoRefreshToggle');
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('change', function() {
            const isEnabled = this.checked;
            console.log('[DEBUG] Auto-refresh toggled:', isEnabled);
            if (isEnabled) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        });
        console.log('[DEBUG] Auto-refresh toggle event listener added');
    } else {
        console.log('[DEBUG] autoRefreshToggle element not found - auto-refresh disabled');
    }
    
    // Load data immediately
    console.log('[DEBUG] Loading initial data');
    setTimeout(() => {
        console.log('[DEBUG] Calling loadSP500Data from setTimeout');
        loadSP500Data();
    }, 100); // Small delay to ensure DOM is fully ready
    
    console.log('[DEBUG] Page initialization complete');
});

// Auto-refresh functions
function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    // Refresh every 5 minutes (300000ms)
    autoRefreshInterval = setInterval(() => {
        console.log('[DEBUG] Auto-refresh triggered');
        loadSP500Data();
    }, 300000);
    console.log('[DEBUG] Auto-refresh started (5 minute intervals)');
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
        console.log('[DEBUG] Auto-refresh stopped');
    }
}

// Load S&P 500 analysis data
async function loadSP500Data() {
    console.log('[DEBUG] Requesting S&P 500 data from API');
    console.log('[DEBUG] loadSP500Data called');
    const startTime = Date.now();
    
    // Clear any previous content
    if (document.getElementById('winnersList')) {
        document.getElementById('winnersList').innerHTML = '<div class="text-center text-muted"><div class="spinner-border spinner-border-sm" role="status"></div> Loading winners...</div>';
    }
    if (document.getElementById('losersList')) {
        document.getElementById('losersList').innerHTML = '<div class="text-center text-muted"><div class="spinner-border spinner-border-sm" role="status"></div> Loading losers...</div>';
    }
    if (document.getElementById('stocksTableBody')) {
        document.getElementById('stocksTableBody').innerHTML = '<tr><td colspan="9" class="text-center">Loading data...</td></tr>';
    }
    
    // Show loading indicator
    showLoading('loadingSpinner');
    
    if (document.getElementById('refreshBtn')) {
        document.getElementById('refreshBtn').disabled = true;
    }
    
    try {
        // First, try to get preloaded data for faster loading
        console.log('[DEBUG] Checking for preloaded data...');
        let data = null;
        let usingCachedData = false;
        let networkError = false;
        
        try {
            const preloadResponse = await fetch('/api/preloaded_data', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                credentials: 'same-origin'  // Include cookies for CSRF if needed
            });
            
            if (preloadResponse.ok) {
                const preloadData = await preloadResponse.json();
                if (preloadData.success && preloadData.data && preloadData.data.enhanced_analysis) {
                    data = {
                        success: true,
                        data: preloadData.data
                    };
                    usingCachedData = true;
                    console.log('[DEBUG] Using preloaded cached data:', preloadData.message);
                } else {
                    console.log('[DEBUG] Preloaded data not available or invalid:', preloadData.message);
                }
            } else {
                console.log('[DEBUG] Preloaded data endpoint returned error:', preloadResponse.status);
            }
        } catch (e) {
            networkError = true;
            console.log('[DEBUG] Network error accessing preloaded data:', e.message);
        }
        
        // If no cached data and no network error, make full API call
        if (!data && !networkError) {
            console.log('[DEBUG] Making full API request to /api/sp500_analysis');
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout
                
                const response = await fetch('/api/sp500_analysis', {
                    method: 'GET',
                    signal: controller.signal,
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    credentials: 'same-origin'
                });
                
                clearTimeout(timeoutId);
                console.log('[DEBUG] API response status:', response.status);
                
                if (response.ok) {
                    data = await response.json();
                    console.log('[DEBUG] API response data received');
                } else {
                    throw new Error(`API request failed with status: ${response.status}`);
                }
            } catch (e) {
                console.log('[DEBUG] Full API request failed:', e.message);
                networkError = true;
            }
        }
        
        // If we still don't have data due to network issues, show a helpful message
        if (!data) {
            console.log('[DEBUG] No data available due to network issues');
            
            // Show network error message
            if (document.getElementById('stocksTableBody')) {
                document.getElementById('stocksTableBody').innerHTML = `
                    <tr>
                        <td colspan="9" class="text-center">
                            <div class="alert alert-warning">
                                <h5>Network Connectivity Issue</h5>
                                <p>Unable to load stock data due to network connectivity issues.</p>
                                <p>This may be due to:</p>
                                <ul class="text-left" style="display: inline-block;">
                                    <li>Server is starting up (please wait 30 seconds and refresh)</li>
                                    <li>Network connectivity problems</li>
                                    <li>Browser security restrictions</li>
                                </ul>
                                <button class="btn btn-primary mt-2" onclick="loadSP500Data()">Try Again</button>
                            </div>
                        </td>
                    </tr>
                `;
            }
            
            // Show error in winners/losers sections
            if (document.getElementById('winnersList')) {
                document.getElementById('winnersList').innerHTML = '<div class="alert alert-warning">Network error - please refresh</div>';
            }
            if (document.getElementById('losersList')) {
                document.getElementById('losersList').innerHTML = '<div class="alert alert-warning">Network error - please refresh</div>';
            }
            
            // Hide loading spinner
            hideLoading('loadingSpinner');
            
            if (document.getElementById('refreshBtn')) {
                document.getElementById('refreshBtn').disabled = false;
            }
            
            if (document.getElementById('lastUpdated')) {
                document.getElementById('lastUpdated').textContent = 'Last updated: Network Error';
            }
            
            return;
        }
        
        if (!data || !data.success) {
            throw new Error(`API returned error: ${data?.error || 'Unknown error'}`);
        }
        
        if (!data.data || !data.data.enhanced_analysis) {
            throw new Error('API response missing enhanced_analysis data');
        }
        
        // The API returns data.data.enhanced_analysis array
        sp500Data = data.data.enhanced_analysis || [];
        console.log('[DEBUG] Parsed sp500Data:', sp500Data.length, 'stocks');
        
        // Measure time taken to fetch and parse data
        const fetchDuration = (Date.now() - startTime) / 1000;
        console.log(`[DEBUG] Data fetched and parsed in ${fetchDuration.toFixed(2)} seconds ${usingCachedData ? '(cached)' : '(fresh)'}`);
        
        // Make sure we have data
        if (!sp500Data || sp500Data.length === 0) {
            showAlert('No S&P 500 data available. Please try again later.', 'warning');
            console.log('[DEBUG] No stocks data available');
            return;
        }
        
        // EXPLICITLY show the winners/losers summary section FIRST
        const winnersSummary = document.getElementById('winnersLosersSummary');
        if (winnersSummary) {
            winnersSummary.style.display = 'flex';
            console.log('[DEBUG] Explicitly showing winnersLosersSummary section');
        } else {
            console.error('[DEBUG] winnersLosersSummary element not found');
        }
        
        // EXPLICITLY show the enhanced results section
        const enhancedResults = document.getElementById('enhancedAnalysisResults');
        if (enhancedResults) {
            enhancedResults.style.display = 'block';
            console.log('[DEBUG] Explicitly showing enhancedAnalysisResults section');
        } else {
            console.error('[DEBUG] enhancedAnalysisResults element not found');
        }
        
        // Display the data in the UI AFTER showing the containers
        console.log('[DEBUG] Calling displaySP500Table with data');
        displaySP500Table(sp500Data);
        console.log('[DEBUG] Calling displayWinnersLosers with data');
        displayWinnersLosers(sp500Data);
        console.log('[DEBUG] Calling displayEnhancedRecommendations with data');
        displayEnhancedRecommendations(sp500Data);
        
        if (document.getElementById('lastUpdated')) {
            const timestamp = data.data.timestamp ? new Date(data.data.timestamp).toLocaleString() : 'Unknown';
            const cacheInfo = usingCachedData ? ' (cached)' : '';
            console.log('[DEBUG] Updating lastUpdated with timestamp:', timestamp);
            document.getElementById('lastUpdated').textContent = `Last updated: ${timestamp}${cacheInfo}`;
        }
        
        // Measure time taken to render data
        const renderDuration = (Date.now() - startTime) / 1000 - fetchDuration;
        console.log(`[DEBUG] Data rendered in ${renderDuration.toFixed(2)} seconds`);
        
        // Show summary statistics
        if (document.getElementById('summaryStats')) {
            const stats = data.data;
            document.getElementById('summaryStats').innerHTML = `
                <div class="row">
                    <div class="col-md-3">
                        <div class="card bg-primary text-white">
                            <div class="card-body text-center">
                                <h5>${stats.total_analyzed || 0}</h5>
                                <small>Stocks Analyzed</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-success text-white">
                            <div class="card-body text-center">
                                <h5>${stats.opportunities_found || 0}</h5>
                                <small>Opportunities Found</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-info text-white">
                            <div class="card-body text-center">
                                <h5>${stats.performance?.success_rate || 'N/A'}</h5>
                                <small>Success Rate</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-warning text-white">
                            <div class="card-body text-center">
                                <h5>${stats.errors_count || 0}</h5>
                                <small>Errors</small>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.getElementById('summaryStats').style.display = 'block';
        }
        
        console.log('[DEBUG] Rendering UI components for stock data completed successfully');
        
    } catch (err) {
        showAlert(`Failed to load S&P 500 data: ${err.message}`, 'danger');
        console.error('[DEBUG] Exception in loadSP500Data:', err);
        
        // Show error in the table
        if (document.getElementById('stocksTableBody')) {
            document.getElementById('stocksTableBody').innerHTML = `
                <tr>
                    <td colspan="9" class="text-center text-danger">
                        <i class="fas fa-exclamation-triangle"></i> 
                        Error loading data: ${err.message}
                    </td>
                </tr>
            `;
        }
        
        // Show error in winners/losers lists
        if (document.getElementById('winnersList')) {
            document.getElementById('winnersList').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i> 
                    Error loading winners: ${err.message}
                </div>
            `;
        }
        
        if (document.getElementById('losersList')) {
            document.getElementById('losersList').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i> 
                    Error loading losers: ${err.message}
                </div>
            `;
        }
    } finally {
        if (document.getElementById('refreshBtn')) {
            document.getElementById('refreshBtn').disabled = false;
        }
        hideLoading('loadingSpinner');
    }
}

// Display S&P 500 data in table
function displaySP500Table(stocks) {
    console.log('[DEBUG] displaySP500Table called with', stocks ? stocks.length : 0, 'stocks');
    const tbody = document.getElementById('stocksTableBody');
    if (!tbody) {
        console.error('[DEBUG] stocksTableBody element not found');
        return;
    }
    
    // Clear the table
    console.log('[DEBUG] Clearing stocksTableBody');
    tbody.innerHTML = '';
    
    // Check if we have stocks data
    if (!Array.isArray(stocks) || stocks.length === 0) {
        console.error('[DEBUG] No stocks data or invalid data type:', typeof stocks);
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center text-warning">
                    <i class="fas fa-exclamation-triangle"></i> No stock data available. Please try again later.
                </td>
            </tr>
        `;
        return;
    }
    
    console.log('[DEBUG] Starting to populate stocks table with', stocks.length, 'stocks');
    
    // Build all HTML at once instead of appending to DOM multiple times
    let tableHtml = '';
    
    stocks.forEach((stock, index) => {
        if (!stock) {
            console.log(`[DEBUG] Skipping null/undefined stock at index ${index}`);
            return; // Skip null/undefined stocks
        }
        
        console.log(`[DEBUG] Processing stock ${index + 1}/${stocks.length}: ${stock.symbol || 'unknown'}`);
        
        const sentimentData = stock.sentiment_data || {};
        const priceData = stock.price_data || {};
        const signalData = stock.signal_data || {};
        
        // Only show real data, no defaults
        const sentimentScore = sentimentData.sentiment_score;
        const confidence = sentimentData.confidence;
        const signalStrength = signalData.signal_strength;
        const action = signalData.action;
        
        // Skip rows with missing critical data
        if (sentimentScore === undefined || confidence === undefined || signalStrength === undefined || action === undefined) {
            console.log(`[DEBUG] Skipping ${stock.symbol} - missing critical data:`, { sentimentScore, confidence, signalStrength, action });
            return;
        }
        
        const sentimentClass = getSentimentClass(sentimentScore);
        const sentimentStrength = getSentimentStrength(sentimentScore);
        const signalClass = getSignalClass(action);
        
        tableHtml += `
            <tr>
                <td>${stock.type || 'Stock'}</td>
                <td><strong>${stock.symbol || 'Unknown'}</strong></td>
                <td>${formatCurrency(priceData.current_price || 0)}</td>
                <td class="${sentimentClass}">
                    ${sentimentScore.toFixed(3)}
                    ${sentimentStrength.badge}
                </td>
                <td>${(confidence * 100).toFixed(1)}%</td>
                <td><span class="badge ${signalClass}">${action}</span></td>
                <td>${signalStrength.toFixed(3)}</td>
                <td>${stock.news_count || 0}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="analyzeStock('${stock.symbol}')">
                        <i class="fas fa-chart-bar"></i> Analyze
                    </button>
                </td>
            </tr>
        `;
    });
    
    // Set the HTML all at once
    if (tableHtml) {
        tbody.innerHTML = tableHtml;
        console.log('[DEBUG] Finished populating stocks table with', stocks.length, 'rows');
    } else {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center text-warning">
                    <i class="fas fa-exclamation-triangle"></i> Failed to render stock data. Please try again later.
                </td>
            </tr>
        `;
        console.error('[DEBUG] Failed to generate table HTML');
    }
}

// Display winners and losers summary
function displayWinnersLosers(stocks) {
    console.log('[DEBUG] displayWinnersLosers called with:', stocks);
    
    // Safety check - ensure stocks is an array
    if (!Array.isArray(stocks)) {
        console.error('[DEBUG] stocks is not an array:', typeof stocks);
        showAlert('Error loading stock data. Please try again later.', 'danger');
        return;
    }
    
    const winnersList = document.getElementById('winnersList');
    const losersList = document.getElementById('losersList');
    
    if (!winnersList || !losersList) {
        console.error('[DEBUG] winnersList or losersList element not found');
        console.error('[DEBUG] winnersList exists:', !!winnersList);
        console.error('[DEBUG] losersList exists:', !!losersList);
        return;
    }
    
    // Sort stocks by type (winners vs losers) and then by sentiment score
    const winners = stocks.filter(stock => stock && stock.type === 'winner' && stock.sentiment_data?.sentiment_score !== undefined).sort((a, b) => {
        const aScore = a.sentiment_data.sentiment_score;
        const bScore = b.sentiment_data.sentiment_score;
        return bScore - aScore;
    });
    const losers = stocks.filter(stock => stock && stock.type === 'loser' && stock.sentiment_data?.sentiment_score !== undefined).sort((a, b) => {
        const aScore = a.sentiment_data.sentiment_score;
        const bScore = b.sentiment_data.sentiment_score;
        return aScore - bScore;
    });
    console.log('[DEBUG] Filtered winners:', winners.length, winners.map(w => w?.symbol || 'unknown'));
    console.log('[DEBUG] Filtered losers:', losers.length, losers.map(l => l?.symbol || 'unknown'));
    
    // Display winners
    winnersList.innerHTML = '';
    console.log('[DEBUG] Rendering winners to winnersList');
    
    if (!winners || winners.length === 0) {
        winnersList.innerHTML = '<div class="alert alert-info">No winners data available. Please refresh to try again.</div>';
        console.log('[DEBUG] No winners found, showing alert');
    } else {
        let winnersHtml = '';
        winners.slice(0, 3).forEach((stock, index) => {
            if (!stock) {
                console.log('[DEBUG] Skipping null/undefined winner at index', index);
                return; // Skip null/undefined stocks
            }
            
            const priceData = stock.price_data || {};
            const sentimentData = stock.sentiment_data || {};
            const changePercent = priceData.change_percent || '0%';
            const isPositive = String(changePercent).includes('-') === false;
            const changeClass = isPositive ? 'text-success' : 'text-danger';
            const changeIcon = isPositive ? 'fa-arrow-up' : 'fa-arrow-down';
            
            winnersHtml += `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div>
                        <strong>${stock.symbol || 'Unknown'}</strong>
                        <br><small class="text-muted">${formatCurrency(priceData.current_price || 0)}</small>
                    </div>
                    <div class="text-end">
                        <span class="${changeClass}">
                            <i class="fas ${changeIcon}"></i> ${changePercent}
                        </span>
                        <br><small class="text-muted">${sentimentData.sentiment_score.toFixed(3)} sentiment</small>
                    </div>
                </div>
            `;
        });
        
        if (winnersHtml) {
            winnersList.innerHTML = winnersHtml;
            console.log('[DEBUG] Winners content added to DOM, length:', winnersHtml.length);
        } else {
            winnersList.innerHTML = '<div class="alert alert-warning">Failed to render winners data. Please refresh to try again.</div>';
            console.log('[DEBUG] No winners HTML generated');
        }
    }
    
    // Display losers
    losersList.innerHTML = '';
    console.log('[DEBUG] Rendering losers to losersList');
    
    if (!losers || losers.length === 0) {
        losersList.innerHTML = '<div class="alert alert-info">No losers data available. Please refresh to try again.</div>';
        console.log('[DEBUG] No losers found, showing alert');
    } else {
        let losersHtml = '';
        losers.slice(0, 3).forEach((stock, index) => {
            if (!stock) {
                console.log('[DEBUG] Skipping null/undefined loser at index', index);
                return; // Skip null/undefined stocks
            }
            
            const priceData = stock.price_data || {};
            const sentimentData = stock.sentiment_data || {};
            const changePercent = priceData.change_percent || '0%';
            const isPositive = String(changePercent).includes('-') === false;
            const changeClass = isPositive ? 'text-success' : 'text-danger';
            const changeIcon = isPositive ? 'fa-arrow-up' : 'fa-arrow-down';
            
            losersHtml += `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div>
                        <strong>${stock.symbol || 'Unknown'}</strong>
                        <br><small class="text-muted">${formatCurrency(priceData.current_price || 0)}</small>
                    </div>
                    <div class="text-end">
                        <span class="${changeClass}">
                            <i class="fas ${changeIcon}"></i> ${changePercent}
                        </span>
                        <br><small class="text-muted">${sentimentData.sentiment_score.toFixed(3)} sentiment</small>
                    </div>
                </div>
            `;
        });
        
        if (losersHtml) {
            losersList.innerHTML = losersHtml;
            console.log('[DEBUG] Losers content added to DOM, length:', losersHtml.length);
        } else {
            losersList.innerHTML = '<div class="alert alert-warning">Failed to render losers data. Please refresh to try again.</div>';
            console.log('[DEBUG] No losers HTML generated');
        }
    }
    
    // Verify content was added
    console.log('[DEBUG] Final winnersList HTML length:', winnersList.innerHTML.length);
    console.log('[DEBUG] Final losersList HTML length:', losersList.innerHTML.length);
}

// Analyze individual stock
function analyzeStock(symbol) {
    showAlert(`Analyzing ${symbol}...`, 'info');
    // This would typically call an API endpoint for detailed analysis
    // For now, just show a basic message
    showAlert(`Detailed analysis for ${symbol} would be performed here.`, 'info');
}

// Run S&P 500 analysis (for the button click)
function runSP500Analysis() {
    loadSP500Data();
}

// Enhanced analysis function
async function runEnhancedAnalysis() {
    showAlert('Starting enhanced analysis...', 'info');
    
    try {
        const response = await fetch('/api/enhanced_analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                symbols: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
                ai_provider: 'ollama' 
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            showAlert(data.error, 'danger');
        } else {
            showAlert('Enhanced analysis completed!', 'success');
        }
        
    } catch (error) {
        showAlert('Error running enhanced analysis: ' + error.message, 'danger');
    }
}

// Helper functions
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'block';
    }
}

function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function getSentimentClass(score) {
    if (score > 0.3) return 'text-success';
    if (score > 0.1) return 'text-info';
    if (score < -0.3) return 'text-danger';
    if (score < -0.1) return 'text-warning';
    return 'text-muted';
}

function getSentimentStrength(score) {
    const absScore = Math.abs(score);
    if (absScore > 0.5) return { badge: '<span class="badge bg-danger">Strong</span>' };
    if (absScore > 0.3) return { badge: '<span class="badge bg-warning">Moderate</span>' };
    if (absScore > 0.1) return { badge: '<span class="badge bg-info">Weak</span>' };
    return { badge: '<span class="badge bg-secondary">Neutral</span>' };
}

function getSignalClass(action) {
    switch (action?.toUpperCase()) {
        case 'BUY':
        case 'CALL':
            return 'bg-success';
        case 'SELL':
        case 'PUT':
            return 'bg-danger';
        case 'HOLD':
            return 'bg-warning';
        default:
            return 'bg-secondary';
    }
}

function formatCurrency(amount) {
    if (typeof amount !== 'number') return '$0.00';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

// Display enhanced analysis results with position sizes and trading notes
function displayEnhancedRecommendations(stocks) {
    console.log('[DEBUG] displayEnhancedRecommendations called with', stocks ? stocks.length : 0, 'stocks');
    
    const container = document.getElementById('enhancedRecommendationsContainer');
    if (!container) {
        console.error('[DEBUG] enhancedRecommendationsContainer element not found');
        return;
    }
    
    // Clear the container
    container.innerHTML = '';
    
    // Check if we have stocks data
    if (!Array.isArray(stocks) || stocks.length === 0) {
        container.innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle"></i> No enhanced analysis data available. Please try again later.
            </div>
        `;
        return;
    }
    
    let recommendationsHtml = '';
    
    stocks.forEach((stock, index) => {
        if (!stock) {
            console.log(`[DEBUG] Skipping null/undefined stock at index ${index}`);
            return;
        }
        
        console.log(`[DEBUG] Processing enhanced analysis for stock ${index + 1}/${stocks.length}: ${stock.symbol || 'unknown'}`);
        
        // Get the comprehensive analysis data
        const comprehensiveAnalysis = stock.comprehensive_analysis || {};
        const optionsRecommendations = comprehensiveAnalysis.options_recommendations || [];
        const stockRecommendations = comprehensiveAnalysis.stock_recommendations || [];
        
        // Get the best options recommendation (first one with highest confidence)
        const bestOption = optionsRecommendations.length > 0 ? optionsRecommendations[0] : null;
        const bestStock = stockRecommendations.length > 0 ? stockRecommendations[0] : null;
        
        if (!bestOption && !bestStock) {
            console.log(`[DEBUG] No recommendations found for ${stock.symbol}`);
            return;
        }
        
        const priceData = stock.price_data || {};
        const sentimentData = stock.sentiment_data || {};
        
        recommendationsHtml += `
            <div class="card mb-4">
                <div class="card-header">
                    <h6 class="mb-0">
                        <i class="fas fa-chart-line"></i> 
                        <strong>${stock.symbol || 'Unknown'}</strong> - 
                        ${formatCurrency(priceData.current_price || 0)} 
                        <span class="badge ${getSentimentClass(sentimentData.sentiment_score || 0)}">
                            ${(sentimentData.sentiment_score || 0).toFixed(3)} sentiment
                        </span>
                    </h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        ${bestStock ? `
                        <div class="col-md-6">
                            <div class="card border-primary">
                                <div class="card-header bg-primary text-white">
                                    <h6><i class="fas fa-building"></i> Stock Recommendation</h6>
                                </div>
                                <div class="card-body">
                                    <p><strong>Action:</strong> <span class="badge ${getSignalClass(bestStock.action)}">${bestStock.action || 'HOLD'}</span></p>
                                    <p><strong>Confidence:</strong> ${((bestStock.confidence || 0) * 100).toFixed(1)}%</p>
                                    <p><strong>Reasoning:</strong> ${bestStock.reasoning || 'No reasoning provided'}</p>
                                    ${bestStock.shares_recommended ? `<p><strong>Shares:</strong> ${bestStock.shares_recommended}</p>` : ''}
                                    ${bestStock.target_price ? `<p><strong>Target:</strong> ${formatCurrency(bestStock.target_price)}</p>` : ''}
                                    ${bestStock.stop_loss_price ? `<p><strong>Stop Loss:</strong> ${formatCurrency(bestStock.stop_loss_price)}</p>` : ''}
                                </div>
                            </div>
                        </div>
                        ` : ''}
                        
                        ${bestOption ? `
                        <div class="col-md-6">
                            <div class="card border-warning">
                                <div class="card-header bg-warning text-dark">
                                    <h6><i class="fas fa-chart-line"></i> Options Recommendation</h6>
                                </div>
                                <div class="card-body">
                                    <p><strong>Action:</strong> <span class="badge ${getSignalClass(bestOption.action)}">${bestOption.action || 'HOLD'}</span></p>
                                    <p><strong>Option Type:</strong> <span class="badge ${bestOption.option_type === 'call' ? 'bg-success' : 'bg-danger'}">${bestOption.option_type ? bestOption.option_type.toUpperCase() : 'N/A'}</span></p>
                                    <p><strong>Strike Price:</strong> ${formatCurrency(bestOption.strike_price || 0)}</p>
                                    <p><strong>Option Price:</strong> ${formatCurrency(bestOption.option_price || 0)}</p>
                                    <p><strong>Days to Expiry:</strong> ${bestOption.days_to_expiry || 'N/A'}</p>
                                    <p><strong>Target Gain:</strong> ${bestOption.target_gain_percent || 'N/A'}%</p>
                                    <p><strong>Stop Loss:</strong> ${bestOption.stop_loss_percent || 'N/A'}%</p>
                                    <p><strong>Confidence:</strong> ${((bestOption.confidence || 0) * 100).toFixed(1)}%</p>
                                    <p><strong>Reasoning:</strong> ${bestOption.reasoning || 'No reasoning provided'}</p>
                                </div>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                    
                    ${bestOption && bestOption.position_recommendations ? `
                    <div class="row mt-3">
                        <div class="col-md-6">
                            <div class="card border-info">
                                <div class="card-header bg-info text-white">
                                    <h6><i class="fas fa-dollar-sign"></i> Position Sizes</h6>
                                </div>
                                <div class="card-body">
                                    ${Object.entries(bestOption.position_recommendations).map(([accountSize, rec]) => `
                                        <div class="mb-2">
                                            <strong>${accountSize} Account:</strong><br>
                                            <small>
                                                Contracts: ${rec.contracts || 'N/A'}<br>
                                                Cost: ${formatCurrency(rec.total_cost || 0)}<br>
                                                Risk: ${rec.risk_percent || 'N/A'}%<br>
                                                R/R Ratio: ${rec.risk_reward_ratio ? rec.risk_reward_ratio.toFixed(2) : 'N/A'}
                                            </small>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="card border-success">
                                <div class="card-header bg-success text-white">
                                    <h6><i class="fas fa-lightbulb"></i> Trading Notes</h6>
                                </div>
                                <div class="card-body">
                                    ${bestOption.trading_notes || bestOption.day_trading_notes ? `
                                        <ul class="list-unstyled">
                                            ${(bestOption.trading_notes || bestOption.day_trading_notes).map(note => `<li><small>${note}</small></li>`).join('')}
                                        </ul>
                                    ` : '<p class="text-muted">No trading notes available</p>'}
                                </div>
                            </div>
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
    });
    
    if (recommendationsHtml) {
        container.innerHTML = recommendationsHtml;
        console.log('[DEBUG] Enhanced recommendations content added to DOM');
    } else {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i> No enhanced recommendations available. Please try again later.
            </div>
        `;
        console.log('[DEBUG] No enhanced recommendations HTML generated');
    }
} 