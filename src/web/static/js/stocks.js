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
            console.log('[DEBUG] Refresh button clicked - triggering full pipeline');
            refreshMarketMoversData();
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
async function loadSP500Data(forceRefresh = false) {
    console.log('[DEBUG] Requesting S&P 500 data from API');
    console.log('[DEBUG] loadSP500Data called with forceRefresh:', forceRefresh);
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
        // First, try to get preloaded data for faster loading (unless forceRefresh is true)
        console.log('[DEBUG] Checking for preloaded data...');
        let data = null;
        let usingCachedData = false;
        let networkError = false;
        
        // Skip cache if forceRefresh is true
        if (!forceRefresh) {
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
        } else {
            console.log('[DEBUG] Force refresh requested - skipping cache');
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
        console.log('[DEBUG] Calling displayEnhancedAnalysis with data');
        // Note: displayEnhancedRecommendations was removed, using displayEnhancedAnalysis instead
        
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
    
    // Ensure we only show exactly 6 stocks (3 winners + 3 losers)
    const limitedStocks = stocks.slice(0, 6);
    console.log('[DEBUG] Limited to', limitedStocks.length, 'stocks for table display');
    
    // Build all HTML at once instead of appending to DOM multiple times
    let tableHtml = '';
    
    limitedStocks.forEach((stock, index) => {
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
        console.log('[DEBUG] Finished populating stocks table with', limitedStocks.length, 'rows');
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
    
    // Debug: Print structure of each stock object
    stocks.forEach((stock, idx) => {
        if (!stock) {
            console.warn(`[DEBUG] Stock at index ${idx} is null/undefined`);
            return;
        }
        const hasPriceData = stock.hasOwnProperty('price_data');
        const hasSentimentData = stock.hasOwnProperty('sentiment_data');
        const changePercent = hasPriceData ? stock.price_data.change_percent : undefined;
        const sentimentScore = hasSentimentData ? stock.sentiment_data.sentiment_score : undefined;
        console.log(`[DEBUG][Stock ${idx}] symbol: ${stock.symbol}, has price_data: ${hasPriceData}, has sentiment_data: ${hasSentimentData}, change_percent:`, changePercent, ', sentiment_score:', sentimentScore);
        if (!hasPriceData) {
            console.warn(`[DEBUG][Stock ${idx}] MISSING price_data`);
        }
        if (!hasSentimentData) {
            console.warn(`[DEBUG][Stock ${idx}] MISSING sentiment_data`);
        }
        if (hasPriceData && typeof changePercent === 'undefined') {
            console.warn(`[DEBUG][Stock ${idx}] price_data MISSING change_percent`);
        }
        if (hasSentimentData && typeof sentimentScore === 'undefined') {
            console.warn(`[DEBUG][Stock ${idx}] sentiment_data MISSING sentiment_score`);
        }
    });
    
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
    
    // Sort stocks by change_percent (winners vs losers)
    const winners = stocks.filter(stock => {
        if (!stock || !stock.price_data || typeof stock.price_data.change_percent === 'undefined') return false;
        const changeValue = parseFloat(String(stock.price_data.change_percent).replace('%', ''));
        return changeValue > 0;
    }).sort((a, b) => {
        const aVal = parseFloat(String(a.price_data.change_percent).replace('%', ''));
        const bVal = parseFloat(String(b.price_data.change_percent).replace('%', ''));
        return bVal - aVal;
    });
    const losers = stocks.filter(stock => {
        if (!stock || !stock.price_data || typeof stock.price_data.change_percent === 'undefined') return false;
        const changeValue = parseFloat(String(stock.price_data.change_percent).replace('%', ''));
        return changeValue < 0;
    }).sort((a, b) => {
        const aVal = parseFloat(String(a.price_data.change_percent).replace('%', ''));
        const bVal = parseFloat(String(b.price_data.change_percent).replace('%', ''));
        return aVal - bVal;
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
async function analyzeStock(symbol) {
    console.log(`[DEBUG] analyzeStock called for symbol: ${symbol}`);
    
    // Show loading state
    showAlert(`Analyzing ${symbol} with enhanced analysis...`, 'info');
    
    // Show the enhanced analysis results section
    const enhancedSection = document.getElementById('enhancedAnalysisResults');
    if (enhancedSection) {
        enhancedSection.style.display = 'block';
    }
    
    // Show loading in the container
    const container = document.getElementById('enhancedAnalysisContainer');
    if (container) {
        container.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Running comprehensive analysis for ${symbol}...</p>
            </div>
        `;
    }
    
    try {
        // Call the comprehensive analysis endpoint
        const response = await fetch('/api/comprehensive_analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                symbol: symbol,
                ai_provider: 'ollama'
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log(`[DEBUG] Enhanced analysis response for ${symbol}:`, data);
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Display the enhanced analysis results
        displayEnhancedAnalysis(data.data, symbol);
        
        showAlert(`Enhanced analysis completed for ${symbol}!`, 'success');
        
    } catch (error) {
        console.error(`[DEBUG] Error analyzing ${symbol}:`, error);
        showAlert(`Error analyzing ${symbol}: ${error.message}`, 'danger');
        
        // Show error in the container
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i> 
                    Error analyzing ${symbol}: ${error.message}
                </div>
            `;
        }
    }
}

// Display enhanced analysis results
function displayEnhancedAnalysis(data, symbol) {
    console.log('[DEBUG] displayEnhancedAnalysis called with data:', data);
    console.log('[DEBUG] Symbol:', symbol);
    
    const container = document.getElementById('enhancedAnalysisContainer');
    if (!container) {
        console.error('[DEBUG] enhancedAnalysisContainer not found');
        return;
    }
    console.log('[DEBUG] Found enhancedAnalysisContainer:', container);
    
    const priceData = data.price_data || {};
    const sentimentData = data.sentiment_data || {};
    const signalData = data.signal_data || {};
    const comprehensiveRecommendations = data.comprehensive_recommendations || {};
    
    console.log('[DEBUG] Price data:', priceData);
    console.log('[DEBUG] Sentiment data:', sentimentData);
    console.log('[DEBUG] Signal data:', signalData);
    console.log('[DEBUG] Comprehensive recommendations:', comprehensiveRecommendations);
    
    // Get the best options recommendation
    const optionsRecommendations = comprehensiveRecommendations.options_recommendations || [];
    const bestOption = optionsRecommendations.length > 0 ? optionsRecommendations[0] : null;
    
    // Get the best stock recommendation
    const stockRecommendations = comprehensiveRecommendations.stock_recommendations || [];
    const bestStock = stockRecommendations.length > 0 ? stockRecommendations[0] : null;
    
    console.log('[DEBUG] Options recommendations count:', optionsRecommendations.length);
    console.log('[DEBUG] Stock recommendations count:', stockRecommendations.length);
    console.log('[DEBUG] Best option:', bestOption);
    console.log('[DEBUG] Best stock:', bestStock);
    
    let html = `
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <h6><i class="fas fa-chart-bar"></i> ${symbol} - Current Data</h6>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-6">
                                <strong>Current Price:</strong><br>
                                <span class="h5 text-primary">${formatCurrency(priceData.current_price || 0)}</span>
                            </div>
                            <div class="col-6">
                                <strong>Change:</strong><br>
                                <span class="h5 ${priceData.change_percent > 0 ? 'text-success' : 'text-danger'}">
                                    ${priceData.change_percent || '0%'}
                                </span>
                            </div>
                        </div>
                        <hr>
                        <div class="row">
                            <div class="col-6">
                                <strong>Sentiment Score:</strong><br>
                                <span class="h6 ${getSentimentClass(sentimentData.sentiment_score || 0)}">
                                    ${(sentimentData.sentiment_score || 0).toFixed(3)}
                                </span>
                            </div>
                            <div class="col-6">
                                <strong>Confidence:</strong><br>
                                <span class="h6">${((sentimentData.confidence || 0) * 100).toFixed(1)}%</span>
                            </div>
                        </div>
                        <hr>
                        <div class="row">
                            <div class="col-6">
                                <strong>Signal:</strong><br>
                                <span class="badge ${getSignalClass(signalData.action)}">${signalData.action || 'HOLD'}</span>
                            </div>
                            <div class="col-6">
                                <strong>Signal Strength:</strong><br>
                                <span class="h6">${(signalData.signal_strength || 0).toFixed(3)}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-success text-white">
                        <h6><i class="fas fa-chart-line"></i> Trading Recommendations</h6>
                    </div>
                    <div class="card-body">
    `;
    
    // Add stock recommendation
    if (bestStock) {
        html += `
            <div class="mb-3">
                <h6><i class="fas fa-stock"></i> Stock Recommendation</h6>
                <div class="alert alert-info">
                    <strong>Action:</strong> <span class="badge ${getSignalClass(bestStock.action)}">${bestStock.action}</span><br>
                    <strong>Confidence:</strong> ${(bestStock.confidence * 100).toFixed(1)}%<br>
                    <strong>Current Price:</strong> ${formatCurrency(bestStock.current_price || 0)}<br>
                    <strong>Risk Level:</strong> <span class="badge bg-secondary">${bestStock.risk_level || 'N/A'}</span><br>
                    <strong>Time Horizon:</strong> ${bestStock.time_horizon || 'N/A'}<br>
                    <small><strong>Reasoning:</strong> ${bestStock.reasoning || 'No reasoning provided'}</small>
                </div>
            </div>
        `;
    }
    
    // Add options recommendation
    if (bestOption) {
        html += `
            <div class="mb-3">
                <h6><i class="fas fa-options"></i> Options Recommendation</h6>
                <div class="alert alert-warning">
                    <strong>Strategy:</strong> ${bestOption.recommendation_type || 'N/A'}<br>
                    <strong>Action:</strong> <span class="badge ${getSignalClass(bestOption.action)}">${bestOption.action}</span><br>
                    <strong>Strike Price:</strong> ${formatCurrency(bestOption.strike_price || 0)}<br>
                    <strong>Expiry:</strong> ${bestOption.days_to_expiry || 'N/A'} days<br>
                    <strong>Target Return:</strong> ${bestOption.target_gain_percent || 'N/A'}%<br>
                    <strong>Option Price:</strong> ${formatCurrency(bestOption.option_price || 0)}<br>
                    <strong>Confidence:</strong> ${(bestOption.confidence * 100).toFixed(1)}%<br>
                    <small><strong>Reasoning:</strong> ${bestOption.reasoning || 'No notes provided'}</small>
                </div>
            </div>
        `;
    }
    
    if (!bestStock && !bestOption) {
        html += `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle"></i> No trading recommendations available for ${symbol}.
            </div>
        `;
    }
    
    html += `
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add position sizing and risk management if available
    const positionSizing = comprehensiveRecommendations.position_sizing;
    const riskManagement = comprehensiveRecommendations.risk_management;
    
    if (positionSizing || riskManagement) {
        html += `
            <div class="row mt-3">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-warning text-dark">
                            <h6><i class="fas fa-shield-alt"></i> Position Sizing & Risk Management</h6>
                        </div>
                        <div class="card-body">
        `;
        
        if (positionSizing) {
            html += `
                <div class="row">
                    <div class="col-md-6">
                        <h6>Position Sizing</h6>
                        <ul class="list-unstyled">
                            <li><strong>Recommended Position Size:</strong> ${positionSizing.recommended_size || 'N/A'}</li>
                            <li><strong>Maximum Position:</strong> ${positionSizing.max_position || 'N/A'}</li>
                            <li><strong>Portfolio Allocation:</strong> ${positionSizing.portfolio_allocation || 'N/A'}</li>
                        </ul>
                    </div>
            `;
        }
        
        if (riskManagement) {
            html += `
                    <div class="col-md-6">
                        <h6>Risk Management</h6>
                        <ul class="list-unstyled">
                            <li><strong>Stop Loss:</strong> ${riskManagement.stop_loss || 'N/A'}</li>
                            <li><strong>Take Profit:</strong> ${riskManagement.take_profit || 'N/A'}</li>
                            <li><strong>Risk/Reward Ratio:</strong> ${riskManagement.risk_reward_ratio || 'N/A'}</li>
                        </ul>
                    </div>
                </div>
            `;
        }
        
        html += `
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    console.log('[DEBUG] About to set HTML content. HTML length:', html.length);
    console.log('[DEBUG] HTML preview:', html.substring(0, 500) + '...');
    container.innerHTML = html;
    console.log('[DEBUG] HTML content set successfully');
}

// Run S&P 500 analysis (for the button click)
function runSP500Analysis() {
    loadSP500Data();
}

// Refresh market movers data - triggers full pipeline
async function refreshMarketMoversData() {
    console.log('[DEBUG] refreshMarketMoversData called - triggering full pipeline');
    
    // Show loading indicator
    showLoading('loadingSpinner');
    
    if (document.getElementById('refreshBtn')) {
        document.getElementById('refreshBtn').disabled = true;
        document.getElementById('refreshBtn').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
    }
    
    try {
        // Trigger the full pipeline to get fresh market movers
        console.log('[DEBUG] Making request to /api/refresh_market_movers');
        const response = await fetch('/api/refresh_market_movers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            credentials: 'same-origin'
        });
        
        console.log('[DEBUG] Refresh API response status:', response.status);
        
        if (response.ok) {
            const result = await response.json();
            console.log('[DEBUG] Refresh API response:', result);
            
            if (result.success) {
                showAlert('Market movers data refreshed successfully!', 'success');
                // Now load the fresh data with forceRefresh=true to bypass cache
                await loadSP500Data(true);
            } else {
                throw new Error(result.error || 'Failed to refresh market movers data');
            }
        } else {
            throw new Error(`Refresh API request failed with status: ${response.status}`);
        }
        
    } catch (error) {
        console.error('[DEBUG] Error refreshing market movers data:', error);
        showAlert('Error refreshing market movers data: ' + error.message, 'danger');
        
        // Still try to load existing data
        await loadSP500Data();
    } finally {
        // Hide loading indicator
        hideLoading('loadingSpinner');
        
        if (document.getElementById('refreshBtn')) {
            document.getElementById('refreshBtn').disabled = false;
            document.getElementById('refreshBtn').innerHTML = '<i class="fas fa-sync-alt"></i> Refresh Winners & Losers Analysis';
        }
    }
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

 