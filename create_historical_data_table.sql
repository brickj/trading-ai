-- Create historical_data table for storing 2-year historical price data
-- This table is used by the Enhanced Trading Strategy for backtesting

CREATE TABLE IF NOT EXISTS historical_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(10,4),
    high DECIMAL(10,4),
    low DECIMAL(10,4),
    close DECIMAL(10,4),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);

-- Create index for efficient queries
CREATE INDEX IF NOT EXISTS idx_historical_data_symbol_date ON historical_data(symbol, date);
CREATE INDEX IF NOT EXISTS idx_historical_data_date ON historical_data(date);

-- Add comment
COMMENT ON TABLE historical_data IS 'Stores 2-year historical price data for enhanced analysis backtesting';
COMMENT ON COLUMN historical_data.symbol IS 'Stock or crypto symbol';
COMMENT ON COLUMN historical_data.date IS 'Trading date';
COMMENT ON COLUMN historical_data.open IS 'Opening price';
COMMENT ON COLUMN historical_data.high IS 'High price for the day';
COMMENT ON COLUMN historical_data.low IS 'Low price for the day';
COMMENT ON COLUMN historical_data.close IS 'Closing price';
COMMENT ON COLUMN historical_data.volume IS 'Trading volume';
COMMENT ON COLUMN historical_data.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN historical_data.updated_at IS 'Record last update timestamp';
