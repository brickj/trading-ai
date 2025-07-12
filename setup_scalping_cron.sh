#!/bin/bash

# Setup Scalping Analysis Cron Job
# This script sets up a cron job to run scalping analysis each morning at 9:35 AM ET

echo "Setting up scalping analysis cron job..."

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/run_scalping_analysis.py"

# Check if the Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: run_scalping_analysis.py not found at $PYTHON_SCRIPT"
    exit 1
fi

# Make the Python script executable
chmod +x "$PYTHON_SCRIPT"

# Create the cron job entry (runs at 9:35 AM ET every weekday)
CRON_JOB="35 9 * * 1-5 cd $SCRIPT_DIR && python3 $PYTHON_SCRIPT >> logs/scalping_cron.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "run_scalping_analysis.py"; then
    echo "Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "run_scalping_analysis.py" | crontab -
fi

# Add the new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "Cron job added successfully!"
echo "Schedule: Every weekday (Monday-Friday) at 9:35 AM ET"
echo "Command: $CRON_JOB"
echo ""
echo "To view current cron jobs: crontab -l"
echo "To edit cron jobs: crontab -e"
echo "To remove all cron jobs: crontab -r"
echo ""
echo "Logs will be written to: logs/scalping_cron.log"
echo "Analysis logs will be written to: logs/scalping_analysis.log"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

echo ""
echo "Setup complete! The scalping analysis will run automatically each morning." 