# Scalping Signals Page Duplication Instructions

## Overview
This document provides comprehensive instructions for duplicating the Scalping Signals page functionality. The system identifies short-term trading opportunities for both stocks and cryptocurrencies by analyzing volume spikes, price movements, sentiment, and market momentum.

## System Architecture

### Data Flow
```
Market Data → Volume Analysis → Price Movement → Sentiment Analysis → Scalping Signals → Database Storage → Frontend Display
```

### Key Components
1. **Scalping Analyzer**: Core engine for identifying scalping opportunities
2. **Market Data Collection**: Real-time price and volume data from multiple APIs
3. **Sentiment Analysis**: News sentiment analysis for trading signals
4. **Signal Generation**: Algorithm-based recommendation generation
5. **Database Storage**: PostgreSQL for signal persistence
6. **Frontend Display**: Real-time card-based interface with filtering

## Database Schema

### Scalping Signals Table
```sql
CREATE TABLE scalping_signals (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    asset_type VARCHAR(10) NOT NULL CHECK (asset_type IN ('stock', 'crypto')),
    date DATE NOT NULL,
    time_collected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    price_open DECIMAL(10,2),
    price_now DECIMAL(10,2),
    volume_ratio DECIMAL(10,4),
    price_change_pct DECIMAL(8,4),
    gap_pct DECIMAL(8,4),
    bid_ask_spread DECIMAL(8,4),
    sentiment_score DECIMAL(5,4),
    sentiment_class VARCHAR(20),
    recommendation TEXT,
    headlines_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date)
);

CREATE INDEX idx_scalping_signals_ticker ON scalping_signals (ticker);
CREATE INDEX idx_scalping_signals_date ON scalping_signals (date);
CREATE INDEX idx_scalping_signals_asset_type ON scalping_signals (asset_type);
CREATE INDEX idx_scalping_signals_recommendation ON scalping_signals (recommendation);
CREATE INDEX idx_scalping_signals_time_collected ON scalping_signals (time_collected);
```

## Core Classes Implementation

### 1. ScalpingAnalyzer Class

```python
class ScalpingAnalyzer:
    """Analyzes scalping opportunities for stocks and cryptocurrencies"""
    
    def __init__(self):
        """Initialize the scalping analyzer"""
        self.sentiment_analyzer = SentimentAnalyzer()
        self.data_fetcher = DataFetcher()
        self.session = requests.Session()
        
        # Scalping thresholds
        self.VOLUME_RATIO_THRESHOLD = 1.5  # Volume spike threshold
        self.PRICE_CHANGE_THRESHOLD = 1.0  # Price movement threshold
        self.SENTIMENT_THRESHOLD = 0.2     # Sentiment threshold
        
        # Market data APIs
        self.ALPHA_VANTAGE_API_KEY = Config.ALPHA_VANTAGE_API_KEY
        self.FINNHUB_API_KEY = getattr(Config, "FINNHUB_API_KEY", None)
        self.POLYGON_API_KEY = getattr(Config, "POLYGON_API_KEY", None)
        
        # News APIs
        self.NEWS_API_KEY = getattr(Config, "NEWS_API_KEY", None)
        self.YAHOO_FINANCE_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"
    
    def get_market_data(self, ticker: str, asset_type: str = "stock") -> Dict[str, Any]:
        """Get market data for scalping analysis"""
        try:
            if asset_type == "crypto":
                return self.get_crypto_market_data(ticker)
            else:
                return self.get_stock_market_data(ticker)
        except Exception as e:
            logger.error(f"Error getting market data for {ticker}: {e}")
            return {"error": str(e)}
    
    def get_stock_market_data(self, ticker: str) -> Dict[str, Any]:
        """Get stock market data using Alpha Vantage"""
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_INTRADAY",
                "symbol": ticker,
                "interval": "5min",
                "apikey": self.ALPHA_VANTAGE_API_KEY
            }
            
            response = self.session.get(url, params=params)
            data = response.json()
            
            if "Time Series (5min)" in data:
                time_series = data["Time Series (5min)"]
                timestamps = sorted(time_series.keys(), reverse=True)
                
                if len(timestamps) >= 2:
                    latest = time_series[timestamps[0]]
                    previous = time_series[timestamps[1]]
                    
                    price_now = float(latest["4. close"])
                    price_open = float(latest["1. open"])
                    price_previous = float(previous["4. close"])
                    
                    volume_now = float(latest["5. volume"])
                    volume_previous = float(previous["5. volume"])
                    
                    # Calculate metrics
                    price_change_pct = ((price_now - price_previous) / price_previous) * 100
                    gap_pct = ((price_open - price_previous) / price_previous) * 100
                    volume_ratio = volume_now / volume_previous if volume_previous > 0 else 1.0
                    
                    return {
                        "price_now": price_now,
                        "price_open": price_open,
                        "price_previous": price_previous,
                        "price_change_pct": price_change_pct,
                        "gap_pct": gap_pct,
                        "volume_ratio": volume_ratio,
                        "volume": volume_now,
                        "high": float(latest["2. high"]),
                        "low": float(latest["3. low"])
                    }
            
            return {"error": "No stock data available"}
            
        except Exception as e:
            logger.error(f"Error getting stock market data for {ticker}: {e}")
            return {"error": str(e)}
    
    def get_crypto_market_data(self, ticker: str) -> Dict[str, Any]:
        """Get crypto market data using Alpha Vantage"""
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "DIGITAL_CURRENCY_DAILY",
                "symbol": ticker,
                "market": "USD",
                "apikey": self.ALPHA_VANTAGE_API_KEY
            }
            
            response = self.session.get(url, params=params)
            data = response.json()
            
            if "Time Series (Digital Currency Daily)" in data:
                time_series = data["Time Series (Digital Currency Daily)"]
                dates = sorted(time_series.keys(), reverse=True)
                
                if len(dates) >= 2:
                    today_data = time_series[dates[0]]
                    yesterday_data = time_series[dates[1]]
                    
                    price_now = float(today_data["4a. close (USD)"])
                    price_open = float(today_data["1a. open (USD)"])
                    price_yesterday = float(yesterday_data["4a. close (USD)"])
                    
                    volume_today = float(today_data["5. volume"])
                    volume_yesterday = float(yesterday_data["5. volume"])
                    
                    # Calculate metrics
                    price_change_pct = ((price_now - price_yesterday) / price_yesterday) * 100
                    gap_pct = ((price_open - price_yesterday) / price_yesterday) * 100
                    volume_ratio = volume_today / volume_yesterday if volume_yesterday > 0 else 1.0
                    
                    return {
                        "price_now": price_now,
                        "price_open": price_open,
                        "price_yesterday": price_yesterday,
                        "price_change_pct": price_change_pct,
                        "gap_pct": gap_pct,
                        "volume_ratio": volume_ratio,
                        "volume": volume_today,
                        "high": float(today_data["2a. high (USD)"]),
                        "low": float(today_data["3a. low (USD)"])
                    }
            
            return {"error": "No crypto data available"}
            
        except Exception as e:
            logger.error(f"Error getting crypto market data for {ticker}: {e}")
            return {"error": str(e)}
    
    def get_news_and_sentiment(self, ticker: str, asset_type: str = "stock") -> Dict[str, Any]:
        """Get news and analyze sentiment for scalping signals"""
        try:
            # Get news data
            if asset_type == "crypto":
                news_data = self.data_fetcher.get_crypto_news(ticker, days_back=1)
            else:
                news_data = self.data_fetcher.get_company_news(ticker, days_back=1)
            
            if not news_data:
                return {
                    "sentiment_score": 0,
                    "sentiment_class": "Neutral",
                    "headlines": []
                }
            
            # Analyze sentiment
            sentiment_data = self.sentiment_analyzer.analyze_news_sentiment(
                news_data, ai_provider="ollama", symbol=ticker
            )
            
            # Extract headlines for storage
            headlines = []
            for article in news_data[:5]:  # Limit to 5 headlines
                headlines.append({
                    "headline": article.get("headline", ""),
                    "summary": article.get("summary", ""),
                    "url": article.get("url", ""),
                    "published": article.get("published", "")
                })
            
            return {
                "sentiment_score": sentiment_data.get("sentiment_score", 0),
                "sentiment_class": sentiment_data.get("sentiment_class", "Neutral"),
                "headlines": headlines
            }
            
        except Exception as e:
            logger.error(f"Error getting news and sentiment for {ticker}: {e}")
            return {
                "sentiment_score": 0,
                "sentiment_class": "Neutral",
                "headlines": []
            }
    
    def generate_scalping_recommendation(self, market_data: Dict, sentiment_data: Dict) -> str:
        """Generate scalping recommendation based on analysis"""
        try:
            volume_ratio = market_data.get("volume_ratio", 0)
            price_change_pct = market_data.get("price_change_pct", 0)
            sentiment_class = sentiment_data.get("sentiment_class", "Neutral")
            
            # Check if meets scalping criteria
            if (
                volume_ratio >= self.VOLUME_RATIO_THRESHOLD
                and abs(price_change_pct) >= self.PRICE_CHANGE_THRESHOLD
            ):
                if sentiment_class == "Bullish" and price_change_pct > 0:
                    return "Long Scalping Opportunity"
                elif sentiment_class == "Bearish" and price_change_pct < 0:
                    return "Short Scalping Opportunity"
                else:
                    return "High Momentum - Monitor Sentiment"
            else:
                return "No Strong Edge"
                
        except Exception as e:
            logger.error(f"Error generating scalping recommendation: {e}")
            return "Analysis Error"
    
    def analyze_scalping_opportunity(self, ticker: str, asset_type: str = "stock") -> Dict[str, Any]:
        """Complete scalping analysis for a single ticker"""
        try:
            # Get market data
            market_data = self.get_market_data(ticker, asset_type)
            if "error" in market_data:
                return {"error": market_data["error"]}
            
            # Get news and sentiment
            sentiment_data = self.get_news_and_sentiment(ticker, asset_type)
            
            # Generate recommendation
            recommendation = self.generate_scalping_recommendation(market_data, sentiment_data)
            
            # Store in database
            self.store_scalping_signal(ticker, asset_type, market_data, sentiment_data, recommendation)
            
            return {
                "ticker": ticker,
                "asset_type": asset_type,
                "market_data": market_data,
                "sentiment_data": sentiment_data,
                "recommendation": recommendation,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing scalping opportunity for {ticker}: {e}")
            return {"error": str(e)}
    
    def store_scalping_signal(self, ticker: str, asset_type: str, market_data: Dict, 
                            sentiment_data: Dict, recommendation: str) -> bool:
        """Store scalping signal in database"""
        try:
            insert_data = {
                "ticker": ticker,
                "asset_type": asset_type,
                "date": date.today(),
                "price_open": market_data.get("price_open"),
                "price_now": market_data.get("price_now"),
                "volume_ratio": market_data.get("volume_ratio"),
                "price_change_pct": market_data.get("price_change_pct"),
                "gap_pct": market_data.get("gap_pct"),
                "bid_ask_spread": 0.0,  # Placeholder
                "sentiment_score": sentiment_data.get("sentiment_score"),
                "sentiment_class": sentiment_data.get("sentiment_class"),
                "recommendation": recommendation,
                "headlines_json": json.dumps(sentiment_data.get("headlines", []))
            }
            
            # Use UPSERT to handle duplicates
            query = """
            INSERT INTO scalping_signals (
                ticker, asset_type, date, time_collected, price_open, price_now, volume_ratio,
                price_change_pct, gap_pct, bid_ask_spread, sentiment_score,
                sentiment_class, recommendation, headlines_json
            ) VALUES (
                %(ticker)s, %(asset_type)s, %(date)s, CURRENT_TIMESTAMP, %(price_open)s, %(price_now)s,
                %(volume_ratio)s, %(price_change_pct)s, %(gap_pct)s, %(bid_ask_spread)s,
                %(sentiment_score)s, %(sentiment_class)s, %(recommendation)s, %(headlines_json)s
            )
            ON CONFLICT (ticker, date)
            DO UPDATE SET
                price_now = EXCLUDED.price_now,
                volume_ratio = EXCLUDED.volume_ratio,
                price_change_pct = EXCLUDED.price_change_pct,
                sentiment_score = EXCLUDED.sentiment_score,
                sentiment_class = EXCLUDED.sentiment_class,
                recommendation = EXCLUDED.recommendation,
                headlines_json = EXCLUDED.headlines_json,
                time_collected = CURRENT_TIMESTAMP
            """
            
            execute_query(query, insert_data)
            logger.info(f"Stored scalping signal for {ticker}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing scalping signal for {ticker}: {e}")
            return False
    
    def run_morning_scalping_analysis(self) -> List[Dict[str, Any]]:
        """Run comprehensive scalping analysis for all watchlist symbols"""
        try:
            logger.info("Starting morning scalping analysis")
            
            # Get watchlist symbols
            from .watchlist_manager import WatchlistManager
            watchlist_manager = WatchlistManager()
            
            stock_symbols = watchlist_manager.get_stocks()
            crypto_symbols = watchlist_manager.get_cryptos()
            
            all_symbols = []
            for symbol in stock_symbols:
                all_symbols.append((symbol, "stock"))
            for symbol in crypto_symbols:
                all_symbols.append((symbol, "crypto"))
            
            results = []
            
            # Analyze each symbol
            for symbol, asset_type in all_symbols:
                try:
                    result = self.analyze_scalping_opportunity(symbol, asset_type)
                    if result and "error" not in result:
                        results.append(result)
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {e}")
                    continue
            
            logger.info(f"Completed scalping analysis: {len(results)} signals generated")
            return results
            
        except Exception as e:
            logger.error(f"Error in morning scalping analysis: {e}")
            return []
    
    def get_todays_scalping_signals(self) -> List[Dict[str, Any]]:
        """Get most recent trading day's scalping signals"""
        try:
            query = """
            SELECT ticker, asset_type, date, time_collected, price_open, price_now,
                   volume_ratio, price_change_pct, gap_pct, sentiment_class, 
                   recommendation, headlines_json
            FROM scalping_signals 
            WHERE date = (
                SELECT MAX(date) 
                FROM scalping_signals 
                WHERE date <= CURRENT_DATE
            )
            ORDER BY recommendation DESC, volume_ratio DESC
            """
            
            results = execute_query(query)
            
            signals = []
            if results is None:
                return signals
            
            for row in results:
                if isinstance(row, dict):
                    signal = dict(row)
                    # Parse headlines JSON
                    if signal.get("headlines_json"):
                        try:
                            signal["headlines"] = json.loads(signal["headlines_json"])
                        except:
                            signal["headlines"] = []
                    signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error getting today's scalping signals: {e}")
            return []
    
    def get_scalping_opportunities_api(self) -> Dict[str, Any]:
        """Get scalping opportunities for API response"""
        try:
            signals = self.get_todays_scalping_signals()
            
            # Filter for actual opportunities (not "No Strong Edge")
            opportunities = [
                signal for signal in signals 
                if signal.get("recommendation") != "No Strong Edge"
            ]
            
            # Convert to serializable format
            serializable_opportunities = []
            for opp in opportunities:
                serializable_opp = {
                    "ticker": opp.get("ticker"),
                    "asset_type": opp.get("asset_type"),
                    "date": opp.get("date").isoformat() if opp.get("date") else None,
                    "time_collected": opp.get("time_collected").isoformat() if opp.get("time_collected") else None,
                    "price_open": float(opp.get("price_open", 0)),
                    "price_now": float(opp.get("price_now", 0)),
                    "volume_ratio": float(opp.get("volume_ratio", 0)),
                    "price_change_pct": float(opp.get("price_change_pct", 0)),
                    "gap_pct": float(opp.get("gap_pct", 0)),
                    "sentiment": opp.get("sentiment_class"),
                    "recommendation": opp.get("recommendation"),
                    "headlines": opp.get("headlines", [])
                }
                serializable_opportunities.append(serializable_opp)
            
            # Create response object
            response = {
                "timestamp": datetime.now().isoformat(),
                "total_signals": len(signals),
                "opportunities": len(opportunities),
                "data": serializable_opportunities,
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error in scalping opportunities API: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "total_signals": 0,
                "opportunities": 0,
                "data": [],
            }
```

### 2. WatchlistManager Class

```python
class WatchlistManager:
    """Manages watchlist for scalping analysis"""
    
    def __init__(self):
        self.db_config = Config.DATABASE_CONFIG
        self.create_table_if_not_exists()
        self.populate_default_watchlist()
    
    def create_table_if_not_exists(self):
        """Create watchlists table if it doesn't exist"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS watchlists (
                            id SERIAL PRIMARY KEY,
                            symbol VARCHAR(20) NOT NULL,
                            type VARCHAR(10) NOT NULL CHECK (type IN ('stock', 'crypto')),
                            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(symbol, type)
                        )
                        """
                    )
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error creating watchlists table: {str(e)}")
            return False
    
    def populate_default_watchlist(self):
        """Populate default watchlist with common symbols"""
        try:
            default_stocks = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC'
            ]
            default_cryptos = [
                'BTC', 'ETH', 'ADA', 'DOT', 'LINK', 'UNI', 'AAVE', 'SOL', 'MATIC', 'AVAX'
            ]
            
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    for stock in default_stocks:
                        cursor.execute(
                            "INSERT INTO watchlists (symbol, type) VALUES (%s, 'stock') ON CONFLICT DO NOTHING",
                            (stock,)
                        )
                    for crypto in default_cryptos:
                        cursor.execute(
                            "INSERT INTO watchlists (symbol, type) VALUES (%s, 'crypto') ON CONFLICT DO NOTHING",
                            (crypto,)
                        )
                    conn.commit()
        except Exception as e:
            logger.error(f"Error populating default watchlist: {str(e)}")
    
    def get_stocks(self):
        """Get all stock symbols from watchlist"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT symbol FROM watchlists WHERE type = 'stock' ORDER BY symbol"
                    )
                    stocks = [row[0] for row in cursor.fetchall()]
                    return stocks
        except Exception as e:
            logger.error(f"Error getting stocks: {str(e)}")
            return []
    
    def get_cryptos(self):
        """Get all crypto symbols from watchlist"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT symbol FROM watchlists WHERE type = 'crypto' ORDER BY symbol"
                    )
                    cryptos = [row[0] for row in cursor.fetchall()]
                    return cryptos
        except Exception as e:
            logger.error(f"Error getting cryptos: {str(e)}")
            return []
```

## API Endpoints

### 1. Scalping Signals Page Route

```python
@app.route("/scalping_signals")
def scalping_signals_page():
    """Scalping signals page - shows historical signals"""
    signals = []
    try:
        logger.info("[SCALPING] GET /scalping_signals page requested")
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
                for row in cur.fetchall():
                    # Parse headlines JSON
                    headlines = []
                    if row["headlines_json"]:
                        try:
                            headlines = json.loads(row["headlines_json"])
                        except Exception:
                            headlines = []
                    signals.append(
                        {
                            "ticker": row["ticker"],
                            "asset_type": row["asset_type"],
                            "date": row["date"],
                            "time_collected": row["time_collected"],
                            "price_open": row["price_open"],
                            "price_now": row["price_now"],
                            "volume_ratio": row["volume_ratio"],
                            "price_change_pct": row["price_change_pct"],
                            "gap_pct": row["gap_pct"],
                            "sentiment_class": row["sentiment_class"],
                            "recommendation": row["recommendation"],
                            "headlines": headlines,
                        }
                    )
        logger.info(f"[SCALPING] Loaded {len(signals)} signals")
    except Exception as e:
        logger.error(f"[SCALPING] Error loading scalping signals: {e}")
    
    return render_template("scalping_signals.html", signals=signals)
```

### 2. Scalping Opportunities API

```python
@app.route("/api/scalping/opportunities", methods=["GET"])
def get_scalping_opportunities():
    """API endpoint to get current scalping opportunities"""
    try:
        scalping_analyzer = ScalpingAnalyzer()
        result = scalping_analyzer.get_scalping_opportunities_api()
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            **result
        })
        
    except Exception as e:
        logger.error(f"[SCALPING] Error getting opportunities: {e}")
        return jsonify({
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500
```

### 3. Scalping Statistics API

```python
@app.route("/api/scalping/stats", methods=["GET"])
def get_scalping_stats():
    """API endpoint to get scalping statistics"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get today's stats
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_signals,
                        COUNT(CASE WHEN recommendation != 'No Strong Edge' THEN 1 END) as opportunities,
                        COUNT(CASE WHEN asset_type = 'stock' THEN 1 END) as stocks,
                        COUNT(CASE WHEN asset_type = 'crypto' THEN 1 END) as cryptos
                    FROM scalping_signals 
                    WHERE date = CURRENT_DATE
                """)
                
                today_stats = cur.fetchone()
                
                return jsonify({
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "today": {
                        "total_signals": today_stats[0] if today_stats else 0,
                        "opportunities": today_stats[1] if today_stats else 0,
                        "stocks": today_stats[2] if today_stats else 0,
                        "cryptos": today_stats[3] if today_stats else 0
                    }
                })
                
    except Exception as e:
        logger.error(f"[SCALPING] Error getting stats: {e}")
        return jsonify({
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500
```

### 4. Run Analysis API

```python
@app.route("/api/scalping/run_analysis", methods=["POST"])
def run_scalping_analysis():
    """API endpoint to run scalping analysis"""
    try:
        scalping_analyzer = ScalpingAnalyzer()
        results = scalping_analyzer.run_morning_scalping_analysis()
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "signals_generated": len(results),
            "message": f"Analysis completed. Generated {len(results)} signals."
        })
        
    except Exception as e:
        logger.error(f"[SCALPING] Error running analysis: {e}")
        return jsonify({
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500
```

### 5. Historical Signals API

```python
@app.route("/api/scalping/history", methods=["GET"])
def get_scalping_history():
    """API endpoint to get historical scalping signals"""
    try:
        days = request.args.get("days", 7, type=int)
        limit = request.args.get("limit", 100, type=int)
        
        query = """
        SELECT ticker, asset_type, date, time_collected, price_open, price_now,
               volume_ratio, price_change_pct, gap_pct, sentiment_class, 
               recommendation, headlines_json
        FROM scalping_signals
        WHERE date >= CURRENT_DATE - INTERVAL '%s days'
        ORDER BY date DESC, time_collected DESC
        LIMIT %s
        """
        
        results = execute_query(query, (days, limit))
        signals = []
        
        if results:
            for row in results:
                if isinstance(row, dict):
                    signal = dict(row)
                    # Parse headlines JSON
                    if signal.get("headlines_json"):
                        try:
                            signal["headlines"] = json.loads(signal["headlines_json"])
                        except:
                            signal["headlines"] = []
                    signals.append(signal)
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "days": days,
            "signals": signals,
            "count": len(signals),
        })
        
    except Exception as e:
        logger.error(f"[SCALPING] Error getting scalping history: {e}")
        return jsonify({
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500
```

## Frontend Implementation

### HTML Template Structure

```html
{% extends "base.html" %}

{% block title %}Scalping Signals - Trading AI{% endblock %}

{% block content %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/scalping_signals.css') }}">

<!-- Header -->
<div class="row mb-4">
    <div class="col-12">
        <h1 class="mb-4"><i class="fas fa-chart-line"></i> Scalping Signals</h1>
        <p class="lead">Real-time scalping opportunities for stocks and cryptocurrencies</p>
    </div>
</div>

<!-- Stats Cards -->
<div class="row mb-4" id="statsCards">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-chart-bar"></i> Scalping Statistics</h5>
            </div>
            <div class="card-body">
                <div class="row text-center">
                    <div class="col-md-3">
                        <div class="text-center">
                            <h4 class="text-primary" id="totalSignals">-</h4>
                            <small>Total Signals</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="text-center">
                            <h4 class="text-success" id="totalOpportunities">-</h4>
                            <small>Opportunities</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="text-center">
                            <h4 class="text-info" id="stockCount">-</h4>
                            <small>Stocks</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="text-center">
                            <h4 class="text-warning" id="cryptoCount">-</h4>
                            <small>Cryptos</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Controls -->
<div class="row mb-4">
    <div class="col-12">
        <div class="card">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center flex-wrap">
                    <div class="btn-toolbar flex-wrap filter-buttons" role="toolbar">
                        <div class="btn-group me-2 mb-2" role="group">
                            <button class="btn btn-outline-primary filter-btn active" data-filter="all">
                                <i class="fas fa-list"></i> All
                            </button>
                        </div>
                        <div class="btn-group me-2 mb-2" role="group">
                            <button class="btn btn-outline-success filter-btn" data-filter="long">
                                <i class="fas fa-arrow-up"></i> Long
                            </button>
                        </div>
                        <div class="btn-group me-2 mb-2" role="group">
                            <button class="btn btn-outline-danger filter-btn" data-filter="short">
                                <i class="fas fa-arrow-down"></i> Short
                            </button>
                        </div>
                        <div class="btn-group me-2 mb-2" role="group">
                            <button class="btn btn-outline-warning filter-btn" data-filter="momentum">
                                <i class="fas fa-fire"></i> Momentum
                            </button>
                        </div>
                        <div class="btn-group me-2 mb-2" role="group">
                            <button class="btn btn-outline-info filter-btn" data-filter="stocks">
                                <i class="fas fa-chart-bar"></i> Stocks
                            </button>
                        </div>
                        <div class="btn-group me-2 mb-2" role="group">
                            <button class="btn btn-outline-secondary filter-btn" data-filter="crypto">
                                <i class="fas fa-coins"></i> Crypto
                            </button>
                        </div>
                    </div>
                    <div class="d-flex align-items-center">
                        <div class="form-check form-switch me-3">
                            <input class="form-check-input" type="checkbox" id="autoRefreshToggle">
                            <label class="form-check-label" for="autoRefreshToggle">
                                <i class="fas fa-sync-alt"></i> Auto-refresh (30min)
                            </label>
                        </div>
                        <button class="btn btn-success me-2" onclick="runAnalysis()">
                            <i class="fas fa-play"></i> Run Analysis
                        </button>
                        <button class="btn btn-primary" onclick="refreshData()">
                            <i class="fas fa-sync-alt"></i> Refresh
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Loading Spinner -->
<div class="row" id="loadingSpinner" style="display: none;">
    <div class="col-12">
        <div class="card">
            <div class="card-body text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Analyzing scalping opportunities...</p>
            </div>
        </div>
    </div>
</div>

<!-- Opportunities Grid -->
<div class="row mb-4">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-bolt"></i> Scalping Opportunities</h5>
            </div>
            <div class="card-body">
                <!-- Modern Summary Pill -->
                <div id="stockSummaryPill"></div>
                <div id="cryptoSummaryPill"></div>
                <!-- Responsive Grid for Opportunities -->
                <div id="opportunitiesGrid" class="row g-3"></div>
            </div>
        </div>
    </div>
</div>

<!-- No Data Message -->
<div class="row" id="noDataMessage" style="display: none;">
    <div class="col-12">
        <div class="alert alert-info">
            <i class="fas fa-info-circle"></i> No scalping opportunities found.
            Click "Run Analysis" to scan for new opportunities.
        </div>
    </div>
</div>

<!-- Floating Refresh Button -->
<button class="btn btn-primary btn-lg refresh-btn" onclick="refreshData()" title="Refresh Data">
    <i class="fas fa-sync-alt"></i>
</button>

{% endblock %}
```

### JavaScript Functions

```javascript
let currentFilter = 'all';
let opportunitiesData = [];
let autoRefreshInterval = null;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    try {
        initializePage();
    } catch (error) {
        console.error('Error in DOMContentLoaded: ' + error.message);
    }
});

function initializePage() {
    try {
        console.log('Scalping signals page DOMContentLoaded');
        loadStats();
        loadOpportunities();
        setupFilterButtons();
        setupAutoRefreshToggle();
    } catch (error) {
        console.error('Error in initializePage: ' + error.message);
    }
}

function setupFilterButtons() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all buttons
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            currentFilter = this.dataset.filter;
            filterOpportunities();
        });
    });
}

function setupAutoRefreshToggle() {
    const toggle = document.getElementById('autoRefreshToggle');
    if (toggle) {
        toggle.addEventListener('change', function() {
            if (this.checked) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        });
        // Initial state based on localStorage or default to off
        const isAutoRefreshEnabled = localStorage.getItem('autoRefreshEnabled') === 'true';
        toggle.checked = isAutoRefreshEnabled;
        if (isAutoRefreshEnabled) {
            startAutoRefresh();
        }
    }
}

function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    autoRefreshInterval = setInterval(() => {
        console.log('Auto-refresh triggered');
        refreshData();
    }, 30 * 60 * 1000); // 30 minutes
    localStorage.setItem('autoRefreshEnabled', 'true');
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
    localStorage.setItem('autoRefreshEnabled', 'false');
}

function showLoading() {
    document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('opportunitiesGrid').style.display = 'none';
    document.getElementById('noDataMessage').style.display = 'none';
    document.getElementById('errorMessage').style.display = 'none';
}

function hideLoading() {
    document.getElementById('loadingSpinner').style.display = 'none';
    document.getElementById('opportunitiesGrid').style.display = 'block';
}

async function loadStats() {
    try {
        console.log('Loading scalping stats...');
        const response = await fetch('/api/scalping/stats');
        const data = await response.json();
        
        if (data.success && data.today) {
            document.getElementById('totalSignals').textContent = data.today.total_signals || 0;
            document.getElementById('totalOpportunities').textContent = data.today.opportunities || 0;
            document.getElementById('stockCount').textContent = data.today.stocks || 0;
            document.getElementById('cryptoCount').textContent = data.today.cryptos || 0;
        }
    } catch (error) {
        console.error('Error loading stats: ' + error);
    }
}

async function loadOpportunities() {
    showLoading();
    try {
        console.log('Loading scalping opportunities...');
        const response = await fetch('/api/scalping/opportunities');
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status} - ${data.error || 'Unknown error'}`);
        }
        
        if (data.data && Array.isArray(data.data)) {
            opportunitiesData = data.data;
            console.log('Loaded opportunities: ' + opportunitiesData.length);
            filterOpportunities();
        } else {
            console.warn('No opportunities data returned from API');
            showNoDataMessage();
        }
    } catch (error) {
        console.error('Error loading opportunities: ' + error);
        showErrorMessage(error.message || 'Failed to load opportunities');
    } finally {
        hideLoading();
    }
}

function filterOpportunities() {
    try {
        console.log('Filtering opportunities with filter: ' + currentFilter);
        let filteredData = opportunitiesData;
        
        // Apply filters
        switch (currentFilter) {
            case 'long':
                filteredData = opportunitiesData.filter(opp => 
                    opp.recommendation === 'Long Scalping Opportunity'
                );
                break;
            case 'short':
                filteredData = opportunitiesData.filter(opp => 
                    opp.recommendation === 'Short Scalping Opportunity'
                );
                break;
            case 'momentum':
                filteredData = opportunitiesData.filter(opp => 
                    opp.recommendation === 'High Momentum - Monitor Sentiment'
                );
                break;
            case 'stocks':
                filteredData = opportunitiesData.filter(opp => 
                    opp.asset_type === 'stock'
                );
                break;
            case 'crypto':
                filteredData = opportunitiesData.filter(opp => 
                    opp.asset_type === 'crypto'
                );
                break;
            default:
                // 'all' - no filtering
                break;
        }
        
        console.log('Filtered opportunities count: ' + filteredData.length);
        renderOpportunities(filteredData);
    } catch (error) {
        console.error('Error in filterOpportunities: ' + error.message);
    }
}

function renderOpportunityCard(opp) {
    // Asset badge
    const badgeClass = opp.asset_type === 'crypto' ? 'modern-badge crypto' : 'modern-badge';
    const badgeIcon = opp.asset_type === 'crypto' ? 'fa-coins' : 'fa-chart-bar';
    
    // Sentiment icon
    let sentimentIcon = 'fa-minus';
    if (opp.sentiment?.toLowerCase() === 'bullish') sentimentIcon = 'fa-arrow-up';
    else if (opp.sentiment?.toLowerCase() === 'bearish') sentimentIcon = 'fa-arrow-down';
    
    // Recommendation class
    let recClass = 'recommendation';
    if (opp.recommendation === 'Short Scalping Opportunity') recClass += ' short';
    if (opp.recommendation === 'High Momentum - Monitor Sentiment') recClass += ' momentum';
    
    return `
        <div class="col-12 col-md-6 col-lg-4 col-xl-3">
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
                    <div class="modern-card-row">
                        <span class="label">Recommendation</span>
                        <span class="${recClass}">${opp.recommendation || 'No Strong Edge'}</span>
                    </div>
                </div>
                <div class="modern-card-footer">
                    <button title="View Details" onclick="viewDetails('${opp.ticker}')"><i class="fas fa-eye"></i></button>
                    <button title="Add to Watchlist" onclick="addToWatchlist('${opp.ticker}')"><i class="fas fa-plus"></i></button>
                </div>
            </div>
        </div>
    `;
}

function renderGroup(group, groupLabel, iconClass, summaryPillId) {
    if (!group.length) {
        document.getElementById(summaryPillId).innerHTML = '';
        return '';
    }
    
    // Calculate group statistics
    const avgVolumeRatio = group.reduce((sum, opp) => sum + (opp.volume_ratio || 0), 0) / group.length;
    const avgPriceChange = group.reduce((sum, opp) => sum + (opp.price_change_pct || 0), 0) / group.length;
    const longOpportunities = group.filter(opp => opp.recommendation === 'Long Scalping Opportunity').length;
    const shortOpportunities = group.filter(opp => opp.recommendation === 'Short Scalping Opportunity').length;
    
    // Modern summary pill
    document.getElementById(summaryPillId).innerHTML = `
        <div class="modern-summary-pill">
            <i class="fas ${iconClass}"></i> ${groupLabel}
            <span class="pill-stat ms-4"><i class="fas fa-signal"></i> <span>${group.length}</span> <span class="pill-label">Signals</span></span>
            <span class="pill-stat"><i class="fas fa-chart-line"></i> <span>${avgVolumeRatio.toFixed(2)}x</span> <span class="pill-label">Avg Vol</span></span>
            <span class="pill-stat"><i class="fas fa-percentage"></i> <span>${avgPriceChange.toFixed(2)}%</span> <span class="pill-label">Avg Change</span></span>
            <span class="pill-stat"><i class="fas fa-arrow-up text-success"></i> <span>${longOpportunities}</span> <span class="pill-label">Long</span></span>
            <span class="pill-stat"><i class="fas fa-arrow-down text-danger"></i> <span>${shortOpportunities}</span> <span class="pill-label">Short</span></span>
        </div>
    `;
    
    // Modern grid of cards
    return `<div class="row g-3">${group.map(opp => renderOpportunityCard(opp)).join('')}</div>`;
}

function renderAllOpportunities(stocks, cryptos) {
    try {
        console.log('renderAllOpportunities called with stocks: ' + stocks.length + ', cryptos: ' + cryptos.length);
        const grid = document.getElementById('opportunitiesGrid');
        
        const stockHtml = renderGroup(stocks, 'Stock Opportunities', 'fa-chart-bar', 'stockSummaryPill');
        const cryptoHtml = renderGroup(cryptos, 'Crypto Opportunities', 'fa-coins', 'cryptoSummaryPill');
        
        grid.innerHTML = stockHtml + cryptoHtml;
    } catch (error) {
        console.error('Error in renderAllOpportunities: ' + error.message);
    }
}

function renderOpportunities(opportunities) {
    try {
        console.log('Rendering ' + (opportunities ? opportunities.length : 0) + ' opportunity cards');
        
        const grid = document.getElementById('opportunitiesGrid');
        if (!opportunities || opportunities.length === 0) {
            console.warn('No opportunities to render');
            showNoDataMessage();
            return;
        }
        
        document.getElementById('noDataMessage').style.display = 'none';

        // Group by asset_type
        const stocks = opportunities.filter(opp => opp.asset_type === 'stock');
        const cryptos = opportunities.filter(opp => opp.asset_type === 'crypto');
        
        console.log('Grouped stocks: ' + stocks.length + ', cryptos: ' + cryptos.length);

        // Call the function to render the opportunities
        renderAllOpportunities(stocks, cryptos);
    } catch (error) {
        console.error('Error in renderOpportunities: ' + error.message);
    }
}

function showNoDataMessage() {
    console.warn('No data message shown (no opportunities)');
    document.getElementById('opportunitiesGrid').innerHTML = '';
    document.getElementById('noDataMessage').style.display = 'block';
}

function showErrorMessage(message) {
    console.warn('Show error message: ' + message);
    document.getElementById('opportunitiesGrid').innerHTML = '';
    document.getElementById('noDataMessage').style.display = 'none';
    document.getElementById('errorMessage').style.display = 'block';
    document.getElementById('errorText').textContent = message;
}

async function runAnalysis() {
    console.log('Run Analysis button clicked');
    showLoading();
    try {
        const response = await fetch('/api/scalping/run_analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        
        if (data.success) {
            console.log('Analysis completed successfully');
            // Reload data after analysis
            await loadStats();
            await loadOpportunities();
            // Show success message
            showAlert('Analysis completed successfully!', 'success');
        } else {
            console.error('Analysis failed: ' + (data.error || 'Unknown error'));
            showAlert('Analysis failed: ' + (data.error || 'Unknown error'), 'danger');
        }
    } catch (error) {
        console.error('Error running analysis: ' + error);
        showAlert('Error running analysis: ' + error.message, 'danger');
    } finally {
        hideLoading();
    }
}

async function refreshData() {
    console.log('Refresh button clicked');
    await loadStats();
    await loadOpportunities();
}

function showAlert(message, type) {
    console.log('Show alert: ' + message);
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Quick action functions
function viewDetails(ticker) {
    console.log('View details clicked for ' + ticker);
    // Navigate to stock analysis page
    window.open(`/?symbol=${ticker}`, '_blank');
}

function addToWatchlist(ticker) {
    console.log('Add to watchlist clicked for ' + ticker);
    // TODO: Implement add to watchlist functionality
    showAlert(`${ticker} added to watchlist!`, 'success');
}
```

## Configuration

### Environment Variables

```python
# API Keys
ALPHA_VANTAGE_API_KEY = "your_alpha_vantage_api_key"
FINNHUB_API_KEY = "your_finnhub_api_key"
POLYGON_API_KEY = "your_polygon_api_key"
NEWS_API_KEY = "your_news_api_key"

# Database Configuration
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "trading_db",
    "user": "trading_user",
    "password": "your_password"
}

# Redis Configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# AI Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:3b"

# Scalping Thresholds
VOLUME_RATIO_THRESHOLD = 1.5
PRICE_CHANGE_THRESHOLD = 1.0
SENTIMENT_THRESHOLD = 0.2
```

## Caching Strategy

### Redis Implementation for Scalping Data

```python
class ScalpingCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True
        )
    
    def get_scalping_opportunities(self):
        """Get cached scalping opportunities"""
        try:
            key = "scalping_opportunities"
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except:
            return None
    
    def set_scalping_opportunities(self, data: Dict, ttl: int = 600):
        """Cache scalping opportunities for 10 minutes"""
        try:
            key = "scalping_opportunities"
            self.redis_client.setex(key, ttl, json.dumps(data))
            return True
        except:
            return False
    
    def get_scalping_stats(self):
        """Get cached scalping statistics"""
        try:
            key = "scalping_stats"
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except:
            return None
    
    def set_scalping_stats(self, data: Dict, ttl: int = 300):
        """Cache scalping statistics for 5 minutes"""
        try:
            key = "scalping_stats"
            self.redis_client.setex(key, ttl, json.dumps(data))
            return True
        except:
            return False
```

## Deployment Steps

### 1. Database Setup
```bash
# Create database
createdb trading_db

# Run schema creation scripts
psql trading_db < scalping_schema.sql
```

### 2. Redis Setup
```bash
# Install Redis
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis-server
```

### 3. AI Model Setup (Ollama)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull qwen2.5:3b
```

### 4. Application Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ALPHA_VANTAGE_API_KEY="your_key"
export FINNHUB_API_KEY="your_key"

# Run application
python app.py
```

## Testing

### Unit Tests
```python
def test_scalping_analyzer():
    analyzer = ScalpingAnalyzer()
    result = analyzer.analyze_scalping_opportunity('AAPL', 'stock')
    assert 'ticker' in result
    assert 'market_data' in result
    assert 'sentiment_data' in result

def test_scalping_recommendation():
    analyzer = ScalpingAnalyzer()
    market_data = {"volume_ratio": 2.0, "price_change_pct": 1.5}
    sentiment_data = {"sentiment_class": "Bullish"}
    recommendation = analyzer.generate_scalping_recommendation(market_data, sentiment_data)
    assert recommendation in ["Long Scalping Opportunity", "Short Scalping Opportunity", "High Momentum - Monitor Sentiment", "No Strong Edge"]

def test_scalping_storage():
    analyzer = ScalpingAnalyzer()
    market_data = {"price_open": 100, "price_now": 102, "volume_ratio": 1.5}
    sentiment_data = {"sentiment_score": 0.3, "sentiment_class": "Bullish", "headlines": []}
    success = analyzer.store_scalping_signal('TEST', 'stock', market_data, sentiment_data, 'Test Recommendation')
    assert success == True

def test_watchlist_manager():
    manager = WatchlistManager()
    stocks = manager.get_stocks()
    cryptos = manager.get_cryptos()
    assert len(stocks) > 0
    assert len(cryptos) > 0
    assert 'AAPL' in stocks
    assert 'BTC' in cryptos
```

## Performance Optimization

### 1. Caching
- Redis caching with 5-10 minute TTL for scalping analysis results
- Database query optimization with proper indexes
- API response caching for frequently accessed data

### 2. Batch Processing
- Process multiple symbols in parallel
- Use shared news data for efficiency
- Implement circuit breakers for external API calls

### 3. Monitoring
- Log all scalping API calls and analysis results
- Monitor cache hit rates
- Track scalping signal accuracy over time

## Troubleshooting

### Common Issues

1. **API Rate Limiting**
   - Implement delays between Alpha Vantage API calls
   - Use multiple API keys if available
   - Cache results aggressively

2. **Market Data Availability**
   - Handle cases where market data is not available
   - Implement fallback to alternative data sources
   - Add error handling for invalid symbols

3. **News Data Issues**
   - Handle cases with limited news
   - Implement fallback to general market news
   - Cache news data to reduce API calls

4. **Memory Issues**
   - Limit concurrent scalping analysis requests
   - Implement garbage collection
   - Monitor memory usage during batch processing

## Conclusion

This implementation provides a complete system for identifying and displaying scalping opportunities for both stocks and cryptocurrencies. The system is designed to be scalable, reliable, and maintainable with proper error handling, caching, and monitoring.

Key features:
- Real-time scalping opportunity identification
- Multi-asset support (stocks and crypto)
- Volume and price movement analysis
- AI-powered sentiment analysis
- Card-based frontend interface
- Redis caching for performance
- PostgreSQL for data persistence
- RESTful API for frontend integration
- Batch processing for efficiency
- Comprehensive error handling and monitoring
- Auto-refresh functionality
- Advanced filtering capabilities
