/* Crypto Analysis JavaScript */

// Global variables
let cryptoData = [];
let sentimentChart = null;
let signalChart = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Load data immediately for best user experience
    loadCryptoData();
});

// Load crypto analysis data
async function loadCryptoData() {
    showLoading('loadingSpinner');
    document.getElementById('refreshBtn').disabled = true;
    
    try {
        // First, try fast mode for instant preload
        console.log('Loading crypto data in fast mode for preload...');
        const fastResponse = await fetch('/api/crypto_analysis?fast=1');
        const fastData = await fastResponse.json();
        
        if (fastData.success && fastData.data.opportunities) {
            console.log('Fast mode data loaded, displaying basic crypto cards...');
            cryptoData = fastData.data.opportunities || [];
            displayCryptoCards(cryptoData);
            updateSummaryStats(cryptoData);
            
            document.getElementById('lastUpdated').textContent = 
                `Last updated: ${new Date(fastData.data.timestamp || fastData.timestamp).toLocaleString()} (basic data)`;
        }
        
        // Then try to get full analysis from cache or trigger background analysis
        console.log('Attempting to load full analysis data...');
        const fullResponse = await fetch('/api/crypto_analysis');
        const fullData = await fullResponse.json();
        
        if (fullData.success && fullData.data.opportunities) {
            console.log('Full analysis data loaded, updating crypto cards...');
            cryptoData = fullData.data.opportunities || [];
            displayCryptoCards(cryptoData);
            updateCharts(cryptoData);
            updateSummaryStats(cryptoData);
            
            document.getElementById('lastUpdated').textContent = 
                `Last updated: ${new Date(fullData.data.timestamp || fullData.timestamp).toLocaleString()}`;
        }
        
    } catch (error) {
        console.error('Error loading crypto data:', error);
        showAlert('Error loading crypto data: ' + error.message, 'danger');
    } finally {
        hideLoading('loadingSpinner');
        document.getElementById('refreshBtn').disabled = false;
    }
}

// Display crypto data in cards
function displayCryptoCards(cryptos) {
    const cardsContainer = document.getElementById('cryptoCardsRow');
    if (!cardsContainer) return;
    
    cardsContainer.innerHTML = '';
    
    if (cryptos.length === 0) {
        cardsContainer.innerHTML = `
            <div class="col-12">
                <div class="alert alert-info text-center">
                    <i class="fas fa-info-circle"></i>
                    No cryptocurrency opportunities with strong signals found at this time.
                </div>
            </div>
        `;
        return;
    }
    
    const row = document.createElement('div');
    row.className = 'row';
    
    cryptos.forEach(crypto => {
        const sentimentClass = getSentimentClass(crypto.sentiment_score);
        const sentimentStrength = getSentimentStrength(crypto.sentiment_score);
        
        // Determine crypto icon
        let icon = 'fas fa-coins';
        if (crypto.symbol === 'BTC') icon = 'fab fa-bitcoin';
        else if (crypto.symbol === 'ETH') icon = 'fab fa-ethereum';
        
        // Determine sentiment bar color and width
        const sentimentScore = crypto.sentiment_score || 0;
        const sentimentWidth = Math.abs(sentimentScore * 100);
        const sentimentColor = sentimentScore > 0 ? 'bg-success' : 'bg-danger';
        
        const cardHtml = `
            <div class="col-md-4 mb-3">
                <div class="card crypto-card">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="${icon}"></i> ${crypto.symbol}</h6>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-6">
                                <small class="text-muted">Price</small>
                                <h6 class="mb-0">${formatCurrency(crypto.current_price || 0)}</h6>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Action</small>
                                <h6 class="mb-0 ${crypto.action === 'BUY' ? 'text-success' : crypto.action === 'SELL' ? 'text-danger' : 'text-secondary'}">${crypto.action || 'HOLD'}</h6>
                            </div>
                        </div>
                        <hr>
                        <small class="text-muted">Sentiment</small>
                        <div class="progress mb-2" style="height: 8px;">
                            <div class="progress-bar ${sentimentColor}" style="width: ${sentimentWidth}%"></div>
                        </div>
                        <small class="text-muted">Confidence: ${((crypto.confidence || 0) * 100).toFixed(0)}%</small>
                    </div>
                </div>
            </div>
        `;
        
        row.innerHTML += cardHtml;
    });
    
    cardsContainer.appendChild(row);
}

// Display crypto data in table (keeping for compatibility)
function displayCryptoTable(cryptos) {
    const tbody = document.getElementById('cryptoTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    cryptos.forEach(crypto => {
        const row = document.createElement('tr');
        const sentimentClass = getSentimentClass(crypto.sentiment_score);
        const sentimentStrength = getSentimentStrength(crypto.sentiment_score);
        const signalClass = getSignalClass(crypto.action);
        
        row.innerHTML = `
            <td><strong>${crypto.symbol}</strong></td>
            <td>${formatCurrency(crypto.current_price)}</td>
            <td class="${sentimentClass}">
                ${crypto.sentiment_score.toFixed(3)}
                ${sentimentStrength.badge}
            </td>
            <td>${(crypto.confidence * 100).toFixed(1)}%</td>
            <td><span class="badge ${signalClass === 'signal-call' ? 'bg-warning' : 
                                    signalClass === 'signal-put' ? 'bg-danger' : 'bg-secondary'}">${crypto.action}</span></td>
            <td>${crypto.signal_strength.toFixed(3)}</td>
            <td>${crypto.news_count}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="analyzeCrypto('${crypto.symbol}')">
                    <i class="fas fa-chart-bar"></i> Analyze
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Update charts with crypto data
function updateCharts(cryptos) {
    // Sentiment Distribution Chart
    const sentimentCounts = {
        positive: cryptos.filter(c => c.sentiment_score > 0.1).length,
        negative: cryptos.filter(c => c.sentiment_score < -0.1).length,
        neutral: cryptos.filter(c => Math.abs(c.sentiment_score) <= 0.1).length
    };
    
    if (sentimentChart) {
        sentimentChart.destroy();
    }
    
    const sentimentCtx = document.getElementById('sentimentChart').getContext('2d');
    sentimentChart = new Chart(sentimentCtx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Negative', 'Neutral'],
            datasets: [{
                data: [sentimentCounts.positive, sentimentCounts.negative, sentimentCounts.neutral],
                backgroundColor: ['#28a745', '#dc3545', '#6c757d']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
    
    // Signal Distribution Chart
    const signalCounts = {
        call: cryptos.filter(c => c.action === 'CALL').length,
        put: cryptos.filter(c => c.action === 'PUT').length,
        hold: cryptos.filter(c => c.action === 'HOLD').length
    };
    
    if (signalChart) {
        signalChart.destroy();
    }
    
    const signalCtx = document.getElementById('signalChart').getContext('2d');
    signalChart = new Chart(signalCtx, {
        type: 'bar',
        data: {
            labels: ['BULLISH', 'BEARISH', 'NEUTRAL'],
            datasets: [{
                data: [signalCounts.call, signalCounts.put, signalCounts.hold],
                backgroundColor: ['#ffc107', '#dc3545', '#6c757d']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Update summary statistics
function updateSummaryStats(cryptos) {
    const bullishCount = cryptos.filter(c => c.action === 'CALL').length;
    const bearishCount = cryptos.filter(c => c.action === 'PUT').length;
    const neutralCount = cryptos.filter(c => c.action === 'HOLD').length;
    const avgSentiment = cryptos.reduce((sum, c) => sum + c.sentiment_score, 0) / cryptos.length;
    
    document.getElementById('bullishCount').textContent = bullishCount;
    document.getElementById('bearishCount').textContent = bearishCount;
    document.getElementById('neutralCount').textContent = neutralCount;
    document.getElementById('avgSentiment').textContent = avgSentiment.toFixed(3);
}

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