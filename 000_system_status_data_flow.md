# 📊 System Status Page Data Flow & Architecture Guide

## 📁 **Files Involved in the System Status Page**

### **Backend (Python) Files:**
- **`src/web/app.py`** - Main Flask application with system status routes and API endpoints
- **`src/utils/api_tracker.py`** - API usage tracking and rate limiting functionality
- **`src/core/database.py`** - Database operations and statistics
- **`src/core/cache.py`** - Cache management and statistics
- **`src/core/telegram_alerts.py`** - Telegram notification system
- **`src/data/data_fetcher.py`** - External API integrations for testing

### **Frontend Files:**
- **`src/web/templates/system_status.html`** - Main page template with comprehensive monitoring UI
- **`src/web/static/css/styles.css`** - Styling for the system status page
- **`src/web/static/js/base.js`** - Common JavaScript functions (alerts, loading spinners)

### **Configuration Files:**
- **`src/core/config.py`** - Application configuration settings
- **`src/core/logger.py`** - Logging system configuration

---

## 🔄 **Data Flow: From System Monitoring to Display**

### **Data Sources:**
1. **System Metrics** - CPU, memory, disk usage via `psutil`
2. **Database Statistics** - Connection status, table counts, performance metrics
3. **API Usage Tracking** - Rate limiting, circuit breaker status, request counts
4. **Application Configuration** - Telegram settings, cache status, debug mode
5. **Job Scheduler** - Background job schedules and execution status
6. **Watchlist Configuration** - Stock and crypto watchlist management

### **Data Journey:**
```
System APIs → Monitoring Functions → Database Queries → Flask API → JavaScript → Real-time UI Display
```

---

## ⏰ **Loading Strategy: Real-time Monitoring with Auto-refresh**

The System Status page uses **real-time monitoring** with multiple loading strategies:

1. **Page loads** with comprehensive system overview and loading indicators
2. **JavaScript automatically triggers** API calls to load current system metrics
3. **Auto-refresh functionality** updates data every 30 seconds
4. **Manual refresh** allows users to trigger immediate status updates
5. **Interactive controls** for configuration changes and system management

---

## 🏗️ **Step-by-Step Architecture**

### **Step 1: Route/Controller**
```python
# src/web/app.py line 2404
@app.route("/system_status")
def system_status_page():
    """System status and Go services monitoring page"""
    return render_template(
        "system_status.html", 
        historical_lookback_days=Config.HISTORICAL_LOOKBACK_DAYS
    )
```
**What happens:** User visits `/system_status` → Flask serves the HTML template

### **Step 2: Template Rendering**
```html
<!-- src/web/templates/system_status.html -->
<div id="systemStatusSection">
    <div class="row">
        <div class="col-12">
            <h1 class="mb-4">
                <i class="fas fa-server"></i> System Status & Performance
            </h1>
            <p class="lead">Monitor system performance and service health</p>
        </div>
    </div>

    <!-- Performance Metrics Section -->
    <div class="row">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-chart-bar"></i> Performance Metrics</h5>
                </div>
                <div class="card-body">
                    <div id="systemMetrics">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="card border-primary mb-3">
                                    <div class="card-body text-center">
                                        <h4 class="text-primary" id="cpuUsage">N/A</h4>
                                        <small>CPU Usage</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card border-success mb-3">
                                    <div class="card-body text-center">
                                        <h4 class="text-success" id="memoryUsage">N/A</h4>
                                        <small>Memory Usage</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Database Status Section -->
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-database"></i> Database Status</h5>
                </div>
                <div class="card-body">
                    <div id="databaseStatus">
                        <!-- Database metrics cards -->
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- System Overview Section -->
    <div class="row mt-4">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-info-circle"></i> System Overview</h5>
                </div>
                <div class="card-body" id="serviceStatus">
                    <!-- Service status cards -->
                </div>
            </div>
        </div>
    </div>

    <!-- Configuration and Settings Sections -->
    <div class="row mt-4">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-toggle-on"></i> Configuration</h5>
                </div>
                <div class="card-body">
                    <!-- System configuration info -->
                </div>
            </div>
        </div>
        
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-cog"></i> User Settings</h5>
                </div>
                <div class="card-body">
                    <!-- AI provider selection, telegram settings, cache management -->
                </div>
            </div>
        </div>
    </div>

    <!-- API Status Section -->
    <div class="row mt-4">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-plug"></i> API Status</h5>
                </div>
                <div class="card-body">
                    <div id="apiStatusContainer">
                        <!-- API status cards -->
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Watchlist Configuration Section -->
    <div class="row mt-4">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-list"></i> Watchlist Configuration</h5>
                </div>
                <div class="card-body">
                    <!-- Stock and crypto watchlist management -->
                </div>
            </div>
        </div>
    </div>

    <!-- Job Scheduler Section -->
    <div class="row mt-4">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-clock"></i> Backend Job Scheduler</h5>
                </div>
                <div class="card-body">
                    <div id="jobSchedulesSection">
                        <!-- Job schedules table and management -->
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```
**What happens:** HTML template loads with comprehensive monitoring sections and interactive controls

### **Step 3: JavaScript Auto-Loads Data**
```javascript
// src/web/templates/system_status.html
document.addEventListener('DOMContentLoaded', function() {
    loadSystemStatus();
    loadWatchlistConfig();
    
    // Set up event listeners
    document.getElementById('refreshBtn').addEventListener('click', loadSystemStatus);
    document.getElementById('autoRefresh').addEventListener('change', toggleAutoRefresh);
    document.getElementById('clearCacheBtn').addEventListener('click', clearCache);
    document.getElementById('testWatchlistBtn').addEventListener('click', testWatchlistOpportunities);
    
    // AI Provider selection
    const aiProviders = document.querySelectorAll('input[name="aiProvider"]');
    aiProviders.forEach(provider => {
        provider.addEventListener('change', function() {
            localStorage.setItem('aiProvider', this.value);
            showAlert(`AI provider changed to ${this.value}`, 'info');
        });
    });
    
    // Load saved AI provider
    const savedProvider = localStorage.getItem('aiProvider') || 'ollama';
    document.getElementById(savedProvider + 'Provider').checked = true;
    
    // Telegram toggle
    document.getElementById('telegramEnabled').addEventListener('change', function() {
        toggleTelegram(this.checked);
    });
    
    // Load telegram status
    loadTelegramStatus();
    loadJobSchedules(); // Load job schedules on page load
});

function toggleAutoRefresh() {
    const autoRefresh = document.getElementById('autoRefresh');
    if (autoRefresh.checked) {
        autoRefreshInterval = setInterval(loadSystemStatus, 30000);
        showAlert('Auto-refresh enabled (30s interval)', 'info');
    } else {
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
        }
        showAlert('Auto-refresh disabled', 'info');
    }
}

async function loadSystemStatus() {
    try {
        const response = await fetch('/api/system_status');
        const data = await response.json();
        
        if (data.status === 'ok') {
            updateSystemMetrics(data);
        } else {
            console.error('System status error:', data.error);
            showAlert('Error loading system status: ' + data.error, 'danger');
        }
    } catch (error) {
        console.error('Error loading system status:', error);
        showAlert('Error loading system status: ' + error.message, 'danger');
    }
}
```
**What happens:** JavaScript automatically fetches system metrics and updates the UI

### **Step 4: Backend API Processing**
```python
# src/web/app.py line 2419
@app.route("/api/system_status")
def system_status():
    """System status information with comprehensive error handling"""
    try:
        # Get basic system metrics with error handling
        system_metrics = {}
        try:
            system_metrics = get_system_metrics()
        except Exception as e:
            log_error(f"Error getting system metrics: {str(e)}")
            system_metrics = {"status": "error", "error": str(e)}
        
        # Get database stats with error handling
        db_stats = {"status": "unavailable"}
        try:
            from src.core.database import get_database_stats
            db_stats = get_database_stats()
        except Exception as e:
            log_error(f"Error getting database stats: {str(e)}")
            db_stats = {"status": "error", "error": str(e)}
        
        # Get cache stats with error handling
        cache_stats = {"status": "unavailable"}
        try:
            cache_stats = get_cache_stats()
        except Exception as e:
            log_error(f"Error getting cache stats: {str(e)}")
            cache_stats = {"error": str(e)}
        
        # Get application config
        config_info = {
            "telegram_enabled": telegram_alerter.is_enabled(),
            "cache_enabled": (Config.ENABLE_CACHE if hasattr(Config, "ENABLE_CACHE") else False),
            "debug_mode": app.debug,
            "version": "1.0.0",
        }
        
        # Get API status information
        api_status = {}
        try:
            from src.utils.api_tracker import api_tracker
            api_status = api_tracker.get_all_api_status()
        except Exception as e:
            log_error(f"Error getting API status: {str(e)}")
            api_status = {"error": str(e)}
        
        return jsonify({
            "status": "ok",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "system": system_metrics,
            "database": db_stats,
            "cache": cache_stats,
            "config": config_info,
            "api_status": api_status,
        })
    except Exception as e:
        log_error(f"Critical error in system_status: {str(e)}")
        return jsonify({
            "status": "error", 
            "error": "System status unavailable",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 500
```
**What happens:** API collects system metrics, database stats, cache info, and API status

### **Step 5: System Metrics Collection**
```python
# src/web/app.py line 2327
def get_system_metrics():
    """Get basic system metrics"""
    try:
        import psutil
        import platform
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        
        # System info
        system_info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "architecture": platform.machine(),
        }
        
        # Process info
        process = psutil.Process()
        process_memory_mb = process.memory_info().rss / (1024**2)
        process_cpu_percent = process.cpu_percent()
        
        return {
            "status": "ok",
            "cpu": {
                "system_percent": cpu_percent,
                "process_percent": process_cpu_percent
            },
            "memory": {
                "system_percent": memory_percent,
                "system_used_gb": round(memory_used_gb, 2),
                "system_total_gb": round(memory_total_gb, 2),
                "process_mb": round(process_memory_mb, 2)
            },
            "disk": {
                "percent": disk_percent,
                "used_gb": round(disk_used_gb, 2),
                "total_gb": round(disk_total_gb, 2)
            },
            "system": system_info,
            "uptime": {
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    except Exception as e:
        log_error(f"Error getting system metrics: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }
```
**What happens:** Collects real-time system performance metrics using `psutil`

### **Step 6: API Usage Tracking**
```python
# src/utils/api_tracker.py
class APITracker:
    """Singleton API tracker for monitoring API usage"""
    
    def __init__(self):
        self.max_requests = 100
        self.time_window = 60  # seconds
        self.request_history: Dict[str, list] = {}
        self.circuit_breaker: Dict[str, Dict[str, Any]] = {}
    
    def record_request(self, api_name: str):
        """Record a successful API request"""
        if api_name not in self.request_history:
            self.request_history[api_name] = []
        self.request_history[api_name].append(self._get_current_time())
        logger.debug(f"Recorded API request for {api_name}")

    def record_failure(self, api_name: str):
        """Record an API failure and potentially open the circuit breaker"""
        if api_name not in self.circuit_breaker:
            self.circuit_breaker[api_name] = {
                "failures": 0,
                "last_failure": None,
                "state": "closed",
            }
        circuit = self.circuit_breaker[api_name]
        circuit["failures"] += 1
        circuit["last_failure"] = datetime.now()
        # Open circuit after 5 consecutive failures
        if circuit["failures"] >= 5:
            circuit["state"] = "open"
            logger.error(f"Circuit breaker opened for {api_name} after {circuit['failures']} failures")

    def get_all_api_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status for all tracked APIs"""
        apis = ["yahoo_finance", "alpha_vantage", "finnhub", "reddit", "ollama", "cryptopanic", "newsapi"]
        return {api: self.get_api_status(api) for api in apis}
```
**What happens:** Tracks API usage, implements rate limiting, and monitors circuit breaker status

### **Step 7: Frontend Data Display**
```javascript
function updateSystemMetrics(data) {
    // Update performance metrics
    const system = data.system || {};
    
    // CPU Usage
    const cpuElement = document.getElementById('cpuUsage');
    if (system.cpu && system.cpu.system_percent !== undefined) {
        cpuElement.textContent = system.cpu.system_percent.toFixed(1) + '%';
        cpuElement.className = system.cpu.system_percent > 80 ? 'text-danger' : 
                              system.cpu.system_percent > 60 ? 'text-warning' : 'text-primary';
    }
    
    // Memory Usage
    const memoryElement = document.getElementById('memoryUsage');
    if (system.memory && system.memory.system_percent !== undefined) {
        memoryElement.textContent = system.memory.system_percent.toFixed(1) + '%';
        memoryElement.className = system.memory.system_percent > 80 ? 'text-danger' : 
                                 system.memory.system_percent > 60 ? 'text-warning' : 'text-success';
    }
    
    // Uptime (calculate from boot time)
    const uptimeElement = document.getElementById('uptime');
    if (system.uptime && system.uptime.boot_time) {
        const bootTime = new Date(system.uptime.boot_time);
        const now = new Date();
        const uptimeMs = now - bootTime;
        const uptimeHours = Math.floor(uptimeMs / (1000 * 60 * 60));
        const uptimeMinutes = Math.floor((uptimeMs % (1000 * 60 * 60)) / (1000 * 60));
        uptimeElement.textContent = `${uptimeHours}h ${uptimeMinutes}m`;
    }
    
    // Update API status
    const apiStatus = data.api_status || {};
    updateApiStatus(apiStatus);
    
    // Update last updated timestamp
    const lastUpdatedElement = document.getElementById('lastUpdated');
    if (data.timestamp) {
        const timestamp = new Date(data.timestamp);
        lastUpdatedElement.textContent = `Last updated: ${timestamp.toLocaleString()}`;
    }
}

function updateApiStatus(apiStatus) {
    const container = document.getElementById('apiStatusContainer');
    if (!container) return;
    
    if (apiStatus.error) {
        container.innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle"></i> API Status Error: ${apiStatus.error}
            </div>
        `;
        return;
    }
    
    let html = '<div class="row">';
    
    Object.entries(apiStatus).forEach(([apiName, status]) => {
        const rateLimit = status.rate_limit || {};
        const circuitBreaker = status.circuit_breaker || {};
        
        const currentRequests = rateLimit.current_requests || 0;
        const maxRequests = rateLimit.max_requests || 100;
        const usagePercent = maxRequests > 0 ? (currentRequests / maxRequests) * 100 : 0;
        
        const circuitState = circuitBreaker.state || 'closed';
        const failures = circuitBreaker.failures || 0;
        
        let statusClass = 'success';
        let statusIcon = 'check-circle';
        let statusText = 'Healthy';
        
        if (circuitState === 'open') {
            statusClass = 'danger';
            statusIcon = 'times-circle';
            statusText = 'Circuit Open';
        } else if (usagePercent > 80) {
            statusClass = 'warning';
            statusIcon = 'exclamation-triangle';
            statusText = 'High Usage';
        } else if (failures > 0) {
            statusClass = 'warning';
            statusIcon = 'exclamation-triangle';
            statusText = `${failures} Failures`;
        }
        
        html += `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card border-${statusClass}">
                    <div class="card-header bg-${statusClass} text-white">
                        <h6 class="mb-0">
                            <i class="fas fa-${statusIcon}"></i> ${apiName.replace('_', ' ').toUpperCase()}
                        </h6>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-6">
                                <small class="text-muted">Status</small><br>
                                <span class="text-${statusClass}">${statusText}</span>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Usage</small><br>
                                <span>${currentRequests}/${maxRequests}</span>
                            </div>
                        </div>
                        <div class="progress mt-2" style="height: 4px;">
                            <div class="progress-bar bg-${statusClass}" style="width: ${usagePercent}%"></div>
                        </div>
                        <small class="text-muted">${usagePercent.toFixed(1)}% of rate limit</small>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}
```
**What happens:** JavaScript updates the UI with real-time system metrics and API status

---

## 📊 **Data Flow Diagram**

```mermaid
graph TD
    A[User visits /system_status] --> B[Flask serves HTML template]
    B --> C[JavaScript loads automatically]
    C --> D[fetch() API call to /api/system_status]
    D --> E[Flask API endpoint]
    E --> F[get_system_metrics() - psutil]
    E --> G[get_database_stats() - PostgreSQL]
    E --> H[get_cache_stats() - Cache system]
    E --> I[api_tracker.get_all_api_status()]
    F --> J[System performance data]
    G --> K[Database connection & stats]
    H --> L[Cache hit rates & size]
    I --> M[API usage & circuit breakers]
    J --> N[JSON response to frontend]
    K --> N
    L --> N
    M --> N
    N --> O[JavaScript updates UI display]
    
    P[User clicks Refresh] --> D
    Q[Auto-refresh every 30s] --> D
    R[User changes settings] --> S[POST to config endpoints]
    
    style A fill:#e1f5fe
    style F fill:#f3e5f5
    style G fill:#e8f5e8
    style H fill:#fff3e0
    style I fill:#fce4ec
    style O fill:#f1f8e9
```

**Alternative ASCII Diagram:**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   User      │    │   Flask     │    │ System      │    │ JavaScript  │
│  Browser    │    │   Server    │    │  Monitoring │    │  Frontend   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       │ 1. GET /system_status                │                   │
       │──────────────────▶│                   │                   │
       │                   │                   │                   │
       │ 2. HTML template  │                   │                   │
       │◀──────────────────│                   │                   │
       │                   │                   │                   │
       │ 3. Auto-load data │                   │                   │
       │──────────────────────────────────────────────────────────▶│
       │                   │                   │                   │
       │ 4. GET /api/system_status            │                   │
       │──────────────────▶│                   │                   │
       │                   │ 5. Collect system metrics             │
       │                   │──────────────────▶│                   │
       │                   │                   │ 6. psutil CPU/Memory│
       │                   │                   │──────────────────▶│
       │                   │                   │ 7. Database stats │
       │                   │                   │──────────────────▶│
       │                   │                   │ 8. API usage tracking│
       │                   │                   │──────────────────▶│
       │                   │                   │                   │
       │ 9. JSON response  │                   │                   │
       │◀──────────────────│                   │                   │
       │                   │                   │                   │
       │ 10. Update UI     │                   │                   │
       │◀──────────────────────────────────────────────────────────│
       │                   │                   │                   │
```

---

## 🎯 **Key Points for Junior Developers**

### **1. Comprehensive System Monitoring**
- **Real-time metrics** using `psutil` for CPU, memory, and disk usage
- **Database monitoring** with connection status and performance stats
- **API usage tracking** with rate limiting and circuit breaker patterns
- **Cache monitoring** with hit rates and memory usage

### **2. Interactive Configuration Management**
- **AI provider selection** (Ollama, DeepSeek, OpenAI) with local storage
- **Telegram notification** toggle with real-time status checking
- **Cache management** with clear cache functionality
- **Watchlist configuration** for stocks and cryptocurrencies

### **3. Job Scheduler Management**
- **Background job scheduling** with time-based execution
- **Job enable/disable** functionality
- **Schedule modification** with real-time updates
- **Job execution history** tracking

### **4. API Status Monitoring**
- **Rate limiting visualization** with usage percentages
- **Circuit breaker status** showing API health
- **Failure tracking** with automatic recovery
- **Real-time updates** every 30 seconds

### **5. User Experience Features**
- **Auto-refresh toggle** for continuous monitoring
- **Manual refresh** for immediate updates
- **Alert system** for status changes and errors
- **Responsive design** with mobile-friendly layout

---

## 🔧 **Database Schema Overview**

### **job_schedules table:**
```sql
CREATE TABLE job_schedules (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    run_time TIME NOT NULL,
    enabled BOOLEAN DEFAULT true,
    last_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **watchlists table:**
```sql
CREATE TABLE watchlists (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    type VARCHAR(10) NOT NULL, -- 'stock' or 'crypto'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🚀 **Benefits of This Architecture**

1. **Real-time Monitoring**: Live system metrics with 30-second auto-refresh
2. **Comprehensive Coverage**: CPU, memory, disk, database, API, and cache monitoring
3. **Interactive Management**: Configuration changes without page reloads
4. **Error Handling**: Graceful degradation when services are unavailable
5. **User-friendly**: Clear visual indicators and status summaries
6. **Scalable**: Easy to add new monitoring metrics or configuration options

This architecture provides **comprehensive system monitoring** with **interactive configuration management** that helps administrators maintain optimal system performance and troubleshoot issues quickly! 🚀 