# News Sources Configuration Guide

This document explains how to configure and use the various news sources available in the trading sentiment analysis application.

## 📰 Available News Sources

### 1. Yahoo Finance News ✅ **FREE**
- **Status**: Active and implemented
- **Cost**: Free
- **Features**: 
  - General market news and analysis
  - Company-specific news
  - Real-time updates
  - No API key required
- **Configuration**: Enabled by default in `config.py`

### 2. Alpha Vantage News ✅ **API KEY REQUIRED**
- **Status**: Active and implemented
- **Cost**: Requires API key (free tier available)
- **Features**:
  - Real-time and historical market news
  - Built-in sentiment analysis
  - Sentiment scores for each article
  - High-quality financial news sources
- **Configuration**: Requires `ALPHA_VANTAGE_API_KEY` in `config.py`

### 3. Finnhub News ✅ **FREE TIER**
- **Status**: Active (existing implementation)
- **Cost**: Free tier available
- **Features**:
  - Company-specific financial news
  - Earnings reports
  - Corporate announcements
- **Configuration**: Uses existing `FINNHUB_API_KEY`

### 4. Reddit Social Sentiment ✅ **FREE**
- **Status**: Active (existing implementation)
- **Cost**: Free
- **Features**:
  - Real-time social sentiment
  - Multiple subreddits (r/stocks, r/investing, r/wallstreetbets)
  - Options-specific discussions
- **Configuration**: Uses `REDDIT_CLIENT_ID` and `REDDIT_SECRET_KEY`

### 5. NewsAPI.org 🔄 **COMING SOON**
- **Status**: Planned for future implementation
- **Cost**: API key required
- **Features**:
  - 150,000+ global news sources
  - Comprehensive market coverage
  - Advanced filtering capabilities

## 🛠️ Configuration

### Setting Up Alpha Vantage News

1. **Get API Key**:
   - Visit [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
   - Sign up for a free account
   - Get your API key

2. **Configure in `src/core/config.py`**:
   ```python
   # Alpha Vantage API Key for news and financial data
   ALPHA_VANTAGE_API_KEY = "your_api_key_here"
   
   # Enable Alpha Vantage news
   ENABLE_ALPHA_VANTAGE_NEWS = True
   ```

### Yahoo Finance News Configuration

Yahoo Finance news is enabled by default and requires no additional setup:

```python
# Enable Yahoo Finance news (free)
ENABLE_YAHOO_NEWS = True
YAHOO_NEWS_MAX_ARTICLES = 5
```

### News Source Settings

You can control which news sources are active:

```python
# ===== NEWS SOURCES CONFIGURATION =====
ENABLE_YAHOO_NEWS = True          # Free Yahoo Finance news
ENABLE_ALPHA_VANTAGE_NEWS = True  # Alpha Vantage news (requires API key)
ENABLE_NEWSAPI_ORG = False        # NewsAPI.org (not implemented yet)

# News source limits
YAHOO_NEWS_MAX_ARTICLES = 5       # Max articles from Yahoo per request
ALPHA_VANTAGE_NEWS_MAX_ARTICLES = 5  # Max articles from Alpha Vantage per request
```

## 📊 Testing News Sources

### Web Interface Testing

1. Start the application: `python3 -m src.web.app`
2. Navigate to **System Status** page
3. Scroll to **News Sources** section
4. Click **Test** button for each news source

### Manual Testing

Test individual news sources:

```python
from src.data.data_fetcher import DataFetcher

fetcher = DataFetcher()

# Test Yahoo Finance
yahoo_news = fetcher.get_yahoo_finance_news('AAPL', limit=3)
print(f"Yahoo Finance: {len(yahoo_news)} articles")

# Test Alpha Vantage
alpha_news = fetcher.get_alpha_vantage_news('AAPL', limit=3)
print(f"Alpha Vantage: {len(alpha_news)} articles")

# Test combined (all sources)
all_news = fetcher.get_company_news('AAPL', days_back=3)
print(f"Combined: {len(all_news)} total articles")
```

## 🎯 Benefits by Source

### Yahoo Finance News
- **Benefit**: Free, reliable market news
- **Best for**: General market sentiment, breaking news
- **Coverage**: Broad market analysis, company announcements

### Alpha Vantage News
- **Benefit**: Sentiment analysis included
- **Best for**: AI-enhanced sentiment analysis
- **Coverage**: High-quality financial news with pre-calculated sentiment scores
- **Unique Features**: 
  - Sentiment scores (-1 to +1)
  - Overall sentiment labels (Bearish, Neutral, Bullish)
  - Ticker-specific sentiment analysis

### Combined Approach
Using multiple news sources provides:
- **Diversified perspectives**
- **Reduced single-source bias**
- **Better sentiment accuracy**
- **Comprehensive market coverage**

## 🔧 Troubleshooting

### Alpha Vantage Issues
- **"API key not configured"**: Check `ALPHA_VANTAGE_API_KEY` in config.py
- **"Rate limit exceeded"**: Alpha Vantage has rate limits (5 API calls per minute, 500 per day for free tier)
- **"No news feed"**: Symbol might not have recent news

### Yahoo Finance Issues
- **"No news found"**: Symbol might not have recent news on Yahoo Finance
- **"Timeout errors"**: Network connectivity issues

### General Issues
- **Import errors**: Make sure you're running from the project root
- **Network timeouts**: Check internet connectivity
- **Empty results**: Try different stock symbols (AAPL, TSLA, MSFT usually have news)

## 📈 News Source Performance

Current implementation fetches news in this priority:

1. **Finnhub**: 3 articles (financial focus)
2. **Yahoo Finance**: 5 articles (general market news)
3. **Alpha Vantage**: 5 articles (with sentiment analysis)
4. **Reddit**: 4 + 3 articles (social sentiment + options)

Total: Up to 20 articles per symbol, filtered and sorted by recency.

## 🚀 Future Enhancements

Planned improvements:
- **NewsAPI.org integration**: 150,000+ global sources
- **Real-time news streaming**: WebSocket connections for instant updates
- **Advanced filtering**: By source quality, relevance scores
- **Custom news sources**: Ability to add proprietary news feeds
- **News sentiment caching**: Reduce API calls with intelligent caching 