-- Create market_movers table
CREATE TABLE IF NOT EXISTS market_movers (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    type VARCHAR(10) NOT NULL CHECK (type IN ('GAINER', 'LOSER')),
    price DECIMAL(12, 4),
    change_amount DECIMAL(12, 4),
    change_percent DECIMAL(10, 4),
    volume BIGINT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analysis_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(symbol, type, timestamp)
);

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_market_movers_type_timestamp ON market_movers(type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_market_movers_symbol ON market_movers(symbol);

-- Drop the old preloaded_data table if it exists
-- DROP TABLE IF EXISTS preloaded_data;
