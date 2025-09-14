/**
 * Frontend logging utility for Trading AI application
 * Captures JavaScript errors, API calls, user actions, and performance metrics
 * 
 * Uses function-based approach for maximum browser compatibility
 */

// Main logger function
function FrontendLogger() {
    // Public properties
    this.logLevel = 'DEBUG'; // DEBUG, INFO, WARN, ERROR
    this.maxLogSize = 1000; // Maximum number of logs to keep in memory
    this.logs = [];
    this.sessionId = this.generateSessionId();
    this.backendLoggingEnabled = true; // Backend logging status
    
    // Initialize
    this.setupErrorHandlers();
    this.startPerformanceMonitoring();
}

// Add methods to the prototype
FrontendLogger.prototype = {
    constructor: FrontendLogger,
    
    generateSessionId: function() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    },
    
    setupErrorHandlers: function() {
        var self = this;
        
        // Global error handler
        window.addEventListener('error', function(event) {
            self.error('JavaScript Error: ' + event.message + ' at ' + event.filename + ':' + event.lineno);
            return false; // Don't suppress default error handling
        });
        
        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', function(event) {
            var reason = event.reason || 'Unknown reason';
            var reasonStr = (typeof reason === 'object' && reason.message) ? reason.message : String(reason);
            self.error('Unhandled Promise Rejection: ' + reasonStr);
        });
    },
    
    startPerformanceMonitoring: function() {
        var self = this;
        
        // Monitor page load performance
        if (window.performance && window.performance.timing) {
            window.addEventListener('load', function() {
                setTimeout(function() {
                    try {
                        var perfData = window.performance.timing;
                        var loadTime = perfData.loadEventEnd - perfData.navigationStart;
                        self.info('Page load time: ' + loadTime + 'ms');
                    } catch (e) {
                        console.warn('Performance monitoring error:', e);
                    }
                }, 0);
            });
        }
    },
    
    shouldLog: function(level) {
        var levels = ['DEBUG', 'INFO', 'WARN', 'ERROR'];
        return levels.indexOf(level) >= levels.indexOf(this.logLevel);
    },
    
    log: function(level, message, category) {
        // Set default category if not provided
        category = category || 'general';
        
        // Check if we should log this message
        if (!this.shouldLog(level)) {
            return;
        }
        
        // Create log entry
        var timestamp = new Date().toISOString();
        var logEntry = {
            timestamp: timestamp,
            level: level,
            message: String(message),
            category: category,
            sessionId: this.sessionId,
            url: window.location.href,
            userAgent: navigator.userAgent
        };
        
        // Add to logs array
        this.logs.push(logEntry);
        
        // Remove old logs if we've reached max size
        if (this.logs.length > this.maxLogSize) {
            this.logs.shift();
        }
        
        // Log to console
        try {
            var consoleMethod = 'log';
            if (level === 'WARN') {
                consoleMethod = 'warn';
            } else if (level === 'ERROR') {
                consoleMethod = 'error';
            }
            
            console[consoleMethod]('[' + timestamp + '] [' + level + '] [' + category + '] ' + message);
        } catch (e) {
            // Fallback if console method doesn't exist
            console.log('[' + timestamp + '] [' + level + '] [' + category + '] ' + message);
        }
        
        // Send to backend if enabled
        if (this.backendLoggingEnabled) {
            this.sendToBackend(logEntry);
        }
    },
    
    sendToBackend: function(logEntry) {
        var self = this;
        
        // Use timeout to prevent blocking
        setTimeout(function() {
            try {
                fetch('/api/frontend_logs', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify(logEntry)
                }).catch(function(error) {
                    // Silently fail to prevent infinite loops
                    console.warn('Failed to send log to backend:', error.message);
                });
            } catch (e) {
                console.warn('Error in sendToBackend:', e);
            }
        }, 0);
    },
    
    // Convenience methods for different log levels
    debug: function(message, category) {
        this.log('DEBUG', message, category);
    },
    
    info: function(message, category) {
        this.log('INFO', message, category);
    },
    
    warn: function(message, category) {
        this.log('WARN', message, category);
    },
    
    error: function(message, category) {
        this.log('ERROR', message, category);
    },
    
    // Specialized logging methods
    logApiCall: function(method, url, status, responseTime, data) {
        var message = 'API ' + method + ' ' + url + ' - Status: ' + status + ', Time: ' + responseTime + 'ms';
        this.info(message, 'api');
        
        if (status >= 400) {
            this.error('API_CALL_FAILED: ' + message, 'api');
        }
        
        if (data && data.error) {
            this.error('API_ERROR: ' + data.error, 'api');
        }
    },
    
    logUserAction: function(action, element, data) {
        var message = 'User Action: ' + action;
        if (element) {
            message += ' on ' + element;
        }
        if (data) {
            message += ' with data: ' + JSON.stringify(data);
        }
        this.info(message, 'user_action');
    },
    
    logPerformance: function(operation, duration, data) {
        var message = 'Performance: ' + operation + ' took ' + duration + 'ms';
        if (data) {
            message += ' - ' + JSON.stringify(data);
        }
        this.info(message, 'performance');
    },
    
    // Get logs with optional filtering
    getLogs: function(level, category) {
        var filteredLogs = this.logs;
        
        if (level) {
            filteredLogs = filteredLogs.filter(function(log) {
                return log.level === level;
            });
        }
        
        if (category) {
            filteredLogs = filteredLogs.filter(function(log) {
                return log.category === category;
            });
        }
        
        return filteredLogs;
    },
    
    // Clear all logs
    clearLogs: function() {
        this.logs = [];
        this.info('Logs cleared', 'system');
    },
    
    // Export logs as JSON file
    exportLogs: function() {
        try {
            var dataStr = JSON.stringify(this.logs, null, 2);
            var dataBlob = new Blob([dataStr], {type: 'application/json'});
            var url = URL.createObjectURL(dataBlob);
            var link = document.createElement('a');
            link.href = url;
            link.download = 'frontend_logs_' + this.sessionId + '.json';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        } catch (e) {
            this.error('Failed to export logs: ' + e.message, 'system');
        }
    }
};

// Create global logger instance immediately
try {
    // Create logger and expose globally
    window.frontendLogger = new FrontendLogger();
    var frontendLogger = window.frontendLogger;

    // Log that logger is initialized
    frontendLogger.info('Logger initialized', 'system');

    // Log DOM ready event
    document.addEventListener('DOMContentLoaded', function() {
        frontendLogger.info('DOM Content Loaded', 'system');
    });

    // Set up window load event
    window.addEventListener('load', function() {
        frontendLogger.info('Page fully loaded', 'system');
    });

    // Set up beforeunload event
    window.addEventListener('beforeunload', function() {
        frontendLogger.info('Page unloading', 'system');
    });

    // Set up visibility change events
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            frontendLogger.info('Page hidden', 'system');
        } else {
            frontendLogger.info('Page visible', 'system');
        }
    });

} catch (e) {
    // Fallback error handling if logger fails to initialize
    console.error('Failed to initialize logger:', e);
}

// Export for Node.js/CommonJS if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FrontendLogger;
} 