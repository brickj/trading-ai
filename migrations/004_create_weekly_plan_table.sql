-- Migration: Create weekly plan table for market calendar events
-- This table stores all market events organized by week for efficient querying

CREATE TABLE IF NOT EXISTS weekly_plan_events (
    id SERIAL PRIMARY KEY,
    week_start_date DATE NOT NULL,
    event_date DATE NOT NULL,
    event_name VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- earnings, economic_data, federal_reserve, options_expiration, market_holidays
    event_subtype VARCHAR(50), -- weekly, monthly, quarterly for options; cpi, gdp, etc for economic
    impact VARCHAR(20) NOT NULL DEFAULT 'medium', -- high, medium, low
    timing VARCHAR(50), -- market_open, market_close, pre_market, after_hours, all_day
    source VARCHAR(100) NOT NULL, -- api_name, calculated, manual
    symbol VARCHAR(20), -- for earnings events
    description TEXT,
    details JSONB, -- additional event-specific data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX idx_weekly_plan_week_start ON weekly_plan_events(week_start_date);
CREATE INDEX idx_weekly_plan_event_date ON weekly_plan_events(event_date);
CREATE INDEX idx_weekly_plan_event_type ON weekly_plan_events(event_type);
CREATE INDEX idx_weekly_plan_symbol ON weekly_plan_events(symbol) WHERE symbol IS NOT NULL;

-- Composite index for the most common query pattern
CREATE INDEX idx_weekly_plan_week_type ON weekly_plan_events(week_start_date, event_type);

-- Comments for documentation
COMMENT ON TABLE weekly_plan_events IS 'Stores market calendar events organized by week for the Weekly Plan feature';
COMMENT ON COLUMN weekly_plan_events.week_start_date IS 'Monday of the week this event belongs to';
COMMENT ON COLUMN weekly_plan_events.event_date IS 'Actual date when the event occurs';
COMMENT ON COLUMN weekly_plan_events.event_type IS 'Category: earnings, economic_data, federal_reserve, options_expiration, market_holidays';
COMMENT ON COLUMN weekly_plan_events.impact IS 'Market impact level: high, medium, low';
COMMENT ON COLUMN weekly_plan_events.details IS 'JSON field for additional event-specific data like estimates, previous values, etc';