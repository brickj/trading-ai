-- Create new market_movers table
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

-- Migrate data from preloaded_data to market_movers if it exists
DO $$
BEGIN
    -- Check if preloaded_data table exists and has data
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'preloaded_data') THEN
        -- Insert gainers
        INSERT INTO market_movers (symbol, type, price, change_amount, change_percent, volume, timestamp, analysis_data)
        SELECT 
            data->>'symbol' as symbol,
            'GAINER' as type,
            (data->>'price')::numeric as price,
            (data->>'change')::numeric as change_amount,
            (data->>'change_percent')::numeric as change_percent,
            NULL as volume,  -- Not available in old data
            timestamp,
            data as analysis_data
        FROM preloaded_data
        WHERE data->>'change_percent'::text > '0';
        
        -- Insert losers
        INSERT INTO market_movers (symbol, type, price, change_amount, change_percent, volume, timestamp, analysis_data)
        SELECT 
            data->>'symbol' as symbol,
            'LOSER' as type,
            (data->>'price')::numeric as price,
            (data->>'change')::numeric as change_amount,
            (data->>'change_percent')::numeric as change_percent,
            NULL as volume,  -- Not available in old data
            timestamp,
            data as analysis_data
        FROM preloaded_data
        WHERE data->>'change_percent'::text <= '0';
        
        -- Drop the old table after migration
        DROP TABLE IF EXISTS preloaded_data;
    END IF;
END $$;
