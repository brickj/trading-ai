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

// Load crypto analysis data
async function loadCryptoData() {
    showLoading('loadingSpinner');
    document.getElementById('refreshBtn').disabled = true;
    
    try {
        const response = await fetch('/api/crypto_analysis');
        const data = await response.json();
        
        if (data.error) {
            showAlert(data.error, 'danger');
            return;
        }
        
        cryptoData = data.results;
        displayCryptoTable(cryptoData);
        updateCharts(cryptoData);
        updateSummaryStats(cryptoData);
        
        document.getElementById('lastUpdated').textContent = 
            `Last updated: ${new Date(data.timestamp).toLocaleString()}`;
        
    } catch (error) {
        showAlert('Error loading crypto data: ' + error.message, 'danger');
    } finally {
        hideLoading('loadingSpinner');
        document.getElementById('refreshBtn').disabled = false;
    }
}

// Display crypto data in table
function displayCryptoTable(cryptos) {
    const tbody = document.getElementById('cryptoTableBody');
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