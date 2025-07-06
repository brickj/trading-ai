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

// Utility: log fetch requests and responses
async function loggedFetch(url, options = {}) {
    console.log('🌐 [FETCH] Request:', { url, ...options });
    try {
        const response = await fetch(url, options);
        const cloned = response.clone();
        let json;
        try {
            json = await cloned.json();
            console.log('🌐 [FETCH] Response:', { 
                url, 
                status: response.status, 
                statusText: response.statusText,
                headers: Object.fromEntries(response.headers.entries()),
                dataStructure: {
                    hasOpportunities: !!json.opportunities,
                    opportunitiesLength: json.opportunities?.length || 0,
                    hasErrors: !!json.errors,
                    errorsLength: json.errors?.length || 0,
                    hasData: !!json.data,
                    dataKeys: json.data ? Object.keys(json.data) : [],
                    topLevelKeys: Object.keys(json),
                    isArray: Array.isArray(json),
                    type: typeof json
                },
                fullResponse: json
            });
        } catch (e) {
            console.log('🌐 [FETCH] Response (non-JSON):', { 
                url, 
                status: response.status, 
                statusText: response.statusText,
                error: e.message 
            });
            json = null;
        }
        return response;
    } catch (error) {
        console.error('❌ [FETCH] Network error:', { url, ...options, error: error.message, stack: error.stack });
        throw error;
    }
}

// Load opportunities data
async function loadOpportunities() {
    console.log('🚀 [LOAD] Starting loadOpportunities for mode:', currentMode);
    showLoading('loadingSpinner');
    document.getElementById('refreshBtn').disabled = true;
    
    try {
        const endpoints = {
            'news': '/api/news_opportunities',
            'watchlist': '/api/watchlist_opportunities',
            'all': '/api/all_opportunities'
        };
        
        const endpoint = endpoints[currentMode];
        console.log('🌐 [LOAD] Fetching from endpoint:', endpoint);
        
        const response = await loggedFetch(endpoint);
        const data = await response.json();
        
        console.log('📊 [LOAD] Raw API response data:', {
            mode: currentMode,
            endpoint: endpoint,
            responseStatus: response.status,
            dataType: typeof data,
            isArray: Array.isArray(data),
            hasError: !!data.error,
            errorMessage: data.error,
            dataKeys: Object.keys(data),
            dataStructure: JSON.stringify(data, null, 2)
        });
        
        if (data.error) {
            console.error('❌ [LOAD] API returned error:', data.error);
            showAlert(data.error, 'danger');
            return;
        }
        
        console.log('✅ [LOAD] API call successful, calling displayOpportunities');
        displayOpportunities(data);
        
        document.getElementById('lastUpdated').textContent = 
            `Last updated: ${new Date().toLocaleString()}`;
        
    } catch (error) {
        console.error('❌ [LOAD] Error in loadOpportunities:', {
            error: error.message,
            stack: error.stack,
            mode: currentMode
        });
        showAlert('Error loading opportunities: ' + error.message, 'danger');
    } finally {
        hideLoading('loadingSpinner');
        document.getElementById('refreshBtn').disabled = false;
        console.log('🏁 [LOAD] loadOpportunities completed');
    }
}

// Display opportunities in the container
function displayOpportunities(data) {
    console.log('🎯 [DISPLAY] Starting displayOpportunities');
    console.log('🎯 [DISPLAY] Input data:', {
        dataType: typeof data,
        isArray: Array.isArray(data),
        keys: Object.keys(data),
        fullData: data
    });
    
    const container = document.getElementById('opportunitiesContainer');
    if (!container) {
        console.error('❌ [DISPLAY] Container not found: opportunitiesContainer');
        return;
    }
    
    console.log('🔍 [DISPLAY] Current mode:', currentMode);
    
    let opportunities = [];
    if (currentMode === 'all') {
        opportunities = [...(data.news_driven || []), ...(data.watchlist || [])];
        console.log('🔍 [DISPLAY] All mode - News-driven opportunities:', data.news_driven || []);
        console.log('🔍 [DISPLAY] All mode - Watchlist opportunities:', data.watchlist || []);
    } else {
        opportunities = data.opportunities || [];
        console.log('🔍 [DISPLAY] Direct mode - opportunities array:', data.opportunities || []);
    }
    
    console.log('🔍 [DISPLAY] Total opportunities to display:', opportunities.length);
    console.log('🔍 [DISPLAY] Opportunities array:', opportunities);
    
    if (opportunities.length === 0) {
        console.log('⚠️ [DISPLAY] No opportunities found, showing empty state');
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-search fa-3x mb-3"></i>
                <h5>No opportunities found</h5>
                <p>Try refreshing or check back later for new opportunities.</p>
            </div>
        `;
        return;
    }
    
    console.log('🔍 [DISPLAY] Creating opportunity cards for:', opportunities.length, 'opportunities');
    container.innerHTML = '';
    
    opportunities.forEach((opp, index) => {
        console.log(`🔍 [DISPLAY] Creating card ${index + 1} for:`, {
            symbol: opp.symbol,
            type: opp.type,
            trigger: opp.trigger,
            fullOpportunity: opp
        });
        try {
            const card = createOpportunityCard(opp);
            container.appendChild(card);
            console.log(`✅ [DISPLAY] Card ${index + 1} added to container successfully`);
        } catch (error) {
            console.error(`❌ [DISPLAY] Error creating card for ${opp.symbol}:`, {
                error: error.message,
                stack: error.stack,
                opportunity: opp
            });
        }
    });
    
    console.log('✅ [DISPLAY] displayOpportunities completed');
}

// Create opportunity card
function createOpportunityCard(opp) {
    console.log('🔍 [CARD] Creating card for opportunity:', {
        symbol: opp.symbol,
        type: opp.type,
        trigger: opp.trigger,
        fullOpportunity: opp
    });
    
    const card = document.createElement('div');
    card.className = 'card mb-3';
    
    // Safely access nested properties with fallbacks
    const symbol = opp.symbol || 'UNKNOWN';
    const trigger = opp.trigger || 'unknown';
    const type = opp.type || 'stock';
    const action = opp.signal_data?.action || 'HOLD';
    const sentimentScore = opp.sentiment_data?.sentiment_score || 0;
    const confidence = opp.sentiment_data?.confidence || 0;
    const newsCount = opp.news_count || 0;
    const currentPrice = opp.price_data?.current_price || 0;
    const strikePrice = opp.trade_signal?.strike_price || 0;
    const optionPrice = opp.trade_signal?.option_price || 0;
    const positionSize = opp.trade_signal?.position_size || 1;
    const signalStrength = opp.signal_data?.signal_strength || 0;
    const reasoning = opp.signal_data?.reasoning || 'No reasoning provided';
    
    console.log('🔍 [CARD] Extracted values:', {
        symbol, trigger, type, action, sentimentScore, confidence,
        newsCount, currentPrice, strikePrice, optionPrice, positionSize, signalStrength,
        reasoning: reasoning.substring(0, 100) + '...'
    });
    
    const triggerBadge = trigger === 'news_driven' ? 
        '<span class="badge bg-info">News-Driven</span>' : 
        '<span class="badge bg-warning">Watchlist</span>';
    
    const typeBadge = type === 'crypto' ? 
        '<span class="badge bg-warning">Crypto</span>' : 
        '<span class="badge bg-primary">Stock</span>';
    
    const actionBadge = action === 'CALL' ? 
        '<span class="badge bg-success">CALL</span>' : 
        '<span class="badge bg-danger">PUT</span>';
    
    const sentimentClass = getSentimentClass(sentimentScore);
    
    console.log('🔍 [CARD] Generated badges:', {
        triggerBadge: triggerBadge.includes('News-Driven') ? 'News-Driven' : 'Watchlist',
        typeBadge: typeBadge.includes('Crypto') ? 'Crypto' : 'Stock',
        actionBadge: actionBadge.includes('CALL') ? 'CALL' : 'PUT',
        sentimentClass
    });
    
    card.innerHTML = `
        <div class="card-header d-flex justify-content-between align-items-center">
            <div>
                <h6 class="mb-0">
                    <strong>${symbol}</strong>
                    ${typeBadge}
                    ${triggerBadge}
                    ${actionBadge}
                </h6>
            </div>
            <div>
                <button class="btn btn-sm btn-outline-success" onclick="executeOpportunity('${symbol}')">
                    <i class="fas fa-play"></i> Execute
                </button>
            </div>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-3">
                    <h6>Price Info</h6>
                    <p><strong>Current:</strong> ${formatCurrency(currentPrice)}</p>
                    <p><strong>Strike:</strong> ${formatCurrency(strikePrice)}</p>
                    <p><strong>Option Price:</strong> ${formatCurrency(optionPrice)}</p>
                </div>
                <div class="col-md-3">
                    <h6>Sentiment</h6>
                    <p><strong>Score:</strong> <span class="${sentimentClass}">${sentimentScore.toFixed(3)}</span></p>
                    <p><strong>Confidence:</strong> ${(confidence * 100).toFixed(1)}%</p>
                    <p><strong>News Count:</strong> ${newsCount}</p>
                </div>
                <div class="col-md-3">
                    <h6>Trade Details</h6>
                    <p><strong>Position Size:</strong> ${positionSize} contracts</p>
                    <p><strong>Total Cost:</strong> ${formatCurrency(optionPrice * positionSize)}</p>
                    <p><strong>Signal Strength:</strong> ${signalStrength.toFixed(3)}</p>
                </div>
                <div class="col-md-3">
                    <h6>Strategy</h6>
                    <p class="small">${reasoning}</p>
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
    
    console.log('✅ [CARD] Card created successfully for:', symbol);
    return card;
}

// Execute opportunity trade
async function executeOpportunity(symbol) {
    try {
        const response = await loggedFetch('/api/execute_trade', {
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