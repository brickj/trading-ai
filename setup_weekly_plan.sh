#!/bin/bash

# Setup script for Weekly Plan feature
# This script creates the database table and populates initial data

echo "🗄️  Setting up Weekly Plan feature..."

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    exit 1
fi

# Run database migration
echo "📊 Creating weekly_plan_events table..."
export PGPASSWORD="trading_password"
if psql -h localhost -p 5432 -U trading_user -d trading_db -f migrations/004_create_weekly_plan_table.sql; then
    echo "✅ Database table created successfully"
else
    echo "❌ Failed to create database table"
    exit 1
fi

# Populate initial data
echo "📅 Populating weekly plan data (6 weeks ahead)..."
python3 -c "
from src.data.weekly_plan_populator import WeeklyPlanPopulator
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

try:
    populator = WeeklyPlanPopulator()
    results = populator.populate_advance_data()
    print(f'✅ Successfully populated weekly plan data: {results}')
    total = sum(results.values())
    print(f'📈 Total events created: {total}')
except Exception as e:
    print(f'❌ Error populating data: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Weekly Plan setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Restart your Flask application"
    echo "   2. Visit /weekly_plan to see the new feature"
    echo "   3. Set up a cron job to run data population weekly:"
    echo "      0 2 * * 1 cd $(pwd) && python3 -c 'from src.data.weekly_plan_populator import WeeklyPlanPopulator; WeeklyPlanPopulator().populate_advance_data()'"
    echo ""
    echo "🔧 API Endpoints available:"
    echo "   GET  /api/weekly_events?start_date=YYYY-MM-DD"
    echo "   GET  /api/weekly_plan/available_weeks"
    echo "   POST /api/weekly_plan/populate"
    echo ""
else
    echo "❌ Weekly Plan setup failed"
    exit 1
fi