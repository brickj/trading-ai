#!/bin/bash
# Setup script for Playwright comprehensive test

echo "🔧 Setting up Playwright for comprehensive page testing..."
echo "=================================================="

# Check if Python virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Virtual environment not activated. Please activate it first:"
    echo "   source .venv/bin/activate"
    exit 1
fi

echo "✅ Virtual environment detected: $VIRTUAL_ENV"

# Install Playwright dependencies
echo "📦 Installing Playwright dependencies..."
pip install -r requirements_playwright.txt

if [ $? -eq 0 ]; then
    echo "✅ Playwright dependencies installed successfully"
else
    echo "❌ Failed to install Playwright dependencies"
    exit 1
fi

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

if [ $? -eq 0 ]; then
    echo "✅ Playwright browsers installed successfully"
else
    echo "❌ Failed to install Playwright browsers"
    exit 1
fi

# Create test artifacts directory
echo "📁 Creating test artifacts directory..."
mkdir -p test_artifacts

if [ $? -eq 0 ]; then
    echo "✅ Test artifacts directory created"
else
    echo "❌ Failed to create test artifacts directory"
    exit 1
fi

echo ""
echo "🎉 Playwright setup complete!"
echo "=================================================="
echo "You can now run the comprehensive test:"
echo "   python tests/playwright_comprehensive_test.py"
echo ""
echo "Make sure the application is running first:"
echo "   python start_app.py" 