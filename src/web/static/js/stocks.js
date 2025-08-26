/* Stocks Page JavaScript - S&P 500 Winners & Losers Analysis */

// Global variables
let isRefreshing = false;
let autoRefreshInterval = null;
let lastUpdated = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 [STOCKS] Initializing stocks page...');
    
    // Add event listeners
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            console.log('🔄 [STOCKS] Manual refresh requested');
            loadStocksAnalysis(true);
        });
    }
    
    const autoRefreshToggle = document.getElementById('autoRefreshToggle');
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('click', toggleAutoRefresh);
    }
    
    // Load initial data
    loadStocksAnalysis(false);
    
    // Set up WebSocket connection for real-time updates
    setupWebSocket();
});

// Set up WebSocket connection for real-time progress updates
function setupWebSocket() {
    if (typeof io !== 'undefined') {
        const socket = io();
        
        socket.on('sp500_progress', function(data) {
            console.log('📡 [WEBSOCKET] Progress update:', data);
            updateProgress(data);
        });
        
        socket.on('connect', function() {
            console.log('🔗 [WEBSOCKET] Connected to server');
        });
        
        socket.on('disconnect', function() {
            console.log('❌ [WEBSOCKET] Disconnected from server');
        });
    } else {
        console.log('⚠️ [STOCKS] Socket.IO not available, progress updates disabled');
    }
}

// Load stocks analysis data
async function loadStocksAnalysis(forceRefresh = false) {
    if (isRefreshing) {
        console.log('⏳ [STOCKS] Already refreshing, skipping request');
        return;
    }
    
    isRefreshing = true;
    showLoading(true);
    
    try {
        console.log('🔍 [STOCKS] Loading S&P 500 analysis...');
        
        // Build API URL
        const params = new URLSearchParams();
        if (forceRefresh) {
            params.append('refresh', '1');
        }
        params.append('limit', '6'); // 3 winners + 3 losers
        
        const url = `/api/sp500_analysis?${params.toString()}`;
        console.log('🌐 [STOCKS] API request:', url);
        
        const response = await fetch(url);
        const result = await response.json();
        
        console.log('📊 [STOCKS] API response:', result);
        
        if (result.status === 'success' && result.data) {
            displayStocksAnalysis(result.data);
            updateLastUpdated();
        } else {
            console.error('❌ [STOCKS] API error:', result.message || 'Unknown error');
            showError('Failed to load stocks analysis: ' + (result.message || 'Unknown error'));
        }
        
    } catch (error) {
        console.error('❌ [STOCKS] Fetch error:', error);
        showError('Failed to load stocks analysis: ' + error.message);
    } finally {
        isRefreshing = false;
        showLoading(false);
    }
}

// Display stocks analysis results
function displayStocksAnalysis(data) {
    console.log('📈 [STOCKS] Displaying analysis results:', data);
    
    // Update market overview
    updateMarketOverview(data);
    
    // Update winners and losers summary
    updateWinnersLosersSummary(data);
    
    // Update summary statistics
    updateSummaryStats(data);
    
    // Show results sections
    document.getElementById('summaryStats').style.display = 'block';
    document.getElementById('enhancedAnalysisResults').style.display = 'block';
    
    // Update legacy table if it exists
    updateLegacyTable(data);
}

// Update market overview section
function updateMarketOverview(data) {
    const enhancedAnalysis = data.enhanced_analysis || [];
    
    if (enhancedAnalysis.length > 0) {
        // Calculate market statistics
        const winners = enhancedAnalysis.filter(stock => stock.type === 'winner');
        const losers = enhancedAnalysis.filter(stock => stock.type === 'loser');
        
        // Update market overview display
        const marketGainers = document.getElementById('marketGainers');
        const marketLosers = document.getElementById('marketLosers');
        const marketVolume = document.getElementById('marketVolume');
        const marketVolatility = document.getElementById('marketVolatility');
        
        if (marketGainers) marketGainers.textContent = winners.length;
        if (marketLosers) marketLosers.textContent = losers.length;
        if (marketVolume) marketVolume.textContent = enhancedAnalysis.length;
        if (marketVolatility) marketVolatility.textContent = 'High';
    }
}

// Update winners and losers summary
function updateWinnersLosersSummary(data) {
    const enhancedAnalysis = data.enhanced_analysis || [];
    
    if (enhancedAnalysis.length === 0) {
        showError('No analysis data available');
        return;
    }
    
    // Separate winners and losers
    const winners = enhancedAnalysis.filter(stock => stock.type === 'winner');
    const losers = enhancedAnalysis.filter(stock => stock.type === 'loser');
    
    console.log('🏆 [STOCKS] Winners:', winners);
    console.log('📉 [STOCKS] Losers:', losers);
    
    // Update winners list
    updateWinnersList(winners);
    
    // Update losers list
    updateLosersList(losers);
}

// Update winners list display
function updateWinnersList(winners) {
    const winnersList = document.getElementById('winnersList');
    if (!winnersList) return;
    
    if (winners.length === 0) {
        winnersList.innerHTML = '<div class="text-center text-muted">No winners data available</div>';
        return;
    }
    
    let html = '';
    winners.forEach(stock => {
        const priceData = stock.price_data || {};
        const sentimentData = stock.sentiment_data || {};
        const changePercent = priceData.change_percent || '0%';
        const currentPrice = priceData.current_price || 'N/A';
        const sentimentScore = sentimentData.sentiment_score || 0;
        const confidence = sentimentData.confidence || 0;
        
        html += `
            <div class="card mb-2 border-success">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1 text-success">${stock.symbol}</h6>
                            <small class="text-muted">$${currentPrice}</small>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-success">${changePercent}</span>
                            <div class="mt-1">
                                <small class="text-muted">Sentiment: ${(sentimentScore * 100).toFixed(0)}%</small>
                            </div>
                        </div>
                    </div>
                    <div class="mt-2">
                        <small class="text-muted">Confidence: ${(confidence * 100).toFixed(0)}%</small>
                        <div class="progress mt-1" style="height: 6px;">
                            <div class="progress-bar bg-success" style="width: ${confidence * 100}%"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    winnersList.innerHTML = html;
}

// Update losers list display
function updateLosersList(losers) {
    const losersList = document.getElementById('losersList');
    if (!losersList) return;
    
    if (losers.length === 0) {
        losersList.innerHTML = '<div class="text-center text-muted">No losers data available</div>';
        return;
    }
    
    let html = '';
    losers.forEach(stock => {
        const priceData = stock.price_data || {};
        const sentimentData = stock.sentiment_data || {};
        const changePercent = priceData.change_percent || '0%';
        const currentPrice = priceData.current_price || 'N/A';
        const sentimentScore = sentimentData.sentiment_score || 0;
        const confidence = sentimentData.confidence || 0;
        
        html += `
            <div class="card mb-2 border-danger">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1 text-danger">${stock.symbol}</h6>
                            <small class="text-muted">$${currentPrice}</small>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-danger">${changePercent}</span>
                            <div class="mt-1">
                                <small class="text-muted">Sentiment: ${(sentimentScore * 100).toFixed(0)}%</small>
                            </div>
                        </div>
                    </div>
                    <div class="mt-2">
                        <small class="text-muted">Confidence: ${(confidence * 100).toFixed(0)}%</small>
                        <div class="progress mt-1" style="height: 6px;">
                            <div class="progress-bar bg-danger" style="width: ${confidence * 100}%"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    losersList.innerHTML = html;
}

// Update summary statistics
function updateSummaryStats(data) {
    const summaryStats = document.getElementById('summaryStats');
    if (!summaryStats) return;
    
    const enhancedAnalysis = data.enhanced_analysis || [];
    const errors = data.errors || [];
    const performance = data.performance || {};
    
    const totalAnalyzed = data.total_analyzed || 0;
    const opportunitiesFound = data.opportunities_found || 0;
    const errorsCount = data.errors_count || 0;
    const executionTime = performance.execution_time || 0;
    const successRate = performance.success_rate || '0%';
    
    const html = `
        <div class="row">
            <div class="col-md-3">
                <div class="text-center">
                    <h4 class="text-primary">${totalAnalyzed}</h4>
                    <small>Total Analyzed</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="text-center">
                    <h4 class="text-success">${opportunitiesFound}</h4>
                    <small>Opportunities Found</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="text-center">
                    <h4 class="text-danger">${errorsCount}</h4>
                    <small>Errors</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="text-center">
                    <h4 class="text-info">${executionTime}s</h4>
                    <small>Execution Time</small>
                </div>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-12">
                <div class="text-center">
                    <small class="text-muted">Success Rate: ${successRate}</small>
                </div>
            </div>
        </div>
    `;
    
    summaryStats.querySelector('.card-body').innerHTML = html;
}

// Update legacy table (if it exists)
function updateLegacyTable(data) {
    const tableBody = document.getElementById('stocksTableBody');
    if (!tableBody) return;
    
    const enhancedAnalysis = data.enhanced_analysis || [];
    
    if (enhancedAnalysis.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No analysis data available</td></tr>';
        return;
    }
    
    let html = '';
    enhancedAnalysis.forEach(stock => {
        const priceData = stock.price_data || {};
        const sentimentData = stock.sentiment_data || {};
        const signalData = stock.signal_data || {};
        
        const currentPrice = priceData.current_price || 'N/A';
        const sentimentScore = sentimentData.sentiment_score || 0;
        const confidence = sentimentData.confidence || 0;
        const action = signalData.action || 'HOLD';
        const signalStrength = signalData.confidence || 0;
        const newsCount = stock.news_count || 0;
        
        html += `
            <tr>
                <td><span class="badge ${stock.type === 'winner' ? 'bg-success' : 'bg-danger'}">${stock.type}</span></td>
                <td><strong>${stock.symbol}</strong></td>
                <td>$${currentPrice}</td>
                <td>${(sentimentScore * 100).toFixed(1)}%</td>
                <td>${(confidence * 100).toFixed(1)}%</td>
                <td><span class="badge bg-${action === 'BUY' ? 'success' : action === 'SELL' ? 'danger' : 'secondary'}">${action}</span></td>
                <td>${(signalStrength * 100).toFixed(1)}%</td>
                <td>${newsCount}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewStockDetails('${stock.symbol}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            </tr>
        `;
    });
    
    tableBody.innerHTML = html;
}

// Update progress bar
function updateProgress(data) {
    const progressContainer = document.getElementById('sp500-progress-container');
    const progressBar = document.getElementById('sp500-progress-bar');
    const progressText = document.getElementById('sp500-progress-text');
    
    if (!progressContainer || !progressBar || !progressText) return;
    
    if (data.status === 'completed') {
        progressContainer.style.display = 'none';
        return;
    }
    
    progressContainer.style.display = 'block';
    
    const current = data.current || 0;
    const total = data.total || 1;
    const percentage = Math.round((current / total) * 100);
    
    progressBar.style.width = `${percentage}%`;
    progressBar.setAttribute('aria-valuenow', current);
    progressBar.setAttribute('aria-valuemax', total);
    
    if (data.symbol && data.symbol !== 'CACHED') {
        progressText.textContent = `Analyzing ${data.symbol}... (${current}/${total})`;
    } else {
        progressText.textContent = `Progress: ${current}/${total} (${percentage}%)`;
    }
}

// Toggle auto-refresh
function toggleAutoRefresh() {
    const toggle = document.getElementById('autoRefreshToggle');
    if (!toggle) return;
    
    if (toggle.checked) {
        console.log('🔄 [STOCKS] Auto-refresh enabled');
        autoRefreshInterval = setInterval(() => {
            console.log('🔄 [STOCKS] Auto-refresh triggered');
            loadStocksAnalysis(false);
        }, 5 * 60 * 1000); // 5 minutes
    } else {
        console.log('⏸️ [STOCKS] Auto-refresh disabled');
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
    }
}

// Show/hide loading spinner
function showLoading(show) {
    const loadingSpinner = document.getElementById('loadingSpinner');
    if (loadingSpinner) {
        loadingSpinner.style.display = show ? 'block' : 'none';
    }
}

// Show error message
function showError(message) {
    console.error('❌ [STOCKS] Error:', message);
    
    // Create error alert
    const errorHtml = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="fas fa-exclamation-triangle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Insert at the top of the container
    const container = document.querySelector('.container');
    if (container) {
        container.insertAdjacentHTML('afterbegin', errorHtml);
    }
}

// Update last updated timestamp
function updateLastUpdated() {
    const lastUpdatedElement = document.getElementById('lastUpdated');
    if (lastUpdatedElement) {
        const now = new Date();
        lastUpdated = now;
        lastUpdatedElement.textContent = `Last updated: ${now.toLocaleTimeString()}`;
    }
}

// View stock details (placeholder function)
function viewStockDetails(symbol) {
    console.log('🔍 [STOCKS] Viewing details for:', symbol);
    // TODO: Implement detailed stock view
    alert(`Detailed view for ${symbol} - Feature coming soon!`);
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
});

console.log('✅ [STOCKS] stocks.js loaded successfully');
