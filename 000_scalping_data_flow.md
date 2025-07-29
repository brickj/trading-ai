# 📊 Scalping Signals Page Data Flow & Architecture Guide

## 📁 **Files Involved in the Scalping Signals Page**

### **Backend (Python) Files:**
- **`src/web/scalping_signals.py`** - Main Flask blueprint with scalping routes and API endpoints
- **`src/core/scalping_analyzer.py`** - Core scalping analysis logic and market data processing
- **`src/core/database.py`** - Database operations for scalping signals storage
- **`src/core/sentiment_analyzer.py`** - Sentiment analysis for scalping opportunities
- **`src/data/data_fetcher.py`** - Market data fetching from various APIs

### **Frontend Files:**
- **`src/web/templates/scalping_signals.html`** - Main page template with modern UI components
- **`src/web/static/css/styles.css`** - Styling for the scalping signals page
- **`src/web/static/js/logger.js`** - Frontend logging functionality

### **Database Tables:**
- **`scalping_signals`** - Stores real-time scalping opportunities and market data
- **`watchlists`** - Contains tickers to analyze for scalping opportunities

---

## 🔄 **Data Flow: From Market Analysis to Display**

### **Data Sources:**
1. **Market Data APIs** - Alpha Vantage, Yahoo Finance, Polygon for real-time price data
2. **News APIs** - NewsAPI, Yahoo Finance for sentiment analysis
3. **Watchlist Database** - Predefined list of stocks and cryptos to analyze
4. **Historical Scalping Signals** - Previous analysis results stored in database

### **Data Journey:**
```
Market APIs → Scalping Analyzer → Database Storage → Flask API → JavaScript → Modern UI Display
```

---

## ⏰ **Loading Strategy: Real-time Analysis with Auto-refresh**

The Scalping Signals page uses **real-time analysis** with multiple loading strategies:

1. **Page loads** with statistics cards and loading spinner
2. **JavaScript automatically triggers** API calls to load current opportunities
3. **Auto-refresh functionality** updates data every 30 minutes
4. **Manual refresh** allows users to trigger new analysis
5. **Filter buttons** allow users to view specific opportunity types

---

## 🏗️ **Step-by-Step Architecture**

### **Step 1: Route/Controller**
```python
# src/web/scalping_signals.py
@scalping_signals_bp.route("/scalping_signals")
def scalping_signals_page():
    """Scalping signals page - shows historical signals"""
    signals = []
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT ticker, asset_type, date, time_collected, price_open, price_now, 
                           volume_ratio, price_change_pct, gap_pct, sentiment_class, 
                           recommendation, headlines_json
                    FROM scalping_signals
                    ORDER BY date DESC, time_collected DESC
                    LIMIT 100
                """)
                # Process results and render template
        return render_template("scalping_signals.html", signals=signals)
    except Exception as e:
        log_error(f"Error loading scalping signals: {e}")
        return render_template("scalping_signals.html", signals=[])
```
**What happens:** User visits `/scalping_signals` → Flask serves the HTML template with historical data

### **Step 2: Template Rendering**
```html
<!-- src/web/templates/scalping_signals.html -->
<div class="container-fluid">
    <!-- Header -->
    <div class="row bg-primary text-white p-3 mb-4">
        <div class="col">
            <h1><i class="fas fa-chart-line"></i> Scalping Signals</h1>
            <p class="mb-0">Real-time scalping opportunities for stocks and cryptocurrencies</p>
        </div>
    </div>

    <!-- Stats Cards -->
    <div class="row mb-4" id="statsCards">
        <div class="col-md-3">
            <div class="card stats-card">
                <div class="card-body text-center">
                    <h5><i class="fas fa-signal"></i> Total Signals</h5>
                    <h3 id="totalSignals">-</h3>
                </div>
            </div>
        </div>
        <!-- More stats cards... -->
    </div>

    <!-- Controls -->
    <div class="row mb-4">
        <div class="col-md-6">
            <div class="filter-buttons">
                <button class="btn btn-outline-primary filter-btn active" data-filter="all">
                    <i class="fas fa-list"></i> All
                </button>
                <button class="btn btn-outline-success filter-btn" data-filter="long">
                    <i class="fas fa-arrow-up"></i> Long Opportunities
                </button>
                <!-- More filter buttons... -->
            </div>
        </div>
        <div class="col-md-6 text-end">
            <button class="btn btn-success me-2" onclick="runAnalysis()">
                <i class="fas fa-play"></i> Run Analysis
            </button>
            <button class="btn btn-primary" onclick="refreshData()">
                <i class="fas fa-sync-alt"></i> Refresh
            </button>
        </div>
    </div>

    <!-- Opportunities Grid -->
    <div class="modern-container">
        <div class="modern-grid" id="opportunitiesGrid"></div>
    </div>
</div>
```
**What happens:** HTML template loads with stats cards, filter buttons, and empty opportunities grid

### **Step 3: JavaScript Auto-Loads Data**
```javascript
// src/web/templates/scalping_signals.html
document.addEventListener('DOMContentLoaded', function() {
    frontendLogger.info('Scalping signals page DOMContentLoaded', 'scalping');
    loadStats();
    loadOpportunities();
    setupFilterButtons();
    setupAutoRefreshToggle();
});

async function loadStats() {
    try {
        const response = await fetch('/api/scalping/stats');
        const data = await response.json();
        if (data.success && data.today) {
            document.getElementById('totalSignals').textContent = data.today.total_signals || 0;
            document.getElementById('totalOpportunities').textContent = data.today.opportunities || 0;
            document.getElementById('stockCount').textContent = data.today.stocks || 0;
            document.getElementById('cryptoCount').textContent = data.today.cryptos || 0;
        }
    } catch (error) {
        frontendLogger.error('Error loading stats: ' + error, 'scalping');
    }
}

async function loadOpportunities() {
    showLoading();
    try {
        const response = await fetch('/api/scalping/opportunities');
        const data = await response.json();
        
        if (data.data && Array.isArray(data.data)) {
            opportunitiesData = data.data;
            filterOpportunities();
        } else {
            showNoDataMessage();
        }
    } catch (error) {
        showErrorMessage(error.message || 'Failed to load opportunities');
    } finally {
        hideLoading();
    }
}
```
**What happens:** JavaScript automatically fetches statistics and opportunities data

### **Step 4: Backend API Processing**
```python
# src/web/scalping_signals.py
@scalping_signals_bp.route("/api/scalping/opportunities", methods=["GET"])
def get_scalping_opportunities():
    """API endpoint to get current scalping opportunities"""
    try:
        log_info("[SCALPING] GET /api/scalping/opportunities called")
        result = scalping_analyzer.get_scalping_opportunities_api()
        return jsonify(result)
    except Exception as e:
        log_error(f"[SCALPING] Error getting scalping opportunities: {e}")
        return jsonify({
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "total_signals": 0,
            "opportunities": 0,
            "data": []
        }), 500

@scalping_signals_bp.route("/api/scalping/stats", methods=["GET"])
def get_scalping_stats():
    """API endpoint to get scalping statistics"""
    try:
        # Get today's stats
        today_query = """
        SELECT 
            COUNT(*) as total_signals,
            COUNT(CASE WHEN recommendation IN ('Long Scalping Opportunity', 'Short Scalping Opportunity') THEN 1 END) as opportunities,
            COUNT(CASE WHEN asset_type = 'stock' THEN 1 END) as stocks,
            COUNT(CASE WHEN asset_type = 'crypto' THEN 1 END) as cryptos
        FROM scalping_signals
        WHERE date = CURRENT_DATE
        """
        today_results = execute_query(today_query)
        today_stats = today_results[0] if today_results else {}
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "today": today_stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500
```
**What happens:** API queries database for scalping opportunities and statistics

### **Step 5: Core Scalping Analysis**
```python
# src/core/scalping_analyzer.py
class ScalpingAnalyzer:
    def __init__(self):
        self.VOLUME_RATIO_THRESHOLD = 2.0
        self.PRICE_CHANGE_THRESHOLD = 2.0
        self.SENTIMENT_THRESHOLD = 2
    
    def get_scalping_opportunities_api(self) -> Dict[str, Any]:
        """Get current scalping opportunities for API"""
        try:
            # Get active watchlist tickers
            watchlist = self.get_active_watchlist_tickers()
            
            opportunities = []
            for item in watchlist:
                ticker = item['ticker']
                asset_type = item['asset_type']
                
                # Get market data
                market_data = self.get_market_data(ticker, asset_type)
                if not market_data:
                    continue
                
                # Get news and sentiment
                sentiment_data = self.get_news_and_sentiment(ticker, asset_type)
                
                # Generate recommendation
                recommendation = self.generate_scalping_recommendation(market_data, sentiment_data)
                
                # Store signal
                self.store_scalping_signal(ticker, asset_type, market_data, sentiment_data, recommendation)
                
                # Add to opportunities if it's a good opportunity
                if 'Opportunity' in recommendation:
                    opportunities.append({
                        'ticker': ticker,
                        'asset_type': asset_type,
                        'price_open': market_data.get('price_open'),
                        'price_now': market_data.get('price_now'),
                        'volume_ratio': market_data.get('volume_ratio'),
                        'price_change_pct': market_data.get('price_change_pct'),
                        'sentiment': sentiment_data.get('sentiment_class'),
                        'recommendation': recommendation
                    })
            
            return {
                "timestamp": datetime.now().isoformat(),
                "total_signals": len(watchlist),
                "opportunities": len(opportunities),
                "data": opportunities
            }
            
        except Exception as e:
            log_error(f"Error in get_scalping_opportunities_api: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "total_signals": 0,
                "opportunities": 0,
                "data": []
            }
```
**What happens:** Core analyzer processes market data and generates scalping recommendations

### **Step 6: Frontend Data Display**
```javascript
function renderOpportunities(opportunities) {
    const grid = document.getElementById('opportunitiesGrid');
    if (!opportunities || opportunities.length === 0) {
        showNoDataMessage();
        return;
    }
    
    // Group by asset type
    const stocks = opportunities.filter(opp => opp.asset_type === 'stock');
    const cryptos = opportunities.filter(opp => opp.asset_type === 'crypto');
    
    let html = '';
    
    // Render stock opportunities
    if (stocks.length > 0) {
        html += `<div class="modern-card-wrapper"><div class="modern-card-group">`;
        html += `<div class="modern-card-group-header">Stocks (${stocks.length})</div>`;
        stocks.forEach(opp => {
            html += renderOpportunityCard(opp);
        });
        html += `</div></div>`;
    }
    
    // Render crypto opportunities
    if (cryptos.length > 0) {
        html += `<div class="modern-card-wrapper"><div class="modern-card-group">`;
        html += `<div class="modern-card-group-header">Cryptocurrencies (${cryptos.length})</div>`;
        cryptos.forEach(opp => {
            html += renderOpportunityCard(opp);
        });
        html += `</div></div>`;
    }
    
    grid.innerHTML = html;
}

function renderOpportunityCard(opp) {
    const badgeClass = opp.asset_type === 'stock' ? 'badge-primary' : 'badge-warning';
    const badgeIcon = opp.asset_type === 'stock' ? 'fa-chart-bar' : 'fa-coins';
    const sentimentIcon = opp.sentiment === 'Bullish' ? 'fa-arrow-up' : 
                        opp.sentiment === 'Bearish' ? 'fa-arrow-down' : 'fa-minus';
    
    return `
        <div class="modern-card">
            <div class="modern-card-header">
                <span class="fw-bold">${opp.ticker}</span>
                <span class="${badgeClass}"><i class="fas ${badgeIcon}"></i>${opp.asset_type}</span>
            </div>
            <div class="modern-card-body">
                <div class="modern-card-row">
                    <span class="label">Price Open</span>
                    <span class="value">$${opp.price_open?.toFixed(2) || 'N/A'}</span>
                </div>
                <div class="modern-card-row">
                    <span class="label">Current Price</span>
                    <span class="value">$${opp.price_now?.toFixed(2) || 'N/A'}</span>
                </div>
                <div class="modern-card-row">
                    <span class="label">Volume Ratio</span>
                    <span class="value ${opp.volume_ratio >= 2 ? 'positive' : 'neutral'}">${opp.volume_ratio?.toFixed(2) || 'N/A'}x</span>
                </div>
                <div class="modern-card-row">
                    <span class="label">Price Change</span>
                    <span class="value ${opp.price_change_pct > 0 ? 'positive' : opp.price_change_pct < 0 ? 'negative' : 'neutral'}">${opp.price_change_pct?.toFixed(2) || 'N/A'}%</span>
                </div>
                <div class="modern-card-row">
                    <span class="label">Sentiment</span>
                    <span class="sentiment"><i class="fas ${sentimentIcon}"></i>${opp.sentiment || 'Neutral'}</span>
                </div>
            </div>
            <div class="modern-card-footer">
                <div class="btn-group">
                    <button class="btn btn-sm btn-outline-primary" onclick="viewDetails('${opp.ticker}')">
                        <i class="fas fa-eye"></i> Details
                    </button>
                    <button class="btn btn-sm btn-outline-success" onclick="addToWatchlist('${opp.ticker}')">
                        <i class="fas fa-plus"></i> Watchlist
                    </button>
                    <button class="btn btn-sm btn-outline-warning" onclick="setAlert('${opp.ticker}')">
                        <i class="fas fa-bell"></i> Alert
                    </button>
                </div>
            </div>
        </div>
    `;
}
```
**What happens:** JavaScript renders modern opportunity cards with real-time data

---

## 📊 **Data Flow Diagram**

```mermaid
graph TD
    A[User visits /scalping_signals] --> B[Flask serves HTML template]
    B --> C[JavaScript loads automatically]
    C --> D[fetch() API call to /api/scalping/stats]
    C --> E[fetch() API call to /api/scalping/opportunities]
    D --> F[Database query: SELECT from scalping_signals]
    E --> G[Scalping Analyzer processes market data]
    G --> H[Market APIs: Alpha Vantage, Yahoo Finance]
    G --> I[News APIs: NewsAPI, Yahoo Finance]
    H --> J[Generate scalping recommendations]
    I --> J
    J --> K[Store results in database]
    F --> L[JSON response to frontend]
    K --> L
    L --> M[JavaScript updates modern UI display]
    
    N[User clicks Run Analysis] --> O[POST /api/scalping/run_analysis]
    O --> G
    
    P[Auto-refresh every 30min] --> C
    
    style A fill:#e1f5fe
    style G fill:#f3e5f5
    style H fill:#e8f5e8
    style I fill:#fff3e0
    style M fill:#fce4ec
```

**Alternative ASCII Diagram:**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   User      │    │   Flask     │    │ Scalping    │    │ JavaScript  │
│  Browser    │    │   Server    │    │  Analyzer   │    │  Frontend   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       │ 1. GET /scalping_signals             │                   │
       │──────────────────▶│                   │                   │
       │                   │                   │                   │
       │ 2. HTML template  │                   │                   │
       │◀──────────────────│                   │                   │
       │                   │                   │                   │
       │ 3. Auto-load data │                   │                   │
       │──────────────────────────────────────────────────────────▶│
       │                   │                   │                   │
       │ 4. GET /api/scalping/opportunities   │                   │
       │──────────────────▶│                   │                   │
       │                   │ 5. Process watchlist tickers         │
       │                   │──────────────────▶│                   │
       │                   │                   │ 6. Fetch market data│
       │                   │                   │──────────────────▶│
       │                   │                   │ 7. Get news & sentiment│
       │                   │                   │──────────────────▶│
       │                   │                   │ 8. Generate recommendations│
       │                   │                   │──────────────────▶│
       │                   │                   │ 9. Store in database│
       │                   │                   │──────────────────▶│
       │                   │                   │                   │
       │ 10. JSON response │                   │                   │
       │◀──────────────────│                   │                   │
       │                   │                   │                   │
       │ 11. Update display│                   │                   │
       │◀──────────────────────────────────────────────────────────│
       │                   │                   │                   │
```

---

## 🎯 **Key Points for Junior Developers**

### **1. Real-time Analysis Architecture**
- **Scalping Analyzer** processes market data in real-time
- **Multiple API sources** provide comprehensive market analysis
- **Database storage** maintains historical scalping signals
- **Auto-refresh** keeps data current throughout the day

### **2. Modern UI Components**
- **Stats cards** show real-time statistics
- **Filter buttons** allow users to view specific opportunity types
- **Modern grid layout** displays opportunities in organized groups
- **Interactive cards** with action buttons for each opportunity

### **3. Data Processing Pipeline**
```
Watchlist → Market Data APIs → News APIs → Sentiment Analysis → Recommendation Engine → Database → UI Display
```

### **4. User Interaction Flow**
1. **Page loads** with statistics and loading spinner
2. **Auto-load** current scalping opportunities
3. **Filter options** allow users to view specific types
4. **Run Analysis** button triggers new market analysis
5. **Auto-refresh** keeps data current every 30 minutes

---

## 🔧 **Database Schema Overview**

### **scalping_signals table:**
```sql
CREATE TABLE scalping_signals (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    asset_type VARCHAR(10) NOT NULL, -- 'stock' or 'crypto'
    date DATE NOT NULL,
    time_collected TIME NOT NULL,
    price_open DECIMAL(10,4),
    price_now DECIMAL(10,4),
    volume_ratio DECIMAL(5,2),
    price_change_pct DECIMAL(5,2),
    gap_pct DECIMAL(5,2),
    sentiment_class VARCHAR(20), -- 'Bullish', 'Bearish', 'Neutral'
    recommendation TEXT,
    headlines_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

1. **Real-time Analysis**: Processes market data as it happens
2. **Comprehensive Coverage**: Analyzes both stocks and cryptocurrencies
3. **Modern UI**: Responsive design with interactive components
4. **Scalable**: Can easily add new data sources or analysis methods
5. **Automated**: Runs analysis automatically each trading day
6. **User-friendly**: Clear statistics and filtering options

This architecture provides **real-time scalping opportunities** with a **modern, responsive interface** that helps traders identify high-probability short-term trading opportunities! 🚀 