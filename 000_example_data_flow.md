# 📊 Backtest Page Data Flow & Architecture Guide

## 📁 **Files Involved in the Backtest Page**

### **Backend (Python) Files:**
- **`src/web/app.py`** - Main Flask application with backtest routes
- **`src/trading/trading_strategy.py`** - Core backtesting logic and calculations
- **`src/core/database.py`** - Database operations for saving/retrieving backtest results
- **`src/core/recommendation_manager.py`** - Manages historical trading recommendations

### **Frontend Files:**
- **`src/web/templates/backtest.html`** - Main page template with form and results sections
- **`src/web/static/css/styles.css`** - Styling for the backtest page
- **`src/web/static/js/base.js`** - Common JavaScript functions (loading spinners, alerts)

### **Database Tables:**
- **`recommendations`** - Stores historical trading recommendations with performance data
- **`backtest_results`** - Caches backtest simulation results for faster loading

---

## 🔄 **Data Flow: From Source to Display**

### **Data Sources:**
1. **Historical Trading Recommendations** - Stored in PostgreSQL `recommendations` table
2. **Stock Price Data** - Fetched from Yahoo Finance API (via `yf.Ticker`)
3. **Simulated Sentiment Data** - Generated randomly for strategy testing

### **Data Journey:**
```
Database (recommendations) → Flask API → JSON Response → JavaScript → HTML Display
```

---

## ⏰ **Loading Strategy: Lazy Loading via AJAX**

The Backtest page uses **lazy loading** - data is NOT loaded when the page first loads. Instead:

1. **Page loads** with empty form and hidden results sections
2. **JavaScript automatically triggers** an API call to load default data (AAPL, 30 days)
3. **User can change parameters** and trigger new API calls
4. **Loading spinners** show while data is being fetched

---

## 🏗️ **Step-by-Step Architecture**

### **Step 1: Route/Controller**
```python
# src/web/app.py
@app.route("/backtest")
def backtest_page():
    """Backtesting page"""
    return render_template(
        "backtest.html", 
        historical_lookback_days=Config.HISTORICAL_LOOKBACK_DAYS
    )
```
**What happens:** User visits `/backtest` → Flask serves the HTML template

### **Step 2: Template Rendering**
```html
<!-- src/web/templates/backtest.html -->
<form id="backtestForm">
    <input type="text" id="symbol" placeholder="e.g., AAPL, TSLA, MSFT">
    <select id="daysBack">
        <option value="30" selected>30 Days</option>
        <option value="60">60 Days</option>
    </select>
    <button type="submit">Run Historical Backtest</button>
</form>

<div id="resultsSection" style="display: none;">
    <!-- Results will be populated by JavaScript -->
</div>
```
**What happens:** HTML template loads with empty form and hidden results

### **Step 3: JavaScript Auto-Loads Data**
```javascript
// src/web/templates/backtest.html
document.addEventListener('DOMContentLoaded', loadSavedResults);

async function loadSavedResults() {
    const defaultSymbol = 'AAPL';
    const defaultPeriod = 30;
    
    // Populate form fields
    document.getElementById('symbol').value = defaultSymbol;
    document.getElementById('daysBack').value = defaultPeriod;
    
    // Make API call to load data
    const response = await fetch('/api/backtest/historical', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            symbol: defaultSymbol,
            days_back: defaultPeriod,
            strategy_type: 'all'
        })
    });
    
    const result = await response.json();
    if (result.data && result.data.total_recommendations > 0) {
        displayHistoricalBacktestResults(result.data);
    }
}
```
**What happens:** JavaScript automatically fetches and displays default data

### **Step 4: Backend API Processing**
```python
# src/web/app.py
@app.route("/api/backtest/historical", methods=["POST"])
def backtest_historical_recommendations():
    try:
        data = request.get_json()
        symbol = data.get("symbol", "").upper()
        days_back = int(data.get("days_back", 30))
        
        # Connect to database
        conn = psycopg2.connect(Config.DATABASE_CONFIG)
        
        # Query historical recommendations
        query = """
            SELECT id, symbol, timestamp, action, strike_price, 
                   sentiment_confidence, final_confidence, profitable
            FROM recommendations 
            WHERE timestamp >= NOW() - INTERVAL %s days
            AND symbol = %s
            ORDER BY timestamp DESC
        """
        
        cur.execute(query, [f"{days_back} days", symbol])
        recommendations = cur.fetchall()
        
        # Process results into backtest format
        backtest_results = process_recommendations_to_backtest(recommendations)
        
        return create_api_response(data=backtest_results)
        
    except Exception as e:
        return create_api_response(error=str(e), status_code=500)
```
**What happens:** API queries database, processes data, returns JSON

### **Step 5: Frontend Data Display**
```javascript
function displayHistoricalBacktestResults(data) {
    // Update summary cards
    document.getElementById('initialCapital').textContent = formatCurrency(data.initial_capital);
    document.getElementById('finalCapital').textContent = formatCurrency(data.final_capital);
    document.getElementById('totalReturn').textContent = data.total_return + '%';
    document.getElementById('winRate').textContent = data.win_rate + '%';
    
    // Display trades table
    displayTradesTable(data.trades || []);
    
    // Show results section
    document.getElementById('resultsSection').style.display = 'block';
}
```
**What happens:** JavaScript updates HTML with the received data

---

## 📊 **Data Flow Diagram**

```mermaid
graph TD
    A[User visits /backtest] --> B[Flask serves HTML template]
    B --> C[JavaScript loads automatically]
    C --> D[fetch() API call to /api/backtest/historical]
    D --> E[Flask API endpoint]
    E --> F[Database query: SELECT from recommendations]
    F --> G[Process recommendations into backtest format]
    G --> H[JSON response to frontend]
    H --> I[JavaScript updates HTML display]
    
    J[User submits form] --> K[fetch() API call with new parameters]
    K --> E
    
    style A fill:#e1f5fe
    style E fill:#f3e5f5
    style F fill:#e8f5e8
    style I fill:#fff3e0
```

**Alternative ASCII Diagram:**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   User      │    │   Flask     │    │ PostgreSQL  │    │ JavaScript  │
│  Browser    │    │   Server    │    │  Database   │    │  Frontend   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       │ 1. GET /backtest  │                   │                   │
       │──────────────────▶│                   │                   │
       │                   │                   │                   │
       │ 2. HTML template  │                   │                   │
       │◀──────────────────│                   │                   │
       │                   │                   │                   │
       │ 3. Auto-load data │                   │                   │
       │──────────────────────────────────────────────────────────▶│
       │                   │                   │                   │
       │ 4. POST /api/backtest/historical      │                   │
       │──────────────────▶│                   │                   │
       │                   │ 5. Query recommendations table        │
       │                   │──────────────────▶│                   │
       │                   │                   │ 6. Historical data│
       │                   │◀──────────────────│                   │
       │                   │                   │                   │
       │ 7. JSON response  │                   │                   │
       │◀──────────────────│                   │                   │
       │                   │                   │                   │
       │ 8. Update display │                   │                   │
       │◀──────────────────────────────────────────────────────────│
       │                   │                   │                   │
```

---

## 🎯 **Key Points for Junior Developers**

### **1. Separation of Concerns**
- **Flask routes** handle HTTP requests
- **Database functions** handle data storage/retrieval
- **JavaScript** handles user interaction and display updates
- **HTML templates** provide the structure

### **2. Async Data Loading**
- Page loads **fast** (no database queries on initial load)
- Data loads **on-demand** via AJAX calls
- **Loading spinners** provide user feedback
- **Error handling** for failed API calls

### **3. Data Processing Pipeline**
```
Database → Raw SQL Results → Python Processing → JSON → JavaScript → HTML Display
```

### **4. User Interaction Flow**
1. **Page loads** with empty form
2. **Auto-load** default data (AAPL, 30 days)
3. **User changes** symbol or time period
4. **Form submission** triggers new API call
5. **Results update** without page reload

---

## 🔧 **Database Schema Overview**

### **recommendations table:**
```sql
CREATE TABLE recommendations (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    recommendation_type VARCHAR(50),
    action VARCHAR(10), -- CALL, PUT, HOLD
    strike_price DECIMAL(10,2),
    sentiment_confidence DECIMAL(5,4),
    final_confidence DECIMAL(5,4),
    sentiment_score DECIMAL(5,4),
    reasoning TEXT,
    actual_outcome DECIMAL(5,4),
    profitable BOOLEAN
);
```

### **backtest_results table:**
```sql
CREATE TABLE backtest_results (
    id SERIAL PRIMARY KEY,
    stock_symbol VARCHAR(16) NOT NULL,
    period_days INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    initial_capital NUMERIC(18,2) NOT NULL,
    final_capital NUMERIC(18,2) NOT NULL,
    total_return NUMERIC(8,2) NOT NULL,
    win_rate NUMERIC(5,2) NOT NULL,
    total_trades INTEGER NOT NULL,
    trades JSONB NOT NULL
);
```

---

## 🚀 **Benefits of This Architecture**

1. **Performance**: Fast initial page load, data loads on-demand
2. **User Experience**: Responsive interface with loading indicators
3. **Scalability**: Database queries only when needed
4. **Maintainability**: Clear separation between frontend and backend
5. **Flexibility**: Easy to add new features or modify existing ones

This architecture provides a **responsive, user-friendly experience** while keeping the backend efficient and the code organized! 🚀 