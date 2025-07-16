/* Opportunities Analysis JavaScript */

// Global variables
let currentMode = 'watchlist'; // Changed default to watchlist
let opportunitiesData = [];
let isRefreshing = false;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners
    document.getElementById('newsBtn').addEventListener('click', () => switchMode('news'));
    document.getElementById('watchlistBtn').addEventListener('click', () => switchMode('watchlist'));
    document.getElementById('refreshBtn').addEventListener('click', () => {
        // Context-aware refresh based on current mode
        console.log('🔄 [REFRESH] Refresh button clicked for mode:', currentMode);
        loadOpportunities(true); // Force refresh for current mode
    });
    
    // Set initial UI state for watchlist mode
    document.querySelectorAll('.btn-group .btn').forEach(btn => {
        btn.classList.remove('btn-primary', 'active');
        btn.classList.add('btn-outline-primary');
    });
    
    // Set watchlist button as active
    const watchlistBtn = document.getElementById('watchlistBtn');
    watchlistBtn.classList.remove('btn-outline-primary');
    watchlistBtn.classList.add('btn-primary', 'active');
    
    // Set initial title
    document.getElementById('opportunitiesTitle').textContent = 'Watchlist Opportunities';
    
    // Load initial data (from cache) - will load watchlist data
    loadOpportunities(false);
    
    // Load watchlist configuration
    loadWatchlistConfig();
});

// Switch between different opportunity modes
function switchMode(mode) {
    currentMode = mode;
    
    // Update button states
    document.querySelectorAll('.btn-group .btn').forEach(btn => {
        btn.classList.remove('btn-primary', 'active');
        btn.classList.add('btn-outline-primary');
    });
    
    const activeBtn = mode === 'news' ? 'newsBtn' : 'watchlistBtn';
    const btn = document.getElementById(activeBtn);
    btn.classList.remove('btn-outline-primary');
    btn.classList.add('btn-primary', 'active');
    
    // Update title
    const titles = {
        'news': 'News-Driven Opportunities',
        'watchlist': 'Watchlist Opportunities'
    };
    document.getElementById('opportunitiesTitle').textContent = titles[mode];
    
    // Load data for current mode (use cached data)
    loadOpportunities(false);
}

// Utility: log fetch requests and responses
async function loggedFetch(url, options = {}) {
    if (window.debugPanel) window.debugPanel.setRequest(url);
    console.log('\ud83c\udf10 [FETCH] Request:', { url, ...options });
    try {
        const response = await fetch(url, options);
        const cloned = response.clone();
        let json;
        try {
            json = await cloned.json();
            if (window.debugPanel) window.debugPanel.setResponse(json);
            console.log('\ud83c\udf10 [FETCH] Response:', { 
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
            if (window.debugPanel) window.debugPanel.setError('Non-JSON response: ' + e.message);
            console.log('\ud83c\udf10 [FETCH] Response (non-JSON):', { 
                url, 
                status: response.status, 
                statusText: response.statusText,
                error: e.message 
            });
            json = null;
        }
        return response;
    } catch (error) {
        if (window.debugPanel) window.debugPanel.setError(error.message);
        console.error('\u274c [FETCH] Network error:', { url, ...options, error: error.message, stack: error.stack });
        throw error;
    }
}

// Load opportunities data
async function loadOpportunities(forceRefresh = false) {
    console.log('🚀 [LOAD] Starting loadOpportunities for mode:', currentMode, 'forceRefresh:', forceRefresh);
    showLoading('loadingSpinner');
    document.getElementById('refreshBtn').disabled = true;
    
    // Update button text if refreshing
    const refreshBtn = document.getElementById('refreshBtn');
    const originalText = refreshBtn.innerHTML;
    if (forceRefresh) {
        isRefreshing = true;
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
    }
    
    try {
        const endpoints = {
            'news': '/api/news_opportunities',
            'watchlist': '/api/watchlist_opportunities'
        };
        
        let endpoint = endpoints[currentMode];
        
        // Add refresh parameter if force refresh is requested
        if (forceRefresh) {
            endpoint += '?refresh=1';
            console.log('🔄 [LOAD] Force refresh requested');
        }
        
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
        if (window.debugPanel) window.debugPanel.setError(error.message);
        console.error('❌ [LOAD] Error in loadOpportunities:', {
            error: error.message,
            stack: error.stack,
            mode: currentMode
        });
        showAlert('Error loading opportunities: ' + error.message, 'danger');
    } finally {
        hideLoading('loadingSpinner');
        
        // Reset refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        refreshBtn.disabled = false;
        if (isRefreshing) {
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
            isRefreshing = false;
        }
        
        console.log('🏁 [LOAD] loadOpportunities completed');
    }
}

// Display opportunities in the container
function displayOpportunities(data) {
    // EXTREME LOGGING FOR DIAGNOSIS
    const logToBackend = (level, message, extra) => {
        fetch('/api/frontend_logs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                level,
                message,
                data: { mode: currentMode, timestamp: new Date().toISOString(), ...extra }
            })
        });
    };
    
    console.log('[DIAG] [DISPLAY] Starting displayOpportunities', { data });
    logToBackend('info', '[DIAG] [DISPLAY] Starting displayOpportunities', { data });
    
    const container = document.getElementById('opportunitiesContainer');
    if (!container) {
        console.error('[DIAG] [DISPLAY] Container not found: opportunitiesContainer');
        logToBackend('error', '[DIAG] [DISPLAY] Container not found: opportunitiesContainer', {});
        return;
    }
    
    console.log('[DIAG] [DISPLAY] Current mode:', currentMode);
    logToBackend('info', '[DIAG] [DISPLAY] Current mode', { currentMode });
    
    // Extract opportunities array - handle both direct and nested data structures
    const responseData = data.data || data;
    console.log('[DIAG] [DISPLAY] Raw responseData:', responseData);
    logToBackend('info', '[DIAG] [DISPLAY] Raw responseData', { responseData });
    
    let opportunities = [];
    if (currentMode === 'news') {
        // Try multiple possible data structures for news opportunities
        opportunities = responseData.opportunities || responseData.news_driven || data.opportunities || [];
        console.log('[DIAG] [DISPLAY] NEWS mode - News opportunities:', opportunities);
        logToBackend('info', '[DIAG] [DISPLAY] NEWS mode - News opportunities', { opportunities });
    } else if (currentMode === 'watchlist') {
        // Try multiple possible data structures for watchlist opportunities
        opportunities = responseData.opportunities || responseData.watchlist || data.opportunities || [];
        console.log('[DIAG] [DISPLAY] WATCHLIST mode - Watchlist opportunities:', opportunities);
        logToBackend('info', '[DIAG] [DISPLAY] WATCHLIST mode - Watchlist opportunities', { opportunities });
    } else {
        opportunities = responseData.opportunities || data.opportunities || [];
        console.log('[DIAG] [DISPLAY] FALLBACK mode - Opportunities:', opportunities);
        logToBackend('info', '[DIAG] [DISPLAY] FALLBACK mode - Opportunities', { opportunities });
    }
    
    console.log('[DIAG] [DISPLAY] Opportunities array length:', opportunities.length);
    logToBackend('info', '[DIAG] [DISPLAY] Opportunities array length', { length: opportunities.length });
    
    if (opportunities.length === 0) {
        container.innerHTML = `<div class="text-center text-muted py-4"><i class="fas fa-search fa-3x mb-3"></i><h5>No trading opportunities found</h5><p>Current market conditions don't show clear trading signals.</p><p class="small">Try switching between News-Driven and Watchlist modes, or check back later.</p><div class="mt-3"><button class="btn btn-outline-primary" onclick="loadOpportunities()"><i class="fas fa-sync-alt"></i> Refresh Analysis</button></div></div>`;
        console.warn('[DIAG] [DISPLAY] No opportunities found - empty state');
        logToBackend('warn', '[DIAG] [DISPLAY] No opportunities found - empty state', {});
        return;
    }
    
    // Log each opportunity in detail
    opportunities.forEach((opp, idx) => {
        console.log(`[DIAG] [DISPLAY] Opportunity ${idx + 1}:`, opp);
        logToBackend('info', `[DIAG] [DISPLAY] Opportunity ${idx + 1}`, { opp });
    });
    
    // Continue with normal rendering...
    // Log to backend the number of opportunities found
    fetch('/api/frontend_logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            level: 'info',
            message: '[FRONTEND] Opportunities array length',
            data: { mode: currentMode, length: opportunities.length, timestamp: new Date().toISOString() }
        })
    });

    if (opportunities.length === 0) {
        fetch('/api/frontend_logs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                level: 'warn',
                message: '[FRONTEND] No opportunities found - empty state',
                data: { mode: currentMode, timestamp: new Date().toISOString() }
            })
        });
    } else {
        fetch('/api/frontend_logs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                level: 'info',
                message: '[FRONTEND] Opportunities found - page populated',
                data: { mode: currentMode, count: opportunities.length, timestamp: new Date().toISOString() }
            })
        });
    }

    console.log('🔍 [DISPLAY] Final opportunities array:', opportunities);
    console.log('🔍 [DISPLAY] Opportunities array length:', opportunities.length);
    
    // Filter out opportunities with no meaningful data (less strict filtering)
    const meaningfulOpportunities = opportunities.filter(opp => {
        // Check if opportunity has basic required fields
        const hasSymbol = opp.symbol && opp.symbol.trim() !== '';
        const hasPrice = opp.price_data?.current_price > 0;
        const hasSentiment = opp.sentiment_data?.confidence > 0;
        const hasSignal = opp.signal_data?.action && opp.signal_data.action !== 'HOLD';
        const hasNews = opp.news_count > 0;
        const hasTradeSignal = opp.trade_signal?.action;
        
        // More lenient filtering - include if it has symbol and at least one other meaningful field
        const isMeaningful = hasSymbol && (hasPrice || hasSentiment || hasSignal || hasNews || hasTradeSignal);
        
        console.log(`🔍 [FILTER] Filtering ${opp.symbol}:`, {
            hasSymbol,
            hasPrice,
            hasSentiment,
            hasSignal,
            hasNews,
            hasTradeSignal,
            isMeaningful,
            priceValue: opp.price_data?.current_price,
            sentimentConfidence: opp.sentiment_data?.confidence,
            signalAction: opp.signal_data?.action,
            newsCount: opp.news_count,
            tradeSignalAction: opp.trade_signal?.action
        });
        
        return isMeaningful;
    });
    
    console.log('🔍 [DISPLAY] Filtered opportunities:', {
        total: opportunities.length,
        meaningful: meaningfulOpportunities.length,
        filtered: opportunities.length - meaningfulOpportunities.length
    });
    
    if (meaningfulOpportunities.length === 0) {
        console.log('⚠️ [DISPLAY] No meaningful opportunities found, showing empty state');
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-search fa-3x mb-3"></i>
                <h5>No trading opportunities found</h5>
                <p>Current market conditions don't show clear trading signals.</p>
                <p class="small">Try switching between News-Driven and Watchlist modes, or check back later.</p>
                <div class="mt-3">
                    <button class="btn btn-outline-primary" onclick="loadOpportunities()">
                        <i class="fas fa-sync-alt"></i> Refresh Analysis
                    </button>
                </div>
            </div>
        `;
        return;
    }
    
    console.log('✅ [DISPLAY] Found meaningful opportunities, creating cards...');
    
    // Clear container and add opportunities
    container.innerHTML = '';
    meaningfulOpportunities.forEach((opp, index) => {
        console.log(`🔍 [DISPLAY] Creating card ${index + 1} for:`, {
            symbol: opp.symbol,
            type: opp.type,
            action: opp.signal_data?.action
        });
        
        const card = createOpportunityCard(opp);
        if (card) {
            container.appendChild(card);
            console.log(`✅ [DISPLAY] Card ${index + 1} added to container successfully`);
        } else {
            console.error(`❌ [DISPLAY] Failed to create card ${index + 1} for ${opp.symbol}`);
        }
    });
    
    console.log('✅ [DISPLAY] displayOpportunities completed successfully');
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
    card.className = 'card mb-3 opportunity-card';
    
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
    
    const typeBadge = '<span class="badge bg-primary">Stock</span>';
    
    const actionBadge = action === 'CALL' ? 
        '<span class="badge bg-success">CALL</span>' : 
        action === 'PUT' ? '<span class="badge bg-danger">PUT</span>' :
        action === 'SELL' ? '<span class="badge bg-danger">SELL</span>' :
        '<span class="badge bg-secondary">HOLD</span>';
    
    const sentimentClass = getSentimentClass(sentimentScore);
    
    console.log('🔍 [CARD] Generated badges:', {
        triggerBadge: triggerBadge.includes('News-Driven') ? 'News-Driven' : 'Watchlist',
        typeBadge: 'Stock',
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
                    <p><strong>Current:</strong> ${currentPrice > 0 ? formatCurrency(currentPrice) : '<span class="text-muted">N/A</span>'}</p>
                    <p><strong>Strike:</strong> ${strikePrice > 0 ? formatCurrency(strikePrice) : '<span class="text-muted">N/A</span>'}</p>
                    <p><strong>Option Price:</strong> ${optionPrice > 0 ? formatCurrency(optionPrice) : '<span class="text-muted">N/A</span>'}</p>
                </div>
                <div class="col-md-3">
                    <h6>Sentiment</h6>
                    <p><strong>Score:</strong> <span class="${sentimentClass}">${sentimentScore.toFixed(3)}</span></p>
                    <p><strong>Confidence:</strong> ${confidence > 0 ? (confidence * 100).toFixed(1) + '%' : '<span class="text-muted">N/A</span>'}</p>
                    <p><strong>News Count:</strong> ${newsCount}</p>
                </div>
                <div class="col-md-3">
                    <h6>Trade Details</h6>
                    <p><strong>Position Size:</strong> ${positionSize} contracts</p>
                    <p><strong>Total Cost:</strong> ${optionPrice > 0 ? formatCurrency(optionPrice * positionSize) : '<span class="text-muted">N/A</span>'}</p>
                    <p><strong>Signal Strength:</strong> ${signalStrength > 0 ? signalStrength.toFixed(3) : '<span class="text-muted">N/A</span>'}</p>
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

// Load watchlist configuration from API
async function loadWatchlistConfig() {
    try {
        console.log('🔧 [CONFIG] Loading watchlist configuration...');
        const response = await fetch('/api/watchlist/config');
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to load watchlist configuration');
        }
        
        const configContainer = document.getElementById('watchlistConfig');
        if (!configContainer) {
            console.error('❌ [CONFIG] Watchlist config container not found');
            return;
        }
        
        // Format stocks for display (no crypto)
        const stocks = data.data.stocks || [];
        const stockSymbols = stocks.map(item => item.symbol).join(', ');
        
        configContainer.innerHTML = `
            <p><small><strong>Watchlist Stocks:</strong> ${stockSymbols || 'None configured'}</small></p>
            <p><small><strong>Total Symbols:</strong> ${stocks.length}</small></p>
        `;
        
        console.log('✅ [CONFIG] Watchlist configuration loaded successfully:', {
            stocks: stocks.length,
            total: stocks.length
        });
        
    } catch (error) {
        console.error('❌ [CONFIG] Error loading watchlist configuration:', error);
        const configContainer = document.getElementById('watchlistConfig');
        if (configContainer) {
            configContainer.innerHTML = `
                <div class="alert alert-warning">
                    <small><i class="fas fa-exclamation-triangle"></i> Failed to load watchlist configuration</small>
                </div>
            `;
        }
    }
}

// Utility functions
function formatCurrency(amount) {
    if (amount === null || amount === undefined || isNaN(amount)) {
        return '$0.00';
    }
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

function getSentimentClass(score) {
    if (score >= 0.6) return 'text-success';
    if (score >= 0.3) return 'text-warning';
    if (score >= -0.3) return 'text-muted';
    if (score >= -0.6) return 'text-warning';
    return 'text-danger';
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top of the page
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

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