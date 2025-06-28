#!/bin/bash

echo "🗄️ PostgreSQL Database Setup for Trading AI Platform"
echo "===================================================="

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Please install it first."
    echo "Run: ./install_postgresql.sh"
    exit 1
fi

echo "✅ PostgreSQL is installed!"
psql --version

# Check if PostgreSQL service is running
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "❌ PostgreSQL service is not running."
    echo "Please start PostgreSQL service:"
    echo "  - If installed via Homebrew: brew services start postgresql@14"
    echo "  - If installed via installer: Check System Preferences > PostgreSQL"
    exit 1
fi

echo "✅ PostgreSQL service is running!"

# Database configuration
DB_NAME="trading_db"
DB_USER="trading_user"
DB_PASSWORD="trading_password"
DB_HOST="localhost"
DB_PORT="5432"

echo ""
echo "📋 Setting up database:"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: $DB_PASSWORD"
echo ""

# Create database and user
echo "🔧 Creating database and user..."

# Connect as postgres superuser to create database and user
psql -h $DB_HOST -U postgres -d postgres << EOF
-- Create database if it doesn't exist
SELECT 'CREATE DATABASE $DB_NAME' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Create user if it doesn't exist
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\c $DB_NAME
GRANT ALL ON SCHEMA public TO $DB_USER;
EOF

if [ $? -eq 0 ]; then
    echo "✅ Database and user created successfully!"
else
    echo "❌ Failed to create database and user."
    echo "You may need to enter the postgres superuser password."
    exit 1
fi

# Test connection with the new user
echo ""
echo "🧪 Testing database connection..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT version();" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Database connection successful!"
else
    echo "❌ Database connection failed."
    exit 1
fi

# Run the Python setup script
echo ""
echo "🔧 Running Python database setup..."
python3 src/utils/setup_postgres.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 PostgreSQL setup completed successfully!"
    echo ""
    echo "📋 Your Trading AI application is now ready with:"
    echo "  - PostgreSQL database: $DB_NAME"
    echo "  - Cache tables for improved performance"
    echo "  - Recommendation tracking tables"
    echo ""
    echo "🚀 You can now start your application:"
    echo "  python3 -m flask --app src.web.app run --host=0.0.0.0 --port=5001"
else
    echo "❌ Python setup failed. Check the error messages above."
    exit 1
fi

# Database setup script for Trading AI Platform
# This script creates the necessary database tables and populates them with default data

echo "🚀 Setting up Trading AI Database..."

# Create tables
echo "📋 Creating database tables..."

# Historical data table
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
CREATE TABLE IF NOT EXISTS historical_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open_price DECIMAL(10,2),
    high_price DECIMAL(10,2),
    low_price DECIMAL(10,2),
    close_price DECIMAL(10,2),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);"

# S&P 500 symbols table
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
CREATE TABLE IF NOT EXISTS sp500_symbols (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255),
    sector VARCHAR(100),
    industry VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"

# API cache table
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
CREATE TABLE IF NOT EXISTS api_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) NOT NULL,
    data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    key_hash VARCHAR(255),
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cache_key),
    UNIQUE(key_hash)
);"

# Recommendations table
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    recommendation_type VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL,
    confidence DECIMAL(5,4),
    sentiment_score DECIMAL(5,4),
    price_data JSONB,
    analysis_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);"

# Watchlists table
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
CREATE TABLE IF NOT EXISTS watchlists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    symbols TEXT[] NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"

# Cache table (legacy)
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
CREATE TABLE IF NOT EXISTS cache (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);"

# App cache table
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
CREATE TABLE IF NOT EXISTS app_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    cache_value JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);"

# Tier management table
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
CREATE TABLE IF NOT EXISTS user_tiers (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) UNIQUE NOT NULL,
    tier_name VARCHAR(50) NOT NULL DEFAULT 'free',
    tier_level INTEGER NOT NULL DEFAULT 0,
    features JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);"

# Insert default tier configuration
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
INSERT INTO user_tiers (user_id, tier_name, tier_level, features) 
VALUES 
    ('default', 'free', 0, '{\"max_api_calls\": 100, \"max_symbols\": 5, \"features\": [\"basic_analysis\", \"system_status\"]}'),
    ('default', 'paid', 1, '{\"max_api_calls\": 1000, \"max_symbols\": 50, \"features\": [\"basic_analysis\", \"enhanced_analysis\", \"portfolio\", \"backtest\", \"opportunities\", \"recommendations\", \"system_status\"]}')
ON CONFLICT (user_id) DO UPDATE SET 
    tier_name = EXCLUDED.tier_name,
    tier_level = EXCLUDED.tier_level,
    features = EXCLUDED.features,
    updated_at = CURRENT_TIMESTAMP;"

echo "✅ Database setup complete!"
echo "📊 Tables created:"
echo "  - historical_data"
echo "  - sp500_symbols" 
echo "  - api_cache"
echo "  - recommendations"
echo "  - watchlists"
echo "  - cache"
echo "  - app_cache"
echo "  - user_tiers"
echo ""
echo "🔑 Default user tier: free"
echo "💳 To upgrade to paid tier, use the tier management API"

# Populate default watchlist symbols
echo "📈 Populating default watchlist symbols..."

# Default stocks
DEFAULT_STOCKS=(
    "AAPL" "MSFT" "GOOGL" "AMZN" "TSLA" "META" "NVDA" "JPM"
    "JNJ" "V" "PG" "UNH" "HD" "MA" "DIS" "PYPL" "BAC" "NFLX"
)

# Default crypto
DEFAULT_CRYPTO=(
    "BTCUSD" "ETHUSD" "ADAUSD" "SOLUSD" "DOTUSD" "LINKUSD"
)

# Insert stocks
for stock in "${DEFAULT_STOCKS[@]}"; do
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
        INSERT INTO watchlists (symbol, type) 
        VALUES ('$stock', 'stock') 
        ON CONFLICT (symbol, type) DO NOTHING;
    "
done

# Insert crypto
for crypto in "${DEFAULT_CRYPTO[@]}"; do
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
        INSERT INTO watchlists (symbol, type) 
        VALUES ('$crypto', 'crypto') 
        ON CONFLICT (symbol, type) DO NOTHING;
    "
done

echo "✅ Default watchlist symbols populated successfully!"

# Verify the setup
echo "🔍 Verifying database setup..."

STOCK_COUNT=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM watchlists WHERE type = 'stock';")
CRYPTO_COUNT=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM watchlists WHERE type = 'crypto';")

echo "📊 Database verification complete:"
echo "   - Stocks in watchlist: $STOCK_COUNT"
echo "   - Crypto in watchlist: $CRYPTO_COUNT"

echo "🎉 Database setup completed successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. Start the Trading AI application: python3 start_app.py"
echo "   2. Visit http://localhost:5001/system_status to manage watchlists"
echo "   3. Crypto symbols are now read-only - contact admin to add new ones" 