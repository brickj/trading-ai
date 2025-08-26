"""
Repository layer for optimized data access patterns
"""

from .base_repository import BaseRepository
from .recommendation_repository import RecommendationRepository
from .market_data_repository import MarketDataRepository
from .user_repository import UserRepository

# Create repository instances (singletons for connection pooling)
recommendation_repo = RecommendationRepository()
market_data_repo = MarketDataRepository()
user_repo = UserRepository()

__all__ = [
    'BaseRepository',
    'RecommendationRepository', 
    'MarketDataRepository',
    'UserRepository',
    'recommendation_repo',
    'market_data_repo',
    'user_repo'
]

