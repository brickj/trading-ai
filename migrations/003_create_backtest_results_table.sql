-- Migration: Create backtest_results table for strategy backtesting persistence
CREATE TABLE IF NOT EXISTS backtest_results (
    id SERIAL PRIMARY KEY,
    stock_symbol VARCHAR(16) NOT NULL,
    period_days INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    initial_capital NUMERIC(18,2) NOT NULL,
    final_capital NUMERIC(18,2) NOT NULL,
    total_return NUMERIC(8,2) NOT NULL,
    win_rate NUMERIC(5,2) NOT NULL,
    total_trades INTEGER NOT NULL,
    trades JSONB NOT NULL,
    UNIQUE(stock_symbol, period_days, timestamp)
);
-- Index for fast lookup by symbol and period
CREATE INDEX IF NOT EXISTS idx_backtest_symbol_period ON backtest_results (stock_symbol, period_days, timestamp DESC); 