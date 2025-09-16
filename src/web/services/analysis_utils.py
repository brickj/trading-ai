"""Utility helpers shared across analysis-related routes."""
from typing import Any, Dict, List, Optional

from ..dependencies import sentiment_analyzer


def analyze_sentiment_with_fallback(
    news_data: Optional[List[Dict[str, Any]]],
    price_data: Dict[str, Any],
    symbol: str,
    ai_provider: Optional[str] = None,
) -> Dict[str, Any]:
    """Analyze sentiment with fallback to price-based analysis."""
    try:
        if news_data and len(news_data) > 0:
            if isinstance(ai_provider, str):
                sentiment_result = sentiment_analyzer.analyze_news_sentiment(
                    news_data, ai_provider=ai_provider, symbol=symbol
                )
            else:
                sentiment_result = sentiment_analyzer.analyze_news_sentiment(
                    news_data, symbol=symbol
                )
            sentiment_result["news_sentiment"] = sentiment_result["sentiment_score"]
            sentiment_result["has_news"] = True
            return sentiment_result

        sentiment_result = sentiment_analyzer.analyze_price_based_sentiment(
            price_data, symbol
        )
        sentiment_result["news_sentiment"] = 0.0
        sentiment_result["has_news"] = False
        return sentiment_result
    except Exception as error:
        message = str(error)
        if (
            "No news articles provided for analysis" in message
            or "No valid news content found" in message
        ):
            try:
                sentiment_result = sentiment_analyzer.analyze_price_based_sentiment(
                    price_data, symbol
                )
                sentiment_result["news_sentiment"] = 0.0
                sentiment_result["has_news"] = False
                return sentiment_result
            except Exception as price_error:
                return {
                    "sentiment_score": 0.0,
                    "confidence": 0.3,
                    "summary": f"Analysis failed for {symbol}",
                    "reasoning": f"Both news and price analysis failed: {price_error}",
                    "provider": "fallback",
                    "analysis_type": "error",
                    "news_sentiment": 0.0,
                    "has_news": False,
                }
        raise


__all__ = ["analyze_sentiment_with_fallback"]
