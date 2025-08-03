import requests
from transformers import pipeline
from datetime import datetime, timedelta

# Initialize sentiment analysis model (FinBERT or equivalent)
sentiment_analyzer = pipeline("sentiment-analysis", model="ProsusAI/finbert")

# Constants for APIs
MARKET_DATA_API = "https://api.example.com/market_data"
NEWS_API = "https://newsapi.org/v2/everything"
NEWS_API_KEY = "your_news_api_key"


# Step 1: Identify Scalping Candidates
def get_scalping_candidates():
    """Fetch market data and filter scalping candidates."""
    response = requests.get(MARKET_DATA_API)
    market_data = response.json()

    candidates = []
    for ticker in market_data:
        volume_ratio = ticker["volume"] / ticker["avg_volume_5d"]
        price_change_pct = (
            abs((ticker["current_price"] - ticker["open_price"]) / ticker["open_price"])
            * 100
        )

        if volume_ratio > 2 and price_change_pct > 2:
            candidates.append(
                {
                    "ticker": ticker["symbol"],
                    "price_open": ticker["open_price"],
                    "price_now": ticker["current_price"],
                    "volume_ratio": volume_ratio,
                    "price_change_pct": price_change_pct,
                }
            )

    return candidates


# Step 2: Perform News Sentiment Analysis
def analyze_sentiment(ticker):
    """Fetch news and analyze sentiment for a given ticker."""
    params = {
        "q": ticker,
        "from": (datetime.now() - timedelta(hours=12)).isoformat(),
        "apiKey": NEWS_API_KEY,
    }
    response = requests.get(NEWS_API, params=params)
    news_data = response.json()

    headlines = news_data.get("articles", [])
    sentiment_scores = []

    for article in headlines:
        sentiment = sentiment_analyzer(article["title"])[0]
        sentiment_scores.append(
            1
            if sentiment["label"] == "POSITIVE"
            else -1
            if sentiment["label"] == "NEGATIVE"
            else 0
        )

    total_score = sum(sentiment_scores)
    sentiment = (
        "Bullish" if total_score > 2 else "Bearish" if total_score < -2 else "Neutral"
    )

    return {
        "sentiment": sentiment,
        "top_headlines": [
            {
                "title": article["title"],
                "sentiment": sentiment_analyzer(article["title"])[0]["label"],
            }
            for article in headlines
        ],
    }


# Step 3: Generate Scalping Recommendations
def generate_recommendations():
    """Combine metrics and sentiment to generate recommendations."""
    candidates = get_scalping_candidates()
    recommendations = []

    for candidate in candidates:
        sentiment_data = analyze_sentiment(candidate["ticker"])
        recommendation = "No Strong Edge"

        if candidate["volume_ratio"] > 2 and candidate["price_change_pct"] > 2:
            if sentiment_data["sentiment"] == "Bullish":
                recommendation = "Long Scalping Opportunity"
            elif sentiment_data["sentiment"] == "Bearish":
                recommendation = "Short Scalping Opportunity"

        recommendations.append(
            {
                **candidate,
                "sentiment": sentiment_data["sentiment"],
                "recommendation": recommendation,
                "top_headlines": sentiment_data["top_headlines"],
            }
        )

    return recommendations


# Example usage
if __name__ == "__main__":
    results = generate_recommendations()
    print(results)
