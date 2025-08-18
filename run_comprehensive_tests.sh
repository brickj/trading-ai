#!/bin/bash

# Comprehensive Test Runner for Trading AI Application
# This script runs both backend and frontend tests

echo "🚀 TRADING AI COMPREHENSIVE TEST SUITE"
echo "============================================================"
echo "🕐 Started at: $(date)"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not detected"
    echo "💡 Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if application is running
echo "🔍 Checking if application is running..."
if curl -s http://localhost:5001/api/system_status > /dev/null 2>&1; then
    echo "✅ Application is running on port 5001"
else
    echo "❌ Application is not running on port 5001"
    echo "💡 Please start the application first: python3 start_app.py"
    exit 1
fi

echo ""
echo "🔧 Running Backend System Tests..."
echo "============================================================"
python3 tests/comprehensive_system_test.py
BACKEND_EXIT_CODE=$?

echo ""
echo "🌐 Running Frontend Page Tests..."
echo "============================================================"
python3 tests/comprehensive_frontend_test.py
FRONTEND_EXIT_CODE=$?

echo ""
echo "🔗 Running Integration Tests..."
echo "============================================================"
python3 tests/run_comprehensive_tests.py
INTEGRATION_EXIT_CODE=$?

echo ""
echo "📊 COMPREHENSIVE TEST REPORT"
echo "============================================================"

# Calculate results
TOTAL_TESTS=3
PASSED_TESTS=0

if [ $BACKEND_EXIT_CODE -eq 0 ]; then
    echo "🔧 Backend System Tests: ✅ PASSED"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "🔧 Backend System Tests: ❌ FAILED"
fi

if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
    echo "🌐 Frontend Page Tests: ✅ PASSED"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "🌐 Frontend Page Tests: ❌ FAILED"
fi

if [ $INTEGRATION_EXIT_CODE -eq 0 ]; then
    echo "🔗 Integration Tests: ✅ PASSED"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "🔗 Integration Tests: ❌ FAILED"
fi

SUCCESS_RATE=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)
echo "📈 Overall Success Rate: ${SUCCESS_RATE}% ($PASSED_TESTS/$TOTAL_TESTS)"

echo ""
if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo "🎉 ALL TESTS PASSED! Your Trading AI system is fully operational!"
elif [ $PASSED_TESTS -ge 2 ]; then
    echo "⚠️  MOST TESTS PASSED! Some issues need attention."
else
    echo "❌ MANY TESTS FAILED! System needs significant attention."
fi

echo ""
echo "📋 Test Coverage Summary:"
echo "   • Backend: Database, APIs, Services, Background Jobs"
echo "   • Frontend: All Pages, Data Display, User Interactions"
echo "   • Integration: End-to-End Workflows, Data Consistency"

echo ""
echo "🕐 Completed at: $(date)"
echo "============================================================"

# Exit with appropriate code
if [ $PASSED_TESTS -ge 2 ]; then
    echo "✅ Most tests passed - system is operational"
    exit 0
else
    echo "❌ Many tests failed - system needs attention"
    exit 1
fi
