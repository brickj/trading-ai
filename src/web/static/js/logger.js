/**
 * Frontend logging utility for Trading AI application
 * Captures JavaScript errors, API calls, user actions, and performance metrics
 */

class FrontendLogger {
    constructor() {
        this.logLevel = 'DEBUG'; // DEBUG, INFO, WARN, ERROR
        this.maxLogSize = 1000; // Maximum number of logs to keep in memory
        this.logs = [];
        this.sessionId = this.generateSessionId();
        this.setupErrorHandlers();
        this.startPerformanceMonitoring();
        this.backendLoggingEnabled = true; // RE-ENABLED backend logging
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    setupErrorHandlers() {
        // Global error handler
        window.addEventListener('error', (event) => {
            this.error('JavaScript Error: ' + event.message + ' at ' + event.filename + ':' + event.lineno);
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            this.error('Unhandled Promise Rejection: ' + event.reason);
        });
    }

    startPerformanceMonitoring() {
        // Monitor page load performance
        if (window.performance && window.performance.timing) {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const perfData = window.performance.timing;
                    const loadTime = perfData.loadEventEnd - perfData.navigationStart;
                    this.info(`Page load time: ${loadTime}ms`);
                }, 0);
            });
        }
    }

    shouldLog(level) {
        const levels = ['DEBUG', 'INFO', 'WARN', 'ERROR'];
        return levels.indexOf(level) >= levels.indexOf(this.logLevel);
    }

    log(level, message, category = 'general') {
        if (!this.shouldLog(level)) return;

        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            level,
            message: String(message),
            category,
            sessionId: this.sessionId,
            url: window.location.href,
            userAgent: navigator.userAgent
        };

        // Add to local storage
        this.logs.push(logEntry);
        if (this.logs.length > this.maxLogSize) {
            this.logs.shift(); // Remove oldest log
        }

        // Console output
        const consoleMethod = level.toLowerCase() === 'warn' ? 'warn' : 
                            level.toLowerCase() === 'error' ? 'error' : 'log';
        console[consoleMethod](`[${timestamp}] [${level}] [${category}] ${message}`);

        // Send to backend with improved error handling
        if (this.backendLoggingEnabled) {
            this.sendToBackend(logEntry);
        }
    }

    sendToBackend(logEntry) {
        // Use a timeout to prevent blocking the main thread
        setTimeout(() => {
            fetch('/api/frontend_logs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                credentials: 'same-origin',
                body: JSON.stringify(logEntry)
            }).catch(error => {
                // Silently fail to prevent infinite loops
                // Only log to console, don't call this.error() to avoid recursion
                console.warn('Failed to send log to backend:', error.message);
            });
        }, 0);
    }

    debug(message, category = 'general') {
        this.log('DEBUG', message, category);
    }

    info(message, category = 'general') {
        this.log('INFO', message, category);
    }

    warn(message, category = 'general') {
        this.log('WARN', message, category);
    }

    error(message, category = 'general') {
        this.log('ERROR', message, category);
    }

    // Specialized logging methods
    logApiCall(method, url, status, responseTime, data = null) {
        const message = `API ${method} ${url} - Status: ${status}, Time: ${responseTime}ms`;
        this.info(message, 'api');
        
        if (status >= 400) {
            this.error(`API_CALL_FAILED: ${message}`, 'api');
        }
        
        if (data && data.error) {
            this.error(`API_ERROR: ${data.error}`, 'api');
        }
    }

    logUserAction(action, element = null, data = null) {
        let message = `User Action: ${action}`;
        if (element) {
            message += ` on ${element}`;
        }
        if (data) {
            message += ` with data: ${JSON.stringify(data)}`;
        }
        this.info(message, 'user_action');
    }

    logPerformance(operation, duration, data = null) {
        let message = `Performance: ${operation} took ${duration}ms`;
        if (data) {
            message += ` - ${JSON.stringify(data)}`;
        }
        this.info(message, 'performance');
    }

    // Get logs for debugging
    getLogs(level = null, category = null) {
        let filteredLogs = this.logs;
        
        if (level) {
            filteredLogs = filteredLogs.filter(log => log.level === level);
        }
        
        if (category) {
            filteredLogs = filteredLogs.filter(log => log.category === category);
        }
        
        return filteredLogs;
    }

    // Clear logs
    clearLogs() {
        this.logs = [];
        this.info('Logs cleared', 'system');
    }

    // Export logs as JSON
    exportLogs() {
        const dataStr = JSON.stringify(this.logs, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `frontend_logs_${this.sessionId}.json`;
        link.click();
        URL.revokeObjectURL(url);
    }
}

// Create global logger instance
const frontendLogger = new FrontendLogger();

// Make it available globally
window.frontendLogger = frontendLogger;

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = frontendLogger;
}

// Add logging for page events
document.addEventListener('DOMContentLoaded', () => {
    frontendLogger.info('DOM Content Loaded', 'system');
});

window.addEventListener('load', () => {
    frontendLogger.info('Page fully loaded', 'system');
});

window.addEventListener('beforeunload', () => {
    frontendLogger.info('Page unloading', 'system');
});

// Add logging for visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        frontendLogger.info('Page hidden', 'system');
    } else {
        frontendLogger.info('Page visible', 'system');
    }
}); 