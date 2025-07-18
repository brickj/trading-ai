#!/bin/bash
# Comprehensive Page Population Test Runner
# Tests that every page is fully populated with real data

echo "🧪 COMPREHENSIVE PAGE POPULATION TEST"
echo "====================================="
echo "This test validates that every page is fully populated with real data"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Virtual environment not activated. Please activate it first:"
    echo "   source .venv/bin/activate"
    exit 1
fi

echo "✅ Virtual environment detected: $VIRTUAL_ENV"

# Check if Playwright is installed
if ! command -v playwright &> /dev/null; then
    echo "🔧 Playwright not found. Setting up Playwright..."
    ./setup_playwright_test.sh
    if [ $? -ne 0 ]; then
        echo "❌ Failed to setup Playwright"
        exit 1
    fi
fi

# Check if application is running
echo "🔍 Checking if application is running..."
if curl -s http://localhost:5001 > /dev/null; then
    echo "✅ Application is running on http://localhost:5001"
else
    echo "❌ Application is not running"
    echo "Please start the application first:"
    echo "   python start_app.py"
    echo ""
    echo "Or in a separate terminal:"
    echo "   ./startup.sh"
    exit 1
fi

# Create test artifacts directory
mkdir -p test_artifacts

# Run the comprehensive test
echo ""
echo "🚀 Starting comprehensive page population test..."
echo "This will test all pages and generate:"
echo "  - Screenshots of each populated page"
echo "  - Video recording of the entire test"
echo "  - Detailed test report (JSON and TXT)"
echo "  - Test log with diagnostic information"
echo ""

python tests/playwright_comprehensive_test.py

# Check test result
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Comprehensive test completed successfully!"
    echo ""
    echo "📁 Test artifacts generated:"
    echo "  - test_artifacts/ (screenshots and video)"
    echo "  - test_log.txt (detailed test log)"
    echo "  - test_report_*.json (JSON test report)"
    echo "  - test_report_*.txt (text test report)"
    echo ""
    echo "📊 Check the test reports to see which pages passed/failed"
else
    echo ""
    echo "❌ Comprehensive test failed"
    echo "Check test_log.txt for detailed error information"
    exit 1
fi 