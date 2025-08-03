#!/bin/bash

# Setup script for Weekly Plan feature cron job
# This script sets up automatic data population for the weekly plan

echo "🕒 Setting up Weekly Plan cron job..."

# Get the current directory
TRADING_DIR=$(pwd)

# Create the cron job command
CRON_CMD="0 2 * * 1 cd $TRADING_DIR && python3 -c 'from src.data.weekly_plan_populator import WeeklyPlanPopulator; WeeklyPlanPopulator().populate_advance_data()' >> $TRADING_DIR/logs/weekly_plan_cron.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "weekly_plan_populator"; then
    echo "⚠️  Weekly plan cron job already exists"
    echo "Current cron jobs:"
    crontab -l | grep "weekly_plan_populator"
else
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "✅ Added weekly plan cron job:"
    echo "   $CRON_CMD"
    echo ""
    echo "📋 This will run every Monday at 2:00 AM to refresh market data"
fi

echo ""
echo "🔍 Current cron jobs:"
crontab -l

echo ""
echo "📁 Logs will be written to: $TRADING_DIR/logs/weekly_plan_cron.log"
echo "🔧 To manually run data population: python3 -c 'from src.data.weekly_plan_populator import WeeklyPlanPopulator; WeeklyPlanPopulator().populate_advance_data()'"
echo ""
echo "✅ Weekly Plan cron setup completed!"