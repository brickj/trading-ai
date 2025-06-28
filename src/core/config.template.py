"""
Configuration Manager for Trading AI Platform.
Centralized configuration management with environment variable support.
"""

import os
import sys

print(f"[DEBUG] Loaded config from: {__file__}")

class Config:
    """Centralized configuration for the Trading AI platform"""

    # Database Configuration
    DATABASE_URL = "postgresql://trading_user:trading_password@localhost:5432/trading_db"
    DATABASE_CONFIG = {
        "host": "localhost",
        "port": 5432,
        "database": "trading_db",
        "user": "trading_user",
        "password": "trading_password",
    }
    DB_POOL_SIZE = 10
    DB_MAX_OVERFLOW = 20

    # API Configuration
    ALPHA_VANTAGE_API_KEY = "your_alpha_vantage_api_key_here"
    FINNHUB_API_KEY = "your_finnhub_api_key_here"
    NEWS_API_KEY = "your_news_api_key_here"
    OPENAI_API_KEY = "your_openai_api_key_here"
    
    # Yahoo Finance API (free, no key required)
    YAHOO_FINANCE_ENABLED = True
    
    # CoinGecko API (free, no key required)
    COINGECKO_ENABLED = True
    
    # Reddit API (free, no key required for basic usage)
    REDDIT_ENABLED = True
    REDDIT_CLIENT_ID = "your_reddit_client_id_here"
    REDDIT_SECRET_KEY = "your_reddit_secret_key_here"

    # Application Configuration
    DEBUG = False
    DEBUG_MODE = False  # For web/app.py compatibility
    PORT = 5001
    WEB_PORT = 5001  # For web/app.py compatibility
    HOST = "0.0.0.0"
    WEB_HOST = "0.0.0.0"  # For web/app.py compatibility
    SECRET_KEY = "your-secret-key-here"

    # Performance Configuration
    MAX_CONCURRENT_REQUESTS = 5
    MAX_BATCH_SIZE = 50  # Maximum number of symbols for bulk analysis
    REQUEST_TIMEOUT = 30
    CACHE_TTL = 3600

    # Analysis Configuration
    BULK_ANALYSIS_NEWS_DAYS = 7
    BULK_ANALYSIS_SP500_LIMIT = 6  # 60% of SP500_STOCKS length for performance
    BULK_ANALYSIS_CRYPTO_LIMIT = 3  # 70% of CRYPTO_SYMBOLS length for performance
    ENHANCED_ANALYSIS_TIMEOUT = 300
    HISTORICAL_LOOKBACK_DAYS = 730  # 2 years

    # Sentiment Analysis Configuration
    SENTIMENT_THRESHOLD = 0.1
    CONFIDENCE_THRESHOLD = 0.3

    # Default Crypto Symbols
    DEFAULT_CRYPTO_SYMBOLS = ["BTCUSD", "ETHUSD", "ADAUSD", "SOLUSD"]
    CRYPTO_SYMBOLS = ["BTCUSD", "ETHUSD", "ADAUSD", "DOTUSD", "LINKUSD"]
    
    # Tier Configuration
    DEFAULT_TIER = "free"
    CURRENT_TIER = "free"
    TIER_NAMES = {
        "free": "Free Tier",
        "paid": "Paid Tier"
    }
    
    # Tier Page Access Configuration
    FREE_TIER_PAGES = ["/", "/system_status", "/logs"]
    PAID_TIER_PAGES = ["/stocks", "/crypto", "/portfolio_page", "/backtest_page", "/opportunities", "/recommendations"]
    TIER_CONTACT_INFO = {
        "email": "support@example.com",
        "message": "Contact support to upgrade to Paid Tier"
    }

    # Logging Configuration
    LOG_LEVEL = "INFO"
    LOG_DIR = "logs"
    ENABLE_FILE_LOGGING = True

    # Cache Configuration
    ENABLE_DATABASE_CACHE = True
    CACHE_CLEANUP_INTERVAL = 3600

    # Telegram Configuration
    TELEGRAM_API_KEY = "your_telegram_api_key_here"
    TELEGRAM_CHAT_IDS = ["your_chat_id_here"]
    TELEGRAM_CHAT_ID = "your_chat_id_here"
    TELEGRAM_ALERTS_ENABLED = True
    TELEGRAM_ALERT_COOLDOWN = 300
    TELEGRAM_ALERT_THRESHOLD = 0.7

    # Ollama Configuration
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_MODEL = "llama3.2"
    ENABLE_OLLAMA_SENTIMENT = True

    # Go Service Integration
    USE_GO_SERVICES = False

    # Go Service Configuration
    GO_SERVICE_TIMEOUT = 30  # seconds
    GO_SERVICE_RETRY_COUNT = 3  # number of retries
    GO_NEWS_SERVICE_URL = "http://localhost:8081"    # News microservice
    GO_SIGNAL_SERVICE_URL = "http://localhost:8082"  # Signal microservice
    GO_RISK_SERVICE_URL = "http://localhost:8083"    # Risk microservice
    GO_PORTFOLIO_SERVICE_URL = "http://localhost:8084"  # Portfolio microservice
    GO_DATA_SERVICE_URL = "http://localhost:8085"  # Data microservice

    # AI Configuration
    PREFERRED_AI_PROVIDER = "ollama"
    AI_PROVIDER_FALLBACKS = ["ollama", "deepseek", "openai"]
    DEEPSEEK_API_KEY = "your_deepseek_api_key_here"

    # Test Configuration
    SP500_STOCKS = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "V", "UNH"
    ]
    BULK_ANALYSIS_CACHE_DURATION = 600
    MAX_POSITION_SIZE = 10000
    WATCHLIST_STOCKS = ["AAPL", "MSFT"]
    ENABLE_ALPHA_VANTAGE_NEWS = True
    API_REQUEST_TIMEOUT = 30
    ENABLE_NEWSAPI_ORG = False
    BULK_ANALYSIS_WATCHLIST_LIMIT = 2
    NEWS_SENTIMENT_THRESHOLD = 0.1
    WATCHLIST_CRYPTO = ["BTCUSD", "ETHUSD"]
    BULK_ANALYSIS_TIMEOUT = 120
    YAHOO_NEWS_MAX_ARTICLES = 10
    NEWS_CONFIDENCE_THRESHOLD = 0.3
    ALPHA_VANTAGE_NEWS_MAX_ARTICLES = 5

    @classmethod
    def validate(cls) -> bool:
        """
        Validate required configuration
        Returns:
            True if configuration is valid
        """
        # Check if API keys are set in config file
        if not cls.ALPHA_VANTAGE_API_KEY or not cls.FINNHUB_API_KEY:
            print("❌ Missing API keys in config file. Please set ALPHA_VANTAGE_API_KEY and FINNHUB_API_KEY.")
            return False
            
        if cls.ALPHA_VANTAGE_API_KEY == "your_alpha_vantage_api_key_here" and cls.FINNHUB_API_KEY == "your_finnhub_api_key_here":
            print("⚠️  Using demo API keys. Some features may be limited.")
            
        return True

    @classmethod
    def get_database_url(cls) -> str:
        """Get database URL from config"""
        if cls.DATABASE_URL != "postgresql://localhost/trading_db":
            return cls.DATABASE_URL

        # Build from individual components
        user = cls.DATABASE_CONFIG["user"]
        password = cls.DATABASE_CONFIG["password"]
        host = cls.DATABASE_CONFIG["host"]
        port = cls.DATABASE_CONFIG["port"]
        database = cls.DATABASE_CONFIG["database"]

        if password:
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"
        else:
            return f"postgresql://{user}@{host}:{port}/{database}"

    @classmethod
    def print_config(cls):
        """Print current configuration (without sensitive data)"""
        print("🔧 Current Configuration:")
        print(
            "  Database: "
            f"{cls.DATABASE_CONFIG['host']}:{cls.DATABASE_CONFIG['port']}/"
            f"{cls.DATABASE_CONFIG['database']}"
        )
        print(f"  Port: {cls.PORT}")
        print(f"  Debug: {cls.DEBUG}")
        print(f"  Max Concurrent Requests: {cls.MAX_CONCURRENT_REQUESTS}")
        print(f"  Cache TTL: {cls.CACHE_TTL}s")
        print(f"  Crypto Symbols: {len(cls.DEFAULT_CRYPTO_SYMBOLS)}")
        print(f"  Telegram Alerts: {cls.TELEGRAM_ALERTS_ENABLED}")
        print(f"  Ollama Sentiment: {cls.ENABLE_OLLAMA_SENTIMENT}")

    @classmethod
    def get(cls, key: str, default=None):
        """Get configuration value by key - compatibility method for tests"""
        return getattr(cls, key, default)

# Validate configuration on import
if not Config.validate():
    print("❌ Configuration validation failed. Please check your environment variables.")
    sys.exit(1) 