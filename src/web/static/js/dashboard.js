// Dashboard Analysis JavaScript
// Provides standard and enhanced analysis functions used on the main dashboard

// Debug panel helper exposed globally so other modules can log
window.debugPanel = {
    setRequest: function(url, body) {
        const reqStatus = document.getElementById('requestStatus');
        const reqData = document.getElementById('requestData');
        if (reqStatus) {
            reqStatus.innerHTML = `<small>POST ${url}</small>`;
        }
        if (reqData) {
            reqData.textContent = body ? JSON.stringify(body, null, 2) : 'No request data';
        }
    },
    setResponse: function(status, data) {
        const resStatus = document.getElementById('responseStatus');
        const resData = document.getElementById('responseData');
        if (resStatus) {
            resStatus.innerHTML = `<small>Status: ${status}</small>`;
        }
        if (resData) {
            resData.textContent = data ? JSON.stringify(data, null, 2) : 'No response data';
        }
    },
    setError: function(message) {
        const resStatus = document.getElementById('responseStatus');
        if (resStatus) {
            resStatus.innerHTML = `<small class="text-danger">${message}</small>`;
        }
    },
    clear: function() {
        const reqStatus = document.getElementById('requestStatus');
        const reqData = document.getElementById('requestData');
        const resStatus = document.getElementById('responseStatus');
        const resData = document.getElementById('responseData');
        if (reqStatus) reqStatus.innerHTML = '<small>No request made yet</small>';
        if (reqData) reqData.textContent = 'No request data';
        if (resStatus) resStatus.innerHTML = '<small>No response received yet</small>';
        if (resData) resData.textContent = 'No response data';
    }
};

// Utility to show/hide How It Works card
function toggleHowItWorks() {
    const card = document.getElementById('howItWorksCard');
    if (!card) return;
    card.style.display = (card.style.display === 'none' || card.style.display === '') ? 'block' : 'none';
}

// Debug panel helpers
function toggleDebugPanel() {
    const body = document.getElementById('debugPanelBody');
    if (!body) return;
    body.style.display = body.style.display === 'none' ? 'block' : 'none';
}

function clearDebugPanel() {
    if (window.debugPanel) {
        window.debugPanel.clear();
    }
}

function copyToClipboard(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const text = el.innerText || el.textContent;
    navigator.clipboard.writeText(text).then(() => {
        showAlert('Copied to clipboard', 'success');
    }).catch(err => {
        showAlert('Copy failed: ' + err, 'danger');
    });
}

// Progress helpers for enhanced analysis
function updateProgress(percent, text) {
    const bar = document.getElementById('progressBar');
    const progressDiv = document.getElementById('analysisProgress');
    const progressText = document.getElementById('progressText');
    if (progressDiv) progressDiv.style.display = 'block';
    if (bar) bar.style.width = percent + '%';
    if (progressText) {
        progressText.style.display = 'block';
        progressText.innerHTML = `<small class="text-muted">${text}</small>`;
    }
}

function resetProgress() {
    const bar = document.getElementById('progressBar');
    const progressDiv = document.getElementById('analysisProgress');
    const progressText = document.getElementById('progressText');
    if (bar) bar.style.width = '0%';
    if (progressDiv) progressDiv.style.display = 'none';
    if (progressText) progressText.style.display = 'none';
}

function setAnalysisType(type) {
    const badge = document.getElementById('analysisTypeBadge');
    if (badge) {
        badge.textContent = type;
        badge.style.display = 'inline-block';
    }
}

function displayResults(data) {
    const section = document.getElementById('resultsSection');
    if (!section) return;
    section.style.display = 'block';
    section.innerHTML = `<div class="col-12"><pre class="bg-light p-3 border rounded">${JSON.stringify(data, null, 2)}</pre></div>`;
}

async function doStandardAnalysis() {
    const symbolInput = document.getElementById('stockSymbol');
    const symbol = symbolInput ? symbolInput.value.trim().toUpperCase() : '';
    if (!symbol) {
        showAlert('Please enter a stock symbol', 'warning');
        return;
    }
    setAnalysisType('Standard');
    window.debugPanel.clear();
    updateProgress(10, 'Submitting standard analysis request...');

    // Button loading state
    const content = document.getElementById('standardBtnContent');
    const loading = document.getElementById('standardBtnLoading');
    const enhancedBtn = document.getElementById('enhancedAnalysisBtn');
    if (content) content.style.display = 'none';
    if (loading) loading.style.display = 'inline';
    if (enhancedBtn) enhancedBtn.disabled = true;
    showLoading('analysisLoading');

    const url = '/api/analyze_stock';
    const body = { symbol: symbol };
    window.debugPanel.setRequest(url, body);

    try {
        const resp = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await resp.json();
        window.debugPanel.setResponse(resp.status, data);
        if (data.status === 'success') {
            displayResults(data.data);
            updateProgress(100, 'Analysis complete');
        } else {
            showAlert(data.error || 'Analysis failed', 'danger');
        }
    } catch (err) {
        window.debugPanel.setError(err.message);
        showAlert('Error performing analysis: ' + err.message, 'danger');
    } finally {
        hideLoading('analysisLoading');
        resetProgress();
        if (content) content.style.display = 'inline';
        if (loading) loading.style.display = 'none';
        if (enhancedBtn) enhancedBtn.disabled = false;
    }
}

async function doEnhancedAnalysis() {
    const symbolInput = document.getElementById('stockSymbol');
    const symbol = symbolInput ? symbolInput.value.trim().toUpperCase() : '';
    if (!symbol) {
        showAlert('Please enter a stock symbol', 'warning');
        return;
    }
    setAnalysisType('Enhanced');
    window.debugPanel.clear();
    updateProgress(5, 'Starting enhanced analysis...');

    const content = document.getElementById('enhancedBtnContent');
    const loading = document.getElementById('enhancedBtnLoading');
    const standardBtn = document.getElementById('standardAnalysisBtn');
    if (content) content.style.display = 'none';
    if (loading) loading.style.display = 'inline';
    if (standardBtn) standardBtn.disabled = true;
    showLoading('analysisLoading');

    const url = '/api/enhanced_analysis';
    const body = { symbol: symbol };
    window.debugPanel.setRequest(url, body);

    try {
        // simulate progress updates
        updateProgress(25, 'Fetching data...');
        const resp = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        updateProgress(75, 'Processing results...');
        const data = await resp.json();
        window.debugPanel.setResponse(resp.status, data);
        if (data.status === 'success') {
            displayResults(data.data);
            updateProgress(100, 'Analysis complete');
        } else {
            showAlert(data.error || 'Analysis failed', 'danger');
        }
    } catch (err) {
        window.debugPanel.setError(err.message);
        showAlert('Error performing analysis: ' + err.message, 'danger');
    } finally {
        hideLoading('analysisLoading');
        setTimeout(resetProgress, 500); // allow user to see 100% before hiding
        if (content) content.style.display = 'inline';
        if (loading) loading.style.display = 'none';
        if (standardBtn) standardBtn.disabled = false;
    }
}

// Expose functions globally for inline event handlers
window.doStandardAnalysis = doStandardAnalysis;
window.doEnhancedAnalysis = doEnhancedAnalysis;
window.toggleHowItWorks = toggleHowItWorks;
window.toggleDebugPanel = toggleDebugPanel;
window.clearDebugPanel = clearDebugPanel;
window.copyToClipboard = copyToClipboard;
