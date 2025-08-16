-- Migration 005: Create foreign_exchanges table
-- This table centralizes all market/exchange information for proper foreign market management

CREATE TABLE IF NOT EXISTS foreign_exchanges (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(50) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    timezone VARCHAR(50) NOT NULL,
    symbol_suffix VARCHAR(10) NOT NULL,
    trading_hours_open TIME,
    trading_hours_close TIME,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert the currently supported exchanges
INSERT INTO foreign_exchanges (code, name, country, currency, timezone, symbol_suffix, trading_hours_open, trading_hours_close) VALUES
('NASDAQ', 'NASDAQ', 'United States', 'USD', 'America/New_York', '', '09:30:00', '16:00:00'),
('NYSE', 'New York Stock Exchange', 'United States', 'USD', 'America/New_York', '', '09:30:00', '16:00:00'),
('LSE', 'London Stock Exchange', 'United Kingdom', 'GBP', 'Europe/London', '.L', '08:00:00', '16:30:00'),
('XETRA', 'Deutsche Börse XETRA', 'Germany', 'EUR', 'Europe/Berlin', '.DE', '09:00:00', '17:30:00'),
('TSE', 'Tokyo Stock Exchange', 'Japan', 'JPY', 'Asia/Tokyo', '.T', '09:00:00', '15:00:00'),
('TSX', 'Toronto Stock Exchange', 'Canada', 'CAD', 'America/Toronto', '.TO', '09:30:00', '16:00:00'),
('HKEX', 'Hong Kong Stock Exchange', 'Hong Kong', 'HKD', 'Asia/Hong_Kong', '.HK', '09:30:00', '16:00:00'),
('Euronext', 'Euronext Paris', 'France', 'EUR', 'Europe/Paris', '.PA', '09:00:00', '17:30:00'),
('AMS', 'Amsterdam Stock Exchange', 'Netherlands', 'EUR', 'Europe/Amsterdam', '.AS', '09:00:00', '17:30:00'),
('B3', 'B3 Stock Exchange', 'Brazil', 'BRL', 'America/Sao_Paulo', '.SA', '10:00:00', '17:00:00'),
('TWSE', 'Taiwan Stock Exchange', 'Taiwan', 'TWD', 'Asia/Taipei', '', '09:00:00', '13:30:00');

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_foreign_exchanges_code ON foreign_exchanges(code);
CREATE INDEX IF NOT EXISTS idx_foreign_exchanges_active ON foreign_exchanges(active);
CREATE INDEX IF NOT EXISTS idx_foreign_exchanges_currency ON foreign_exchanges(currency);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_foreign_exchanges_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_foreign_exchanges_updated_at 
    BEFORE UPDATE ON foreign_exchanges 
    FOR EACH ROW 
    EXECUTE FUNCTION update_foreign_exchanges_updated_at();

-- Add comments for documentation
COMMENT ON TABLE foreign_exchanges IS 'Centralized table for all supported stock exchanges and markets';
COMMENT ON COLUMN foreign_exchanges.code IS 'Short exchange code (e.g., LSE, TSX)';
COMMENT ON COLUMN foreign_exchanges.symbol_suffix IS 'Yahoo Finance suffix for symbols (e.g., .L for LSE)';
COMMENT ON COLUMN foreign_exchanges.currency IS 'Native currency for this exchange';
COMMENT ON COLUMN foreign_exchanges.timezone IS 'Exchange timezone for market hours';
