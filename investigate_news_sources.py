#!/usr/bin/env python3
"""
Investigate why different stocks are getting similar news content.
This will help us understand if the issue is with news sources, content filtering, or data processing.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.data_fetcher import DataFetcher
from collections import Counter
import json

def analyze_news_sources():
    """Analyze news sources for different stocks to see if they're getting similar content"""
    
    print("🔍 Investigating News Sources for Different Stocks")
    print("=" * 60)
    
    data_fetcher = DataFetcher()
    
    # Test with the stocks from our analysis
    test_symbols = ["ANET", "AZO", "ALL", "ALB", "AES", "AMZN"]
    
    news_analysis = {}
    
    for symbol in test_symbols:
        print(f"\n📊 Analyzing {symbol}...")
        
        try:
            # Get news from different sources
            finnhub_news = data_fetcher.get_company_news(symbol, days_back=7)
            
            print(f"   📰 Finnhub: {len(finnhub_news)} articles")
            
            # Analyze the first few articles to see content
            if finnhub_news:
                print(f"   📄 Sample headlines:")
                for i, article in enumerate(finnhub_news[:3]):
                    if isinstance(article, dict):
                        headline = article.get("headline", article.get("title", "No headline"))
                        source = article.get("source", "Unknown")
                        print(f"      {i+1}. [{source}] {headline[:80]}...")
                    else:
                        print(f"      {i+1}. Invalid article format: {type(article)}")
            
            # Store for comparison
            news_analysis[symbol] = {
                "finnhub_count": len(finnhub_news),
                "finnhub_articles": finnhub_news[:5] if finnhub_news else [],
                "headlines": [article.get("headline", article.get("title", "")) for article in finnhub_news[:5] if isinstance(article, dict)]
            }
            
        except Exception as e:
            print(f"   ❌ Error analyzing {symbol}: {e}")
            news_analysis[symbol] = {"error": str(e)}
    
    # Compare news content across stocks
    print("\n" + "=" * 60)
    print("📊 NEWS CONTENT COMPARISON")
    print("=" * 60)
    
    # Check for duplicate headlines across stocks
    all_headlines = []
    for symbol, data in news_analysis.items():
        if "headlines" in data:
            all_headlines.extend([(symbol, headline) for headline in data["headlines"]])
    
    # Find duplicate headlines
    headline_texts = [headline for _, headline in all_headlines]
    headline_counter = Counter(headline_texts)
    
    print(f"📈 Total unique headlines: {len(set(headline_texts))}")
    print(f"📈 Total headlines: {len(headline_texts)}")
    
    # Show duplicates
    duplicates = {text: count for text, count in headline_counter.items() if count > 1}
    if duplicates:
        print(f"\n🚨 DUPLICATE HEADLINES FOUND ({len(duplicates)}):")
        for headline, count in duplicates.items():
            print(f"   '{headline[:60]}...' appears {count} times")
    else:
        print(f"\n✅ No duplicate headlines found")
    
    # Check news sources
    print(f"\n📰 NEWS SOURCE ANALYSIS:")
    all_sources = []
    for symbol, data in news_analysis.items():
        if "finnhub_articles" in data:
            for article in data["finnhub_articles"]:
                if isinstance(article, dict):
                    source = article.get("source", "Unknown")
                    all_sources.append(source)
    
    source_counter = Counter(all_sources)
    print(f"   Most common news sources:")
    for source, count in source_counter.most_common(5):
        print(f"      {source}: {count} articles")
    
    # Check if news is stock-specific or general market news
    print(f"\n🎯 STOCK-SPECIFIC vs GENERAL NEWS:")
    stock_specific_count = 0
    general_news_count = 0
    
    for symbol, data in news_analysis.items():
        if "headlines" in data:
            for headline in data["headlines"]:
                headline_lower = headline.lower()
                symbol_lower = symbol.lower()
                
                # Check if headline mentions the specific stock
                if symbol_lower in headline_lower or f"({symbol_lower})" in headline_lower:
                    stock_specific_count += 1
                else:
                    general_news_count += 1
    
    print(f"   Stock-specific headlines: {stock_specific_count}")
    print(f"   General market headlines: {general_news_count}")
    print(f"   Stock-specific ratio: {stock_specific_count/(stock_specific_count+general_news_count)*100:.1f}%")

def test_news_api_behavior():
    """Test if the news APIs are returning the same content for different stocks"""
    
    print("\n🧪 Testing News API Behavior")
    print("=" * 60)
    
    data_fetcher = DataFetcher()
    
    # Test with very different stocks
    test_pairs = [
        ("AAPL", "TSLA"),  # Tech vs Auto
        ("JPM", "XOM"),    # Finance vs Energy
        ("MSFT", "KO"),    # Tech vs Consumer
    ]
    
    for stock1, stock2 in test_pairs:
        print(f"\n🔍 Comparing {stock1} vs {stock2}:")
        
        try:
            # Get news for both stocks
            news1 = data_fetcher.get_company_news(stock1, days_back=7)
            news2 = data_fetcher.get_company_news(stock2, days_back=7)
            
            print(f"   {stock1}: {len(news1)} articles")
            print(f"   {stock2}: {len(news2)} articles")
            
            # Check for overlapping headlines
            headlines1 = [article.get("headline", "") for article in news1[:5] if isinstance(article, dict)]
            headlines2 = [article.get("headline", "") for article in news2[:5] if isinstance(article, dict)]
            
            overlap = set(headlines1) & set(headlines2)
            if overlap:
                print(f"   🚨 OVERLAP: {len(overlap)} identical headlines")
                for headline in overlap:
                    print(f"      '{headline[:60]}...'")
            else:
                print(f"   ✅ No overlapping headlines")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def check_finnhub_api_behavior():
    """Check if Finnhub API is returning stock-specific or general news"""
    
    print("\n🔍 Checking Finnhub API Behavior")
    print("=" * 60)
    
    import requests
    from src.core.config import Config
    
    # Test Finnhub API directly
    test_symbols = ["AAPL", "TSLA", "JPM"]
    
    for symbol in test_symbols:
        print(f"\n📊 Testing Finnhub API for {symbol}:")
        
        try:
            url = f"https://finnhub.io/api/v1/company-news"
            params = {
                "symbol": symbol,
                "from": "2025-06-23",  # 7 days ago
                "to": "2025-06-30",    # today
                "token": Config.FINNHUB_API_KEY,
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                news_data = response.json()
                print(f"   ✅ Got {len(news_data)} articles")
                
                # Check first few articles
                for i, article in enumerate(news_data[:3]):
                    headline = article.get("headline", "No headline")
                    source = article.get("source", "Unknown")
                    print(f"      {i+1}. [{source}] {headline[:80]}...")
                    
                    # Check if headline mentions the stock
                    if symbol.lower() in headline.lower():
                        print(f"         ✅ Stock-specific")
                    else:
                        print(f"         ⚠️  General news")
            else:
                print(f"   ❌ API error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    analyze_news_sources()
    test_news_api_behavior()
    check_finnhub_api_behavior() 