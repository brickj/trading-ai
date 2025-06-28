/* Opportunities Analysis JavaScript */

// Global variables
let currentMode = 'news';
let opportunitiesData = [];

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners
    document.getElementById('newsBtn').addEventListener('click', () => switchMode('news'));
    document.getElementById('watchlistBtn').addEventListener('click', () => switchMode('watchlist'));
    document.getElementById('allBtn').addEventListener('click', () => switchMode('all'));
    document.getElementById('refreshBtn').addEventListener('click', loadOpportunities);
    
    // Load initial data
    loadOpportunities();
});

// Switch between different opportunity modes
function switchMode(mode) {
    currentMode = mode;
    
    // Update button states
    document.querySelectorAll('.btn-group .btn').forEach(btn => {
        btn.classList.remove('btn-primary', 'active');
        btn.classList.add('btn-outline-primary');
    });
    
    const activeBtn = mode === 'news' ? 'newsBtn' : mode === 'watchlist' ? 'watchlistBtn' : 'allBtn';
    const btn = document.getElementById(activeBtn);
    btn.classList.remove('btn-outline-primary');
    btn.classList.add('btn-primary', 'active');
    
    // Update title
    const titles = {
        'news': 'News-Driven Opportunities',
        'watchlist': 'Watchlist Opportunities', 
        'all': 'All Trading Opportunities'
    };
    document.getElementById('opportunitiesTitle').textContent = titles[mode];
    
    // Load data for current mode
    loadOpportunities();
}

// Load opportunities data
async function loadOpportunities() {
    showLoading('loadingSpinner');
    document.getElementById('refreshBtn').disabled = true;
    
    try {
        const endpoints = {
            'news': '/api/news_opportunities',
            'watchlist': '/api/watchlist_opportunities',
            'all': '/api/all_opportunities'
        };
        
        const response = await fetch(endpoints[currentMode]);
        const data = await response.json();
        
        if (data.error) {
            showAlert(data.error, 'danger');
            return;
        }
        
        displayOpportunities(data);
        
        document.getElementById('lastUpdated').textContent = 
            `Last updated: ${new Date().toLocaleString()}`;
        
    } catch (error) {
        showAlert('Error loading opportunities: ' + error.message, 'danger');
    } finally {
        hideLoading('loadingSpinner');
        document.getElementById('refreshBtn').disabled = false;
    }
}

// Display opportunities in the container
function displayOpportunities(data) {
    const container = document.getElementById('opportunitiesContainer');
    
    let opportunities = [];
    if (currentMode === 'all') {
        opportunities = [...(data.news_driven || []), ...(data.watchlist || [])];
    } else {
        opportunities = data.opportunities || [];
    }
    
    if (opportunities.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-search fa-3x mb-3"></i>
                <h5>No opportunities found</h5>
                <p>Try refreshing or check back later for new opportunities.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = '';
    
    opportunities.forEach(opp => {
        const card = createOpportunityCard(opp);
        container.appendChild(card);
    });
}

// Create opportunity card
function createOpportunityCard(opp) {
    const card = document.createElement('div');
    card.className = 'card mb-3';
    
    const triggerBadge = opp.trigger === 'news_driven' ? 
        '<span class="badge bg-info">News-Driven</span>' : 
        '<span class="badge bg-warning">Watchlist</span>';
    
    const typeBadge = opp.type === 'crypto' ? 
        '<span class="badge bg-warning">Crypto</span>' : 
        '<span class="badge bg-primary">Stock</span>';
    
    const actionBadge = opp.signal_data.action === 'CALL' ? 
        '<span class="badge bg-success">CALL</span>' : 
        '<span class="badge bg-danger">PUT</span>';
    
    const sentimentClass = getSentimentClass(opp.sentiment_data.sentiment_score);
    
    card.innerHTML = `
        <div class="card-header d-flex justify-content-between align-items-center">
            <div>
                <h6 class="mb-0">
                    <strong>${opp.symbol}</strong>
                    ${typeBadge}
                    ${triggerBadge}
                    ${actionBadge}
                </h6>
            </div>
            <div>
                <button class="btn btn-sm btn-outline-success" onclick="executeOpportunity('${opp.symbol}')">
                    <i class="fas fa-play"></i> Execute
                </button>
            </div>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-3">
                    <h6>Price Info</h6>
                    <p><strong>Current:</strong> ${formatCurrency(opp.price_data.current_price)}</p>
                    <p><strong>Strike:</strong> ${formatCurrency(opp.trade_signal.strike_price)}</p>
                    <p><strong>Option Price:</strong> ${formatCurrency(opp.trade_signal.option_price)}</p>
                </div>
                <div class="col-md-3">
                    <h6>Sentiment</h6>
                    <p><strong>Score:</strong> <span class="${sentimentClass}">${opp.sentiment_data.sentiment_score.toFixed(3)}</span></p>
                    <p><strong>Confidence:</strong> ${(opp.sentiment_data.confidence * 100).toFixed(1)}%</p>
                    <p><strong>News Count:</strong> ${opp.news_count}</p>
                </div>
                <div class="col-md-3">
                    <h6>Trade Details</h6>
                    <p><strong>Position Size:</strong> ${opp.trade_signal.position_size} contracts</p>
                    <p><strong>Total Cost:</strong> ${formatCurrency(opp.trade_signal.option_price * opp.trade_signal.position_size)}</p>
                    <p><strong>Signal Strength:</strong> ${opp.signal_data.signal_strength.toFixed(3)}</p>
                </div>
                <div class="col-md-3">
                    <h6>Strategy</h6>
                    <p class="small">${opp.signal_data.reasoning}</p>
                    ${opp.articles ? `<p class="small text-muted">Based on ${opp.articles.length} recent articles</p>` : ''}
                </div>
            </div>
            
            ${opp.articles ? `
            <div class="mt-3">
                <h6>Recent News Headlines:</h6>
                <ul class="small">
                    ${opp.articles.slice(0, 3).map(article => 
                        `<li>${article.headline || 'No headline'}</li>`
                    ).join('')}
                </ul>
            </div>
            ` : ''}
        </div>
    `;
    
    return card;
}

// Execute opportunity trade
async function executeOpportunity(symbol) {
    try {
        const response = await fetch('/api/execute_trade', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ symbol: symbol })
        });
        
        const data = await response.json();
        
        if (data.execution_result.status === 'executed') {
            showAlert(`Trade executed for ${symbol}! Remaining capital: ${formatCurrency(data.execution_result.remaining_capital)}`, 'success');
        } else {
            showAlert(data.execution_result.message, 'warning');
        }
        
    } catch (error) {
        showAlert('Error executing trade: ' + error.message, 'danger');
    }
}

// Analyze watchlist opportunities (for the button click)
function analyzeWatchlistOpportunities() {
    switchMode('watchlist');
}

// Auto-refresh every 5 minutes
setInterval(() => {
    if (document.visibilityState === 'visible') {
        loadOpportunities();
    }
}, 5 * 60 * 1000); 