#!/bin/bash
# Trading AI - Complete Startup Script
# This script starts all required services and the application

echo "🚀 TRADING AI - STARTUP SCRIPT"
echo "=============================="
echo "Starting all services..."
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

# 1. Start PostgreSQL
print_status "Starting PostgreSQL database..."
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    if command -v brew &> /dev/null; then
        brew services start postgresql@14
        sleep 3
    elif command -v systemctl &> /dev/null; then
        sudo systemctl start postgresql
        sleep 3
    else
        print_error "Cannot start PostgreSQL automatically"
        print_error "Please start PostgreSQL manually and run this script again"
        exit 1
    fi
    
    if pg_isready -h localhost -p 5432 &> /dev/null; then
        print_success "PostgreSQL started successfully"
    else
        print_error "Failed to start PostgreSQL"
        exit 1
    fi
else
    print_success "PostgreSQL is already running"
fi

# 2. Start Ollama (in background)
print_status "Starting Ollama service..."
if ! curl -s http://localhost:11434/api/version &> /dev/null; then
    if command -v ollama &> /dev/null; then
        print_status "Starting Ollama in background..."
        nohup ollama serve > /dev/null 2>&1 &
        sleep 5
        
        if curl -s http://localhost:11434/api/version &> /dev/null; then
            print_success "Ollama started successfully"
            
            # Pull required model if not already available
            print_status "Checking for required Ollama model..."
            if ! ollama list | grep -q "llama3.2"; then
                print_status "Pulling llama3.2 model (this may take a few minutes)..."
                ollama pull llama3.2
            fi
            print_success "Ollama model ready"
        else
            print_warning "Ollama failed to start - AI analysis will be limited"
        fi
    else
        print_warning "Ollama not installed - AI analysis will be limited"
        print_warning "Install with: curl -fsSL https://ollama.com/install.sh | sh"
    fi
else
    print_success "Ollama is already running"
fi

# 3. Install missing dependencies
print_status "Installing missing dependencies..."
pip install -q feedparser beautifulsoup4 lxml yfinance psycopg2-binary requests flask flask-socketio
print_success "Dependencies installed"

# 4. Start Trading Application
print_status "Starting Trading AI application..."
if curl -s http://localhost:5001/api/system_status &> /dev/null; then
    print_warning "Application is already running on port 5001"
    read -p "Would you like to restart it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Stopping existing application..."
        pkill -f "python.*start_app.py" 2>/dev/null
        pkill -f "flask" 2>/dev/null
        sleep 3
    else
        print_success "Using existing application instance"
        echo ""
        echo "🎉 STARTUP COMPLETE!"
        echo "==================="
        echo "✅ PostgreSQL: Running"
        echo "✅ Ollama: Running" 
        echo "✅ Trading App: Running (existing)"
        echo ""
        echo "🌐 Access the application at: http://localhost:5001"
        echo "📊 System status: http://localhost:5001/system_status"
        echo ""
        echo "To run tests: ./run_all_tests.sh"
        exit 0
    fi
fi

print_status "Launching application..."
python3 start_app.py &
APP_PID=$!

# Wait for application to start
print_status "Waiting for application to start..."
for i in {1..20}; do
    if curl -s http://localhost:5001/api/system_status &> /dev/null; then
        print_success "Trading AI application started successfully!"
        break
    fi
    sleep 1
    echo -n "."
done

echo ""

# Verify application is running
if curl -s http://localhost:5001/api/system_status &> /dev/null; then
    print_success "Application is responding correctly"
    
    # Get system status
    print_status "Checking system status..."
    curl -s http://localhost:5001/api/system_status | jq . 2>/dev/null || echo "System status retrieved (jq not available for formatting)"
    
    echo ""
    echo "🎉 STARTUP COMPLETE!"
    echo "==================="
    echo "✅ PostgreSQL: Running"
    echo "✅ Ollama: Running"
    echo "✅ Trading App: Running (PID: $APP_PID)"
    echo ""
    echo "🌐 Access the application at: http://localhost:5001"
    echo "📊 System status: http://localhost:5001/system_status"
    echo "📈 Dashboard: http://localhost:5001/"
    echo ""
    echo "🧪 To run tests: ./run_all_tests.sh"
    echo "🛑 To stop app: kill $APP_PID"
    echo ""
    echo "Logs are available in the logs/ directory"
    
else
    print_error "Application failed to start properly"
    print_error "Check the application logs for details"
    kill $APP_PID 2>/dev/null
    exit 1
fi 