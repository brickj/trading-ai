/* Opportunities Analysis JavaScript */

// Global variables
let currentMode = 'watchlist'; // Changed default to watchlist
let opportunitiesData = [];
let isRefreshing = false;
let isRequestInProgress = false; // Add debounce flag
let lastRequestTime = 0; // Track last request time

// Debounce function to prevent rapid successive calls
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Debounced version of loadOpportunities
const debouncedLoadOpportunities = debounce((forceRefresh) => {
    loadOpportunities(forceRefresh);
}, 500); // 500ms debounce

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners
    document.getElementById('newsBtn').addEventListener('click', () => switchMode('news'));
    document.getElementById('watchlistBtn').addEventListener('click', () => switchMode('watchlist'));
    document.getElementById('refreshBtn').addEventListener('click', () => {
        // Context-aware refresh based on current mode
        console.log('🔄 [REFRESH] Refresh button clicked for mode:', currentMode);
        debouncedLoadOpportunities(true); // Use debounced version with force refresh
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
    debouncedLoadOpportunities(false); // Use debounced version
    
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
    debouncedLoadOpportunities(false); // Use debounced version
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
    // Prevent multiple simultaneous requests
    if (isRequestInProgress) {
        console.log('⚠️ [LOAD] Request already in progress, skipping...');
        return;
    }
    
    // Check if we're making requests too frequently
    const now = Date.now();
    if (now - lastRequestTime < 1000) { // Minimum 1 second between requests
        console.log('⚠️ [LOAD] Request too frequent, skipping...');
        return;
    }
    
    isRequestInProgress = true;
    lastRequestTime = now;
    
    console.log('🚀 [LOAD] Starting loadOpportunities for mode:', currentMode, 'forceRefresh:', forceRefresh);
    
    // Clear any existing error messages
    clearAlerts();
    
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
        
        // Add timeout and retry logic
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
        
        try {
            const response = await loggedFetch(endpoint, {
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            
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
                
        } catch (fetchError) {
            clearTimeout(timeoutId);
            
            // Check if it's an abort error (timeout)
            if (fetchError.name === 'AbortError') {
                console.warn('⚠️ [LOAD] Request timed out, retrying once...');
                // Retry once with a shorter timeout
                const retryController = new AbortController();
                const retryTimeoutId = setTimeout(() => retryController.abort(), 15000);
                
                try {
                    const retryResponse = await loggedFetch(endpoint, {
                        signal: retryController.signal
                    });
                    clearTimeout(retryTimeoutId);
                    
                    const retryData = await retryResponse.json();
                    
                    if (retryData.error) {
                        console.error('❌ [LOAD] Retry API returned error:', retryData.error);
                        showAlert(retryData.error, 'danger');
                        return;
                    }
                    
                    console.log('✅ [LOAD] Retry successful, calling displayOpportunities');
                    displayOpportunities(retryData);
                    
                    document.getElementById('lastUpdated').textContent = 
                        `Last updated: ${new Date().toLocaleString()}`;
                        
                } catch (retryError) {
                    clearTimeout(retryTimeoutId);
                    throw retryError;
                }
            } else {
                throw fetchError;
            }
        }
        
    } catch (error) {
        if (window.debugPanel) window.debugPanel.setError(error.message);
        console.error('❌ [LOAD] Error in loadOpportunities:', {
            error: error.message,
            stack: error.stack,
            mode: currentMode,
            name: error.name
        });
        
        // More specific error messages
        let errorMessage = 'Error loading opportunities';
        if (error.name === 'AbortError') {
            errorMessage = 'Request timed out. Please try again.';
        } else if (error.message.includes('Failed to fetch')) {
            errorMessage = 'Network error. Please check your connection and try again.';
        } else if (error.message.includes('404')) {
            errorMessage = 'Service temporarily unavailable. Please try again later.';
        } else if (error.message.includes('500')) {
            errorMessage = 'Server error. Please try again later.';
        } else {
            errorMessage = 'Error loading opportunities: ' + error.message;
        }
        
        showAlert(errorMessage, 'danger');
    } finally {
        hideLoading('loadingSpinner');
        
        // Reset refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        refreshBtn.disabled = false;
        if (isRefreshing) {
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
            isRefreshing = false;
        }
        
        // Reset request in progress flag
        isRequestInProgress = false;
        
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
    console.log('🔍 [ANALYZE] analyzeWatchlistOpportunities called');
    
    // Switch to watchlist mode first
    switchMode('watchlist');
    
    // Then trigger a refresh to run the analysis
    debouncedLoadOpportunities(true); // Use debounced version with force refresh
}

// Socket.IO event handlers for real-time progress updates
if (typeof io !== 'undefined') {
    const socket = io();
    
    // Handle watchlist progress updates
    socket.on('watchlist_progress', function(data) {
        console.log('📡 [SOCKET] Watchlist progress:', data);
        
        const { symbol, completed, total, status } = data;
        
        // Update loading message with progress
        const loadingSpinner = document.getElementById('loadingSpinner');
        if (loadingSpinner && status === 'processing') {
            const progressText = loadingSpinner.querySelector('p');
            if (progressText) {
                progressText.textContent = `Analyzing ${symbol}... (${completed}/${total})`;
            }
        }
        
        // Show completion message
        if (status === 'completed') {
            const progressText = loadingSpinner?.querySelector('p');
            if (progressText) {
                progressText.textContent = `Analysis completed! Found ${data.opportunities_found || 0} opportunities.`;
            }
        }
    });
    
    // Handle general progress updates
    socket.on('progress', function(data) {
        console.log('📡 [SOCKET] General progress:', data);
        
        const { current, total, symbol, status } = data;
        
        // Update loading message
        const loadingSpinner = document.getElementById('loadingSpinner');
        if (loadingSpinner) {
            const progressText = loadingSpinner.querySelector('p');
            if (progressText) {
                if (status === 'processing') {
                    progressText.textContent = `Processing ${symbol}... (${current}/${total})`;
                } else if (status === 'completed') {
                    progressText.textContent = 'Analysis completed!';
                }
            }
        }
    });
    
    // Handle errors
    socket.on('error', function(data) {
        console.error('📡 [SOCKET] Error:', data);
        showAlert('Analysis error: ' + (data.message || 'Unknown error'), 'danger');
    });
}

// Auto-refresh every 5 minutes
setInterval(() => {
    if (document.visibilityState === 'visible') {
        console.log('🔄 [AUTO-REFRESH] Auto-refreshing opportunities...');
        debouncedLoadOpportunities(false); // Use debounced version
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
        
        // Format stocks for display
        const stocks = data.data.stocks || [];
        const cryptos = data.data.crypto || [];
        
        let configHtml = '';
        
        if (stocks.length > 0) {
            const stockSymbols = stocks.map(item => item.symbol).join(', ');
            configHtml += `<p><small><strong>Watchlist Stocks:</strong> ${stockSymbols}</small></p>`;
        } else {
            configHtml += `<p><small><strong>Watchlist Stocks:</strong> <span class="text-muted">None configured</span></small></p>`;
        }
        
        if (cryptos.length > 0) {
            const cryptoSymbols = cryptos.map(item => item.symbol).join(', ');
            configHtml += `<p><small><strong>Watchlist Crypto:</strong> ${cryptoSymbols}</small></p>`;
        } else {
            configHtml += `<p><small><strong>Watchlist Crypto:</strong> <span class="text-muted">None configured</span></small></p>`;
        }
        
        configHtml += `<p><small><strong>Total Symbols:</strong> ${stocks.length + cryptos.length}</small></p>`;
        
        // Add analysis settings if available
        if (data.data.stock_limit) {
            configHtml += `<p><small><strong>Analysis Limit:</strong> ${data.data.stock_limit} symbols</small></p>`;
        }
        
        if (data.data.news_days) {
            configHtml += `<p><small><strong>News Days:</strong> ${data.data.news_days} days</small></p>`;
        }
        
        // Add message if no symbols configured
        if (stocks.length === 0 && cryptos.length === 0) {
            configHtml += `<div class="alert alert-warning mt-2"><small><i class="fas fa-exclamation-triangle"></i> No watchlist symbols configured. Add symbols in System Status page to enable watchlist analysis.</small></div>`;
        }
        
        configContainer.innerHTML = configHtml;
        
        console.log('✅ [CONFIG] Watchlist configuration loaded successfully:', {
            stocks: stocks.length,
            cryptos: cryptos.length,
            total: stocks.length + cryptos.length
        });
        
    } catch (error) {
        console.error('❌ [CONFIG] Error loading watchlist configuration:', error);
        const configContainer = document.getElementById('watchlistConfig');
        if (configContainer) {
            configContainer.innerHTML = `
                <div class="alert alert-warning">
                    <small><i class="fas fa-exclamation-triangle"></i> Failed to load watchlist configuration</small>
                </div>
                <p><small><strong>Error:</strong> ${error.message}</small></p>
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

function clearAlerts() {
    // Remove all existing alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (alert.parentNode) {
            alert.remove();
        }
    });
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