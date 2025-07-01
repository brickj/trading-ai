#!/usr/bin/env python3
"""
Test script to check if Ollama returns the same sentiment for different news content.
This will help us determine if the issue is with Ollama or the integration.
"""

import requests
import json
import time

def test_ollama_sentiment(news_text, test_name):
    """
    Test Ollama sentiment analysis with given news text
    """
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
    
    try:
        print(f"\n🧪 Testing: {test_name}")
        print(f"📝 News content: {news_text[:100]}...")
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=60,
        )
        
        if response.status_code != 200:
            print(f"❌ Ollama API error: {response.status_code} - {response.text}")
            return None
            
        result = response.json()
        content = result.get("response", "")
        
        print(f"🔍 Raw Ollama response: {content[:200]}...")
        
        # Try to parse JSON
        try:
            parsed = json.loads(content)
            sentiment_score = parsed.get("sentiment_score", "MISSING")
            confidence = parsed.get("confidence", "MISSING")
            summary = parsed.get("summary", "MISSING")
            
            print(f"✅ Parsed result:")
            print(f"   Sentiment Score: {sentiment_score}")
            print(f"   Confidence: {confidence}")
            print(f"   Summary: {summary[:100]}...")
            
            return {
                "sentiment_score": sentiment_score,
                "confidence": confidence,
                "summary": summary,
                "raw_response": content
            }
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print(f"📄 Full response: {content}")
            return None
            
    except Exception as e:
        print(f"❌ Error calling Ollama: {e}")
        return None

def main():
    """Run the Ollama sentiment test with different news content"""
    
    print("🚀 Testing Ollama Sentiment Analysis with Different News Content")
    print("=" * 80)
    
    # Test 1: Very positive news
    positive_news = """
    Headline: Apple Reports Record-Breaking Quarterly Earnings
    Summary: Apple Inc. announced exceptional quarterly results with revenue growth of 25% and record iPhone sales. The company exceeded all analyst expectations and raised its guidance for the next quarter. CEO Tim Cook expressed optimism about future growth prospects.
    
    Headline: Apple Stock Surges 15% on Strong Earnings Report
    Summary: Apple shares jumped significantly after the company reported better-than-expected earnings. Analysts are upgrading their price targets and recommending the stock as a strong buy.
    """
    
    # Test 2: Very negative news
    negative_news = """
    Headline: Tesla Faces Major Production Delays and Quality Issues
    Summary: Tesla reported significant production problems and quality control issues that have led to delays in vehicle deliveries. The company's stock has fallen 20% this week as investors worry about future profitability.
    
    Headline: Tesla Recalls 100,000 Vehicles Due to Safety Concerns
    Summary: Tesla announced a major vehicle recall affecting over 100,000 cars due to critical safety issues. The recall is expected to cost the company millions and damage its reputation for quality.
    """
    
    # Test 3: Neutral news
    neutral_news = """
    Headline: Microsoft Announces Quarterly Results in Line with Expectations
    Summary: Microsoft reported quarterly earnings that met analyst expectations. Revenue was stable with moderate growth in cloud services offset by declines in other segments.
    
    Headline: Microsoft Stock Trades Sideways After Earnings Report
    Summary: Microsoft shares showed little movement after the company reported earnings that were largely in line with Wall Street estimates. Analysts maintain their current ratings.
    """
    
    # Test 4: Mixed news
    mixed_news = """
    Headline: Amazon Reports Strong Cloud Growth but Retail Struggles
    Summary: Amazon's cloud computing division showed excellent performance with 30% growth, but the retail segment faced challenges due to increased competition and rising costs.
    
    Headline: Amazon Faces Regulatory Scrutiny While Expanding Market Share
    Summary: Amazon continues to gain market share in e-commerce but faces increasing regulatory pressure from multiple government agencies investigating antitrust concerns.
    """
    
    # Run all tests
    tests = [
        ("Very Positive News", positive_news),
        ("Very Negative News", negative_news),
        ("Neutral News", neutral_news),
        ("Mixed News", mixed_news),
    ]
    
    results = {}
    
    for test_name, news_content in tests:
        result = test_ollama_sentiment(news_content, test_name)
        results[test_name] = result
        time.sleep(2)  # Small delay between requests
    
    # Analyze results
    print("\n" + "=" * 80)
    print("📊 ANALYSIS RESULTS")
    print("=" * 80)
    
    sentiment_scores = []
    confidences = []
    
    for test_name, result in results.items():
        if result:
            sentiment_scores.append(result["sentiment_score"])
            confidences.append(result["confidence"])
            print(f"✅ {test_name}: sentiment={result['sentiment_score']}, confidence={result['confidence']}")
        else:
            print(f"❌ {test_name}: FAILED")
    
    # Check for identical results
    if len(set(sentiment_scores)) == 1 and len(set(confidences)) == 1:
        print(f"\n🚨 PROBLEM DETECTED: All tests returned identical results!")
        print(f"   Sentiment Score: {sentiment_scores[0]}")
        print(f"   Confidence: {confidences[0]}")
        print(f"   This indicates Ollama is not properly analyzing different content.")
    else:
        print(f"\n✅ GOOD NEWS: Ollama is returning different results for different content!")
        print(f"   Sentiment Scores: {sentiment_scores}")
        print(f"   Confidences: {confidences}")
        print(f"   This means the issue is likely in the integration, not Ollama itself.")
    
    # Check if results match what we see in the app
    print(f"\n🔍 COMPARISON WITH APP RESULTS:")
    print(f"   App shows: sentiment=-0.200, confidence=0.600 for all stocks")
    print(f"   Test results: {sentiment_scores}")
    
    if -0.2 in sentiment_scores and 0.6 in confidences:
        print(f"   ⚠️  WARNING: Test found the same values as the app!")
        print(f"   This suggests Ollama might be returning cached or default responses.")
    else:
        print(f"   ✅ Test results are different from app results.")
        print(f"   This suggests the issue is in the app's integration, not Ollama.")

if __name__ == "__main__":
    main() 