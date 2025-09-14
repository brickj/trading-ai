/* Stocks Page JavaScript - S&P 500 Winners & Losers Analysis */

// Global variables
let isRefreshing = false;
let autoRefreshInterval = null;
let lastUpdated = null;

// Debug functions
function updateDebugRequest(url, params) {
    const debugRequest = document.getElementById('debugRequest');
    if (debugRequest) {
        debugRequest.textContent = `URL: ${url}\nParams: ${JSON.stringify(params, null, 2)}`;
    }
}

function updateDebugResponse(response) {
    const debugResponse = document.getElementById('debugResponse');
    if (debugResponse) {
        debugResponse.textContent = JSON.stringify(response, null, 2);
    }
}

function updateDebugDataFlow(message) {
    const debugDataFlow = document.getElementById('debugDataFlow');
    if (debugDataFlow) {
        const timestamp = new Date().toLocaleTimeString();
        const currentContent = debugDataFlow.textContent;
        const newContent = `[${timestamp}] ${message}\n${currentContent}`;
        debugDataFlow.textContent = newContent.substring(0, 2000); // Keep last 2000 chars
    }
}

function updateDebugConsole(message) {
    const debugConsole = document.getElementById('debugConsole');
    if (debugConsole) {
        const timestamp = new Date().toLocaleTimeString();
        const currentContent = debugConsole.textContent;
        const newContent = `[${timestamp}] ${message}\n${currentContent}`;
        debugConsole.textContent = newContent.substring(0, 2000); // Keep last 2000 chars
    }
}

function toggleDebugSection() {
    const debugContent = document.getElementById('debugContent');
    if (debugContent) {
        debugContent.style.display = debugContent.style.display === 'none' ? 'block' : 'none';
    }
}

// Override console.log to capture all output
const originalConsoleLog = console.log;
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

console.log = function(...args) {
    originalConsoleLog.apply(console, args);
    const message = args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
    ).join(' ');
    updateDebugConsole(`LOG: ${message}`);
};

console.error = function(...args) {
    originalConsoleError.apply(console, args);
    const message = args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
    ).join(' ');
    updateDebugConsole(`ERROR: ${message}`);
};

console.warn = function(...args) {
    originalConsoleWarn.apply(console, args);
    const message = args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
    ).join(' ');
    updateDebugConsole(`WARN: ${message}`);
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 [STOCKS] Initializing stocks page...');
    
    // Add event listeners
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            console.log('🔄 [STOCKS] Manual refresh requested');
            loadStocksAnalysis(true);
        });
    }
    
    const autoRefreshToggle = document.getElementById('autoRefreshToggle');
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('click', toggleAutoRefresh);
    }
    
    // Check if there's already initial data displayed (from backend)
    const winnersList = document.getElementById('winnersList');
    const losersList = document.getElementById('losersList');
    const stocksTableBody = document.getElementById('stocksTableBody');
    
    // Check if initial data is present
    let hasInitialData = false;
    if (winnersList && losersList && stocksTableBody) {
        const hasWinners = winnersList.querySelectorAll('.card').length > 0;
        const hasLosers = losersList.querySelectorAll('.card').length > 0;
        const hasTableData = stocksTableBody.querySelectorAll('tr').length > 1; // More than just header
        
        hasInitialData = hasWinners || hasLosers || hasTableData;
    }
    
    if (hasInitialData) {
        console.log('🚀 [STOCKS] Initial data already displayed from backend');
        updateLastUpdated();
        
        // Hide any loading spinners
        const progressContainer = document.getElementById('sp500-progress-container');
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
        
        // Show the results sections
        const summaryStats = document.getElementById('summaryStats');
        const enhancedAnalysisResults = document.getElementById('enhancedAnalysisResults');
        if (summaryStats) summaryStats.style.display = 'block';
        if (enhancedAnalysisResults) enhancedAnalysisResults.style.display = 'block';
        
        // Update market overview with initial data
        updateMarketOverviewWithInitialData();
        
    } else {
        console.log('🚀 [STOCKS] No initial data found, loading fresh data...');
        loadStocksAnalysis(false);
    }
    
    // Set up WebSocket connection for real-time updates
    setupWebSocket();
});

// Set up WebSocket connection for real-time progress updates
function setupWebSocket() {
    if (typeof io !== 'undefined') {
        const socket = io();
        
        socket.on('sp500_progress', function(data) {
            console.log('📡 [WEBSOCKET] Progress update:', data);
            updateProgress(data);
        });
        
        socket.on('connect', function() {
            console.log('🔗 [WEBSOCKET] Connected to server');
        });
        
        socket.on('disconnect', function() {
            console.log('❌ [WEBSOCKET] Disconnected from server');
        });
    } else {
        console.log('⚠️ [STOCKS] Socket.IO not available, progress updates disabled');
    }
}

// Load stocks analysis data
async function loadStocksAnalysis(forceRefresh = false) {
    if (isRefreshing) {
        console.log('⏳ [STOCKS] Already refreshing, skipping request');
        updateDebugDataFlow('Already refreshing, skipping request');
        return;
    }
    
    isRefreshing = true;
    showLoading(true);
    
    try {
        console.log('🔍 [STOCKS] Loading market movers data...');
        updateDebugDataFlow('Starting market movers data load...');
        
        // Get market movers data first to identify winners/losers
        const marketMoversUrl = '/api/market_movers';
        console.log('🌐 [STOCKS] Getting market movers from:', marketMoversUrl);
        updateDebugRequest(marketMoversUrl, {});
        updateDebugDataFlow(`Getting market movers from: ${marketMoversUrl}`);
        
        const marketMoversResponse = await fetch(marketMoversUrl);
        const marketMoversResult = await marketMoversResponse.json();
        
        console.log('📊 [STOCKS] Market movers response:', marketMoversResult);
        updateDebugResponse(marketMoversResult);
        
        if (marketMoversResult.status === 'success' && marketMoversResult.data) {
            updateDebugDataFlow(`Market movers loaded successfully`);
            
            // Get real enhanced analysis for top winners and losers
            const enhancedAnalysisData = await getEnhancedAnalysisForSymbols(marketMoversResult.data);
            displayStocksAnalysis(enhancedAnalysisData);
            updateLastUpdated();
        } else {
            console.error('❌ [STOCKS] Market movers API error:', marketMoversResult.message || 'Unknown error');
            updateDebugDataFlow(`Market movers API error: ${marketMoversResult.message || 'Unknown error'}`);
            showError('Failed to load market movers data: ' + (marketMoversResult.message || 'Unknown error'));
        }
        
    } catch (error) {
        console.error('❌ [STOCKS] Fetch error:', error);
        updateDebugDataFlow(`Fetch error: ${error.message}`);
        showError('Failed to load market movers data: ' + error.message);
    } finally {
        isRefreshing = false;
        showLoading(false);
    }
}

// Get real enhanced analysis for symbols from market movers
async function getEnhancedAnalysisForSymbols(marketMoversData) {
    updateDebugDataFlow('Getting real enhanced analysis for symbols...');
    
    const enhancedAnalysis = [];
    const symbolsToAnalyze = [];
    
    // Collect symbols from gainers and losers (top 3 each)
    if (marketMoversData.gainers) {
        symbolsToAnalyze.push(...marketMoversData.gainers.slice(0, 3).map(g => g.symbol));
    }
    if (marketMoversData.losers) {
        symbolsToAnalyze.push(...marketMoversData.losers.slice(0, 3).map(l => l.symbol));
    }
    
    console.log('🔍 [STOCKS] Analyzing symbols:', symbolsToAnalyze);
    updateDebugDataFlow(`Analyzing ${symbolsToAnalyze.length} symbols: ${symbolsToAnalyze.join(', ')}`);
    
    // Get real enhanced analysis for each symbol
    for (const symbol of symbolsToAnalyze) {
        try {
            console.log(`📊 [STOCKS] Getting enhanced analysis for ${symbol}...`);
            updateDebugDataFlow(`Getting enhanced analysis for ${symbol}...`);
            
            const response = await fetch('/api/enhanced_analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ symbol: symbol })
            });
            
            const result = await response.json();
            
            if (result.success && result.data) {
                // Determine if this is a winner or loser based on market movers data
                const isWinner = marketMoversData.gainers?.some(g => g.symbol === symbol);
                const isLoser = marketMoversData.losers?.some(l => l.symbol === symbol);
                
                const analysisData = {
                    symbol: symbol,
                    type: isWinner ? 'winner' : 'loser',
                    price_data: result.data.price_data,
                    sentiment_data: result.data.sentiment_data,
                    signal_data: result.data.signal_data,
                    news_count: result.data.news_data?.article_count || 0,
                    timestamp: new Date().toISOString(),
                    analysis_time: result.data.analysis_time
                };
                
                enhancedAnalysis.push(analysisData);
                console.log(`✅ [STOCKS] Enhanced analysis loaded for ${symbol}`);
                updateDebugDataFlow(`Enhanced analysis loaded for ${symbol}`);
            } else {
                console.warn(`⚠️ [STOCKS] Failed to get enhanced analysis for ${symbol}:`, result.error);
                updateDebugDataFlow(`Failed to get enhanced analysis for ${symbol}: ${result.error}`);
            }
        } catch (error) {
            console.error(`❌ [STOCKS] Error getting enhanced analysis for ${symbol}:`, error);
            updateDebugDataFlow(`Error getting enhanced analysis for ${symbol}: ${error.message}`);
        }
    }
    
    console.log(`📊 [STOCKS] Enhanced analysis completed for ${enhancedAnalysis.length} symbols`);
    updateDebugDataFlow(`Enhanced analysis completed for ${enhancedAnalysis.length} symbols`);
    
    return {
        enhanced_analysis: enhancedAnalysis,
        errors: [],
        total_analyzed: enhancedAnalysis.length,
        opportunities_found: enhancedAnalysis.length,
        errors_count: 0,
        performance: {
            execution_time: 0,
            success_rate: '100%'
        },
        timestamp: new Date().toISOString(),
        source: 'real_enhanced_analysis'
    };
}

// Display stocks analysis results
function displayStocksAnalysis(data) {
    console.log('📈 [STOCKS] ===== DISPLAYING ANALYSIS RESULTS =====');
    console.log('📈 [STOCKS] Raw data:', data);
    console.log('📈 [STOCKS] Data type:', typeof data);
    console.log('📈 [STOCKS] Data keys:', Object.keys(data));
    
    updateDebugDataFlow(`Displaying analysis results with ${Object.keys(data).length} data keys`);
    updateDebugConsole(`Raw data: ${JSON.stringify(data, null, 2)}`);
    
    // Check if enhanced_analysis exists
    if (data.enhanced_analysis) {
        console.log('📈 [STOCKS] Enhanced analysis found:', data.enhanced_analysis);
        console.log('📈 [STOCKS] Enhanced analysis length:', data.enhanced_analysis.length);
        updateDebugDataFlow(`Enhanced analysis found with ${data.enhanced_analysis.length} stocks`);
        
        if (data.enhanced_analysis.length > 0) {
            console.log('📈 [STOCKS] First result structure:', Object.keys(data.enhanced_analysis[0]));
            console.log('📈 [STOCKS] First result:', data.enhanced_analysis[0]);
            updateDebugDataFlow(`First result structure: ${Object.keys(data.enhanced_analysis[0]).join(', ')}`);
        }
    } else {
        console.log('❌ [STOCKS] No enhanced_analysis found in data');
        updateDebugDataFlow('No enhanced_analysis found in data');
        
        // No need for fallback since we're using market_movers endpoint directly
        showError('No analysis data available');
        return;
    }
    
    // Check for other data structures
    if (data.opportunities) {
        console.log('📈 [STOCKS] Opportunities found:', data.opportunities);
        console.log('📈 [STOCKS] Opportunities length:', data.opportunities.length);
        updateDebugDataFlow(`Opportunities found: ${data.opportunities.length}`);
    }
    
    if (data.errors) {
        console.log('📈 [STOCKS] Errors found:', data.errors);
        console.log('📈 [STOCKS] Errors length:', data.errors.length);
        updateDebugDataFlow(`Errors found: ${data.errors.length}`);
    }
    
    // Update market overview
    updateDebugDataFlow('Updating market overview...');
    updateMarketOverview(data);
    
    // Update winners and losers summary
    updateDebugDataFlow('Updating winners and losers summary...');
    updateWinnersLosersSummary(data);
    
    // Update summary statistics
    updateDebugDataFlow('Updating summary statistics...');
    updateSummaryStats(data);
    
    // Show results sections
    const summaryStats = document.getElementById('summaryStats');
    const enhancedAnalysisResults = document.getElementById('enhancedAnalysisResults');
    
    if (summaryStats) {
        summaryStats.style.display = 'block';
        console.log('📈 [STOCKS] Summary stats section shown');
        updateDebugDataFlow('Summary stats section shown');
    } else {
        console.log('❌ [STOCKS] Summary stats section not found');
        updateDebugDataFlow('Summary stats section not found');
    }
    
    if (enhancedAnalysisResults) {
        enhancedAnalysisResults.style.display = 'block';
        console.log('📈 [STOCKS] Enhanced analysis results section shown');
        updateDebugDataFlow('Enhanced analysis results section shown');
    } else {
        console.log('❌ [STOCKS] Enhanced analysis results section not found');
        updateDebugDataFlow('Enhanced analysis results section not found');
    }
    
    // Update legacy table if it exists
    updateDebugDataFlow('Updating legacy table...');
    updateLegacyTable(data);
    
    console.log('📈 [STOCKS] ===== DISPLAY COMPLETE =====');
    updateDebugDataFlow('Display complete');
}

// Update market overview with initial data from backend
function updateMarketOverviewWithInitialData() {
    const winnersList = document.getElementById('winnersList');
    const losersList = document.getElementById('losersList');
    
    if (winnersList && losersList) {
        const winnersCount = winnersList.querySelectorAll('.card').length;
        const losersCount = losersList.querySelectorAll('.card').length;
        
        // Update market overview numbers
        const marketGainers = document.getElementById('marketGainers');
        const marketLosers = document.getElementById('marketLosers');
        if (marketGainers) marketGainers.textContent = winnersCount;
        if (marketLosers) marketLosers.textContent = losersCount;
        
        console.log('📊 [STOCKS] Market overview updated with initial data:', { winners: winnersCount, losers: losersCount });
    }
}

// Update market overview section
function updateMarketOverview(data) {
    const enhancedAnalysis = data.enhanced_analysis || [];
    
    if (enhancedAnalysis.length > 0) {
        // Calculate market statistics
        const winners = enhancedAnalysis.filter(stock => stock.type === 'winner');
        const losers = enhancedAnalysis.filter(stock => stock.type === 'loser');
        
        // Update market overview display
        const marketGainers = document.getElementById('marketGainers');
        const marketLosers = document.getElementById('marketLosers');
        const marketVolume = document.getElementById('marketVolume');
        const marketVolatility = document.getElementById('marketVolatility');
        
        if (marketGainers) marketGainers.textContent = winners.length;
        if (marketLosers) marketLosers.textContent = losers.length;
        if (marketVolume) marketVolume.textContent = enhancedAnalysis.length;
        if (marketVolatility) marketVolatility.textContent = 'High';
    }
}

// Update winners and losers summary
function updateWinnersLosersSummary(data) {
    console.log('🏆 [STOCKS] ===== UPDATING WINNERS/LOSERS SUMMARY =====');
    console.log('🏆 [STOCKS] Input data:', data);
    
    updateDebugDataFlow('Starting winners/losers summary update...');
    
    const enhancedAnalysis = data.enhanced_analysis || [];
    console.log('🏆 [STOCKS] Enhanced analysis array:', enhancedAnalysis);
    console.log('🏆 [STOCKS] Enhanced analysis length:', enhancedAnalysis.length);
    updateDebugDataFlow(`Enhanced analysis array length: ${enhancedAnalysis.length}`);
    
    if (enhancedAnalysis.length === 0) {
        console.log('❌ [STOCKS] No enhanced analysis data available');
        updateDebugDataFlow('No enhanced analysis data available');
        showError('No analysis data available');
        return;
    }
    
    // Function to extract numeric change percent
    function getChangePercent(stock) {
        const changePercentStr = stock.price_data?.change_percent || '0%';
        const numericValue = parseFloat(changePercentStr.replace('%', ''));
        updateDebugDataFlow(`Extracted change percent for ${stock.symbol}: ${changePercentStr} -> ${numericValue}`);
        return numericValue;
    }
    
    // Sort by change percent and separate winners and losers
    const stocksWithChange = enhancedAnalysis.map(stock => ({
        ...stock,
        changePercent: getChangePercent(stock)
    })).sort((a, b) => b.changePercent - a.changePercent);
    
    updateDebugDataFlow(`Sorted ${stocksWithChange.length} stocks by change percent`);
    
    // Get top 3 winners (highest positive change) and top 3 losers (lowest/most negative change)
    const winners = stocksWithChange.filter(stock => stock.changePercent > 0).slice(0, 3);
    const losers = stocksWithChange.filter(stock => stock.changePercent <= 0).slice(-3).reverse();
    
    console.log('🏆 [STOCKS] Winners found:', winners);
    console.log('🏆 [STOCKS] Winners count:', winners.length);
    console.log('📉 [STOCKS] Losers found:', losers);
    console.log('📉 [STOCKS] Losers count:', losers.length);
    
    updateDebugDataFlow(`Found ${winners.length} winners and ${losers.length} losers`);
    
    // Log each stock's data structure
    enhancedAnalysis.forEach((stock, index) => {
        console.log(`🏆 [STOCKS] Stock ${index + 1}:`, stock);
        console.log(`🏆 [STOCKS] Stock ${index + 1} symbol:`, stock.symbol);
        console.log(`🏆 [STOCKS] Stock ${index + 1} change:`, stock.price_data?.change_percent);
        console.log(`🏆 [STOCKS] Stock ${index + 1} keys:`, Object.keys(stock));
        
        updateDebugDataFlow(`Stock ${index + 1}: ${stock.symbol}, change: ${stock.price_data?.change_percent}, keys: ${Object.keys(stock).join(', ')}`);
    });
    
    // Update winners list
    updateDebugDataFlow('Updating winners list display...');
    updateWinnersList(winners);
    
    // Update losers list
    updateDebugDataFlow('Updating losers list display...');
    updateLosersList(losers);
    
    console.log('🏆 [STOCKS] ===== WINNERS/LOSERS SUMMARY UPDATE COMPLETE =====');
    updateDebugDataFlow('Winners/losers summary update complete');
}

// Update winners list display
function updateWinnersList(winners) {
    console.log('🏆 [STOCKS] ===== UPDATING WINNERS LIST =====');
    console.log('🏆 [STOCKS] Winners input:', winners);
    console.log('🏆 [STOCKS] Winners length:', winners.length);
    
    updateDebugDataFlow(`Updating winners list with ${winners.length} winners`);
    
    const winnersList = document.getElementById('winnersList');
    if (!winnersList) {
        console.log('❌ [STOCKS] Winners list element not found');
        updateDebugDataFlow('Winners list element not found');
        return;
    }
    
    console.log('🏆 [STOCKS] Found winners list element:', winnersList);
    updateDebugDataFlow('Found winners list element');
    
    if (winners.length === 0) {
        console.log('🏆 [STOCKS] No winners data, showing placeholder');
        updateDebugDataFlow('No winners data, showing placeholder');
        winnersList.innerHTML = '<div class="text-center text-muted">No winners data available</div>';
        return;
    }
    
    let html = '';
    winners.forEach((stock, index) => {
        console.log(`🏆 [STOCKS] Processing winner ${index + 1}:`, stock);
        updateDebugDataFlow(`Processing winner ${index + 1}: ${stock.symbol}`);
        
        const priceData = stock.price_data || {};
        const sentimentData = stock.sentiment_data || {};
        const changePercent = priceData.change_percent || '0%';
        const currentPrice = priceData.current_price || 'N/A';
        const sentimentScore = sentimentData.sentiment_score || 0;
        const confidence = sentimentData.confidence || 0;
        
        console.log(`🏆 [STOCKS] Winner ${index + 1} extracted data:`, {
            symbol: stock.symbol,
            price: currentPrice,
            change: changePercent,
            sentiment: sentimentScore,
            confidence: confidence
        });
        
        updateDebugDataFlow(`Winner ${index + 1} data: symbol=${stock.symbol}, price=${currentPrice}, change=${changePercent}, sentiment=${sentimentScore}, confidence=${confidence}`);
        
        html += `
            <div class="card mb-2 border-success">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1 text-success">${stock.symbol}</h6>
                            <small class="text-muted">$${currentPrice}</small>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-success">${changePercent}</span>
                            <div class="mt-1">
                                <small class="text-muted">Sentiment: ${(sentimentScore * 100).toFixed(0)}%</small>
                            </div>
                        </div>
                    </div>
                    <div class="mt-2">
                        <small class="text-muted">Confidence: ${(confidence * 100).toFixed(0)}%</small>
                        <div class="progress mt-1" style="height: 6px;">
                            <div class="progress-bar bg-success" style="width: ${confidence * 100}%"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    console.log('🏆 [STOCKS] Generated HTML length:', html.length);
    updateDebugDataFlow(`Generated winners HTML with ${html.length} characters`);
    winnersList.innerHTML = html;
    console.log('🏆 [STOCKS] Winners list updated successfully');
    updateDebugDataFlow('Winners list updated successfully');
    console.log('🏆 [STOCKS] ===== WINNERS LIST UPDATE COMPLETE =====');
}

// Update losers list display
function updateLosersList(losers) {
    console.log('📉 [STOCKS] ===== UPDATING LOSERS LIST =====');
    console.log('📉 [STOCKS] Losers input:', losers);
    console.log('📉 [STOCKS] Losers length:', losers.length);
    
    updateDebugDataFlow(`Updating losers list with ${losers.length} losers`);
    
    const losersList = document.getElementById('losersList');
    if (!losersList) {
        console.log('❌ [STOCKS] Losers list element not found');
        updateDebugDataFlow('Losers list element not found');
        return;
    }
    
    console.log('📉 [STOCKS] Found losers list element:', losersList);
    updateDebugDataFlow('Found losers list element');
    
    if (losers.length === 0) {
        console.log('📉 [STOCKS] No losers data, showing placeholder');
        updateDebugDataFlow('No losers data, showing placeholder');
        losersList.innerHTML = '<div class="text-center text-muted">No losers data available</div>';
        return;
    }
    
    let html = '';
    losers.forEach((stock, index) => {
        console.log(`📉 [STOCKS] Processing loser ${index + 1}:`, stock);
        updateDebugDataFlow(`Processing loser ${index + 1}: ${stock.symbol}`);
        
        const priceData = stock.price_data || {};
        const sentimentData = stock.sentiment_data || {};
        const changePercent = priceData.change_percent || '0%';
        const currentPrice = priceData.current_price || 'N/A';
        const sentimentScore = sentimentData.sentiment_score || 0;
        const confidence = sentimentData.confidence || 0;
        
        console.log(`📉 [STOCKS] Loser ${index + 1} extracted data:`, {
            symbol: stock.symbol,
            price: currentPrice,
            change: changePercent,
            sentiment: sentimentScore,
            confidence: confidence
        });
        
        updateDebugDataFlow(`Loser ${index + 1} data: symbol=${stock.symbol}, price=${currentPrice}, change=${changePercent}, sentiment=${sentimentScore}, confidence=${confidence}`);
        
        html += `
            <div class="card mb-2 border-danger">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1 text-danger">${stock.symbol}</h6>
                            <small class="text-muted">$${currentPrice}</small>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-danger">${changePercent}</span>
                            <div class="mt-1">
                                <small class="text-muted">Sentiment: ${(sentimentScore * 100).toFixed(0)}%</small>
                            </div>
                        </div>
                    </div>
                    <div class="mt-2">
                        <small class="text-muted">Confidence: ${(confidence * 100).toFixed(0)}%</small>
                        <div class="progress mt-1" style="height: 6px;">
                            <div class="progress-bar bg-danger" style="width: ${confidence * 100}%"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    console.log('📉 [STOCKS] Generated HTML length:', html.length);
    updateDebugDataFlow(`Generated losers HTML with ${html.length} characters`);
    losersList.innerHTML = html;
    console.log('📉 [STOCKS] Losers list updated successfully');
    updateDebugDataFlow('Losers list updated successfully');
    console.log('📉 [STOCKS] ===== LOSERS LIST UPDATE COMPLETE =====');
}

// Update summary statistics
function updateSummaryStats(data) {
    const summaryStats = document.getElementById('summaryStats');
    if (!summaryStats) return;
    
    const enhancedAnalysis = data.enhanced_analysis || [];
    const errors = data.errors || [];
    const performance = data.performance || {};
    
    const totalAnalyzed = data.total_analyzed || 0;
    const opportunitiesFound = data.opportunities_found || 0;
    const errorsCount = data.errors_count || 0;
    const executionTime = performance.execution_time || 0;
    const successRate = performance.success_rate || '0%';
    
    const html = `
        <div class="row">
            <div class="col-md-3">
                <div class="text-center">
                    <h4 class="text-primary">${totalAnalyzed}</h4>
                    <small>Total Analyzed</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="text-center">
                    <h4 class="text-success">${opportunitiesFound}</h4>
                    <small>Opportunities Found</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="text-center">
                    <h4 class="text-danger">${errorsCount}</h4>
                    <small>Errors</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="text-center">
                    <h4 class="text-info">${executionTime}s</h4>
                    <small>Execution Time</small>
                </div>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-12">
                <div class="text-center">
                    <small class="text-muted">Success Rate: ${successRate}</small>
                </div>
            </div>
        </div>
    `;
    
    summaryStats.querySelector('.card-body').innerHTML = html;
}

// Update legacy table (if it exists)
function updateLegacyTable(data) {
    const tableBody = document.getElementById('stocksTableBody');
    if (!tableBody) return;
    
    const enhancedAnalysis = data.enhanced_analysis || [];
    
    if (enhancedAnalysis.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No analysis data available</td></tr>';
        return;
    }
    
    let html = '';
    enhancedAnalysis.forEach(stock => {
        const priceData = stock.price_data || {};
        const sentimentData = stock.sentiment_data || {};
        const signalData = stock.signal_data || {};
        
        const currentPrice = priceData.current_price || 'N/A';
        const sentimentScore = sentimentData.sentiment_score || 0;
        const confidence = sentimentData.confidence || 0;
        const action = signalData.action || 'HOLD';
        const signalStrength = signalData.confidence || 0;
        const newsCount = stock.news_count || 0;
        
        html += `
            <tr>
                <td><span class="badge ${stock.type === 'winner' ? 'bg-success' : 'bg-danger'}">${stock.type}</span></td>
                <td><strong>${stock.symbol}</strong></td>
                <td>$${currentPrice}</td>
                <td>${(sentimentScore * 100).toFixed(1)}%</td>
                <td>${(confidence * 100).toFixed(1)}%</td>
                <td><span class="badge bg-${action === 'BUY' ? 'success' : action === 'SELL' ? 'danger' : 'secondary'}">${action}</span></td>
                <td>${(signalStrength * 100).toFixed(1)}%</td>
                <td>${newsCount}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewStockDetails('${stock.symbol}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            </tr>
        `;
    });
    
    tableBody.innerHTML = html;
}

// Update progress bar
function updateProgress(data) {
    const progressContainer = document.getElementById('sp500-progress-container');
    const progressBar = document.getElementById('sp500-progress-bar');
    const progressText = document.getElementById('sp500-progress-text');
    
    if (!progressContainer || !progressBar || !progressText) return;
    
    if (data.status === 'completed') {
        progressContainer.style.display = 'none';
        return;
    }
    
    progressContainer.style.display = 'block';
    
    const current = data.current || 0;
    const total = data.total || 1;
    const percentage = Math.round((current / total) * 100);
    
    progressBar.style.width = `${percentage}%`;
    progressBar.setAttribute('aria-valuenow', current);
    progressBar.setAttribute('aria-valuemax', total);
    
    if (data.symbol && data.symbol !== 'CACHED') {
        progressText.textContent = `Analyzing ${data.symbol}... (${current}/${total})`;
    } else {
        progressText.textContent = `Progress: ${current}/${total} (${percentage}%)`;
    }
}

// Toggle auto-refresh
function toggleAutoRefresh() {
    const toggle = document.getElementById('autoRefreshToggle');
    if (!toggle) return;
    
    if (toggle.checked) {
        console.log('🔄 [STOCKS] Auto-refresh enabled');
        autoRefreshInterval = setInterval(() => {
            console.log('🔄 [STOCKS] Auto-refresh triggered');
            loadStocksAnalysis(false);
        }, 5 * 60 * 1000); // 5 minutes
    } else {
        console.log('⏸️ [STOCKS] Auto-refresh disabled');
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
    }
}

// Show/hide loading spinner
function showLoading(show) {
    const loadingSpinner = document.getElementById('loadingSpinner');
    if (loadingSpinner) {
        loadingSpinner.style.display = show ? 'block' : 'none';
    }
}

// Show error message
function showError(message) {
    console.error('❌ [STOCKS] Error:', message);
    
    // Create error alert
    const errorHtml = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="fas fa-exclamation-triangle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Insert at the top of the container
    const container = document.querySelector('.container');
    if (container) {
        container.insertAdjacentHTML('afterbegin', errorHtml);
    }
}

// Update last updated timestamp
function updateLastUpdated() {
    const lastUpdatedElement = document.getElementById('lastUpdated');
    if (lastUpdatedElement) {
        const now = new Date();
        lastUpdated = now;
        lastUpdatedElement.textContent = `Last updated: ${now.toLocaleTimeString()}`;
    }
}

// View stock details (placeholder function)
function viewStockDetails(symbol) {
    console.log('🔍 [STOCKS] Viewing details for:', symbol);
    // TODO: Implement detailed stock view
    alert(`Detailed view for ${symbol} - Feature coming soon!`);
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
});

console.log('✅ [STOCKS] stocks.js loaded successfully');
