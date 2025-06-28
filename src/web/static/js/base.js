/* Trading AI Dashboard - Base JavaScript */

// Theme management
function toggleTheme() {
    log.userAction('Theme Toggle Clicked');
    
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const icon = document.getElementById('themeIcon');
    if (newTheme === 'dark') {
        icon.className = 'fas fa-moon';
    } else {
        icon.className = 'fas fa-sun';
    }
    
    log.userAction('Theme Changed', { from: currentTheme, to: newTheme });
}

// Initialize theme from localStorage
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const html = document.documentElement;
    html.setAttribute('data-theme', savedTheme);
    
    const icon = document.getElementById('themeIcon');
    if (savedTheme === 'dark') {
        icon.className = 'fas fa-moon';
    } else {
        icon.className = 'fas fa-sun';
    }
}

// Format currency
function formatCurrency(amount) {
    if (typeof amount !== 'number') return 'N/A';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Format percentage
function formatPercentage(value) {
    if (typeof value !== 'number') return 'N/A';
    return (value * 100).toFixed(2) + '%';
}

// Get sentiment class for styling
function getSentimentClass(score) {
    if (score > 0.3) return 'text-success';
    if (score < -0.3) return 'text-danger';
    return 'text-warning';
}

// Get sentiment strength
function getSentimentStrength(score) {
    const absScore = Math.abs(score);
    if (absScore > 0.7) {
        return { text: 'Very Strong', badge: '<span class="badge bg-success">Very Strong</span>' };
    } else if (absScore > 0.5) {
        return { text: 'Strong', badge: '<span class="badge bg-info">Strong</span>' };
    } else if (absScore > 0.3) {
        return { text: 'Moderate', badge: '<span class="badge bg-warning">Moderate</span>' };
    } else if (absScore > 0.1) {
        return { text: 'Weak', badge: '<span class="badge bg-secondary">Weak</span>' };
    } else {
        return { text: 'Neutral', badge: '<span class="badge bg-light text-dark">Neutral</span>' };
    }
}

// Get signal class for styling
function getSignalClass(action) {
    switch (action) {
        case 'BUY': return 'bg-success text-white';
        case 'SELL': return 'bg-danger text-white';
        case 'HOLD': return 'bg-warning text-dark';
        default: return 'bg-secondary text-white';
    }
}

// Show/hide loading spinner
function showLoading(elementId) {
    log.userAction('Loading Started', { element: elementId });
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'block';
    }
}

function hideLoading(elementId) {
    log.userAction('Loading Ended', { element: elementId });
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}

// Show alert messages
function showAlert(message, type) {
    log.userAction('Alert Shown', { message, type });
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Socket.IO connection with logging
const socket = io();

socket.on('connect', function() {
    log.info('Socket.IO connected', { socketId: socket.id }, 'WEBSOCKET');
});

socket.on('disconnect', function() {
    log.warn('Socket.IO disconnected', null, 'WEBSOCKET');
});

socket.on('analysis_progress', function(data) {
    log.debug('Analysis Progress Update', data, 'WEBSOCKET');
    
    const loadingText = document.getElementById('loadingText');
    if (loadingText && data.message) {
        loadingText.textContent = data.message;
    }
});

// Enhanced error handling for debugging
function debugLog(message, data = null) {
    log.debug(message, data, 'DEBUG');
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    log.info('Page Loaded', { url: window.location.href }, 'NAVIGATION');
});

// Log any unhandled errors
window.addEventListener('error', function(event) {
    log.error('JavaScript Error', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack
    }, 'ERROR');
});

// Global error handler for async operations
window.addEventListener('unhandledrejection', function(event) {
    log.error('Unhandled Promise Rejection', {
        reason: event.reason,
        promise: event.promise
    }, 'ERROR');
}); 