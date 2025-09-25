"""
Core functionality for the trading system.
This package contains the fundamental components:
- Configuration management
- Sentiment analysis
- Service clients
- Recommendation management
"""

from .config import Config
from .sentiment_analyzer import SentimentAnalyzer
# from .go_service_client import GoServiceClient  # Module removed
from .recommendation_manager import get_recommendation_manager, RecommendationManager

__all__ = [
    "Config",
    "SentimentAnalyzer",
    # "GoServiceClient",  # Module removed
    "RecommendationManager",
    "get_recommendation_manager",
]
