/* S&P 500 Analysis JavaScript */

// Global variables
let sp500Data = [];

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners
    if (document.getElementById('refreshBtn')) {
        document.getElementById('refreshBtn').addEventListener('click', loadSP500Data);
    }
    
    // Don't auto-load data - let user click refresh button to avoid crashes
    // setTimeout(loadSP500Data, 1000);
});

// Load S&P 500 analysis data
async function loadSP500Data() {
    console.log('[DEBUG] Requesting S&P 500 data from API');
    console.log('[DEBUG] loadSP500Data called');
    showLoading('loadingSpinner');
    if (document.getElementById('refreshBtn')) {
        document.getElementById('refreshBtn').disabled = true;
    }
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
        
        console.log('[DEBUG] Making fetch request to /api/sp500_analysis');
        const response = await fetch('/api/sp500_analysis', {
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        console.log('[DEBUG] API response status:', response.status);
        const data = await response.json();
        
        if (response.ok) {
            console.log('[DEBUG] API request succeeded');
        } else {
            console.error('[DEBUG] API request failed with status:', response.status);
        }
        
        console.log('[DEBUG] API response data:', data);
        
        if (data.error) {
            showAlert(data.error, 'danger');
            console.log('[DEBUG] API error:', data.error);
            return;
        }
        
        // The API returns data.data.enhanced_analysis array
        sp500Data = data.data.enhanced_analysis || [];
        console.log('[DEBUG] Parsed sp500Data:', sp500Data);
        console.log('[DEBUG] Number of stocks in response:', sp500Data.length);
        
        // Display the data in the UI
        console.log('[DEBUG] Calling displaySP500Table with data');
        displaySP500Table(sp500Data);
        console.log('[DEBUG] Calling displayWinnersLosers with data');
        displayWinnersLosers(sp500Data);
        
        if (document.getElementById('lastUpdated')) {
            const timestamp = data.data.timestamp ? new Date(data.data.timestamp).toLocaleString() : 'Unknown';
            console.log('[DEBUG] Updating lastUpdated with timestamp:', timestamp);
            document.getElementById('lastUpdated').textContent = `Last updated: ${timestamp}`;
        }
        
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
        
        console.log('[DEBUG] Rendering UI components for stock data');
        
    } catch (err) {
        showAlert('Failed to load S&P 500 data', 'danger');
        console.error('[DEBUG] Exception in loadSP500Data:', err);
    } finally {
        if (document.getElementById('refreshBtn')) {
            document.getElementById('refreshBtn').disabled = false;
        }
        hideLoading('loadingSpinner');
    }
}

// Display S&P 500 data in table
function displaySP500Table(stocks) {
    console.log('[DEBUG] displaySP500Table called with', stocks.length, 'stocks');
    const tbody = document.getElementById('stocksTableBody');
    if (!tbody) {
        console.error('[DEBUG] stocksTableBody element not found');
        return;
    }
    
    console.log('[DEBUG] Clearing stocksTableBody');
    tbody.innerHTML = '';
    
    console.log('[DEBUG] Starting to populate stocks table');
    stocks.forEach((stock, index) => {
        console.log(`[DEBUG] Processing stock ${index + 1}/${stocks.length}: ${stock.symbol}`);
        const row = document.createElement('tr');
        const sentimentData = stock.sentiment_data || {};
        const priceData = stock.price_data || {};
        const signalData = stock.signal_data || {};
        const sentimentClass = getSentimentClass(sentimentData.sentiment_score || 0);
        const sentimentStrength = getSentimentStrength(sentimentData.sentiment_score || 0);
        const signalClass = getSignalClass(signalData.action || 'HOLD');
        
        row.innerHTML = `
            <td>${stock.type || 'Stock'}</td>
            <td><strong>${stock.symbol}</strong></td>
            <td>${formatCurrency(priceData.current_price || 0)}</td>
            <td class="${sentimentClass}">
                ${(sentimentData.sentiment_score || 0).toFixed(3)}
                ${sentimentStrength.badge}
            </td>
            <td>${((sentimentData.confidence || 0) * 100).toFixed(1)}%</td>
            <td><span class="badge ${signalClass}">${signalData.action || 'HOLD'}</span></td>
            <td>${(signalData.signal_strength || 0).toFixed(3)}</td>
            <td>${stock.news_count || 0}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="analyzeStock('${stock.symbol}')">
                    <i class="fas fa-chart-bar"></i> Analyze
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
    console.log('[DEBUG] Finished populating stocks table with', stocks.length, 'rows');
}

// Display winners and losers summary
function displayWinnersLosers(stocks) {
    console.log('[DEBUG] displayWinnersLosers called with:', stocks);
    const winnersList = document.getElementById('winnersList');
    const losersList = document.getElementById('losersList');
    const winnersSummary = document.getElementById('winnersLosersSummary');
    const enhancedResults = document.getElementById('enhancedAnalysisResults');
    
    if (!winnersList || !losersList) {
        console.error('[DEBUG] winnersList or losersList element not found');
        console.error('[DEBUG] winnersList exists:', !!winnersList);
        console.error('[DEBUG] losersList exists:', !!losersList);
        return;
    }
    
    // Sort stocks by type (winners vs losers) and then by sentiment score
    const winners = stocks.filter(stock => stock.type === 'winner').sort((a, b) => {
        const aScore = (a.sentiment_data?.sentiment_score || 0);
        const bScore = (b.sentiment_data?.sentiment_score || 0);
        return bScore - aScore;
    });
    const losers = stocks.filter(stock => stock.type === 'loser').sort((a, b) => {
        const aScore = (a.sentiment_data?.sentiment_score || 0);
        const bScore = (b.sentiment_data?.sentiment_score || 0);
        return aScore - bScore;
    });
    console.log('[DEBUG] Filtered winners:', winners.length, winners.map(w => w.symbol));
    console.log('[DEBUG] Filtered losers:', losers.length, losers.map(l => l.symbol));
    
    // Display winners
    winnersList.innerHTML = '';
    console.log('[DEBUG] Rendering winners to winnersList');
    winners.slice(0, 5).forEach(stock => {
        const priceData = stock.price_data || {};
        const sentimentData = stock.sentiment_data || {};
        const changePercent = priceData.change_percent || '0%';
        const isPositive = changePercent.includes('-') === false;
        const changeClass = isPositive ? 'text-success' : 'text-danger';
        const changeIcon = isPositive ? 'fa-arrow-up' : 'fa-arrow-down';
        winnersList.innerHTML += `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <div>
                    <strong>${stock.symbol}</strong>
                    <br><small class="text-muted">${formatCurrency(priceData.current_price || 0)}</small>
                </div>
                <div class="text-end">
                    <span class="${changeClass}">
                        <i class="fas ${changeIcon}"></i> ${changePercent}
                    </span>
                    <br><small class="text-muted">${(sentimentData.sentiment_score || 0).toFixed(3)} sentiment</small>
                </div>
            </div>
        `;
    });
    console.log('[DEBUG] Winners HTML content length:', winnersList.innerHTML.length);
    
    // Display losers
    losersList.innerHTML = '';
    console.log('[DEBUG] Rendering losers to losersList');
    losers.slice(0, 5).forEach(stock => {
        const priceData = stock.price_data || {};
        const sentimentData = stock.sentiment_data || {};
        const changePercent = priceData.change_percent || '0%';
        const isPositive = changePercent.includes('-') === false;
        const changeClass = isPositive ? 'text-success' : 'text-danger';
        const changeIcon = isPositive ? 'fa-arrow-up' : 'fa-arrow-down';
        losersList.innerHTML += `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <div>
                    <strong>${stock.symbol}</strong>
                    <br><small class="text-muted">${formatCurrency(priceData.current_price || 0)}</small>
                </div>
                <div class="text-end">
                    <span class="${changeClass}">
                        <i class="fas ${changeIcon}"></i> ${changePercent}
                    </span>
                    <br><small class="text-muted">${(sentimentData.sentiment_score || 0).toFixed(3)} sentiment</small>
                </div>
            </div>
        `;
    });
    console.log('[DEBUG] Losers HTML content length:', losersList.innerHTML.length);
    
    // Show the summary sections
    if (winnersSummary) {
        winnersSummary.style.display = 'block';
        console.log('[DEBUG] winnersSummary shown (display set to block)');
    } else {
        console.error('[DEBUG] winnersSummary element not found');
    }
    
    if (enhancedResults) {
        enhancedResults.style.display = 'block';
        console.log('[DEBUG] enhancedResults shown (display set to block)');
    } else {
        console.error('[DEBUG] enhancedResults element not found');
    }
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