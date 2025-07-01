#!/usr/bin/env python3
"""
Debug script to check what news content is being sent to Ollama for different stocks.
This will help us see if the app is sending the same news content to all stocks.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.data_fetcher import DataFetcher
from src.core.sentiment_analyzer import SentimentAnalyzer

def debug_news_content():
    """Debug what news content is being sent to Ollama for different stocks"""
    
    print("🔍 Debugging News Content Sent to Ollama")
    print("=" * 60)
    
    # Initialize components
    data_fetcher = DataFetcher()
    sentiment_analyzer = SentimentAnalyzer()
    
    # Test stocks
    test_symbols = ["AAPL", "TSLA", "MSFT", "AMZN"]
    
    for symbol in test_symbols:
        print(f"\n📊 Analyzing {symbol}...")
        
        try:
            # Get news data
            news_data = data_fetcher.get_company_news(symbol, days_back=7)
            print(f"   📰 Got {len(news_data)} news articles")
            
            if not news_data:
                print(f"   ⚠️  No news data for {symbol}")
                continue
            
            # Show first few news articles
            print(f"   📄 Sample news articles:")
            for i, article in enumerate(news_data[:3]):
                if isinstance(article, dict):
                    headline = article.get("headline", article.get("title", "No headline"))
                    summary = article.get("summary", article.get("description", "No summary"))
                    print(f"      {i+1}. Headline: {headline[:80]}...")
                    print(f"         Summary: {summary[:80]}...")
                else:
                    print(f"      {i+1}. Invalid article format: {type(article)}")
            
            # Get price data for fallback
            price_data = data_fetcher.get_stock_price(symbol)
            print(f"   💰 Current price: ${price_data.get('current_price', 0):.2f}")
            
            # Test sentiment analysis
            print(f"   🤖 Testing sentiment analysis...")
            try:
                sentiment_result = sentiment_analyzer.analyze_news_sentiment(news_data)
                print(f"   ✅ Sentiment: {sentiment_result['sentiment_score']:.3f}")
                print(f"   ✅ Confidence: {sentiment_result['confidence']:.3f}")
                print(f"   ✅ Summary: {sentiment_result['summary'][:100]}...")
            except Exception as e:
                print(f"   ❌ Sentiment analysis failed: {e}")
                
        except Exception as e:
            print(f"   ❌ Error analyzing {symbol}: {e}")
        
        print("-" * 40)

def test_ollama_with_real_news():
    """Test Ollama with the actual news content from the app"""
    
    print("\n🧪 Testing Ollama with Real News Content")
    print("=" * 60)
    
    data_fetcher = DataFetcher()
    
    # Test with a specific stock
    symbol = "AAPL"
    print(f"📊 Testing with {symbol}...")
    
    try:
        # Get news data
        news_data = data_fetcher.get_company_news(symbol, days_back=7)
        print(f"📰 Got {len(news_data)} news articles for {symbol}")
        
        if news_data:
            # Prepare news text exactly like the app does
            news_text = ""
            for article in news_data[:5]:  # Limit to 5 most recent articles
                if isinstance(article, dict):
                    headline = article.get("headline", article.get("title", ""))
                    summary = article.get("summary", article.get("description", article.get("selftext", "")))
                    if headline or summary:
                        news_text += f"Headline: {headline}\nSummary: {summary}\n\n"
            
            print(f"📝 Prepared news text length: {len(news_text)} characters")
            print(f"📄 First 200 chars: {news_text[:200]}...")
            
            # Test with Ollama directly
            import requests
            import json
            
            prompt = f"""
            Analyze the sentiment of the following financial news articles and provide:
            1. A sentiment score between -1 (very negative) and 1 (very positive)
            2. A confidence level between 0 and 1
            3. A brief summary of the overall sentiment
            
            News articles:
            {news_text}
            
            IMPORTANT: Respond with ONLY this exact JSON format, no additional text or explanation:
            {{
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "summary": "your analysis here"
            }}
            """
            
            messages = [
                {
                    "role": "system",
                    "content": "You are a financial sentiment analysis expert. Analyze news sentiment for trading decisions.",
                },
                {"role": "user", "content": prompt},
            ]
            
            # Convert messages to a single prompt for Ollama
            full_prompt = ""
            for message in messages:
                if message["role"] == "system":
                    full_prompt += f"System: {message['content']}\n\n"
                elif message["role"] == "user":
                    full_prompt += f"User: {message['content']}\n\n"
            
            payload = {
                "model": "qwen2.5:3b",
                "prompt": full_prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 200},
            }
            
            print(f"🤖 Sending to Ollama...")
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=60,
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("response", "")
                print(f"🔍 Raw Ollama response: {content[:300]}...")
                
                try:
                    parsed = json.loads(content)
                    print(f"✅ Parsed result:")
                    print(f"   Sentiment Score: {parsed.get('sentiment_score', 'MISSING')}")
                    print(f"   Confidence: {parsed.get('confidence', 'MISSING')}")
                    print(f"   Summary: {parsed.get('summary', 'MISSING')[:100]}...")
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON: {e}")
                    print(f"📄 Full response: {content}")
            else:
                print(f"❌ Ollama API error: {response.status_code} - {response.text}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_news_content()
    test_ollama_with_real_news() 