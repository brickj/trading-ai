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
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    setupErrorHandlers() {
        // Global error handler
        window.addEventListener('error', (event) => {
            this.error('JavaScript Error', {
                message: event.error?.message || event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error?.stack,
                url: window.location.href
            });
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            this.error('Unhandled Promise Rejection', {
                reason: event.reason,
                promise: event.promise,
                url: window.location.href
            });
        });
    }

    startPerformanceMonitoring() {
        // Monitor page load performance
        window.addEventListener('load', () => {
            setTimeout(() => {
                const perfData = performance.getEntriesByType('navigation')[0];
                if (perfData) {
                    this.performance('Page Load', {
                        domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                        loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
                        totalTime: perfData.loadEventEnd - perfData.fetchStart
                    });
                }
            }, 0);
        });
    }

    formatLog(level, category, message, data = null) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            level: level,
            category: category,
            message: message,
            data: data,
            url: window.location.href,
            userAgent: navigator.userAgent,
            sessionId: this.sessionId
        };

        // Add to local storage
        this.logs.push(logEntry);
        if (this.logs.length > this.maxLogSize) {
            this.logs.shift(); // Remove oldest log
        }

        // Console output for development
        const consoleMethod = level.toLowerCase();
        if (console[consoleMethod]) {
            console[consoleMethod](`[${level}] ${category}: ${message}`, data || '');
        }

        return logEntry;
    }

    // Main logging methods
    debug(message, data = null, category = 'GENERAL') {
        if (this.shouldLog('DEBUG')) {
            const log = this.formatLog('DEBUG', category, message, data);
            this.sendToBackend(log);
        }
    }

    info(message, data = null, category = 'GENERAL') {
        if (this.shouldLog('INFO')) {
            const log = this.formatLog('INFO', category, message, data);
            this.sendToBackend(log);
        }
    }

    warn(message, data = null, category = 'GENERAL') {
        if (this.shouldLog('WARN')) {
            const log = this.formatLog('WARN', category, message, data);
            this.sendToBackend(log);
        }
    }

    error(message, data = null, category = 'ERROR') {
        if (this.shouldLog('ERROR')) {
            const log = this.formatLog('ERROR', category, message, data);
            this.sendToBackend(log);
        }
    }

    // Specialized logging methods
    apiCall(method, url, params = null, responseStatus = null, responseTime = null, error = null) {
        const logData = {
            method: method,
            url: url,
            params: params,
            responseStatus: responseStatus,
            responseTime: responseTime,
            error: error
        };

        const status = error ? 'FAILED' : 'SUCCESS';
        const message = `${status} | ${method} ${url} | Status: ${responseStatus} | Time: ${responseTime}ms`;
        
        if (error) {
            this.error(message, logData, 'API_CALL');
        } else {
            this.info(message, logData, 'API_CALL');
        }
    }

    userAction(action, details = null) {
        this.info(`User Action: ${action}`, details, 'USER_ACTION');
    }

    performance(operation, metrics) {
        this.info(`Performance: ${operation}`, metrics, 'PERFORMANCE');
    }

    formSubmission(formId, data = null, result = null) {
        this.info(`Form Submitted: ${formId}`, { data, result }, 'FORM');
    }

    buttonClick(buttonId, context = null) {
        this.info(`Button Clicked: ${buttonId}`, context, 'USER_INTERACTION');
    }

    pageView(page, params = null) {
        this.info(`Page View: ${page}`, params, 'NAVIGATION');
    }

    shouldLog(level) {
        const levels = ['DEBUG', 'INFO', 'WARN', 'ERROR'];
        const currentLevelIndex = levels.indexOf(this.logLevel);
        const logLevelIndex = levels.indexOf(level);
        return logLevelIndex >= currentLevelIndex;
    }

    async sendToBackend(logEntry) {
        // Only send WARN and ERROR logs to backend to avoid spam
        if (!['WARN', 'ERROR'].includes(logEntry.level)) {
            return;
        }

        try {
            const response = await fetch('/api/frontend_logs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(logEntry),
                // Don't wait for response to avoid blocking
                keepalive: true
            });
            
            if (!response.ok) {
                console.warn('Failed to send log to backend:', response.status);
            }
        } catch (error) {
            console.warn('Error sending log to backend:', error);
        }
    }

    // Get all logs for debugging
    getAllLogs() {
        return this.logs;
    }

    // Export logs as JSON
    exportLogs() {
        const logsJson = JSON.stringify(this.logs, null, 2);
        const blob = new Blob([logsJson], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `trading_ai_logs_${new Date().toISOString().slice(0, 19)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Clear logs
    clearLogs() {
        this.logs = [];
        this.info('Logs cleared', null, 'SYSTEM');
    }

    // Set log level
    setLogLevel(level) {
        if (['DEBUG', 'INFO', 'WARN', 'ERROR'].includes(level)) {
            this.logLevel = level;
            this.info(`Log level set to ${level}`, null, 'SYSTEM');
        }
    }
}

// Enhanced fetch wrapper with automatic logging
class LoggedFetch {
    constructor(logger) {
        this.logger = logger;
    }

    async fetch(url, options = {}) {
        const startTime = performance.now();
        const method = options.method || 'GET';
        
        this.logger.debug(`Starting ${method} request to ${url}`, options, 'API_CALL');
        
        try {
            const response = await fetch(url, options);
            const endTime = performance.now();
            const responseTime = Math.round(endTime - startTime);
            
            this.logger.apiCall(method, url, options.body, response.status, responseTime);
            
            return response;
        } catch (error) {
            const endTime = performance.now();
            const responseTime = Math.round(endTime - startTime);
            
            this.logger.apiCall(method, url, options.body, null, responseTime, error.message);
            throw error;
        }
    }
}

// Global logger instance
const frontendLogger = new FrontendLogger();
const loggedFetch = new LoggedFetch(frontendLogger);

// Convenience functions
window.log = {
    debug: (message, data, category) => frontendLogger.debug(message, data, category),
    info: (message, data, category) => frontendLogger.info(message, data, category),
    warn: (message, data, category) => frontendLogger.warn(message, data, category),
    error: (message, data, category) => frontendLogger.error(message, data, category),
    apiCall: (method, url, params, status, time, error) => frontendLogger.apiCall(method, url, params, status, time, error),
    userAction: (action, details) => frontendLogger.userAction(action, details),
    performance: (operation, metrics) => frontendLogger.performance(operation, metrics),
    formSubmission: (formId, data, result) => frontendLogger.formSubmission(formId, data, result),
    buttonClick: (buttonId, context) => frontendLogger.buttonClick(buttonId, context),
    pageView: (page, params) => frontendLogger.pageView(page, params),
    getAllLogs: () => frontendLogger.getAllLogs(),
    exportLogs: () => frontendLogger.exportLogs(),
    clearLogs: () => frontendLogger.clearLogs(),
    setLogLevel: (level) => frontendLogger.setLogLevel(level)
};

// Replace global fetch with logged version for automatic API logging
window.originalFetch = window.fetch;
window.fetch = (url, options) => loggedFetch.fetch(url, options);

// Log page load
document.addEventListener('DOMContentLoaded', () => {
    frontendLogger.pageView(window.location.pathname, {
        referrer: document.referrer,
        timestamp: new Date().toISOString()
    });
});

console.log('🔥 Frontend Logger initialized!');
console.log('Usage: log.info("message", data, "category")');
console.log('Export logs: log.exportLogs()');
console.log('View all logs: log.getAllLogs()'); 