/* Trading AI Dashboard - Base JavaScript */

// Theme management
function toggleTheme() {
    try {
        if (window.frontendLogger && typeof window.frontendLogger.logUserAction === 'function') {
            window.frontendLogger.logUserAction('Theme Toggle Clicked');
        }
        
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        const icon = document.getElementById('themeIcon');
        if (icon) {
            if (newTheme === 'dark') {
                icon.className = 'fas fa-moon';
            } else {
                icon.className = 'fas fa-sun';
            }
        }
        
        if (window.frontendLogger && typeof window.frontendLogger.logUserAction === 'function') {
            window.frontendLogger.logUserAction('Theme Changed', null, { from: currentTheme, to: newTheme });
        }
    } catch (e) {
        console.error('Error in toggleTheme:', e);
    }
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
    frontendLogger.logUserAction('Loading Started', elementId);
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'block';
    }
}

function hideLoading(elementId) {
    frontendLogger.logUserAction('Loading Ended', elementId);
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}

// Show alert messages
function showAlert(message, type) {
    frontendLogger.logUserAction('Alert Shown', null, { message, type });
    
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
    frontendLogger.info('Socket.IO connected', 'websocket');
});

socket.on('disconnect', function() {
    frontendLogger.warn('Socket.IO disconnected', 'websocket');
});

socket.on('analysis_progress', function(data) {
    frontendLogger.debug('Analysis Progress Update: ' + JSON.stringify(data), 'websocket');
    
    const loadingText = document.getElementById('loadingText');
    if (loadingText && data.message) {
        loadingText.textContent = data.message;
    }
});

// Enhanced error handling for debugging
function debugLog(message, data = null) {
    frontendLogger.debug(message + (data ? ': ' + JSON.stringify(data) : ''), 'debug');
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', function() {
    try {
        initializeTheme();
        if (window.frontendLogger && typeof window.frontendLogger.info === 'function') {
            window.frontendLogger.info('Page Loaded: ' + window.location.href, 'navigation');
        } else {
            console.log('[' + new Date().toISOString() + '] [INFO] [navigation] Page Loaded: ' + window.location.href);
        }
    } catch (e) {
        console.error('Error in DOMContentLoaded handler:', e);
    }
});

// Safe logger function that won't break if frontendLogger isn't available
function safeLogError(message, category) {
    try {
        if (window.frontendLogger && typeof window.frontendLogger.error === 'function') {
            try {
                window.frontendLogger.error(message, category);
            } catch (logError) {
                console.error('Error logging with frontendLogger:', logError);
                console.error('[' + new Date().toISOString() + '] [ERROR] [' + (category || 'system') + '] ' + message);
            }
        } else {
            console.error('[' + new Date().toISOString() + '] [ERROR] [' + (category || 'system') + '] ' + message);
        }
    } catch (e) {
        console.error('Error in safeLogError:', e);
    }
}

// Log any unhandled errors
window.addEventListener('error', function(event) {
    safeLogError('JavaScript Error: ' + event.message + ' at ' + event.filename + ':' + event.lineno, 'error');
});

// Global error handler for async operations
window.addEventListener('unhandledrejection', function(event) {
    safeLogError('Unhandled Promise Rejection: ' + (event.reason || 'Unknown reason'), 'error');
}); 