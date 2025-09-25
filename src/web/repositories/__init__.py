"""
Repository layer for optimized data access patterns
"""

from .base_repository import BaseRepository
from .market_data_repository import MarketDataRepository

# Create repository instances (singletons for connection pooling)
market_data_repo = MarketDataRepository()

__all__ = [
    'BaseRepository',
    'MarketDataRepository',
    'market_data_repo',
]

