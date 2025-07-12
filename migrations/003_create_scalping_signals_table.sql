-- Migration 003: Create scalping_signals table
-- This table stores scalping opportunities identified during morning trading sessions

CREATE TABLE IF NOT EXISTS scalping_signals (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    asset_type VARCHAR(10) NOT NULL CHECK (asset_type IN ('stock', 'crypto')),
    date DATE NOT NULL,
    time_collected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    price_open FLOAT,
    price_now FLOAT,
    volume_ratio FLOAT,
    price_change_pct FLOAT,
    gap_pct FLOAT,
    bid_ask_spread FLOAT,
    sentiment_score INTEGER,
    sentiment_class VARCHAR(10) CHECK (sentiment_class IN ('Bullish', 'Neutral', 'Bearish')),
    recommendation VARCHAR(50),
    headlines_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure one record per ticker per day
    UNIQUE(ticker, date)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_scalping_signals_ticker ON scalping_signals(ticker);
CREATE INDEX IF NOT EXISTS idx_scalping_signals_date ON scalping_signals(date);
CREATE INDEX IF NOT EXISTS idx_scalping_signals_recommendation ON scalping_signals(recommendation);
CREATE INDEX IF NOT EXISTS idx_scalping_signals_sentiment ON scalping_signals(sentiment_class);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_scalping_signals_updated_at 
    BEFORE UPDATE ON scalping_signals 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add active column to watchlists table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'watchlists' AND column_name = 'active') THEN
        ALTER TABLE watchlists ADD COLUMN active BOOLEAN DEFAULT TRUE;
    END IF;
END $$;

-- Create index on active column for watchlists
CREATE INDEX IF NOT EXISTS idx_watchlists_active ON watchlists(active); 