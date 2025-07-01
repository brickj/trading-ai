#!/bin/bash
"""
Comprehensive Test Runner for Trading AI Application
===================================================

This script sets up the environment and runs the comprehensive Playwright test suite.
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Comprehensive Playwright Test Runner${NC}"
echo "=================================================================="

# Check if Flask app is running
echo -e "${BLUE}📡 Checking if Flask app is running...${NC}"
if curl -s http://localhost:5001 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Flask app is running${NC}"
else
    echo -e "${RED}❌ Flask app is not running on localhost:5001${NC}"
    echo -e "${YELLOW}Please start the app first with: python start_app.py${NC}"
    exit 1
fi

# Check if Python is available
echo -e "${BLUE}🐍 Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✅ Python3 found${NC}"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    echo -e "${GREEN}✅ Python found${NC}"
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Python not found${NC}"
    exit 1
fi

# Check if virtual environment is activated
echo -e "${BLUE}🌐 Checking virtual environment...${NC}"
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "${GREEN}✅ Virtual environment active: $VIRTUAL_ENV${NC}"
else
    echo -e "${YELLOW}⚠️  No virtual environment detected${NC}"
    echo -e "${YELLOW}Consider activating one with: source .venv/bin/activate${NC}"
fi

# Install Playwright if needed
echo -e "${BLUE}🎭 Checking Playwright installation...${NC}"
if $PYTHON_CMD -c "import playwright" 2>/dev/null; then
    echo -e "${GREEN}✅ Playwright is installed${NC}"
else
    echo -e "${YELLOW}📦 Installing Playwright...${NC}"
    $PYTHON_CMD -m pip install playwright pytest-playwright
    echo -e "${BLUE}🌐 Installing Playwright browsers...${NC}"
    $PYTHON_CMD -m playwright install chromium
fi

# Create necessary directories
echo -e "${BLUE}📁 Creating test directories...${NC}"
mkdir -p test-results/screenshots
mkdir -p test-results/videos
mkdir -p logs

# Run the comprehensive test
echo -e "${BLUE}🧪 Running comprehensive Playwright test suite...${NC}"
echo "=================================================================="
$PYTHON_CMD test_comprehensive_playwright.py

# Check test results
if [ $? -eq 0 ]; then
    echo -e "${GREEN}🎉 Test runner completed successfully!${NC}"
    echo -e "${BLUE}📊 Check the test-results/ directory for:${NC}"
    echo "   📄 JSON test reports"
    echo "   📸 Screenshots (if any errors detected)"
    echo "   🎥 Video recordings"
    echo "   📝 Log files"
else
    echo -e "${RED}❌ Test runner encountered issues${NC}"
    echo -e "${YELLOW}Check the logs/ directory for detailed error information${NC}"
fi

echo "=================================================================="
echo -e "${BLUE}Test runner finished at $(date)${NC}"
