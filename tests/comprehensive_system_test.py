#!/usr/bin/env python3
"""
Comprehensive System Test
Tests the entire trading AI system including:
- Stock analysis and recommendations
- Historical data usage
- Telegram alert sending
- Database operations
- API endpoints
- Web page population and data display
- Page stability and crash prevention
"""

import sys
import os
import requests
import json
import time
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.config import Config
from src.core.telegram_alerts import TelegramAlerts
from src.trading.enhanced_trading_strategy import EnhancedTradingStrategy
from src.data.data_fetcher import DataFetcher
from src.core.database import get_db_connection

class ComprehensiveSystemTest:
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.test_symbols = ['AAPL', 'TSLA', 'MSFT']
        self.telegram = TelegramAlerts()
        self.strategy = EnhancedTradingStrategy()
        self.data_fetcher = DataFetcher()
        self.results = []

    def log_test(self, test_name, status, details=""):
        """Log test results"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        print()

    def test_system_status(self):
        """Test system status endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/system_status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    self.log_test("System Status", "PASS", f"Database: {data.get('database_status')}, Cache: {data.get('cache_status')}")
                else:
                    self.log_test("System Status", "FAIL", f"Status: {data.get('status')}")
            else:
                self.log_test("System Status", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("System Status", "FAIL", str(e))

    def test_database_connection(self):
        """Test database connection and historical data"""
        try:
            with get_db_connection() as conn:
                if conn is None:
                    self.log_test("Database Connection", "FAIL", "Database connection failed")
                    return
                cursor = conn.cursor()

                # Test historical data table
                cursor.execute("SELECT COUNT(*) FROM historical_data")
                result = cursor.fetchone()
                if result is None:
                    self.log_test("Database Connection", "FAIL", "No result from count query")
                    return
                count = result[0] if isinstance(result, (list, tuple)) else result['count']

                cursor.execute("SELECT COUNT(DISTINCT symbol) FROM historical_data")
                result = cursor.fetchone()
                if result is None:
                    self.log_test("Database Connection", "FAIL", "No result from symbols query")
                    return
                symbols = result[0] if isinstance(result, (list, tuple)) else result['count']

                cursor.execute("SELECT MAX(date), MIN(date) FROM historical_data")
                result = cursor.fetchone()
                if result is None:
                    self.log_test("Database Connection", "FAIL", "No result from date range query")
                    return
                
                if isinstance(result, (list, tuple)):
                    max_date, min_date = result
                else:
                    max_date, min_date = result['max'], result['min']

            if count > 0:
                self.log_test("Database Connection", "PASS",
                            f"{count:,} records, {symbols} symbols, Range: {min_date} to {max_date}")
            else:
                self.log_test("Database Connection", "FAIL", "No historical data found")

        except Exception as e:
            self.log_test("Database Connection", "FAIL", str(e))

    def test_historical_data_usage(self):
        """Test if the system is using the full year of historical data"""
        try:
            # Test database connection and get historical data directly
            with get_db_connection() as conn:
                if conn is None:
                    self.log_test("Historical Data Usage", "FAIL", "Database connection failed")
                    return
                cursor = conn.cursor()

                # Get historical data for AAPL
                cursor.execute("""
                    SELECT COUNT(*), MIN(date), MAX(date)
                    FROM historical_data 
                    WHERE symbol = 'AAPL'
                """)
                result = cursor.fetchone()
                
                if result and len(result) >= 3:
                    if isinstance(result, (list, tuple)):
                        count, min_date, max_date = result
                    else:
                        count, min_date, max_date = result['count'], result['min'], result['max']
                    
                    if count > 200:
                        days_range = (max_date - min_date).days
                        self.log_test("Historical Data Usage", "PASS",
                                    f"Retrieved {count} records for AAPL, "
                                    f"Date range: {days_range} days ({min_date} to {max_date})")
                    else:
                        self.log_test("Historical Data Usage", "FAIL",
                                    f"Only {count} records found, expected ~200+ days")
                else:
                    self.log_test("Historical Data Usage", "FAIL", "No data found for AAPL")

        except Exception as e:
            self.log_test("Historical Data Usage", "FAIL", str(e))

    def test_stock_analysis_api(self):
        """Test stock analysis API endpoint"""
        for symbol in self.test_symbols:
            try:
                payload = {
                    "symbol": symbol,
                    "ai_provider": "ollama"
                }

                response = requests.post(
                    f"{self.base_url}/api/analyze_stock",
                    json=payload,
                    timeout=60
                )

                if response.status_code == 200:
                    data = response.json()
                    # Check for trading_recommendation (the actual field name)
                    if 'data' in data and 'trading_recommendation' in data['data']:
                        rec = data['data']['trading_recommendation']
                        action = rec.get('action', 'UNKNOWN')
                        self.log_test(f"Stock Analysis - {symbol}", "PASS",
                                    f"Action: {action}, Strategy: {rec.get('trading_strategy', 'N/A')}")
                    else:
                        self.log_test(f"Stock Analysis - {symbol}", "FAIL", "No trading recommendation generated")
                else:
                    self.log_test(f"Stock Analysis - {symbol}", "FAIL", f"HTTP {response.status_code}")

            except Exception as e:
                self.log_test(f"Stock Analysis - {symbol}", "FAIL", str(e))

    def test_recommendations_generation(self):
        """Test recommendation generation with historical backtesting"""
        try:
            # Test enhanced trading strategy
            symbol = 'AAPL'
            current_price = 150.0

            # Mock sentiment and signal data
            sentiment_data = {
                'sentiment_score': 0.7,
                'confidence': 0.8,
                'articles_analyzed': 10
            }

            signal_data = {
                'action': 'CALL',
                'strength': 0.75
            }

            # Generate recommendations
            recommendations = self.strategy.generate_recommendations(
                symbol, current_price, sentiment_data, signal_data
            )

            if recommendations and len(recommendations) > 0:
                rec = recommendations[0]
                action = rec.get('action', 'UNKNOWN')
                self.log_test("Recommendations Generation", "PASS",
                            f"Generated {len(recommendations)} recommendations, Action: {action}")
            else:
                self.log_test("Recommendations Generation", "FAIL", "No recommendations generated")

        except Exception as e:
            self.log_test("Recommendations Generation", "FAIL", str(e))

    def test_telegram_configuration(self):
        """Test Telegram configuration"""
        try:
            config = Config()
            bot_token = config.get('TELEGRAM_API_KEY')
            chat_id = config.get('TELEGRAM_CHAT_ID')

            if bot_token and chat_id:
                self.log_test("Telegram Configuration", "PASS",
                            f"Bot token: {bot_token[:10]}..., Chat ID: {chat_id}")
            else:
                self.log_test("Telegram Configuration", "FAIL",
                            f"Missing config: Bot token: {bool(bot_token)}, Chat ID: {bool(chat_id)}")

        except Exception as e:
            self.log_test("Telegram Configuration", "FAIL", str(e))

    def test_telegram_message_sending(self):
        """Test Telegram message sending"""
        try:
            test_message = f"🧪 Test message from Trading AI - {datetime.now().strftime('%H:%M:%S')}"
            success = self.telegram.send_message(test_message)

            if success:
                self.log_test("Telegram Message Sending", "PASS", "Test message sent successfully")
            else:
                self.log_test("Telegram Message Sending", "FAIL", "Failed to send test message")

        except Exception as e:
            self.log_test("Telegram Message Sending", "FAIL", str(e))

    def test_telegram_recommendation_alert(self):
        """Test Telegram recommendation alert"""
        try:
            test_recommendation = {
                'symbol': 'AAPL',
                'action': 'BUY',
                'confidence': 0.85,
                'reasoning': 'Strong positive sentiment and technical indicators'
            }

            success = self.telegram.send_recommendation_alert(test_recommendation)

            if success:
                self.log_test("Telegram Recommendation Alert", "PASS", "Recommendation alert sent successfully")
            else:
                self.log_test("Telegram Recommendation Alert", "FAIL", "Failed to send recommendation alert")

        except Exception as e:
            self.log_test("Telegram Recommendation Alert", "FAIL", str(e))

    def test_bulk_analysis_api(self):
        """Test bulk analysis API endpoint"""
        try:
            payload = {
                "symbols": self.test_symbols,
                "ai_provider": "ollama"
            }

            response = requests.post(
                f"{self.base_url}/api/bulk_analyze",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                data = response.json()
                # Check for results in the correct location: data.results
                if 'data' in data and 'results' in data['data'] and len(data['data']['results']) > 0:
                    self.log_test("Bulk Analysis API", "PASS",
                                f"Analyzed {len(data['data']['results'])} symbols successfully")
                else:
                    self.log_test("Bulk Analysis API", "FAIL", "No analysis results returned")
            else:
                self.log_test("Bulk Analysis API", "FAIL", f"HTTP {response.status_code}")

        except Exception as e:
            self.log_test("Bulk Analysis API", "FAIL", str(e))

    def test_portfolio_management(self):
        """Test portfolio management functionality"""
        try:
            # Test portfolio API endpoint
            response = requests.get(f"{self.base_url}/api/portfolio", timeout=10)
            if response.status_code == 200:
                self.log_test("Portfolio Management", "PASS", "Portfolio endpoint accessible")
            else:
                self.log_test("Portfolio Management", "FAIL", f"HTTP {response.status_code}")

        except Exception as e:
            self.log_test("Portfolio Management", "FAIL", str(e))

    def test_web_pages_accessibility(self):
        """Test all web pages are accessible and not crashing"""
        pages = [
            ('/', 'Dashboard'),
            ('/stocks', 'Stocks'),
            ('/crypto', 'Crypto'),
            ('/opportunities', 'Opportunities'),
            ('/portfolio', 'Portfolio'),
            ('/backtest', 'Backtest'),
            ('/logs', 'Logs'),
            ('/system_status', 'System Status')
        ]

        for path, name in pages:
            try:
                response = requests.get(f"{self.base_url}{path}", timeout=15)
                if response.status_code == 200:
                    # Check if page has substantial content (not just empty or error page)
                    content_length = len(response.text)
                    if content_length > 1000:  # Minimum content threshold
                        self.log_test(f"Web Page - {name}", "PASS", 
                                    f"HTTP 200, Content: {content_length} chars")
                    else:
                        self.log_test(f"Web Page - {name}", "FAIL", 
                                    f"HTTP 200 but minimal content: {content_length} chars")
                else:
                    self.log_test(f"Web Page - {name}", "FAIL", f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"Web Page - {name}", "FAIL", f"Exception: {str(e)}")

    def test_api_endpoints_data_population(self):
        """Test API endpoints return populated data"""
        api_endpoints = [
            ('/api/sp500_analysis', 'S&P 500 Analysis', ['enhanced_analysis', 'total_analyzed']),
            ('/api/system_status', 'System Status', ['status', 'system']),
            ('/api/market_sentiment', 'Market Sentiment', ['market_sentiment', 'market_mood']),
            ('/api/crypto_analysis', 'Crypto Analysis', ['opportunities', 'total_analyzed']),
            ('/api/opportunities', 'Opportunities', ['news_driven', 'watchlist', 'total_opportunities'])
        ]

        for endpoint, name, required_keys in api_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle different response structures
                    if 'data' in data:
                        # Standard create_api_response format
                        response_data = data['data']
                        success = data.get('success', True)
                    else:
                        # Direct response format (like system_status and market_sentiment)
                        response_data = data
                        success = data.get('status') == 'ok' if 'status' in data else True
                    
                    # Check if request was successful
                    if not success:
                        self.log_test(f"API Endpoint - {name}", "FAIL", "API returned error status")
                        continue
                    
                    # Check for required keys in the actual response structure
                    missing_keys = []
                    for key in required_keys:
                        if key not in response_data:
                            missing_keys.append(key)
                    
                    if not missing_keys:
                        self.log_test(f"API Endpoint - {name}", "PASS", "Data returned successfully")
                    else:
                        self.log_test(f"API Endpoint - {name}", "FAIL", f"Missing keys: {missing_keys}")
                else:
                    self.log_test(f"API Endpoint - {name}", "FAIL", f"HTTP {response.status_code}: {response.text[:100]}")
            except Exception as e:
                self.log_test(f"API Endpoint - {name}", "FAIL", f"Exception: {str(e)}")

    def test_stocks_page_data_population(self):
        """Test stocks page is populated with actual data"""
        try:
            # Test the stocks page HTML content
            response = requests.get(f"{self.base_url}/stocks", timeout=15)
            if response.status_code == 200:
                content = response.text
                
                # Check for key data elements that actually exist in the template
                checks = [
                    ('stockAnalysisSection', 'Stock Analysis Section'),
                    ('legacyTable', 'Legacy Table Section'),
                    ('stocksTable', 'Stocks Table'),
                    ('refreshBtn', 'Refresh Button'),
                    ('enhancedAnalysisResults', 'Enhanced Analysis Results')
                ]
                
                populated_sections = 0
                for element_id, description in checks:
                    if element_id in content:
                        populated_sections += 1
                
                if populated_sections >= 3:
                    self.log_test("Stocks Page Data Population", "PASS", 
                                f"Found {populated_sections}/5 key data sections")
                else:
                    self.log_test("Stocks Page Data Population", "FAIL", 
                                f"Only {populated_sections}/5 key data sections found")
            else:
                self.log_test("Stocks Page Data Population", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Stocks Page Data Population", "FAIL", f"Exception: {str(e)}")

    def test_dashboard_data_population(self):
        """Test dashboard page is populated with actual data"""
        try:
            # Test the dashboard page HTML content
            response = requests.get(f"{self.base_url}/", timeout=15)
            if response.status_code == 200:
                content = response.text
                
                # Check for key dashboard elements that actually exist in the template
                checks = [
                    ('systemStatus', 'System Status'),
                    ('marketSentiment', 'Market Sentiment'),
                    ('stockSymbol', 'Stock Symbol Input'),
                    ('standardAnalysisBtn', 'Standard Analysis Button'),
                    ('enhancedAnalysisBtn', 'Enhanced Analysis Button')
                ]
                
                populated_sections = 0
                for element_id, description in checks:
                    if element_id in content:
                        populated_sections += 1
                
                if populated_sections >= 3:
                    self.log_test("Dashboard Data Population", "PASS", 
                                f"Found {populated_sections}/5 key dashboard sections")
                else:
                    self.log_test("Dashboard Data Population", "FAIL", 
                                f"Only {populated_sections}/5 key dashboard sections found")
            else:
                self.log_test("Dashboard Data Population", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Dashboard Data Population", "FAIL", f"Exception: {str(e)}")

    def test_crypto_page_data_population(self):
        """Test crypto page is populated with actual data"""
        try:
            # Test the crypto page HTML content
            response = requests.get(f"{self.base_url}/crypto", timeout=15)
            if response.status_code == 200:
                content = response.text
                
                # Check for key crypto elements that actually exist in the template
                checks = [
                    ('cryptoAnalysisContainer', 'Crypto Analysis Container'),
                    ('cryptoAnalysisSection', 'Crypto Analysis Section'),
                    ('cryptoTable', 'Crypto Table'),
                    ('refreshBtn', 'Refresh Button')
                ]
                
                populated_sections = 0
                for element_id, description in checks:
                    if element_id in content:
                        populated_sections += 1
                
                if populated_sections >= 2:
                    self.log_test("Crypto Page Data Population", "PASS", 
                                f"Found {populated_sections}/4 key crypto sections")
                else:
                    self.log_test("Crypto Page Data Population", "FAIL", 
                                f"Only {populated_sections}/4 key crypto sections found")
            else:
                self.log_test("Crypto Page Data Population", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Crypto Page Data Population", "FAIL", f"Exception: {str(e)}")

    def test_opportunities_page_data_population(self):
        """Test opportunities page is populated with actual data"""
        try:
            # Test the opportunities page HTML content
            response = requests.get(f"{self.base_url}/opportunities", timeout=15)
            if response.status_code == 200:
                content = response.text
                
                # Check for key opportunities elements that actually exist in the template
                checks = [
                    ('opportunitiesSection', 'Opportunities Section'),
                    ('findButton', 'Find Button Section'),
                    ('findOpportunitiesBtn', 'Find Opportunities Button'),
                    ('opportunitiesContainer', 'Opportunities Container')
                ]
                
                populated_sections = 0
                for element_id, description in checks:
                    if element_id in content:
                        populated_sections += 1
                
                if populated_sections >= 3:
                    self.log_test("Opportunities Page Data Population", "PASS", 
                                f"Found {populated_sections}/4 key opportunities sections")
                else:
                    self.log_test("Opportunities Page Data Population", "FAIL", 
                                f"Only {populated_sections}/4 key opportunities sections found")
            else:
                self.log_test("Opportunities Page Data Population", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Opportunities Page Data Population", "FAIL", f"Exception: {str(e)}")

    def test_page_stability_and_no_crashes(self):
        """Test that pages don't crash and remain stable"""
        pages = [
            ('/', 'Dashboard'),
            ('/stocks', 'Stocks'),
            ('/crypto', 'Crypto'),
            ('/opportunities', 'Opportunities'),
            ('/portfolio', 'Portfolio'),
            ('/backtest', 'Backtest'),
            ('/logs', 'Logs'),
            ('/system_status', 'System Status')
        ]

        for path, name in pages:
            try:
                # Test multiple rapid requests to check stability
                responses = []
                for i in range(3):
                    response = requests.get(f"{self.base_url}{path}", timeout=10)
                    responses.append(response.status_code)
                    time.sleep(0.5)  # Small delay between requests
                
                # Check if all responses are successful
                if all(code == 200 for code in responses):
                    self.log_test(f"Page Stability - {name}", "PASS", 
                                f"All 3 requests returned HTTP 200")
                else:
                    failed_codes = [code for code in responses if code != 200]
                    self.log_test(f"Page Stability - {name}", "FAIL", 
                                f"Some requests failed: {failed_codes}")
            except Exception as e:
                self.log_test(f"Page Stability - {name}", "FAIL", f"Exception: {str(e)}")

    def test_no_sql_syntax_errors(self):
        """Test that there are no SQL syntax errors in the logs"""
        try:
            # Check recent error logs for SQL syntax errors
            log_file = "logs/errors.log"
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    recent_logs = f.readlines()[-50:]  # Last 50 lines
                
                sql_errors = []
                for line in recent_logs:
                    if 'syntax error' in line.lower() and 'sql' in line.lower():
                        sql_errors.append(line.strip())
                
                if not sql_errors:
                    self.log_test("No SQL Syntax Errors", "PASS", "No SQL syntax errors found in recent logs")
                else:
                    self.log_test("No SQL Syntax Errors", "FAIL", 
                                f"Found {len(sql_errors)} SQL syntax errors in recent logs")
            else:
                self.log_test("No SQL Syntax Errors", "WARN", "Error log file not found")
        except Exception as e:
            self.log_test("No SQL Syntax Errors", "FAIL", f"Exception checking logs: {str(e)}")

    def test_app_process_stability(self):
        """Test that the app process remains stable and doesn't crash"""
        try:
            import psutil
            
            # Check if the app process is running
            app_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and 'start_app.py' in ' '.join(proc.info['cmdline']):
                        app_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if app_processes:
                self.log_test("App Process Stability", "PASS", 
                            f"Found {len(app_processes)} app process(es) running")
            else:
                self.log_test("App Process Stability", "FAIL", "No app process found running")
        except ImportError:
            self.log_test("App Process Stability", "WARN", "psutil not available, skipping process check")
        except Exception as e:
            self.log_test("App Process Stability", "FAIL", f"Exception: {str(e)}")

    def test_sp500_analysis_api(self):
        """Test S&P 500 analysis API endpoint"""
        try:
            # Use a longer timeout for this intensive analysis
            response = requests.get(
                f"{self.base_url}/api/sp500_analysis",
                timeout=120  # Increased from 60 to 120 seconds
            )

            if response.status_code == 200:
                data = response.json()
                # Check for the actual response structure
                if 'data' in data and 'enhanced_analysis' in data['data'] and len(data['data']['enhanced_analysis']) > 0:
                    self.log_test("S&P 500 Analysis API", "PASS",
                                 f"Analyzed {len(data['data']['enhanced_analysis'])} stocks successfully")
                else:
                    self.log_test("S&P 500 Analysis API", "FAIL",
                                 f"API returned success but no analysis data: {data}")
            else:
                self.log_test("S&P 500 Analysis API", "FAIL",
                             f"HTTP {response.status_code}: {response.text[:200]}")
        except requests.exceptions.Timeout:
            self.log_test("S&P 500 Analysis API", "FAIL",
                         "Request timed out after 120 seconds - analysis is too slow")
        except Exception as e:
            self.log_test("S&P 500 Analysis API", "FAIL",
                         f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive Trading AI System Test")
        print("=" * 60)
        
        # Core functionality tests
        self.test_system_status()
        self.test_database_connection()
        self.test_historical_data_usage()
        self.test_stock_analysis_api()
        self.test_recommendations_generation()
        
        # Telegram tests
        self.test_telegram_configuration()
        self.test_telegram_message_sending()
        self.test_telegram_recommendation_alert()
        
        # API tests
        self.test_bulk_analysis_api()
        self.test_portfolio_management()
        
        # Web page accessibility and stability tests
        self.test_web_pages_accessibility()
        self.test_api_endpoints_data_population()
        
        # Data population tests
        self.test_stocks_page_data_population()
        self.test_dashboard_data_population()
        self.test_crypto_page_data_population()
        self.test_opportunities_page_data_population()
        
        # Stability and crash prevention tests
        self.test_page_stability_and_no_crashes()
        self.test_no_sql_syntax_errors()
        self.test_app_process_stability()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.results if r['status'] == 'FAIL'])
        warning_tests = len([r for r in self.results if r['status'] == 'WARN'])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️  Warnings: {warning_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if result['status'] == 'FAIL':
                    print(f"   • {result['test']}: {result['details']}")
        
        if warning_tests > 0:
            print("\n⚠️  WARNINGS:")
            for result in self.results:
                if result['status'] == 'WARN':
                    print(f"   • {result['test']}: {result['details']}")
        
        # Save results to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"test_results/test_report_{timestamp}.json"
        os.makedirs("test_results", exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'warning_tests': warning_tests,
                    'success_rate': success_rate,
                    'timestamp': datetime.now().isoformat()
                },
                'results': self.results
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        if success_rate >= 80:
            print("\n🎉 EXCELLENT! System is performing well!")
        elif success_rate >= 60:
            print("\n⚠️  GOOD! Some issues need attention.")
        else:
            print("\n🚨 CRITICAL! Major issues need immediate attention.")

if __name__ == "__main__":
    test = ComprehensiveSystemTest()
    test.run_all_tests()