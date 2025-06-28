#!/bin/bash
# Trading AI - Comprehensive Test Suite Runner
# This script runs all available tests and generates comprehensive reports

echo "🧪 TRADING AI - COMPREHENSIVE TEST SUITE"
echo "========================================"
echo "Starting test execution at: $(date)"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    print_warning "PostgreSQL is not running. Starting PostgreSQL..."
    if command -v brew &> /dev/null; then
        brew services start postgresql@14
    elif command -v systemctl &> /dev/null; then
        sudo systemctl start postgresql
    else
        print_error "Cannot start PostgreSQL automatically. Please start it manually."
        exit 1
    fi
    sleep 3
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/version &> /dev/null; then
    print_warning "Ollama is not running. Please start Ollama service:"
    print_warning "  ollama serve"
    print_warning "  ollama pull llama3.2"
    print_warning "Tests will continue but AI analysis will fail."
    sleep 2
fi

# Check if the trading app is running
print_status "Checking if Trading AI application is running..."
if ! curl -s http://localhost:5001/api/system_status > /dev/null; then
    print_error "Trading AI application is not running."
    print_error "Please start the application first:"
    print_error "  python3 start_app.py"
    print_error ""
    print_error "Or run this script to start it automatically:"
    read -p "Would you like to start the application now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Starting Trading AI application..."
        python3 start_app.py &
        APP_PID=$!
        sleep 10
        if ! curl -s http://localhost:5001/api/system_status > /dev/null; then
            print_error "Failed to start the application"
            kill $APP_PID 2>/dev/null
            exit 1
        fi
        print_success "Application started successfully"
    else
        exit 1
    fi
fi

print_success "All prerequisites checked"
echo ""

# Create test results directory
mkdir -p test_results
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_DIR="test_results/run_${TIMESTAMP}"
mkdir -p "$RESULTS_DIR"

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"
    local test_file="$3"
    
    print_status "Running $test_name..."
    echo "Command: $test_command" >> "$RESULTS_DIR/test_log.txt"
    echo "Started at: $(date)" >> "$RESULTS_DIR/test_log.txt"
    
    if eval "$test_command" > "$RESULTS_DIR/${test_file}.log" 2>&1; then
        print_success "$test_name completed successfully"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo "PASSED" >> "$RESULTS_DIR/test_log.txt"
    else
        print_error "$test_name failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "FAILED" >> "$RESULTS_DIR/test_log.txt"
    fi
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo "Completed at: $(date)" >> "$RESULTS_DIR/test_log.txt"
    echo "---" >> "$RESULTS_DIR/test_log.txt"
    echo ""
}

# Run all test suites
echo "🔬 EXECUTING TEST SUITES"
echo "========================"

# 1. Comprehensive System Test
run_test "Comprehensive System Test" \
         "python3 tests/comprehensive_system_test.py" \
         "comprehensive_system_test"

# 2. Web Page Data Population Test
run_test "Web Page Data Population Test" \
         "python3 tests/web_page_data_test.py" \
         "web_page_data_test"

# 3. Integration Tests
if [ -f "tests/run_integration_tests.py" ]; then
    run_test "Integration Tests" \
             "python3 tests/run_integration_tests.py" \
             "integration_tests"
fi

# 4. Unit Tests
if [ -f "tests/run_tests.py" ]; then
    run_test "Unit Tests" \
             "python3 tests/run_tests.py" \
             "unit_tests"
fi

# 5. Telegram Test (if available)
if [ -f "tests/telegram_test.py" ]; then
    run_test "Telegram Integration Test" \
             "python3 tests/telegram_test.py" \
             "telegram_test"
fi

# 6. API Endpoint Tests
print_status "Running API Endpoint Tests..."
echo "API Endpoint Tests" >> "$RESULTS_DIR/test_log.txt"
echo "Started at: $(date)" >> "$RESULTS_DIR/test_log.txt"

# Test key API endpoints
API_TESTS=(
    "system_status|GET|/api/system_status"
    "analyze_stock|POST|/api/analyze_stock|{\"symbol\":\"AAPL\",\"ai_provider\":\"demo\"}"
    "sp500_analysis|GET|/api/sp500_analysis"
    "crypto_analysis|GET|/api/crypto_analysis"
    "portfolio|GET|/api/portfolio"
    "recommendations|GET|/api/recommendations"
)

api_passed=0
api_total=0

for test in "${API_TESTS[@]}"; do
    IFS='|' read -r name method endpoint data <<< "$test"
    api_total=$((api_total + 1))
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$data" "http://localhost:5001$endpoint")
    else
        response=$(curl -s -w "%{http_code}" -X "$method" "http://localhost:5001$endpoint")
    fi
    
    http_code="${response: -3}"
    if [ "$http_code" = "200" ]; then
        print_success "API Test: $name"
        api_passed=$((api_passed + 1))
        echo "$name: PASSED (HTTP $http_code)" >> "$RESULTS_DIR/api_test.log"
    else
        print_error "API Test: $name (HTTP $http_code)"
        echo "$name: FAILED (HTTP $http_code)" >> "$RESULTS_DIR/api_test.log"
    fi
done

if [ $api_passed -eq $api_total ]; then
    print_success "API Endpoint Tests completed successfully"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo "PASSED" >> "$RESULTS_DIR/test_log.txt"
else
    print_error "API Endpoint Tests failed ($api_passed/$api_total passed)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo "FAILED" >> "$RESULTS_DIR/test_log.txt"
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo "Completed at: $(date)" >> "$RESULTS_DIR/test_log.txt"
echo "---" >> "$RESULTS_DIR/test_log.txt"
echo ""

# Generate summary report
echo "📊 TEST EXECUTION SUMMARY"
echo "========================="
echo "Total Tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
echo ""

# Create summary file
cat > "$RESULTS_DIR/summary.txt" << EOF
Trading AI Test Execution Summary
=================================
Execution Date: $(date)
Test Results Directory: $RESULTS_DIR

Test Results:
- Total Tests: $TOTAL_TESTS
- Passed: $PASSED_TESTS
- Failed: $FAILED_TESTS
- Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%

Individual Test Logs:
- Comprehensive System Test: comprehensive_system_test.log
- Web Page Data Test: web_page_data_test.log
- Integration Tests: integration_tests.log
- Unit Tests: unit_tests.log
- API Endpoint Tests: api_test.log
- Detailed Log: test_log.txt

JSON Reports (if available):
- test_results.json
- test_report_web_pages_*.json
EOF

# Copy JSON reports if they exist
if [ -f "test_results.json" ]; then
    cp test_results.json "$RESULTS_DIR/"
fi

for json_file in test_report_web_pages_*.json; do
    if [ -f "$json_file" ]; then
        cp "$json_file" "$RESULTS_DIR/"
    fi
done

print_status "Test results saved to: $RESULTS_DIR"
print_status "Summary: $RESULTS_DIR/summary.txt"

# Final status
if [ $FAILED_TESTS -eq 0 ]; then
    print_success "🎉 ALL TESTS PASSED!"
    exit 0
else
    print_error "⚠️  $FAILED_TESTS TESTS FAILED"
    print_error "Check logs in $RESULTS_DIR for details"
    exit 1
fi 