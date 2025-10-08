#!/bin/bash

# Stop all Trading AI services (Python Flask + Go microservices)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🛑 Stopping All Trading AI Services${NC}"
echo "=================================================="

# Stop Flask application
echo -e "${BLUE}🐍 Stopping Flask application...${NC}"
if [ -f pids/flask_app.pid ]; then
    PID=$(cat pids/flask_app.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "Stopping Flask application (PID: $PID)..."
        kill $PID
        rm pids/flask_app.pid
        echo -e "${GREEN}✅ Flask application stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  Flask application was not running${NC}"
        rm pids/flask_app.pid
    fi
else
    echo -e "${YELLOW}⚠️  Flask application PID file not found${NC}"
fi

# Stop Go services
echo -e "${BLUE}🚀 Stopping Go microservices...${NC}"
cd go
./scripts/stop_services.sh
cd ..

# Clean up any remaining processes
echo -e "${BLUE}🧹 Cleaning up remaining processes...${NC}"

# Kill any remaining Python processes
pkill -f "start_app.py" 2>/dev/null || true
pkill -f "flask" 2>/dev/null || true

# Kill any remaining Go processes
pkill -f "data_fetcher" 2>/dev/null || true
pkill -f "cache_service" 2>/dev/null || true
pkill -f "background_workers" 2>/dev/null || true

echo -e "${GREEN}🎉 All services stopped successfully!${NC}"
echo "=================================================="
