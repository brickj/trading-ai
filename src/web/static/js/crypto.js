// Cryptocurrency Analysis JavaScript
// Original GitHub version - simplified and working

let cryptoData = [];

// Initialize crypto data loading when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Crypto page loaded');
    loadCryptoData();
    
    // Set up refresh button
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            console.log('Refresh button clicked');
            loadCryptoData();
        });
    }
});

// Load cryptocurrency data from the backend
async function loadCryptoData() {
    try {
        console.log('Loading crypto data...');
        
        // Show loading spinner
        const loadingSpinner = document.getElementById('loadingSpinner');
        if (loadingSpinner) {
            loadingSpinner.style.display = 'block';
        }
        
        // First try fast mode for instant results
        const response = await fetch('/api/crypto_analysis?fast=1');
        const data = await response.json();
        
        console.log('API Response:', data);
        
        if (data.status === 'success' && data.data && data.data.opportunities) {
            cryptoData = data.data.opportunities;
            console.log('Loaded', cryptoData.length, 'crypto opportunities');
            
            // Display the crypto cards
            displayCryptoCards(cryptoData);
            
            // Update summary statistics
            updateSummaryStats(cryptoData);
            
            // Update charts
            updateCharts(cryptoData);
            
            // Update last updated timestamp
            const lastUpdated = document.getElementById('lastUpdated');
            if (lastUpdated) {
                const timestamp = data.data.timestamp || new Date().toISOString();
                lastUpdated.textContent = `Last updated: ${new Date(timestamp).toLocaleString()}`;
            }
        } else {
            console.error('Invalid API response:', data);
            showError('Failed to load cryptocurrency data');
        }
        
        // Hide loading spinner
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
        
    } catch (error) {
        console.error('Error loading crypto data:', error);
        showError('Error loading crypto data: ' + error.message);
        
        // Hide loading spinner
        const loadingSpinner = document.getElementById('loadingSpinner');
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
    }
}

// Display cryptocurrency opportunities as cards
function displayCryptoCards(cryptos) {
    console.log('Displaying', cryptos.length, 'crypto cards');
    
    const cardsContainer = document.getElementById('cryptoCardsRow');
    if (!cardsContainer) {
        console.error('cryptoCardsRow container not found');
        return;
    }
    
    // Clear existing content
    cardsContainer.innerHTML = '';
    
    if (cryptos.length === 0) {
        cardsContainer.innerHTML = `
            <div class="col-12">
                <div class="alert alert-info text-center">
                    <i class="fas fa-info-circle"></i>
                    No cryptocurrency opportunities found at this time.
                </div>
            </div>
        `;
        return;
    }
    
    // Create crypto cards
    cryptos.forEach(crypto => {
        const symbol = crypto.symbol || 'Unknown';
        const price = crypto.price_data?.current_price || 0;
        const sentimentScore = crypto.sentiment_data?.sentiment_score || 0;
        const confidence = crypto.sentiment_data?.confidence || 0;
        const action = crypto.signal_data?.action || 'HOLD';
        const signalStrength = crypto.signal_data?.signal_strength || 0;
        
        // Determine sentiment color
        const sentimentColor = sentimentScore > 0 ? 'success' : sentimentScore < 0 ? 'danger' : 'secondary';
        
        // Determine action color
        const actionColor = action === 'BUY' ? 'success' : action === 'SELL' ? 'danger' : 'secondary';
        
        // Create card element
        const cardDiv = document.createElement('div');
        cardDiv.className = 'col-md-6 col-lg-4 mb-3';
        cardDiv.innerHTML = `
            <div class="card border-warning h-100">
                <div class="card-header bg-warning text-dark">
                    <h5 class="mb-0">
                        <i class="fab fa-bitcoin"></i> ${symbol}
                        <span class="badge bg-${actionColor} float-end">${action}</span>
                    </h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-6">
                            <small class="text-muted">Price</small>
                            <p class="mb-2"><strong>$${formatPrice(price)}</strong></p>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">Signal Strength</small>
                            <p class="mb-2"><strong>${(signalStrength * 100).toFixed(1)}%</strong></p>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-6">
                            <small class="text-muted">Sentiment</small>
                            <p class="mb-2">
                                <span class="badge bg-${sentimentColor}">
                                    ${sentimentScore.toFixed(3)}
                                </span>
                            </p>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">Confidence</small>
                            <p class="mb-2"><strong>${(confidence * 100).toFixed(1)}%</strong></p>
                        </div>
                    </div>
                    
                    <div class="mt-3">
                        <button class="btn btn-sm btn-outline-info" onclick="showCryptoInfo('${symbol}')">
                            <i class="fas fa-info-circle"></i> Details
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        cardsContainer.appendChild(cardDiv);
    });
    
    console.log('Crypto cards displayed successfully');
}

// Update summary statistics
function updateSummaryStats(cryptos) {
    const bullishCount = cryptos.filter(c => c.signal_data?.action === 'BUY').length;
    const bearishCount = cryptos.filter(c => c.signal_data?.action === 'SELL').length;
    const neutralCount = cryptos.filter(c => c.signal_data?.action === 'HOLD').length;
    const avgSentiment = cryptos.length > 0 ? 
        cryptos.reduce((sum, c) => sum + (c.sentiment_data?.sentiment_score || 0), 0) / cryptos.length : 0;
    
    // Calculate total volume and avg volatility (using available data)
    const totalVolume = cryptos.reduce((sum, c) => sum + (c.price_data?.volume || 0), 0);
    const avgPrice = cryptos.length > 0 ? 
        cryptos.reduce((sum, c) => sum + (c.price_data?.current_price || 0), 0) / cryptos.length : 0;
    
    // Update the actual HTML elements on the page
    const gainersElem = document.getElementById('cryptoGainers');
    if (gainersElem) gainersElem.textContent = bullishCount;
    
    const losersElem = document.getElementById('cryptoLosers');
    if (losersElem) losersElem.textContent = bearishCount;
    
    const volumeElem = document.getElementById('cryptoVolume');
    if (volumeElem) volumeElem.textContent = `$${(totalVolume / 1000000).toFixed(1)}M`;
    
    const volatilityElem = document.getElementById('cryptoVolatility');
    if (volatilityElem) volatilityElem.textContent = `${Math.abs(avgSentiment * 100).toFixed(1)}%`;
    
    // Also update the detailed summary section
    const bullishElem = document.getElementById('bullishCount');
    if (bullishElem) bullishElem.textContent = bullishCount;
    
    const bearishElem = document.getElementById('bearishCount');
    if (bearishElem) bearishElem.textContent = bearishCount;
    
    const neutralElem = document.getElementById('neutralCount');
    if (neutralElem) neutralElem.textContent = neutralCount;
    
    const avgSentimentElem = document.getElementById('avgSentiment');
    if (avgSentimentElem) avgSentimentElem.textContent = avgSentiment.toFixed(3);
}

// Update charts with crypto data
function updateCharts(cryptos) {
    updateSentimentChart(cryptos);
    updateSignalChart(cryptos);
}

// Update sentiment distribution chart
function updateSentimentChart(cryptos) {
    const canvas = document.getElementById('sentimentDistributionChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Calculate sentiment distribution
    const positive = cryptos.filter(c => (c.sentiment_data?.sentiment_score || 0) > 0).length;
    const negative = cryptos.filter(c => (c.sentiment_data?.sentiment_score || 0) < 0).length;
    const neutral = cryptos.filter(c => (c.sentiment_data?.sentiment_score || 0) === 0).length;
    
    // Destroy existing chart if it exists
    if (window.sentimentChart) {
        window.sentimentChart.destroy();
    }
    
    window.sentimentChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Negative', 'Neutral'],
            datasets: [{
                data: [positive, negative, neutral],
                backgroundColor: [
                    '#28a745',
                    '#dc3545', 
                    '#6c757d'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

// Update signal distribution chart
function updateSignalChart(cryptos) {
    const canvas = document.getElementById('signalChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Calculate signal distribution
    const buySignals = cryptos.filter(c => c.signal_data?.action === 'BUY').length;
    const sellSignals = cryptos.filter(c => c.signal_data?.action === 'SELL').length;
    const holdSignals = cryptos.filter(c => c.signal_data?.action === 'HOLD').length;
    
    // Destroy existing chart if it exists
    if (window.signalChart) {
        window.signalChart.destroy();
    }
    
    window.signalChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['BUY', 'SELL', 'HOLD'],
            datasets: [{
                label: 'Number of Signals',
                data: [buySignals, sellSignals, holdSignals],
                backgroundColor: [
                    '#28a745',
                    '#dc3545',
                    '#ffc107'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// Show detailed crypto information
function showCryptoInfo(symbol) {
    const crypto = cryptoData.find(c => c.symbol === symbol);
    if (!crypto) {
        alert('Crypto data not found for ' + symbol);
        return;
    }
    
    const price = crypto.price_data?.current_price || 0;
    const sentiment = crypto.sentiment_data?.sentiment_score || 0;
    const confidence = crypto.sentiment_data?.confidence || 0;
    const action = crypto.signal_data?.action || 'HOLD';
    const strength = crypto.signal_data?.signal_strength || 0;
    const summary = crypto.sentiment_data?.summary || 'No summary available';
    
    const message = `
        <strong>${symbol} Analysis</strong><br><br>
        <strong>Price:</strong> $${formatPrice(price)}<br>
        <strong>Sentiment:</strong> ${sentiment.toFixed(3)} (${(confidence * 100).toFixed(1)}% confidence)<br>
        <strong>Signal:</strong> ${action} (${(strength * 100).toFixed(1)}% strength)<br><br>
        <strong>Summary:</strong><br>
        ${summary}
    `;
    
    // Show in a modal or alert
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-info';
    alertDiv.innerHTML = message;
    
    // Find a place to show it (replace the alert if needed)
    const existingAlert = document.querySelector('.alert-info');
    if (existingAlert && existingAlert.id === 'crypto-threshold-info') {
        existingAlert.parentNode.insertBefore(alertDiv, existingAlert.nextSibling);
        setTimeout(() => alertDiv.remove(), 10000); // Remove after 10 seconds
    } else {
        alert(message.replace(/<br>/g, '\n').replace(/<strong>/g, '').replace(/<\/strong>/g, ''));
    }
}

// Show error message
function showError(message) {
    console.error(message);
    const cardsContainer = document.getElementById('cryptoCardsRow');
    if (cardsContainer) {
        cardsContainer.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    ${message}
                </div>
            </div>
        `;
    }
}

// Format price for display
function formatPrice(price) {
    if (price > 1000) {
        return price.toLocaleString('en-US', { maximumFractionDigits: 2 });
    } else if (price > 1) {
        return price.toFixed(2);
    } else {
        return price.toFixed(6);
    }
}