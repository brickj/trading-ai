# Crypto Page Duplication Instructions

## Overview
This document provides comprehensive instructions for duplicating the Crypto page functionality. The system analyzes cryptocurrencies from a watchlist, performs sentiment analysis on crypto news, generates trading signals, and displays opportunities in a card-based interface.

## System Architecture

### Data Flow
```
Crypto Watchlist → Market Data (Alpha Vantage) → News Analysis → Sentiment Analysis → Trading Signals → Frontend Cards Display
```

### Key Components
1. **Watchlist Management**: Crypto symbols stored in PostgreSQL
2. **Market Data Collection**: Real-time crypto prices and metrics
3. **News Analysis**: Crypto-specific news sentiment analysis
4. **Trading Strategy**: Crypto-specific recommendation generation
5. **Scalping Analysis**: Short-term trading opportunities
6. **Frontend Display**: Card-based interface with real-time updates

## Database Schema

### Watchlists Table
```sql
CREATE TABLE watchlists (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    type VARCHAR(10) NOT NULL CHECK (type IN ('stock', 'crypto')),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, type)
);

CREATE INDEX idx_watchlists_type ON watchlists (type);
CREATE INDEX idx_watchlists_symbol ON watchlists (symbol);
```

### Scalping Signals Table
```sql
CREATE TABLE scalping_signals (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    asset_type VARCHAR(10) NOT NULL CHECK (asset_type IN ('stock', 'crypto')),
    date DATE NOT NULL,
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scalping_signals_ticker ON scalping_signals (ticker);
CREATE INDEX idx_scalping_signals_date ON scalping_signals (date);
CREATE INDEX idx_scalping_signals_asset_type ON scalping_signals (asset_type);
```

### Preloaded Opportunities Table
```sql
CREATE TABLE preloaded_opportunities (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    opportunity_type VARCHAR(20) NOT NULL,
    data JSONB NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_preloaded_opportunities_symbol ON preloaded_opportunities (symbol);
CREATE INDEX idx_preloaded_opportunities_type ON preloaded_opportunities (opportunity_type);
CREATE INDEX idx_preloaded_opportunities_timestamp ON preloaded_opportunities (timestamp);
```

## Core Classes Implementation

### 1. WatchlistManager Class

```python
class WatchlistManager:
    """Manages watchlist stocks and cryptocurrencies in PostgreSQL database"""
    
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
        """Populate default watchlist with common cryptos"""
        try:
            default_cryptos = [
                'BTC', 'ETH', 'ADA', 'DOT', 'LINK', 'UNI', 'AAVE', 'SOL', 'MATIC', 'AVAX'
            ]
            
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    for crypto in default_cryptos:
                        cursor.execute(
                            "INSERT INTO watchlists (symbol, type) VALUES (%s, 'crypto') ON CONFLICT DO NOTHING",
                            (crypto,)
                        )
                    conn.commit()
        except Exception as e:
            logger.error(f"Error populating default watchlist: {str(e)}")
    
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
    
    def add_crypto(self, symbol: str):
        """Add a crypto to the watchlist"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO watchlists (symbol, type) VALUES (%s, 'crypto') ON CONFLICT DO NOTHING",
                        (symbol.upper(),)
                    )
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error adding crypto {symbol}: {str(e)}")
            return False
```

### 2. ScalpingAnalyzer Class

```python
class ScalpingAnalyzer:
    """Analyzes scalping opportunities for cryptocurrencies"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.data_fetcher = DataFetcher()
        self.session = requests.Session()
        
        # Crypto-specific thresholds
        self.VOLUME_RATIO_THRESHOLD = 1.5
        self.PRICE_CHANGE_THRESHOLD = 1.0
        self.SENTIMENT_THRESHOLD = 0.2
        
        # API keys
        self.ALPHA_VANTAGE_API_KEY = Config.ALPHA_VANTAGE_API_KEY
    
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
    
    def get_crypto_news_and_sentiment(self, ticker: str) -> Dict[str, Any]:
        """Get crypto news and analyze sentiment"""
        try:
            # Get crypto news from Alpha Vantage
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "NEWS_SENTIMENT",
                "tickers": ticker,
                "apikey": self.ALPHA_VANTAGE_API_KEY,
                "limit": 20
            }
            
            response = self.session.get(url, params=params)
            data = response.json()
            
            headlines = []
            sentiment_scores = []
            
            if "feed" in data:
                for article in data["feed"][:5]:  # Limit to 5 articles
                    headline = article["title"]
                    summary = article["summary"]
                    
                    headlines.append({
                        "headline": headline,
                        "summary": summary,
                        "url": article["url"],
                        "published": article["time_published"]
                    })
                    
                    # Get sentiment score if available
                    if "overall_sentiment_score" in article:
                        sentiment_scores.append(float(article["overall_sentiment_score"]))
            
            # Calculate average sentiment
            if sentiment_scores:
                sentiment_score = sum(sentiment_scores) / len(sentiment_scores)
            else:
                sentiment_score = 0.0
            
            # Classify sentiment
            if sentiment_score > 0.1:
                sentiment_class = "Bullish"
            elif sentiment_score < -0.1:
                sentiment_class = "Bearish"
            else:
                sentiment_class = "Neutral"
            
            return {
                "sentiment_score": sentiment_score,
                "sentiment_class": sentiment_class,
                "headlines": headlines,
            }
            
        except Exception as e:
            logger.error(f"Error getting crypto news and sentiment for {ticker}: {e}")
            return {"sentiment_score": 0, "sentiment_class": "Neutral", "headlines": []}
    
    def generate_crypto_scalping_recommendation(self, market_data: Dict, sentiment_data: Dict) -> str:
        """Generate crypto scalping recommendation"""
        try:
            volume_ratio = market_data.get("volume_ratio", 0)
            price_change_pct = market_data.get("price_change_pct", 0)
            sentiment_class = sentiment_data.get("sentiment_class", "Neutral")
            
            # Check if meets crypto scalping criteria
            if (
                volume_ratio >= self.VOLUME_RATIO_THRESHOLD
                and abs(price_change_pct) >= self.PRICE_CHANGE_THRESHOLD
            ):
                if sentiment_class == "Bullish" and price_change_pct > 0:
                    return "Long Crypto Scalping Opportunity"
                elif sentiment_class == "Bearish" and price_change_pct < 0:
                    return "Short Crypto Scalping Opportunity"
                else:
                    return "High Crypto Momentum - Monitor Sentiment"
            else:
                return "No Strong Crypto Edge"
                
        except Exception as e:
            logger.error(f"Error generating crypto recommendation: {e}")
            return "Analysis Error"
    
    def analyze_crypto_opportunity(self, ticker: str) -> Dict[str, Any]:
        """Complete crypto analysis for a single ticker"""
        try:
            # Get market data
            market_data = self.get_crypto_market_data(ticker)
            if "error" in market_data:
                return {"error": market_data["error"]}
            
            # Get news and sentiment
            sentiment_data = self.get_crypto_news_and_sentiment(ticker)
            
            # Generate recommendation
            recommendation = self.generate_crypto_scalping_recommendation(market_data, sentiment_data)
            
            # Store in database
            self.store_scalping_signal(ticker, "crypto", market_data, sentiment_data, recommendation)
            
            return {
                "symbol": ticker,
                "type": "crypto",
                "market_data": market_data,
                "sentiment_data": sentiment_data,
                "recommendation": recommendation,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing crypto opportunity for {ticker}: {e}")
            return {"error": str(e)}
```

### 3. BatchProcessor Class

```python
class BatchProcessor:
    """Processes crypto analysis in batches for performance"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.data_fetcher = DataFetcher()
        self.scalping_analyzer = ScalpingAnalyzer()
    
    def _process_single_crypto(self, symbol: str, shared_news: List[Dict], days_back: int) -> Optional[Dict[str, Any]]:
        """Process a single crypto symbol"""
        try:
            # Get crypto price data
            price_data = self.data_fetcher.get_crypto_price(symbol)
            if not price_data or "current_price" not in price_data:
                return {"error": f"No price data available for {symbol}"}
            
            # Get crypto-specific news
            crypto_news = self.data_fetcher.get_crypto_news(symbol, days_back=days_back)
            if not crypto_news:
                crypto_news = shared_news
            
            # Analyze sentiment
            try:
                if crypto_news and len(crypto_news) > 0:
                    sentiment_data = self.sentiment_analyzer.analyze_news_sentiment(
                        crypto_news, ai_provider="ollama", symbol=symbol
                    )
                else:
                    sentiment_data = self.sentiment_analyzer.analyze_price_based_sentiment(
                        price_data, symbol
                    )
            except Exception as e:
                if "No news articles" in str(e):
                    sentiment_data = self.sentiment_analyzer.analyze_price_based_sentiment(
                        price_data, symbol
                    )
                else:
                    raise e
            
            # Get crypto-specific recommendations
            from src.core.recommendation_manager import get_recommendation_manager
            
            crypto_recommendation = get_recommendation_manager().get_crypto_specific_recommendations(
                symbol, sentiment_data, price_data
            )
            
            signal_data = {
                "action": crypto_recommendation.get("action", "HOLD"),
                "signal_strength": abs(crypto_recommendation.get("sentiment_score", 0)) * crypto_recommendation.get("confidence", 0),
                "confidence": crypto_recommendation.get("confidence", 0),
                "reasoning": crypto_recommendation.get("reasoning", "No reasoning provided"),
            }
            
            return {
                "symbol": symbol,
                "price_data": price_data,
                "news_data": crypto_news,
                "sentiment_data": sentiment_data,
                "signal_data": signal_data,
                "type": "crypto",
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error processing crypto {symbol}: {e}")
            return {"error": str(e)}
    
    def process_crypto_batch(self, crypto_symbols: List[str], days_back: int = 2) -> Dict[str, Any]:
        """Process multiple crypto symbols in batch"""
        try:
            results = {}
            errors = []
            
            # Get shared crypto news for efficiency
            shared_news = self.data_fetcher.get_crypto_news("BTC", days_back=days_back)
            
            for symbol in crypto_symbols:
                result = self._process_single_crypto(symbol, shared_news, days_back)
                if result and "error" not in result:
                    results[symbol] = result
                elif result and "error" in result:
                    errors.append({"symbol": symbol, "error": result["error"]})
            
            return {
                "results": results,
                "errors": errors,
                "total_processed": len(crypto_symbols),
                "successful": len(results),
                "failed": len(errors),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in crypto batch processing: {e}")
            return {"error": str(e)}
```

### 4. DataFetcher Class (Crypto Extensions)

```python
class DataFetcher:
    """Extended data fetcher with crypto-specific methods"""
    
    def get_crypto_price(self, symbol: str) -> Dict:
        """Get crypto price data from Alpha Vantage"""
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "DIGITAL_CURRENCY_DAILY",
                "symbol": symbol,
                "market": "USD",
                "apikey": self.alpha_vantage_api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if "Time Series (Digital Currency Daily)" in data:
                time_series = data["Time Series (Digital Currency Daily)"]
                latest_date = max(time_series.keys())
                latest_data = time_series[latest_date]
                
                return {
                    "current_price": float(latest_data["4a. close (USD)"]),
                    "open": float(latest_data["1a. open (USD)"]),
                    "high": float(latest_data["2a. high (USD)"]),
                    "low": float(latest_data["3a. low (USD)"]),
                    "volume": float(latest_data["5. volume"]),
                    "market_cap": float(latest_data.get("6. market cap (USD)", 0)),
                    "timestamp": latest_date
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching crypto price for {symbol}: {e}")
            return None
    
    def get_crypto_news(self, symbol: str, days_back: int = 2) -> List[Dict]:
        """Get crypto news articles"""
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "NEWS_SENTIMENT",
                "tickers": symbol,
                "apikey": self.alpha_vantage_api_key,
                "limit": 50
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if "feed" in data:
                news_articles = []
                cutoff_date = datetime.now() - timedelta(days=days_back)
                
                for article in data["feed"]:
                    article_date = datetime.fromisoformat(article["time_published"].replace("Z", "+00:00"))
                    
                    if article_date >= cutoff_date:
                        news_articles.append({
                            "headline": article["title"],
                            "summary": article["summary"],
                            "url": article["url"],
                            "published": article["time_published"],
                            "sentiment": article.get("overall_sentiment_score", 0)
                        })
                
                return news_articles[:5]  # Limit to 5 articles
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching crypto news for {symbol}: {e}")
            return []
```

## API Endpoints

### 1. Crypto Analysis Endpoint

```python
@app.route("/api/crypto_analysis")
def crypto_analysis():
    """Analyze cryptocurrencies for trading opportunities"""
    try:
        # Get query parameters
        refresh_requested = request.args.get('refresh', '0') == '1'
        fast_mode = request.args.get('fast', '0') == '1'
        
        # Use the analysis service for crypto analysis
        result = analysis_service.get_crypto_analysis(refresh=refresh_requested)
        
        return jsonify({
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in crypto analysis: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500
```

### 2. Crypto Watchlist Management

```python
@app.route("/api/crypto_watchlist", methods=["GET"])
def get_crypto_watchlist():
    """Get current crypto watchlist"""
    try:
        cryptos = watchlist_manager.get_cryptos()
        return jsonify({
            "cryptos": cryptos,
            "count": len(cryptos),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/crypto_watchlist", methods=["POST"])
def add_crypto_to_watchlist():
    """Add crypto to watchlist"""
    try:
        data = request.get_json()
        symbol = data.get("symbol", "").upper()
        
        if not symbol:
            return jsonify({"error": "Symbol is required"}), 400
        
        success = watchlist_manager.add_crypto(symbol)
        
        if success:
            return jsonify({
                "message": f"Added {symbol} to crypto watchlist",
                "symbol": symbol
            })
        else:
            return jsonify({"error": f"Failed to add {symbol}"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

## Frontend Implementation

### JavaScript Functions

```javascript
// Load cryptocurrency data from the backend
async function loadCryptoData() {
    try {
        console.log('Loading crypto data...');
        
        // Show loading spinner
        const loadingSpinner = document.getElementById('loadingSpinner');
        if (loadingSpinner) {
            loadingSpinner.style.display = 'block';
        }
        
        // First try fast mode for instant results
        const response = await fetch('/api/crypto_analysis?fast=1');
        const data = await response.json();
        
        console.log('API Response:', data);
        
        if (data.status === 'success' && data.data && data.data.opportunities) {
            cryptoData = data.data.opportunities;
            console.log('Loaded', cryptoData.length, 'crypto opportunities');
            
            // Display the crypto cards
            displayCryptoCards(cryptoData);
            
            // Update summary statistics
            updateSummaryStats(cryptoData);
            
            // Update charts
            updateCharts(cryptoData);
            
            // Update last updated timestamp
            const lastUpdated = document.getElementById('lastUpdated');
            if (lastUpdated) {
                const timestamp = data.data.timestamp || new Date().toISOString();
                lastUpdated.textContent = `Last updated: ${new Date(timestamp).toLocaleString()}`;
            }
        } else {
            console.error('Invalid API response:', data);
            showError('Failed to load cryptocurrency data');
        }
        
        // Hide loading spinner
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
        
    } catch (error) {
        console.error('Error loading crypto data:', error);
        showError('Error loading crypto data: ' + error.message);
        
        // Hide loading spinner
        const loadingSpinner = document.getElementById('loadingSpinner');
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
    }
}

// Display cryptocurrency opportunities as cards
function displayCryptoCards(cryptos) {
    console.log('Displaying', cryptos.length, 'crypto cards');
    
    const cardsContainer = document.getElementById('cryptoCardsRow');
    if (!cardsContainer) {
        console.error('cryptoCardsRow container not found');
        return;
    }
    
    // Clear existing content
    cardsContainer.innerHTML = '';
    
    if (cryptos.length === 0) {
        cardsContainer.innerHTML = `
            <div class="col-12">
                <div class="alert alert-info text-center">
                    <i class="fas fa-info-circle"></i>
                    No cryptocurrency opportunities found at this time.
                </div>
            </div>
        `;
        return;
    }
    
    // Create crypto cards
    cryptos.forEach(crypto => {
        const symbol = crypto.symbol || 'Unknown';
        const priceData = crypto.price_data || {};
        const sentimentData = crypto.sentiment_data || {};
        const signalData = crypto.signal_data || {};
        
        const currentPrice = priceData.current_price || 0;
        const priceChange = priceData.change_percent || 0;
        const volume = priceData.volume || 0;
        const sentimentScore = sentimentData.sentiment_score || 0;
        const confidence = sentimentData.confidence || 0;
        const action = signalData.action || 'HOLD';
        const signalStrength = signalData.signal_strength || 0;
        const newsCount = crypto.news_data ? crypto.news_data.length : 0;
        
        // Determine card styling based on sentiment and action
        let cardClass = 'card';
        let badgeClass = 'badge-secondary';
        let actionClass = 'text-muted';
        
        if (action === 'BUY') {
            cardClass += ' border-success';
            badgeClass = 'badge-success';
            actionClass = 'text-success';
        } else if (action === 'SELL') {
            cardClass += ' border-danger';
            badgeClass = 'badge-danger';
            actionClass = 'text-danger';
        }
        
        const cardHtml = `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="${cardClass} h-100">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">
                            <i class="fab fa-bitcoin"></i> ${symbol}
                        </h6>
                        <span class="badge ${badgeClass}">${action}</span>
                    </div>
                    <div class="card-body">
                        <div class="row mb-2">
                            <div class="col-6">
                                <small class="text-muted">Price</small>
                                <div class="fw-bold">$${currentPrice.toFixed(2)}</div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Change</small>
                                <div class="fw-bold ${priceChange >= 0 ? 'text-success' : 'text-danger'}">
                                    ${priceChange >= 0 ? '+' : ''}${priceChange.toFixed(2)}%
                                </div>
                            </div>
                        </div>
                        
                        <div class="row mb-2">
                            <div class="col-6">
                                <small class="text-muted">Sentiment</small>
                                <div class="fw-bold">
                                    ${(sentimentScore * 100).toFixed(1)}%
                                </div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Confidence</small>
                                <div class="fw-bold">
                                    ${(confidence * 100).toFixed(1)}%
                                </div>
                            </div>
                        </div>
                        
                        <div class="row mb-2">
                            <div class="col-6">
                                <small class="text-muted">Signal Strength</small>
                                <div class="fw-bold">
                                    ${(signalStrength * 100).toFixed(1)}%
                                </div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">News</small>
                                <div class="fw-bold">${newsCount}</div>
                            </div>
                        </div>
                        
                        <div class="mt-3">
                            <small class="text-muted">Volume</small>
                            <div class="fw-bold">${volume.toLocaleString()}</div>
                        </div>
                    </div>
                    <div class="card-footer">
                        <div class="d-flex justify-content-between">
                            <button class="btn btn-sm btn-outline-primary" onclick="viewCryptoDetails('${symbol}')">
                                <i class="fas fa-eye"></i> Details
                            </button>
                            <button class="btn btn-sm btn-outline-success" onclick="addToPortfolio('${symbol}', '${action}')">
                                <i class="fas fa-plus"></i> Add
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        cardsContainer.innerHTML += cardHtml;
    });
}

// Update summary statistics
function updateSummaryStats(cryptos) {
    const totalCryptos = cryptos.length;
    const buySignals = cryptos.filter(c => c.signal_data?.action === 'BUY').length;
    const sellSignals = cryptos.filter(c => c.signal_data?.action === 'SELL').length;
    const holdSignals = cryptos.filter(c => c.signal_data?.action === 'HOLD').length;
    
    const avgSentiment = cryptos.reduce((sum, c) => sum + (c.sentiment_data?.sentiment_score || 0), 0) / totalCryptos;
    const avgConfidence = cryptos.reduce((sum, c) => sum + (c.sentiment_data?.confidence || 0), 0) / totalCryptos;
    
    // Update summary cards
    document.getElementById('totalCryptos').textContent = totalCryptos;
    document.getElementById('buySignals').textContent = buySignals;
    document.getElementById('sellSignals').textContent = sellSignals;
    document.getElementById('holdSignals').textContent = holdSignals;
    document.getElementById('avgSentiment').textContent = (avgSentiment * 100).toFixed(1) + '%';
    document.getElementById('avgConfidence').textContent = (avgConfidence * 100).toFixed(1) + '%';
}

// View crypto details
function viewCryptoDetails(symbol) {
    // Implementation for detailed crypto view
    console.log(`Viewing details for ${symbol}`);
    // Could open a modal or navigate to detailed page
}

// Add crypto to portfolio
function addCryptoToPortfolio(symbol, action) {
    // Implementation for adding crypto to portfolio
    console.log(`Adding ${symbol} with action ${action} to portfolio`);
    // Could make API call to portfolio service
}
```

## Configuration

### Environment Variables

```python
# API Keys
ALPHA_VANTAGE_API_KEY = "your_alpha_vantage_api_key"
OPENAI_API_KEY = "your_openai_api_key"
DEEPSEEK_API_KEY = "your_deepseek_api_key"

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

# Crypto Trading Thresholds
CRYPTO_CONFIDENCE_THRESHOLD = 0.6
CRYPTO_SENTIMENT_THRESHOLD = 0.3
CRYPTO_VOLUME_RATIO_THRESHOLD = 1.5
CRYPTO_PRICE_CHANGE_THRESHOLD = 1.0
```

## Caching Strategy

### Redis Implementation for Crypto Data

```python
class CryptoCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True
        )
    
    def get_crypto_analysis(self, symbol: str):
        """Get cached crypto analysis"""
        try:
            key = f"crypto_analysis:{symbol}"
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except:
            return None
    
    def set_crypto_analysis(self, symbol: str, data: Dict, ttl: int = 900):
        """Cache crypto analysis for 15 minutes"""
        try:
            key = f"crypto_analysis:{symbol}"
            self.redis_client.setex(key, ttl, json.dumps(data))
            return True
        except:
            return False
    
    def get_crypto_opportunities(self):
        """Get cached crypto opportunities"""
        try:
            key = "crypto_opportunities"
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except:
            return None
    
    def set_crypto_opportunities(self, data: Dict, ttl: int = 600):
        """Cache crypto opportunities for 10 minutes"""
        try:
            key = "crypto_opportunities"
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
psql trading_db < crypto_schema.sql
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
export OPENAI_API_KEY="your_key"

# Run application
python app.py
```

## Testing

### Unit Tests
```python
def test_crypto_watchlist():
    manager = WatchlistManager()
    cryptos = manager.get_cryptos()
    assert len(cryptos) > 0
    assert 'BTC' in cryptos

def test_crypto_scalping_analysis():
    analyzer = ScalpingAnalyzer()
    result = analyzer.analyze_crypto_opportunity('BTC')
    assert 'symbol' in result
    assert 'market_data' in result
    assert 'sentiment_data' in result

def test_crypto_batch_processing():
    processor = BatchProcessor()
    result = processor.process_crypto_batch(['BTC', 'ETH'])
    assert 'results' in result
    assert 'errors' in result
    assert len(result['results']) <= 2
```

## Performance Optimization

### 1. Caching
- Redis caching with 10-15 minute TTL for crypto analysis results
- Preloaded opportunities table for fast data retrieval
- Database query optimization with proper indexes

### 2. Batch Processing
- Process multiple crypto symbols in parallel
- Use shared news data for efficiency
- Implement circuit breakers for external API calls

### 3. Monitoring
- Log all crypto API calls and analysis results
- Monitor cache hit rates
- Track crypto analysis accuracy over time

## Troubleshooting

### Common Issues

1. **API Rate Limiting**
   - Implement delays between Alpha Vantage API calls
   - Use multiple API keys if available
   - Cache results aggressively

2. **Crypto Data Availability**
   - Handle cases where crypto data is not available
   - Implement fallback to price-based analysis
   - Add error handling for invalid crypto symbols

3. **News Data Issues**
   - Handle cases with limited crypto news
   - Implement fallback to general crypto news
   - Cache news data to reduce API calls

4. **Memory Issues**
   - Limit concurrent crypto analysis requests
   - Implement garbage collection
   - Monitor memory usage during batch processing

## Conclusion

This implementation provides a complete system for analyzing cryptocurrencies and generating trading recommendations. The system is designed to be scalable, reliable, and maintainable with proper error handling, caching, and monitoring.

Key features:
- Crypto watchlist management
- Real-time crypto market data integration
- AI-powered crypto news sentiment analysis
- Scalping opportunity identification
- Card-based frontend interface
- Redis caching for performance
- PostgreSQL for data persistence
- RESTful API for frontend integration
- Batch processing for efficiency
- Comprehensive error handling and monitoring
