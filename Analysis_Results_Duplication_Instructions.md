# Analysis Results Duplication Instructions

## Overview
This document provides comprehensive instructions for duplicating the Analysis Results functionality from the stocks page. The system calculates sentiment scores, trading signals, and recommendations for S&P 500 stocks using AI-powered analysis and historical backtesting.

## System Architecture

### Data Flow
```
Market Data (Alpha Vantage) → Database Storage → Sentiment Analysis → Trading Signals → Historical Backtesting → Frontend Display
```

### Key Components
1. **Data Collection**: Market movers from Alpha Vantage API
2. **Sentiment Analysis**: AI-powered news analysis using Ollama/OpenAI
3. **Trading Strategy**: Enhanced strategy with historical backtesting
4. **Database Storage**: PostgreSQL with Redis caching
5. **Frontend Display**: Real-time updates via JavaScript

## Database Schema

### Market Movers Table
```sql
CREATE TABLE market_movers (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    type VARCHAR(10) NOT NULL CHECK (type IN ('GAINER', 'LOSER')),
    price DECIMAL(10,2),
    change_amount DECIMAL(10,2),
    change_percent DECIMAL(8,4),
    volume BIGINT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analysis_data JSONB
);

CREATE INDEX idx_market_movers_symbol ON market_movers (symbol);
CREATE INDEX idx_market_movers_timestamp ON market_movers (timestamp);
```

### Recommendations Table
```sql
CREATE TABLE recommendations (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    recommendation_type VARCHAR(20),
    action VARCHAR(10),
    strike_price DECIMAL(10,2),
    days_to_expiry INTEGER,
    option_price DECIMAL(10,2),
    sentiment_confidence DECIMAL(5,4),
    historical_confidence DECIMAL(5,4),
    final_confidence DECIMAL(5,4),
    sentiment_score DECIMAL(5,4),
    current_stock_price DECIMAL(10,2),
    reasoning TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_recommendations_symbol ON recommendations (symbol);
CREATE INDEX idx_recommendations_timestamp ON recommendations (timestamp);
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
```

## Core Classes Implementation

### 1. SentimentAnalyzer Class

```python
class SentimentAnalyzer:
    def __init__(self):
        self.openai_api_key = Config.OPENAI_API_KEY
        self.ollama_base_url = "http://localhost:11434"
        self.ollama_model = "qwen2.5:3b"
        self.deepseek_api_key = Config.DEEPSEEK_API_KEY
        self.deepseek_base_url = "https://api.deepseek.com/v1"
    
    def analyze_news_sentiment(self, news_articles, ai_provider="ollama", symbol=None):
        """
        Analyze sentiment of news articles using AI
        
        Args:
            news_articles: List of news article dictionaries
            ai_provider: AI provider to use (ollama, openai, deepseek)
            symbol: Stock symbol for context
            
        Returns:
            Dict with sentiment_score (-1 to 1), confidence (0 to 1), summary
        """
        if not news_articles or len(news_articles) < 2:
            return {
                "sentiment_score": 0.1,
                "confidence": 0.6,
                "summary": "Limited news data available"
            }
        
        # Prepare headlines for analysis
        headlines = [article.get('headline', '') for article in news_articles]
        
        # Call appropriate AI provider
        if ai_provider == "ollama":
            return self._call_ollama_api(headlines, symbol)
        elif ai_provider == "openai":
            return self._call_openai_api(headlines, symbol)
        elif ai_provider == "deepseek":
            return self._call_deepseek_api(headlines, symbol)
    
    def get_trading_signal(self, sentiment_data):
        """
        Generate trading signals based on sentiment analysis
        
        Args:
            sentiment_data: Sentiment analysis results
            
        Returns:
            Dict with stock and options recommendations
        """
        sentiment_score = sentiment_data.get("sentiment_score", 0)
        confidence = sentiment_data.get("confidence", 0)
        
        # Configuration thresholds
        CONFIDENCE_THRESHOLD = 0.6
        SENTIMENT_THRESHOLD = 0.3
        
        if confidence < CONFIDENCE_THRESHOLD or abs(sentiment_score) < SENTIMENT_THRESHOLD:
            stock_action = "HOLD"
            options_action = "HOLD"
            reasoning = "Low confidence or weak sentiment signal"
        elif sentiment_score > SENTIMENT_THRESHOLD:
            stock_action = "BUY"
            options_action = "CALL"
            reasoning = f"Positive sentiment ({sentiment_score:.2f}) with high confidence ({confidence:.2f})"
        elif sentiment_score < -SENTIMENT_THRESHOLD:
            stock_action = "SELL"
            options_action = "PUT"
            reasoning = f"Negative sentiment ({sentiment_score:.2f}) with high confidence ({confidence:.2f})"
        else:
            stock_action = "HOLD"
            options_action = "HOLD"
            reasoning = "Neutral sentiment"
        
        return {
            "stock_recommendation": {
                "action": stock_action,
                "signal_strength": abs(sentiment_score) * confidence if stock_action in ["BUY", "SELL"] else 0,
                "confidence": confidence,
                "reasoning": reasoning,
            },
            "options_recommendation": {
                "action": options_action,
                "signal_strength": abs(sentiment_score) * confidence if options_action in ["CALL", "PUT"] else 0,
                "confidence": confidence,
                "reasoning": reasoning,
            }
        }
```

### 2. EnhancedTradingStrategy Class

```python
class EnhancedTradingStrategy:
    def __init__(self):
        self.alpha_vantage_api_key = Config.ALPHA_VANTAGE_API_KEY
        self.cache = {}
        self.rate_limit_delay = 12  # Alpha Vantage free tier: 5 calls per minute
        self.recommendation_manager = RecommendationManager()
    
    def get_comprehensive_recommendations(self, symbol, current_price, sentiment_data, signal_data):
        """
        Get comprehensive recommendations across multiple strategy types
        
        Args:
            symbol: Stock symbol
            current_price: Current stock price
            sentiment_data: Sentiment analysis results
            signal_data: Trading signal data
            
        Returns:
            Dict: Comprehensive recommendations with rankings
        """
        # Generate options recommendations
        options_recommendations = self.generate_multiple_recommendations(
            symbol, current_price, sentiment_data, signal_data
        )
        
        # Test options recommendations against historical data
        enhanced_recommendations = self.test_recommendations_against_historical_data(
            options_recommendations
        )
        
        # Generate stock recommendations
        stock_recommendations = self.generate_stock_recommendations(
            symbol, current_price, sentiment_data, signal_data
        )
        
        # Test stock recommendations against historical data
        enhanced_stock_recommendations = self.test_stock_recommendations_against_historical_data(
            stock_recommendations
        )
        
        # Add category labels
        for rec in enhanced_recommendations:
            rec["category"] = "Options"
        
        for rec in enhanced_stock_recommendations:
            rec["category"] = "Stock"
        
        # Combine all recommendations
        all_recommendations = enhanced_recommendations + enhanced_stock_recommendations
        
        # Sort by confidence (highest first)
        all_recommendations.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        # Re-rank all recommendations
        for i, rec in enumerate(all_recommendations):
            rec["overall_rank"] = i + 1
        
        # Determine top recommendation
        top_recommendation = all_recommendations[0] if all_recommendations else None
        
        return {
            "all_recommendations": all_recommendations,
            "top_recommendation": top_recommendation,
            "total_recommendations": len(all_recommendations),
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def test_recommendations_against_historical_data(self, recommendations):
        """
        Test recommendations against historical data for confidence calculation
        
        Args:
            recommendations: List of recommendation dictionaries
            
        Returns:
            List of enhanced recommendations with historical confidence scores
        """
        enhanced_recommendations = []
        
        for rec in recommendations:
            # Get historical data for backtesting
            historical_data = self.get_historical_data(rec["symbol"])
            
            if historical_data and len(historical_data) > 10:
                # Calculate historical performance
                historical_stats = self.calculate_historical_performance(
                    rec, historical_data
                )
                
                # Update recommendation with historical confidence
                rec["historical_stats"] = historical_stats
                rec["historical_confidence"] = historical_stats.get("confidence", 0.5)
                
                # Calculate final confidence (weighted average)
                sentiment_confidence = rec.get("confidence", 0.5)
                historical_confidence = rec.get("historical_confidence", 0.5)
                rec["final_confidence"] = (sentiment_confidence * 0.6) + (historical_confidence * 0.4)
            else:
                rec["historical_confidence"] = 0.5
                rec["final_confidence"] = rec.get("confidence", 0.5)
                rec["historical_stats"] = {"total_trades": 0, "profitable_trades": 0}
            
            enhanced_recommendations.append(rec)
        
        return enhanced_recommendations
```

### 3. RecommendationManager Class

```python
class RecommendationManager:
    def __init__(self):
        self.table_name = "recommendations"
    
    def save_recommendation(self, recommendation):
        """
        Save a single trading recommendation to the database
        
        Args:
            recommendation: Dictionary containing recommendation data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Extract recommendation data
                    symbol = recommendation.get("symbol", "")
                    recommendation_type = recommendation.get("recommendation_type", "stock")
                    action = recommendation.get("action", "HOLD")
                    strike_price = recommendation.get("strike_price")
                    days_to_expiry = recommendation.get("days_to_expiry")
                    option_price = recommendation.get("option_price")
                    sentiment_confidence = recommendation.get("confidence", 0.5)
                    historical_confidence = recommendation.get("historical_confidence", 0.5)
                    final_confidence = recommendation.get("final_confidence", 0.5)
                    sentiment_score = recommendation.get("sentiment_score", 0)
                    current_stock_price = recommendation.get("current_stock_price", 0)
                    reasoning = recommendation.get("reasoning", "")
                    
                    # Insert recommendation
                    cur.execute(
                        f"""
                        INSERT INTO {self.table_name} (
                            symbol, recommendation_type, action, strike_price,
                            days_to_expiry, option_price, sentiment_confidence,
                            historical_confidence, final_confidence, sentiment_score,
                            current_stock_price, reasoning
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                        """,
                        (
                            symbol, recommendation_type, action, strike_price,
                            days_to_expiry, option_price, sentiment_confidence,
                            historical_confidence, final_confidence, sentiment_score,
                            current_stock_price, reasoning,
                        ),
                    )
                    
                    result = cur.fetchone()
                    if result:
                        recommendation_id = result[0]
                        conn.commit()
                        return True
                    
        except Exception as e:
            logger.error(f"Error saving recommendation: {e}")
            return False
        
        return False
```

### 4. DataFetcher Class

```python
class DataFetcher:
    def __init__(self):
        self.alpha_vantage_api_key = Config.ALPHA_VANTAGE_API_KEY
        self.rate_limit_delay = 12  # Alpha Vantage free tier: 5 calls per minute
    
    def get_stock_price(self, symbol):
        """
        Get current stock price and basic data
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict with price data
        """
        try:
            # Use Alpha Vantage API
            url = f"https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.alpha_vantage_api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if "Global Quote" in data:
                quote = data["Global Quote"]
                return {
                    "current_price": float(quote.get("05. price", 0)),
                    "change_amount": float(quote.get("09. change", 0)),
                    "change_percent": float(quote.get("10. change percent", 0).replace("%", "")),
                    "volume": int(quote.get("06. volume", 0)),
                    "high": float(quote.get("03. high", 0)),
                    "low": float(quote.get("04. low", 0)),
                    "open": float(quote.get("02. open", 0))
                }
            
        except Exception as e:
            logger.error(f"Error fetching price data for {symbol}: {e}")
            return None
    
    def get_company_news(self, symbol, days_back=2):
        """
        Get company news articles
        
        Args:
            symbol: Stock symbol
            days_back: Number of days to look back
            
        Returns:
            List of news article dictionaries
        """
        try:
            # Use Alpha Vantage News API
            url = f"https://www.alphavantage.co/query"
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
                
                return news_articles[:3]  # Limit to 3 articles
            
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []
        
        return []
```

## API Endpoints

### 1. Market Movers Endpoint

```python
@app.route("/api/market_movers", methods=["GET"])
def get_market_movers():
    """Get top gainers and losers from database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT symbol, type, change_percent, price, volume, timestamp
                    FROM market_movers
                    ORDER BY timestamp DESC
                    """
                )
                rows = cur.fetchall()
        
        gainers = []
        losers = []
        
        for row in rows:
            stock_data = {
                "symbol": row["symbol"],
                "type": row["type"].lower(),
                "change_percent": row["change_percent"],
                "price": row["price"],
                "volume": row["volume"],
                "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None,
            }
            
            if row["type"] == "GAINER":
                gainers.append(stock_data)
            elif row["type"] == "LOSER":
                losers.append(stock_data)
        
        gainers.sort(key=lambda item: item["change_percent"], reverse=True)
        losers.sort(key=lambda item: item["change_percent"])
        
        return jsonify({
            "gainers": gainers[:5],
            "losers": losers[:5],
            "total_gainers": len(gainers),
            "total_losers": len(losers),
            "timestamp": datetime.now().isoformat(),
            "source": "market_movers_table"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

### 2. Enhanced Analysis Endpoint

```python
@app.route("/api/enhanced_analysis", methods=["POST"])
def enhanced_analysis():
    """Enhanced stock analysis with multiple strategies and backtesting"""
    data = request.get_json()
    
    if not data or "symbol" not in data:
        return jsonify({"error": "Missing required parameter: symbol"}), 400
    
    symbol = data["symbol"].strip().upper()
    
    # Check cache for enhanced analysis result
    cache_key = f"enhanced_analysis:{symbol}"
    if redis_cache.health_check():
        cached_result = redis_cache.get(cache_key)
        if cached_result:
            return jsonify({"data": cached_result})
    
    # Initialize services
    enhanced_strategy = EnhancedTradingStrategy()
    data_fetcher = DataFetcher()
    sentiment_analyzer = SentimentAnalyzer()
    
    # Get price data
    price_data = data_fetcher.get_stock_price(symbol)
    if not price_data or "current_price" not in price_data:
        return jsonify({
            "error": f"Could not fetch price data for {symbol}"
        }), 400
    
    # Get news data
    news_data = data_fetcher.get_company_news(symbol, days_back=2)
    if len(news_data) > 3:
        news_data = news_data[:3]
    
    # Calculate sentiment
    if len(news_data) < 2:
        sentiment_data = {
            "sentiment_score": 0.1,
            "confidence": 0.6,
            "summary": "Enhanced analysis with limited news data",
        }
    else:
        sentiment_data = sentiment_analyzer.analyze_news_sentiment(
            news_data, ai_provider="ollama", symbol=symbol
        )
    
    # Generate trading signals
    signal_data = sentiment_analyzer.get_trading_signal(sentiment_data)
    
    # Get comprehensive recommendations
    recommendations = enhanced_strategy.get_comprehensive_recommendations(
        symbol, price_data["current_price"], sentiment_data, signal_data
    )
    
    # Prepare response data
    response_data = {
        "symbol": symbol,
        "price_data": price_data,
        "sentiment_data": sentiment_data,
        "signal_data": signal_data,
        "news_count": len(news_data),
        "enhanced_analysis": {
            "symbol": symbol,
            "price_data": price_data,
            "sentiment_data": sentiment_data,
            "signal_data": signal_data,
            "recommendations": recommendations,
            "news_data": {"article_count": len(news_data)},
            "analysis_type": "enhanced",
        },
        "timestamp": datetime.now().isoformat(),
    }
    
    # Cache the result for 15 minutes
    if redis_cache.health_check():
        redis_cache.set(cache_key, response_data, ttl=900)
    
    return jsonify({
        "data": response_data,
        "message": "Enhanced analysis with multiple strategies completed successfully"
    })
```

## Frontend Implementation

### JavaScript Functions

```javascript
// Get enhanced analysis for symbols from market movers
async function getEnhancedAnalysisForSymbols(marketMoversData) {
    const enhancedAnalysis = [];
    const symbolsToAnalyze = [];
    
    // Extract symbols from market movers
    if (marketMoversData.gainers) {
        symbolsToAnalyze.push(...marketMoversData.gainers.map(g => g.symbol));
    }
    if (marketMoversData.losers) {
        symbolsToAnalyze.push(...marketMoversData.losers.map(l => l.symbol));
    }
    
    // Get enhanced analysis for each symbol
    for (const symbol of symbolsToAnalyze) {
        try {
            const response = await fetch('/api/enhanced_analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ symbol: symbol })
            });
            
            const result = await response.json();
            
            if (result.data) {
                // Determine if this is a winner or loser
                const isWinner = marketMoversData.gainers?.some(g => g.symbol === symbol);
                const isLoser = marketMoversData.losers?.some(l => l.symbol === symbol);
                
                const analysisData = {
                    symbol: symbol,
                    type: isWinner ? 'winner' : 'loser',
                    price_data: result.data.price_data,
                    sentiment_data: result.data.sentiment_data,
                    signal_data: result.data.signal_data,
                    news_count: result.data.news_data?.article_count || 0,
                    timestamp: new Date().toISOString(),
                    analysis_time: result.data.analysis_time
                };
                
                enhancedAnalysis.push(analysisData);
            }
        } catch (error) {
            console.error(`Error getting analysis for ${symbol}:`, error);
        }
    }
    
    return {
        enhanced_analysis: enhancedAnalysis,
        source: 'real_enhanced_analysis'
    };
}

// Display stocks analysis results
function displayStocksAnalysis(data) {
    const enhancedAnalysis = data.enhanced_analysis || [];
    
    if (enhancedAnalysis.length === 0) {
        showError('No analysis data available');
        return;
    }
    
    // Update summary statistics
    updateSummaryStats(data);
    
    // Update table with analysis results
    updateAnalysisTable(enhancedAnalysis);
}

// Update analysis table
function updateAnalysisTable(enhancedAnalysis) {
    const tableBody = document.getElementById('stocksTableBody');
    if (!tableBody) return;
    
    let html = '';
    enhancedAnalysis.forEach(stock => {
        const priceData = stock.price_data || {};
        const sentimentData = stock.sentiment_data || {};
        const signalData = stock.signal_data || {};
        
        const currentPrice = priceData.current_price || 'N/A';
        const sentimentScore = sentimentData.sentiment_score || 0;
        const confidence = sentimentData.confidence || 0;
        const action = signalData.stock_recommendation?.action || 'HOLD';
        const signalStrength = signalData.stock_recommendation?.confidence || 0;
        const newsCount = stock.news_count || 0;
        
        html += `
            <tr>
                <td><span class="badge ${stock.type === 'winner' ? 'bg-success' : 'bg-danger'}">${stock.type}</span></td>
                <td><strong>${stock.symbol}</strong></td>
                <td>$${currentPrice}</td>
                <td>${(sentimentScore * 100).toFixed(1)}%</td>
                <td>${(confidence * 100).toFixed(1)}%</td>
                <td><span class="badge bg-${action === 'BUY' ? 'success' : action === 'SELL' ? 'danger' : 'secondary'}">${action}</span></td>
                <td>${(signalStrength * 100).toFixed(1)}%</td>
                <td>${newsCount}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewStockDetails('${stock.symbol}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            </tr>
        `;
    });
    
    tableBody.innerHTML = html;
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

# Trading Thresholds
CONFIDENCE_THRESHOLD = 0.6
SENTIMENT_THRESHOLD = 0.3
```

## Caching Strategy

### Redis Implementation

```python
class RedisCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True
        )
    
    def health_check(self):
        """Check if Redis is available"""
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def get(self, key):
        """Get value from cache"""
        try:
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except:
            return None
    
    def set(self, key, value, ttl=900):
        """Set value in cache with TTL"""
        try:
            self.redis_client.setex(key, ttl, json.dumps(value))
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
psql trading_db < schema.sql
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
def test_sentiment_analysis():
    analyzer = SentimentAnalyzer()
    news_articles = [
        {"headline": "Company reports strong earnings", "summary": "Positive news"},
        {"headline": "Stock price rises significantly", "summary": "Good performance"}
    ]
    
    result = analyzer.analyze_news_sentiment(news_articles)
    assert result["sentiment_score"] > 0
    assert result["confidence"] > 0

def test_trading_signal():
    analyzer = SentimentAnalyzer()
    sentiment_data = {
        "sentiment_score": 0.8,
        "confidence": 0.9
    }
    
    signal = analyzer.get_trading_signal(sentiment_data)
    assert signal["stock_recommendation"]["action"] == "BUY"
```

## Performance Optimization

### 1. Caching
- Redis caching with 15-minute TTL for analysis results
- Database query optimization with proper indexes
- API rate limiting to prevent abuse

### 2. Batch Processing
- Process multiple symbols in parallel
- Use background jobs for heavy computations
- Implement circuit breakers for external API calls

### 3. Monitoring
- Log all API calls and analysis results
- Monitor cache hit rates
- Track analysis accuracy over time

## Troubleshooting

### Common Issues

1. **API Rate Limiting**
   - Implement delays between API calls
   - Use multiple API keys if available
   - Cache results aggressively

2. **Database Connection Issues**
   - Implement connection pooling
   - Add retry logic for failed connections
   - Monitor database performance

3. **AI Model Failures**
   - Implement fallback providers
   - Add error handling for model responses
   - Cache successful results

4. **Memory Issues**
   - Limit concurrent analysis requests
   - Implement garbage collection
   - Monitor memory usage

## Conclusion

This implementation provides a complete system for analyzing stock sentiment and generating trading recommendations. The system is designed to be scalable, reliable, and maintainable with proper error handling, caching, and monitoring.

Key features:
- AI-powered sentiment analysis
- Historical backtesting for confidence calculation
- Real-time market data integration
- Comprehensive recommendation system
- Redis caching for performance
- PostgreSQL for data persistence
- RESTful API for frontend integration
