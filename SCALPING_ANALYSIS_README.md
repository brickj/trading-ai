# 🎯 Scalping Analysis System

A comprehensive scalping analysis system that identifies real-time trading opportunities for stocks and cryptocurrencies using market data, news sentiment analysis, and automated recommendations.

**⏰ Scheduled to run at 9:55 AM ET on trading days (Monday-Friday)**

## 🚀 Quick Start

### 1. Setup Database Tables
```bash
# Run the migration to create scalping tables
psql -d trading_db -f migrations/003_create_scalping_signals_table.sql
```

### 2. Test the System
```bash
# Run comprehensive tests
python3 test_scalping_analysis.py
```

### 3. Run Manual Analysis
```bash
# Run scalping analysis manually
python3 run_scalping_analysis.py
```

### 4. Automated Scheduling
```bash
# Scalping analysis is automatically scheduled at 9:55 AM ET on trading days
# No manual setup required - integrated into the main application scheduler
```

### 5. View Results
- **Web Interface**: http://localhost:5000/scalping_signals
- **API Endpoints**: See API Documentation below

## 📊 System Overview

### Core Components

1. **Scalping Analyzer** (`src/core/scalping_analyzer.py`)
   - Main analysis engine
   - Integrates market data, news, and sentiment
   - Generates trading recommendations

2. **Database Schema** (`migrations/003_create_scalping_signals_table.sql`)
   - `scalping_signals` table with proper indexing
   - Supports both stocks and cryptocurrencies
   - Stores historical analysis results

3. **Web API** (`src/web/scalping_signals.py`)
   - RESTful endpoints for data access
   - Real-time statistics and filtering
   - Integration with existing Flask app

4. **Frontend Interface** (`src/web/templates/scalping_signals.html`)
   - Modern, responsive dashboard
   - Real-time data updates
   - Advanced filtering and visualization

## 🔍 Analysis Process

### Step 1: Load Watchlist Tickers
- Queries active tickers from `watchlists` table
- Filters by `active = TRUE`
- Supports both stocks and cryptocurrencies

### Step 2: Market Data Analysis
For each ticker, calculates:
- **Volume Ratio**: Current volume ÷ 5-day average volume
- **Price Change**: % change from open to current price
- **Gap**: % change from previous close to open
- **Bid-Ask Spread**: Market liquidity indicator

### Step 3: News Sentiment Analysis
- Fetches last 12 hours of news headlines
- Performs sentiment analysis using AI models
- Aggregates sentiment scores per ticker
- Classifies as Bullish/Bearish/Neutral

### Step 4: Recommendation Generation
**Long Scalping Opportunity**:
- Volume ratio ≥ 2.0
- Price change ≥ 2.0%
- Sentiment = Bullish

**Short Scalping Opportunity**:
- Volume ratio ≥ 2.0
- Price change ≥ 2.0%
- Sentiment = Bearish

**High Momentum - Monitor Sentiment**:
- Meets volume/price criteria
- Mixed or neutral sentiment

### Step 5: Database Storage
- Stores results in `scalping_signals` table
- One record per ticker per day
- UPSERT functionality for updates
- JSON storage for headlines

## 🌐 API Endpoints

### Get Current Opportunities
```http
GET /api/scalping/opportunities
```
Returns current scalping opportunities with metadata.

### Run Analysis
```http
POST /api/scalping/run_analysis
```
Manually triggers scalping analysis for all active tickers.

### Get Today's Signals
```http
GET /api/scalping/today
```
Returns all signals generated today.

### Get Historical Data
```http
GET /api/scalping/history?days=7&limit=100
```
Returns historical signals with optional filtering.

### Filter by Type
```http
GET /api/scalping/opportunities_by_type?type=stock&recommendation=long
```
Filter opportunities by asset type and recommendation.

### Get Statistics
```http
GET /api/scalping/stats
```
Returns comprehensive statistics for today and weekly data.

### Setup Tables
```http
POST /api/scalping/setup
```
Creates/verifies database tables.

## 📈 Response Format

### Opportunities API Response
```json
{
  "timestamp": "2024-01-15T14:30:00Z",
  "total_signals": 25,
  "opportunities": 8,
  "data": [
    {
      "ticker": "AAPL",
      "asset_type": "stock",
      "price_open": 190.50,
      "price_now": 195.80,
      "volume_ratio": 2.7,
      "price_change_pct": 2.8,
      "sentiment": "Bullish",
      "recommendation": "Long Scalping Opportunity",
      "top_headlines": [
        {
          "title": "Apple posts stronger-than-expected earnings",
          "sentiment": "Positive"
        }
      ]
    }
  ]
}
```

### Statistics API Response
```json
{
  "success": true,
  "timestamp": "2024-01-15T14:30:00Z",
  "today": {
    "total_signals": 25,
    "opportunities": 8,
    "stocks": 18,
    "cryptos": 7,
    "avg_volume_ratio": 1.8,
    "avg_price_change": 1.2,
    "bullish_count": 12,
    "bearish_count": 8,
    "neutral_count": 5
  },
  "weekly": {
    "total_signals": 125,
    "opportunities": 45
  }
}
```

## ⚙️ Configuration

### Environment Variables
```bash
# Required API Keys
ALPHA_VANTAGE_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here  # For sentiment analysis

# Optional API Keys
FINNHUB_API_KEY=your_key_here
POLYGON_API_KEY=your_key_here
NEWS_API_KEY=your_key_here
```

### Scalping Thresholds
```python
# In src/core/scalping_analyzer.py
VOLUME_RATIO_THRESHOLD = 2.0      # Minimum volume ratio
PRICE_CHANGE_THRESHOLD = 2.0      # Minimum price change %
SENTIMENT_THRESHOLD = 2           # Sentiment score threshold
```

## 🔧 Automation

### Automated Scheduling
The scalping analysis is integrated into the main application scheduler:

```bash
# Runs automatically at 9:55 AM ET on trading days (Monday-Friday)
# Integrated with existing APScheduler in the Flask application
# No manual cron setup required
```

### Manual Execution
```bash
# Run analysis manually
python3 run_scalping_analysis.py

# Test the system
python3 test_scalping_analysis.py
```

## 📊 Database Schema

### scalping_signals Table
```sql
CREATE TABLE scalping_signals (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    asset_type VARCHAR(10) NOT NULL CHECK (asset_type IN ('stock', 'crypto')),
    date DATE NOT NULL,
    time_collected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    price_open FLOAT,
    price_now FLOAT,
    volume_ratio FLOAT,
    price_change_pct FLOAT,
    gap_pct FLOAT,
    bid_ask_spread FLOAT,
    sentiment_score INTEGER,
    sentiment_class VARCHAR(10) CHECK (sentiment_class IN ('Bullish', 'Neutral', 'Bearish')),
    recommendation VARCHAR(50),
    headlines_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date)
);
```

### Indexes
- `idx_scalping_signals_ticker` - For ticker lookups
- `idx_scalping_signals_date` - For date filtering
- `idx_scalping_signals_recommendation` - For recommendation filtering
- `idx_scalping_signals_sentiment` - For sentiment filtering

## 🧪 Testing

### Run All Tests
```bash
python3 test_scalping_analysis.py
```

### Test Components
1. **Database Setup**: Table creation and verification
2. **Watchlist Loading**: Active ticker retrieval
3. **Market Data**: Real-time price and volume data
4. **Sentiment Analysis**: News sentiment processing
5. **Recommendation Generation**: Trading signal logic
6. **API Endpoints**: Web service functionality
7. **Full Analysis**: End-to-end workflow

## 🚨 Troubleshooting

### Common Issues

1. **No Active Tickers**
   - Add tickers to watchlist via web interface
   - Ensure `active = TRUE` in database

2. **API Rate Limits**
   - Check API key configuration
   - Implement rate limiting if needed

3. **Database Connection**
   - Verify PostgreSQL is running
   - Check database credentials

4. **Sentiment Analysis Failures**
   - Ensure AI service is running (Ollama/OpenAI)
   - Check API key configuration

### Logs
- **Application Logs**: `logs/scalping_analysis.log`
- **Cron Logs**: `logs/scalping_cron.log`
- **Web App Logs**: Standard Flask logging

## 🔮 Future Enhancements

### Planned Features
1. **Real-time Streaming**: WebSocket updates for live data
2. **Advanced Filters**: Technical indicators, market cap, sector
3. **Backtesting**: Historical performance analysis
4. **Alert System**: Email/SMS notifications for opportunities
5. **Portfolio Integration**: Position sizing recommendations
6. **Machine Learning**: Enhanced prediction models

### Integration Points
- **Trading Execution**: Connect to broker APIs
- **Risk Management**: Position sizing and stop-loss
- **Performance Tracking**: P&L and win rate analysis
- **Market Data**: Additional data sources (Polygon, IEX, etc.)

## 📝 License

This scalping analysis system is part of the Trading AI Platform.
See the main project license for details.

## 🤝 Contributing

1. Follow the existing code structure
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure database migrations are backward compatible

---

**Note**: This system is designed for educational and research purposes. Always perform your own due diligence before making trading decisions. 