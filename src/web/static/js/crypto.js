/* Crypto Analysis JavaScript */

// Global variables
let cryptoData = [];
let sentimentChart = null;
let signalChart = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Auto-load data after a short delay
    setTimeout(loadCryptoData, 1000);
});

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

// Load crypto data
async function loadCryptoData() {
    console.log('🔍 [CRYPTO] Starting to load crypto data...');
    try {
        // Show loading spinner
        showLoading('loadingSpinner');
        
        // Fetch crypto analysis data
        const response = await loggedFetch('/api/crypto_analysis');
        console.log('🔍 [CRYPTO] Raw API response:', response);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('🔍 [CRYPTO] Parsed data:', data);
        
        if (data.success === true && data.data && data.data.opportunities) {
            console.log('🔍 [CRYPTO] Found opportunities:', data.data.opportunities.length);
            cryptoData = data.data.opportunities;
            displayCryptoData(data.data);
            
            // Call the summary stats update function directly
            try {
                updateCryptoSummaryStats(data.data.opportunities);
            } catch (e) {
                console.error('Failed to update summary stats:', e);
            }
            
            createSentimentChart(data.data);
            createSignalChart(data.data);
        } else {
            console.error('❌ [CRYPTO] Invalid data structure:', data);
            showAlert('Invalid data structure received from server', 'danger');
        }
    } catch (error) {
        console.error('❌ [CRYPTO] Error loading crypto data:', error);
        showAlert(`Failed to load crypto data: ${error.message}`, 'danger');
    } finally {
        hideLoading('loadingSpinner');
    }
}

// Display crypto data
function displayCryptoData(data) {
    console.log('🔍 [DISPLAY] Starting displayCryptoData with:', data);
    
    if (!data || !data.opportunities || !Array.isArray(data.opportunities)) {
        console.error('❌ [DISPLAY] Invalid data structure:', data);
        return;
    }
    
    console.log('🔍 [DISPLAY] Found opportunities:', data.opportunities.length);
    
    let container = document.getElementById('cryptoCardsRow');
    console.log('🔍 [DISPLAY] Container element:', container);
    
    if (!container) {
        // If not present, create and insert it into the correct place
        const parent = document.querySelector('#cryptoContainer .card-body');
        console.log('🔍 [DISPLAY] Parent element:', parent);
        
        if (parent) {
            container = document.createElement('div');
            container.id = 'cryptoCardsRow';
            parent.appendChild(container);
            console.log('🔍 [DISPLAY] Created new container');
        } else {
            console.error('❌ [DISPLAY] Could not find parent container');
            return;
        }
    }
    
    // Clear existing content
    container.innerHTML = '';
    console.log('🔍 [DISPLAY] Cleared container');
    
    if (data.opportunities.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No crypto opportunities found at this time.</div>';
        console.log('🔍 [DISPLAY] No opportunities found');
        return;
    }
    
    // Create cards for each opportunity
    data.opportunities.forEach((opp, index) => {
        console.log(`🔍 [DISPLAY] Creating card ${index + 1} for:`, opp.symbol);
        const card = createCryptoCard(opp);
        container.appendChild(card);
    });
    
    console.log('🔍 [DISPLAY] Finished creating all cards');
}

// Create crypto card
function createCryptoCard(opp) {
    console.log('🔍 [CARD] Creating crypto card for opportunity:', {
        symbol: opp.symbol,
        type: opp.type,
        trigger: opp.trigger,
        fullOpportunity: opp
    });
    
    const card = document.createElement('div');
    card.className = 'card mb-3';
    card.setAttribute('data-symbol', opp.symbol);
    
    // Safely access nested properties with fallbacks
    const symbol = opp.symbol || 'UNKNOWN';
    const trigger = opp.trigger || 'unknown';
    const type = opp.type || 'crypto';
    const action = opp.signal_data?.action || 'HOLD';
    const sentimentScore = opp.sentiment_data?.sentiment_score || 0;
    const confidence = opp.sentiment_data?.confidence || 0;
    const newsCount = opp.sentiment_data?.analysis_metadata?.general_news_count || opp.news_count || 0;
    const currentPrice = opp.price_data?.current_price || 0;
    const change24h = opp.price_data?.change_24h || 0;
    const marketCap = opp.price_data?.market_cap || 0;
    const signalStrength = opp.signal_data?.signal_strength || 0;
    const reasoning = opp.signal_data?.reasoning || 'No reasoning provided';
    
    console.log('🔍 [CARD] Extracted values:', {
        symbol, trigger, type, action, sentimentScore, confidence,
        newsCount, currentPrice, change24h, marketCap, signalStrength, reasoning: reasoning.substring(0, 100) + '...'
    });
    
    const triggerBadge = trigger === 'news_driven' ? 
        '<span class="badge bg-info">News-Driven</span>' : 
        '<span class="badge bg-warning">Watchlist</span>';
    
    const typeBadge = type === 'crypto' ? 
        '<span class="badge bg-warning">Crypto</span>' : 
        '<span class="badge bg-primary">Stock</span>';
    
    // Action badge: only show BUY, SELL, HOLD for crypto
    let actionBadge = '';
    if (action === 'BUY') {
        actionBadge = '<span class="badge bg-success">BUY</span>';
    } else if (action === 'SELL') {
        actionBadge = '<span class="badge bg-danger">SELL</span>';
    } else if (action === 'HOLD') {
        actionBadge = '<span class="badge bg-secondary">HOLD</span>';
    }
    
    const sentimentClass = getSentimentClass(sentimentScore);
    
    // Format 24h change with color coding
    const change24hFormatted = change24h !== 0 ? 
        `${change24h > 0 ? '+' : ''}${change24h.toFixed(2)}%` : 
        '0.00%';
    const change24hClass = change24h > 0 ? 'text-success' : change24h < 0 ? 'text-danger' : 'text-muted';
    
    // Format market cap
    const marketCapFormatted = marketCap > 0 ? 
        formatMarketCap(marketCap) : 
        'N/A';
    
    console.log('🔍 [CARD] Generated badges:', {
        triggerBadge: triggerBadge.includes('News-Driven') ? 'News-Driven' : 'Watchlist',
        typeBadge: typeBadge.includes('Crypto') ? 'Crypto' : 'Stock',
        actionBadge: actionBadge.includes('BUY') ? 'BUY' : actionBadge.includes('SELL') ? 'SELL' : 'HOLD',
        sentimentClass
    });
    
    card.innerHTML = `
        <div class="card-header d-flex justify-content-between align-items-center">
            <div>
                <h6 class="mb-0">
                    <strong class="crypto-symbol">${symbol}</strong>
                    ${typeBadge}
                    ${triggerBadge}
                    ${actionBadge}
                </h6>
            </div>
            <div>
                <button class="btn btn-sm btn-outline-success" onclick="executeCryptoOpportunity('${symbol}')">
                    <i class="fas fa-play"></i> Execute
                </button>
            </div>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-3">
                    <h6>Price Info</h6>
                    <p><strong>Current:</strong> ${formatCurrency(currentPrice)}</p>
                    <p><strong>24h Change:</strong> <span class="${change24hClass}">${change24hFormatted}</span></p>
                    <p><strong>Market Cap:</strong> <span class="text-muted">${marketCapFormatted}</span></p>
                </div>
                <div class="col-md-3">
                    <h6>Sentiment</h6>
                    <p><strong>Score:</strong> <span class="${sentimentClass}">${sentimentScore.toFixed(3)}</span></p>
                    <p><strong>Confidence:</strong> ${(confidence * 100).toFixed(1)}%</p>
                    <p><strong>News Count:</strong> ${newsCount}</p>
                </div>
                <div class="col-md-3">
                    <h6>Trade Details</h6>
                    <p><strong>Action:</strong> ${action}</p>
                    <p><strong>Signal Strength:</strong> ${signalStrength.toFixed(3)}</p>
                    <p><strong>Risk Level:</strong> <span class="badge bg-warning">Medium</span></p>
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
    
    console.log('✅ [CARD] Crypto card created successfully for:', symbol);
    return card;
}

// Execute crypto opportunity trade
async function executeCryptoOpportunity(symbol) {
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
            showAlert(`Crypto trade executed for ${symbol}! Remaining capital: ${formatCurrency(data.execution_result.remaining_capital)}`, 'success');
        } else {
            showAlert(data.execution_result.message, 'warning');
        }
        
    } catch (error) {
        showAlert('Error executing crypto trade: ' + error.message, 'danger');
    }
}

// Utility functions
function getSentimentClass(score) {
    if (score > 0.3) return 'text-success';
    if (score < -0.3) return 'text-danger';
    return 'text-secondary';
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

function formatMarketCap(amount) {
    if (amount >= 1e9) {
        return `$${(amount / 1e9).toFixed(2)}B`;
    } else if (amount >= 1e6) {
        return `$${(amount / 1e6).toFixed(2)}M`;
    } else if (amount >= 1e3) {
        return `$${(amount / 1e3).toFixed(2)}K`;
    } else {
        return `$${amount.toFixed(2)}`;
    }
}

// Auto-refresh every 5 minutes
setInterval(() => {
    if (document.visibilityState === 'visible') {
        loadCryptoData();
    }
}, 5 * 60 * 1000);

// Show crypto info
function showCryptoInfo(symbol) {
    const crypto = cryptoData.find(c => c.symbol === symbol);
    if (!crypto) return;
    
    const displaySymbol = symbol.replace('USD', '/USD');
    
    showAlert(`
        <strong>${displaySymbol}</strong><br>
        Price: ${formatCurrency(crypto.current_price)}<br>
        Sentiment: ${crypto.sentiment_score.toFixed(3)} (${(crypto.confidence * 100).toFixed(1)}% confidence)<br>
        Signal: ${crypto.action} (Strength: ${crypto.signal_strength.toFixed(3)})<br>
        <small>Note: Crypto options trading is limited. Consider spot or futures trading.</small>
    `, 'info');
}

// Analyze individual crypto
function analyzeCrypto(symbol) {
    showAlert(`Analyzing ${symbol}...`, 'info');
    // This would typically call an API endpoint for detailed analysis
    // For now, just show the crypto info
    showCryptoInfo(symbol);
}

// Run crypto analysis (for the button click)
function runCryptoAnalysis() {
    loadCryptoData();
}

// Add event listener for refresh button
if (document.getElementById('refreshBtn')) {
    document.getElementById('refreshBtn').addEventListener('click', loadCryptoData);
}

// Update crypto summary statistics
function updateCryptoSummaryStats(opportunities) {
    console.log('📊 [SUMMARY] Updating crypto summary statistics for', opportunities.length, 'opportunities');
    
    try {
        // Calculate summary statistics
        const totalOpportunities = opportunities.length;
        const bullishCount = opportunities.filter(opp => 
            opp.sentiment_data?.sentiment_score > 0.1
        ).length;
        const bearishCount = opportunities.filter(opp => 
            opp.sentiment_data?.sentiment_score < -0.1
        ).length;
        const neutralCount = totalOpportunities - bullishCount - bearishCount;
        
        const avgSentiment = opportunities.reduce((sum, opp) => 
            sum + (opp.sentiment_data?.sentiment_score || 0), 0
        ) / totalOpportunities;
        
        const avgConfidence = opportunities.reduce((sum, opp) => 
            sum + (opp.sentiment_data?.confidence || 0), 0
        ) / totalOpportunities;
        
        console.log('📊 [SUMMARY] Calculated stats:', {
            totalOpportunities,
            bullishCount,
            bearishCount,
            neutralCount,
            avgSentiment: avgSentiment.toFixed(3),
            avgConfidence: avgConfidence.toFixed(3)
        });
        
        // Update the summary statistics in the DOM
        const summaryStats = document.getElementById('summaryStats');
        if (summaryStats) {
            // Create summary content
            summaryStats.innerHTML = `
                <div class="row">
                    <div class="col-md-3">
                        <div class="text-center">
                            <h4 id="bullishCount" class="text-success">${bullishCount}</h4>
                            <small class="text-muted">Bullish</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="text-center">
                            <h4 id="bearishCount" class="text-danger">${bearishCount}</h4>
                            <small class="text-muted">Bearish</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="text-center">
                            <h4 id="neutralCount" class="text-secondary">${neutralCount}</h4>
                            <small class="text-muted">Neutral</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="text-center">
                            <h4 id="avgSentiment" class="text-info">${avgSentiment.toFixed(3)}</h4>
                            <small class="text-muted">Avg Sentiment</small>
                        </div>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-12">
                        <div class="alert alert-info">
                            <strong>Crypto Market Summary:</strong> 
                            ${totalOpportunities} cryptocurrencies analyzed. 
                            Average confidence: ${(avgConfidence * 100).toFixed(1)}%. 
                            Market sentiment is ${avgSentiment > 0.1 ? 'bullish' : avgSentiment < -0.1 ? 'bearish' : 'neutral'}.
                        </div>
                    </div>
                </div>
            `;
            
            console.log('✅ [SUMMARY] Summary statistics updated successfully');
        } else {
            console.warn('⚠️ [SUMMARY] Summary stats container not found');
        }
        
    } catch (error) {
        console.error('❌ [SUMMARY] Error updating summary statistics:', error);
    }
}

// Create sentiment distribution chart
function createSentimentChart(data) {
    console.log('📈 [CHART] Creating sentiment chart with data:', data);
    
    try {
        const ctx = document.getElementById('sentimentDistributionChart');
        if (!ctx) {
            console.warn('⚠️ [CHART] Sentiment chart canvas not found');
            return;
        }
        
        // Destroy existing chart if it exists
        if (sentimentChart) {
            sentimentChart.destroy();
        }
        
        // Prepare data for the chart
        const opportunities = data.opportunities || [];
        const bullishCount = opportunities.filter(opp => 
            opp.sentiment_data?.sentiment_score > 0.1
        ).length;
        const bearishCount = opportunities.filter(opp => 
            opp.sentiment_data?.sentiment_score < -0.1
        ).length;
        const neutralCount = opportunities.length - bullishCount - bearishCount;
        
        sentimentChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Bullish', 'Bearish', 'Neutral'],
                datasets: [{
                    data: [bullishCount, bearishCount, neutralCount],
                    backgroundColor: ['#28a745', '#dc3545', '#6c757d'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#fff'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Sentiment Distribution',
                        color: '#fff'
                    }
                }
            }
        });
        
        console.log('✅ [CHART] Sentiment chart created successfully');
    } catch (error) {
        console.error('❌ [CHART] Error creating sentiment chart:', error);
    }
}

// Create signal distribution chart
function createSignalChart(data) {
    console.log('📈 [CHART] Creating signal chart with data:', data);
    
    try {
        const ctx = document.getElementById('signalChart');
        if (!ctx) {
            console.warn('⚠️ [CHART] Signal chart canvas not found');
            return;
        }
        
        // Destroy existing chart if it exists
        if (signalChart) {
            signalChart.destroy();
        }
        
        // Prepare data for the chart
        const opportunities = data.opportunities || [];
        const buyCount = opportunities.filter(opp => 
            opp.signal_data?.action === 'BUY'
        ).length;
        const sellCount = opportunities.filter(opp => 
            opp.signal_data?.action === 'SELL'
        ).length;
        const holdCount = opportunities.filter(opp => 
            opp.signal_data?.action === 'HOLD'
        ).length;
        
        signalChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['BUY', 'SELL', 'HOLD'],
                datasets: [{
                    label: 'Signal Count',
                    data: [buyCount, sellCount, holdCount],
                    backgroundColor: ['#28a745', '#dc3545', '#6c757d'],
                    borderWidth: 1,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Signal Distribution',
                        color: '#fff'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#fff'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#fff'
                        }
                    }
                }
            }
        });
        
        console.log('✅ [CHART] Signal chart created successfully');
    } catch (error) {
        console.error('❌ [CHART] Error creating signal chart:', error);
    }
} 