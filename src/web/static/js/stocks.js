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
    showLoading('loadingSpinner');
    if (document.getElementById('refreshBtn')) {
        document.getElementById('refreshBtn').disabled = true;
    }
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
        
        const response = await fetch('/api/sp500_analysis', {
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        const data = await response.json();
        
        if (data.error) {
            showAlert(data.error, 'danger');
            return;
        }
        
        // The API returns data.data.enhanced_analysis array
        sp500Data = data.data.enhanced_analysis || [];
        displaySP500Table(sp500Data);
        displayWinnersLosers(sp500Data);
        
        if (document.getElementById('lastUpdated')) {
            document.getElementById('lastUpdated').textContent = 
                `Last updated: ${new Date(data.data.timestamp).toLocaleString()}`;
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
        
    } catch (error) {
        if (error.name === 'AbortError') {
            showAlert('S&P 500 analysis timed out. The analysis is taking longer than expected. Please try again later or contact support if the issue persists.', 'warning');
        } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
            showAlert('Network error loading S&P 500 data. Please check your connection and try again.', 'danger');
        } else {
            showAlert('Error loading S&P 500 data: ' + error.message, 'danger');
        }
    } finally {
        hideLoading('loadingSpinner');
        if (document.getElementById('refreshBtn')) {
            document.getElementById('refreshBtn').disabled = false;
        }
    }
}

// Display S&P 500 data in table
function displaySP500Table(stocks) {
    const tbody = document.getElementById('stocksTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    stocks.forEach(stock => {
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
}

// Display winners and losers summary
function displayWinnersLosers(stocks) {
    const winnersList = document.getElementById('winnersList');
    const losersList = document.getElementById('losersList');
    const winnersSummary = document.getElementById('winnersLosersSummary');
    const enhancedResults = document.getElementById('enhancedAnalysisResults');
    
    if (!winnersList || !losersList) return;
    
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
    
    // Display winners
    winnersList.innerHTML = '';
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
    
    // Display losers
    losersList.innerHTML = '';
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
    
    // Show the summary sections
    if (winnersSummary) {
        winnersSummary.style.display = 'block';
    }
    if (enhancedResults) {
        enhancedResults.style.display = 'block';
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