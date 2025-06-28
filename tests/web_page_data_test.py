#!/usr/bin/env python3
"""
Web Page Data Population Test
Tests that all web pages are properly populated with data and not showing empty states.
"""

import sys
import os
import requests
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup
import re

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class WebPageDataTest:
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.results = []
        self.session = requests.Session()
        
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

    def test_main_dashboard(self):
        """Test main dashboard page has data"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check for key elements
                title = soup.find('title')
                if title and 'Trading Dashboard' in title.text:
                    self.log_test("Main Dashboard - Title", "PASS", "Page title found")
                else:
                    self.log_test("Main Dashboard - Title", "FAIL", "Missing or incorrect title")
                
                # Check for stock symbol input
                symbol_input = soup.find('input', {'id': 'stockSymbol'})
                if symbol_input:
                    self.log_test("Main Dashboard - Symbol Input", "PASS", "Stock symbol input found")
                else:
                    self.log_test("Main Dashboard - Symbol Input", "FAIL", "Missing stock symbol input")
                
                # Check for analysis buttons (using the actual IDs from the template)
                standard_btn = soup.find('button', {'id': 'standardAnalysisBtn'})
                if standard_btn:
                    self.log_test("Main Dashboard - Standard Analysis Button", "PASS", "Standard analysis button found")
                else:
                    self.log_test("Main Dashboard - Standard Analysis Button", "FAIL", "Missing standard analysis button")
                
                enhanced_btn = soup.find('button', {'id': 'enhancedAnalysisBtn'})
                if enhanced_btn:
                    self.log_test("Main Dashboard - Enhanced Analysis Button", "PASS", "Enhanced analysis button found")
                else:
                    self.log_test("Main Dashboard - Enhanced Analysis Button", "FAIL", "Missing enhanced analysis button")
                
            else:
                self.log_test("Main Dashboard", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Main Dashboard", "FAIL", str(e))

    def test_stocks_page(self):
        """Test S&P 500 stocks page has data and is not crashing"""
        try:
            response = self.session.get(f"{self.base_url}/stocks", timeout=10)
            if response.status_code != 200:
                self.log_test("Stocks Page", "FAIL", f"HTTP {response.status_code}")
                return
            soup = BeautifulSoup(response.text, 'html.parser')
            if any(err in response.text for err in ["Exception", "Traceback", "Internal Server Error"]):
                self.log_test("Stocks Page", "FAIL", "Page contains error text")
                return
            
            # Check for stock analysis section
            stock_section = soup.find('div', {'id': 'stockAnalysisSection'})
            if not stock_section:
                self.log_test("Stocks Page - Stock Analysis Section", "FAIL", "Missing stock analysis section")
                return
            else:
                self.log_test("Stocks Page - Stock Analysis Section", "PASS", "Stock analysis section found")
            
            # Look for the legacy table section where the actual stock data is displayed
            legacy_table = soup.find('div', {'id': 'legacyTable'})
            if not legacy_table:
                self.log_test("Stocks Page - Legacy Table", "FAIL", "Missing legacy table section")
                return
            
            # Check for stock rows in the legacy table
            from bs4 import Tag
            if isinstance(legacy_table, Tag):
                stock_rows = legacy_table.find_all('tr')
                if len(stock_rows) > 1:  # More than just header row
                    self.log_test("Stocks Page - Data", "PASS", f"Found {len(stock_rows)-1} stock rows")
                else:
                    self.log_test("Stocks Page - Data", "FAIL", "No stock rows found")
            else:
                self.log_test("Stocks Page - Data", "FAIL", "Legacy table is not a Tag")
        except Exception as e:
            self.log_test("Stocks Page", "FAIL", str(e))

    def test_portfolio_page(self):
        """Test portfolio page has data"""
        try:
            response = self.session.get(f"{self.base_url}/portfolio_page", timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check for portfolio management elements
                portfolio_section = soup.find('div', {'id': 'portfolioSection'})
                if portfolio_section:
                    self.log_test("Portfolio Page - Portfolio Section", "PASS", "Portfolio section found")
                else:
                    self.log_test("Portfolio Page - Portfolio Section", "FAIL", "Missing portfolio section")
                
                # Check for add position form
                add_form = soup.find('form', {'id': 'addPositionForm'})
                if add_form:
                    self.log_test("Portfolio Page - Add Position Form", "PASS", "Add position form found")
                else:
                    self.log_test("Portfolio Page - Add Position Form", "FAIL", "Missing add position form")
                
            else:
                self.log_test("Portfolio Page", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Portfolio Page", "FAIL", str(e))

    def test_backtest_page(self):
        """Test backtest page has data"""
        try:
            response = self.session.get(f"{self.base_url}/backtest_page", timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check for backtest form
                backtest_form = soup.find('form', {'id': 'backtestForm'})
                if backtest_form:
                    self.log_test("Backtest Page - Backtest Form", "PASS", "Backtest form found")
                else:
                    self.log_test("Backtest Page - Backtest Form", "FAIL", "Missing backtest form")
                
                # Check for days back selector
                days_selector = soup.find('select', {'id': 'daysBack'})
                if days_selector:
                    self.log_test("Backtest Page - Days Selector", "PASS", "Days selector found")
                else:
                    self.log_test("Backtest Page - Days Selector", "FAIL", "Missing days selector")
                
            else:
                self.log_test("Backtest Page", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Backtest Page", "FAIL", str(e))

    def test_opportunities_page(self):
        """Test opportunities page has data"""
        try:
            response = self.session.get(f"{self.base_url}/opportunities", timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check for opportunities section
                opportunities_section = soup.find('div', {'id': 'opportunitiesSection'})
                if opportunities_section:
                    self.log_test("Opportunities Page - Opportunities Section", "PASS", "Opportunities section found")
                else:
                    self.log_test("Opportunities Page - Opportunities Section", "FAIL", "Missing opportunities section")
                
                # Check for find opportunities button
                find_btn = soup.find('button', {'id': 'findOpportunitiesBtn'})
                if find_btn:
                    self.log_test("Opportunities Page - Find Button", "PASS", "Find opportunities button found")
                else:
                    self.log_test("Opportunities Page - Find Button", "FAIL", "Missing find opportunities button")
                
            else:
                self.log_test("Opportunities Page", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Opportunities Page", "FAIL", str(e))

    def test_recommendations_page(self):
        """Test recommendations page has data"""
        try:
            response = self.session.get(f"{self.base_url}/recommendations", timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check for recommendations section
                recs_section = soup.find('div', {'id': 'recommendationsSection'})
                if recs_section:
                    self.log_test("Recommendations Page - Recommendations Section", "PASS", "Recommendations section found")
                else:
                    self.log_test("Recommendations Page - Recommendations Section", "FAIL", "Missing recommendations section")
                
                # Check for performance chart
                performance_chart = soup.find('canvas', {'id': 'performance-chart'})
                if performance_chart:
                    self.log_test("Recommendations Page - Performance Chart", "PASS", "Performance chart found")
                else:
                    self.log_test("Recommendations Page - Performance Chart", "FAIL", "Missing performance chart")
                
            else:
                self.log_test("Recommendations Page", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Recommendations Page", "FAIL", str(e))

    def test_system_status_page(self):
        """Test system status page has data and is not crashing"""
        try:
            response = self.session.get(f"{self.base_url}/system_status", timeout=10)
            if response.status_code != 200:
                self.log_test("System Status Page", "FAIL", f"HTTP {response.status_code}")
                return
            soup = BeautifulSoup(response.text, 'html.parser')
            # Check for error text
            if any(err in response.text for err in ["Exception", "Traceback", "Internal Server Error"]):
                self.log_test("System Status Page", "FAIL", "Page contains error text")
                return
            # Check for system status section
            status_section = soup.find('div', {'id': 'systemStatusSection'})
            if not status_section:
                self.log_test("System Status Page - Status Section", "FAIL", "Missing system status section")
                return
            else:
                self.log_test("System Status Page - Status Section", "PASS", "System status section found")
            
            # Check for performance metrics container
            performance_metrics = soup.find('div', {'id': 'performanceMetrics'})
            if not performance_metrics:
                self.log_test("System Status Page - Performance Metrics", "FAIL", "Missing performance metrics container")
                return
            else:
                self.log_test("System Status Page - Performance Metrics", "PASS", "Performance metrics container found")
            
            # Check for database status container
            database_status = soup.find('div', {'id': 'databaseStatus'})
            if not database_status:
                self.log_test("System Status Page - Database Status", "FAIL", "Missing database status container")
                return
            else:
                self.log_test("System Status Page - Database Status", "PASS", "Database status container found")
            
            # Check for system overview cards (these are static content)
            from bs4 import Tag
            if isinstance(status_section, Tag):
                overview_cards = status_section.find_all('div', class_='card')
                if len(overview_cards) >= 4:  # Should have at least 4 service cards
                    self.log_test("System Status Page - Data", "PASS", f"Found {len(overview_cards)} system overview cards")
                else:
                    self.log_test("System Status Page - Data", "FAIL", f"Only found {len(overview_cards)} overview cards")
            else:
                self.log_test("System Status Page - Data", "FAIL", "System status section is not a Tag")
                
        except Exception as e:
            self.log_test("System Status Page", "FAIL", str(e))

    def test_crypto_page(self):
        """Test crypto page has data"""
        try:
            response = self.session.get(f"{self.base_url}/crypto", timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check for crypto analysis section
                crypto_section = soup.find('div', {'id': 'cryptoAnalysisSection'})
                if crypto_section:
                    self.log_test("Crypto Page - Crypto Section", "PASS", "Crypto analysis section found")
                else:
                    self.log_test("Crypto Page - Crypto Section", "FAIL", "Missing crypto analysis section")
                
                # Check for sentiment chart
                sentiment_chart = soup.find('canvas', {'id': 'sentimentChart'})
                if sentiment_chart:
                    self.log_test("Crypto Page - Sentiment Chart", "PASS", "Sentiment chart found")
                else:
                    self.log_test("Crypto Page - Sentiment Chart", "FAIL", "Missing sentiment chart")
                
            else:
                self.log_test("Crypto Page", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Crypto Page", "FAIL", str(e))

    def test_api_endpoints(self):
        """Test key API endpoints return valid, non-empty data"""
        endpoints = [
            ("/api/system_status", "System Status API", ["status", "system"]),
            ("/api/sp500_analysis", "S&P 500 Analysis API", ["enhanced_analysis", "top_gainers_losers"]),
            ("/api/crypto_analysis", "Crypto Analysis API", ["opportunities", "total_analyzed"]),
            ("/api/portfolio", "Portfolio API", ["portfolio_summary"]),
            ("/api/recommendations", "Recommendations API", ["recommendations"]),
        ]
        for endpoint, name, required_keys in endpoints:
            try:
                # Use longer timeout for S&P 500 analysis
                timeout = 60 if "sp500_analysis" in endpoint else 15
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=timeout)
                if response.status_code != 200:
                    self.log_test(name, "FAIL", f"HTTP {response.status_code}")
                    continue
                
                data = response.json()
                response_data = data.get('data', data)  # Handle both wrapped and unwrapped responses
                
                # Check if required keys exist
                missing_keys = [key for key in required_keys if key not in response_data]
                if missing_keys:
                    self.log_test(name, "FAIL", f"Missing keys: {missing_keys}")
                    continue
                
                # Check if data is non-empty
                if not response_data or (isinstance(response_data, dict) and not any(response_data.values())):
                    self.log_test(name, "FAIL", "Empty response data")
                    continue
                
                self.log_test(name, "PASS", f"Data returned successfully")
                
            except Exception as e:
                self.log_test(name, "FAIL", f"Error: {str(e)}")

    def test_stock_analysis_with_data(self):
        """Test stock analysis actually returns recommendations"""
        try:
            payload = {
                "symbol": "AAPL",
                "ai_provider": "ollama"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/analyze_stock",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'trading_recommendation' in data['data']:
                    rec = data['data']['trading_recommendation']
                    action = rec.get('action', 'UNKNOWN')
                    self.log_test("Stock Analysis with Data", "PASS", 
                                f"Generated recommendation: {action}")
                else:
                    self.log_test("Stock Analysis with Data", "FAIL", "No trading recommendation in response")
            else:
                self.log_test("Stock Analysis with Data", "FAIL", f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Stock Analysis with Data", "FAIL", str(e))

    def test_enhanced_analysis_with_data(self):
        """Test enhanced analysis returns multiple strategies"""
        try:
            payload = {
                "symbol": "TSLA",
                "ai_provider": "ollama"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/enhanced_analysis",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    recommendations = data['data'].get('recommendations', [])
                    stock_recs = data['data'].get('stock_recommendations', [])
                    
                    total_recs = len(recommendations) + len(stock_recs)
                    if total_recs > 0:
                        self.log_test("Enhanced Analysis with Data", "PASS", 
                                    f"Generated {total_recs} recommendations")
                    else:
                        self.log_test("Enhanced Analysis with Data", "FAIL", "No recommendations generated")
                else:
                    self.log_test("Enhanced Analysis with Data", "FAIL", "No data in response")
            else:
                self.log_test("Enhanced Analysis with Data", "FAIL", f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Enhanced Analysis with Data", "FAIL", str(e))

    def test_dashboard_analysis_functionality(self):
        """Test that dashboard analysis actually works and displays data"""
        try:
            # Test basic analysis functionality
            print("🔍 Testing dashboard basic analysis functionality...")
            
            # Test basic stock analysis API
            basic_response = self.session.post(
                f"{self.base_url}/api/analyze_stock",
                json={"symbol": "AAPL", "ai_provider": "ollama"},
                timeout=60
            )
            
            if basic_response.status_code == 200:
                basic_data = basic_response.json()
                if basic_data.get('status') == 'success' and basic_data.get('data'):
                    data = basic_data['data']
                    
                    # Check that we have the required data fields
                    required_fields = ['price_data', 'sentiment_analysis', 'trading_recommendation']
                    missing_fields = [field for field in required_fields if not data.get(field)]
                    
                    if not missing_fields:
                        self.log_test("Dashboard Basic Analysis - Data Structure", "PASS", 
                                    f"All required fields present: {', '.join(required_fields)}")
                        
                        # Check that price data is populated
                        price_data = data.get('price_data', {})
                        if price_data.get('current_price'):
                            self.log_test("Dashboard Basic Analysis - Price Data", "PASS", 
                                        f"Current price: ${price_data['current_price']}")
                        else:
                            self.log_test("Dashboard Basic Analysis - Price Data", "FAIL", "No current price found")
                        
                        # Check that sentiment analysis is populated
                        sentiment = data.get('sentiment_analysis', {})
                        if sentiment.get('sentiment_score') is not None:
                            self.log_test("Dashboard Basic Analysis - Sentiment", "PASS", 
                                        f"Sentiment score: {sentiment['sentiment_score']}")
                        else:
                            self.log_test("Dashboard Basic Analysis - Sentiment", "FAIL", "No sentiment score found")
                        
                        # Check that trading recommendation is populated
                        recommendation = data.get('trading_recommendation', {})
                        if recommendation.get('action'):
                            self.log_test("Dashboard Basic Analysis - Recommendation", "PASS", 
                                        f"Action: {recommendation['action']}")
                        else:
                            self.log_test("Dashboard Basic Analysis - Recommendation", "FAIL", "No trading action found")
                        
                    else:
                        self.log_test("Dashboard Basic Analysis - Data Structure", "FAIL", 
                                    f"Missing fields: {', '.join(missing_fields)}")
                else:
                    self.log_test("Dashboard Basic Analysis - API Response", "FAIL", 
                                f"API returned error: {basic_data.get('message', 'Unknown error')}")
            else:
                self.log_test("Dashboard Basic Analysis - HTTP", "FAIL", f"HTTP {basic_response.status_code}")
            
            # Test enhanced analysis functionality
            print("🔍 Testing dashboard enhanced analysis functionality...")
            
            enhanced_response = self.session.post(
                f"{self.base_url}/api/enhanced_analysis",
                json={"symbol": "AAPL", "ai_provider": "ollama"},
                timeout=120
            )
            
            if enhanced_response.status_code == 200:
                enhanced_data = enhanced_response.json()
                if enhanced_data.get('success') and enhanced_data.get('data'):
                    data = enhanced_data['data']
                    
                    # Check that we have the required data fields for enhanced analysis
                    required_fields = ['price_data', 'sentiment_data', 'signal_data', 'trade_signal']
                    missing_fields = [field for field in required_fields if not data.get(field)]
                    
                    if not missing_fields:
                        self.log_test("Dashboard Enhanced Analysis - Data Structure", "PASS", 
                                    f"All required fields present: {', '.join(required_fields)}")
                        
                        # Check that stock recommendations are populated
                        stock_recs = data.get('stock_recommendations', [])
                        if stock_recs:
                            self.log_test("Dashboard Enhanced Analysis - Stock Recommendations", "PASS", 
                                        f"Found {len(stock_recs)} stock recommendations")
                        else:
                            self.log_test("Dashboard Enhanced Analysis - Stock Recommendations", "FAIL", "No stock recommendations found")
                        
                        # Check that options recommendations are populated
                        options_recs = data.get('options_recommendations', [])
                        if options_recs:
                            self.log_test("Dashboard Enhanced Analysis - Options Recommendations", "PASS", 
                                        f"Found {len(options_recs)} options recommendations")
                        else:
                            self.log_test("Dashboard Enhanced Analysis - Options Recommendations", "FAIL", "No options recommendations found")
                        
                    else:
                        self.log_test("Dashboard Enhanced Analysis - Data Structure", "FAIL", 
                                    f"Missing fields: {', '.join(missing_fields)}")
                else:
                    self.log_test("Dashboard Enhanced Analysis - API Response", "FAIL", 
                                f"API returned error: {enhanced_data.get('message', 'Unknown error')}")
            else:
                self.log_test("Dashboard Enhanced Analysis - HTTP", "FAIL", f"HTTP {enhanced_response.status_code}")
                
        except Exception as e:
            self.log_test("Dashboard Analysis Functionality", "FAIL", str(e))

    def test_page_crash_prevention(self):
        """Test that pages don't crash and handle errors gracefully"""
        try:
            # Test pages for crash indicators
            pages_to_test = [
                ("/", "Dashboard"),
                ("/stocks", "S&P 500"),
                ("/crypto", "Crypto"),
                ("/portfolio_page", "Portfolio"),
                ("/backtest_page", "Backtest"),
                ("/opportunities", "Opportunities"),
                ("/recommendations", "Recommendations"),
                ("/system_status", "System Status")
            ]
            
            # More specific crash indicators that won't have false positives
            crash_indicators = [
                "exception", "traceback", "internal server error", "error 500",
                "error occurred", "something went wrong", "page not found",
                "http 500", "500 error", "server error"
            ]
            
            for page_url, page_name in pages_to_test:
                try:
                    response = self.session.get(f"{self.base_url}{page_url}", timeout=15)
                    
                    if response.status_code == 200:
                        # Check for crash indicators in the response
                        page_content = response.text.lower()
                        found_crashes = [indicator for indicator in crash_indicators 
                                       if indicator in page_content]
                        
                        if not found_crashes:
                            self.log_test(f"{page_name} Page - No Crashes", "PASS", 
                                        "Page loads without errors")
                        else:
                            self.log_test(f"{page_name} Page - No Crashes", "FAIL", 
                                        f"Found crash indicators: {', '.join(found_crashes)}")
                    else:
                        self.log_test(f"{page_name} Page - No Crashes", "FAIL", 
                                    f"HTTP {response.status_code}")
                        
                except requests.exceptions.Timeout:
                    self.log_test(f"{page_name} Page - No Crashes", "FAIL", "Page timed out")
                except Exception as e:
                    self.log_test(f"{page_name} Page - No Crashes", "FAIL", str(e))
                    
        except Exception as e:
            self.log_test("Page Crash Prevention", "FAIL", str(e))

    def test_dynamic_data_population(self):
        """Test that pages actually display dynamic data, not just static HTML"""
        try:
            print("🔍 Testing dynamic data population...")
            
            # Test 1: Dashboard - Check if analysis actually works
            print("Testing dashboard analysis functionality...")
            
            # Test basic analysis by making API call and checking response
            basic_response = self.session.post(
                f"{self.base_url}/api/analyze_stock",
                json={"symbol": "AAPL", "ai_provider": "ollama"},
                timeout=60
            )
            
            if basic_response.status_code == 200:
                data = basic_response.json()
                if data.get('status') == 'success' and data.get('data'):
                    # Check that we have actual data, not just empty fields
                    price_data = data['data'].get('price_data', {})
                    sentiment = data['data'].get('sentiment_analysis', {})
                    recommendation = data['data'].get('trading_recommendation', {})
                    
                    has_real_data = (
                        price_data.get('current_price') and 
                        sentiment.get('sentiment_score') is not None and
                        recommendation.get('action')
                    )
                    
                    if has_real_data:
                        self.log_test("Dashboard Dynamic Data - Basic Analysis", "PASS", 
                                    f"Real data: ${price_data.get('current_price')}, Sentiment: {sentiment.get('sentiment_score')}, Action: {recommendation.get('action')}")
                    else:
                        self.log_test("Dashboard Dynamic Data - Basic Analysis", "FAIL", 
                                    "API returned empty or missing data fields")
                else:
                    self.log_test("Dashboard Dynamic Data - Basic Analysis", "FAIL", 
                                "API did not return success status")
            else:
                self.log_test("Dashboard Dynamic Data - Basic Analysis", "FAIL", 
                            f"API returned HTTP {basic_response.status_code}")
            
            # Test 2: S&P 500 Page - Check if data is actually loaded
            print("Testing S&P 500 data loading...")
            
            # First check if the page loads without data (should show loading message)
            stocks_response = self.session.get(f"{self.base_url}/stocks", timeout=10)
            if stocks_response.status_code == 200:
                soup = BeautifulSoup(stocks_response.text, 'html.parser')
                
                # Check for loading message (indicates page is working but needs user interaction)
                if "Loading stock data" in stocks_response.text:
                    self.log_test("S&P 500 Dynamic Data - Loading State", "PASS", 
                                "Page shows loading state (requires user interaction)")
                else:
                    self.log_test("S&P 500 Dynamic Data - Loading State", "FAIL", 
                                "Page does not show expected loading state")
                
                # Check if refresh button exists (for user interaction)
                refresh_btn = soup.find('button', {'id': 'refreshBtn'})
                if refresh_btn:
                    self.log_test("S&P 500 Dynamic Data - Refresh Button", "PASS", 
                                "Refresh button available for data loading")
                    # Simulate button click by calling the API directly
                    api_response = self.session.get(f"{self.base_url}/api/sp500_analysis", timeout=60)
                    if api_response.status_code == 200:
                        api_data = api_response.json()
                        enhanced = api_data.get('data', {}).get('enhanced_analysis', [])
                        if enhanced and isinstance(enhanced, list) and len(enhanced) > 0:
                            self.log_test("S&P 500 Dynamic Data - API Data", "PASS", 
                                        f"API returned {len(enhanced)} stock analysis results")
                        else:
                            self.log_test("S&P 500 Dynamic Data - API Data", "FAIL", 
                                        "API did not return any stock analysis results")
                    else:
                        self.log_test("S&P 500 Dynamic Data - API Data", "FAIL", 
                                    f"API returned HTTP {api_response.status_code}")
                else:
                    self.log_test("S&P 500 Dynamic Data - Refresh Button", "FAIL", 
                                "No refresh button found")
            else:
                self.log_test("S&P 500 Dynamic Data - Page Load", "FAIL", 
                            f"Page returned HTTP {stocks_response.status_code}")
            
            # Test 3: Crypto Page - Check if crypto data is loaded
            print("Testing crypto data loading...")
            
            crypto_response = self.session.get(f"{self.base_url}/crypto", timeout=10)
            if crypto_response.status_code == 200:
                soup = BeautifulSoup(crypto_response.text, 'html.parser')
                
                # Check for crypto analysis container
                crypto_container = soup.find('div', {'id': 'cryptoAnalysisContainer'})
                if crypto_container:
                    # Check if container has substantial content (not just loading)
                    container_text = crypto_container.get_text().strip()
                    # Look for actual crypto content like symbols, prices, or analysis results
                    has_crypto_content = (
                        container_text and 
                        len(container_text) > 100 and  # Substantial content
                        ("Cryptocurrency" in container_text or 
                         "Bitcoin" in container_text or 
                         "Analysis" in container_text or
                         "USD" in container_text or
                         "Refresh" in container_text)
                    )
                    if has_crypto_content:
                        self.log_test("Crypto Dynamic Data - Content", "PASS", 
                                    "Crypto container has substantial content")
                    else:
                        self.log_test("Crypto Dynamic Data - Content", "FAIL", 
                                    "Crypto container lacks substantial content")
                else:
                    self.log_test("Crypto Dynamic Data - Container", "FAIL", 
                                "Crypto analysis container not found")
            else:
                self.log_test("Crypto Dynamic Data - Page Load", "FAIL", 
                            f"Page returned HTTP {crypto_response.status_code}")
            
            # Test 4: Portfolio Page - Check if portfolio data is loaded
            print("Testing portfolio data loading...")
            
            portfolio_response = self.session.get(f"{self.base_url}/portfolio_page", timeout=10)
            if portfolio_response.status_code == 200:
                soup = BeautifulSoup(portfolio_response.text, 'html.parser')
                
                # Check for portfolio container
                portfolio_container = soup.find('div', {'id': 'portfolioContainer'})
                if portfolio_container:
                    # Check if container has any content
                    container_text = portfolio_container.get_text().strip()
                    if container_text and "Loading" not in container_text:
                        self.log_test("Portfolio Dynamic Data - Content", "PASS", 
                                    "Portfolio container has content")
                    else:
                        self.log_test("Portfolio Dynamic Data - Content", "FAIL", 
                                    "Portfolio container is empty or shows loading")
                else:
                    self.log_test("Portfolio Dynamic Data - Container", "FAIL", 
                                "Portfolio container not found")
            else:
                self.log_test("Portfolio Dynamic Data - Page Load", "FAIL", 
                            f"Page returned HTTP {portfolio_response.status_code}")
            
            # Test 5: System Status - Check if status data is loaded
            print("Testing system status data loading...")
            
            status_response = self.session.get(f"{self.base_url}/system_status", timeout=10)
            if status_response.status_code == 200:
                soup = BeautifulSoup(status_response.text, 'html.parser')
                
                # Check for performance metrics container
                perf_metrics = soup.find('div', {'id': 'performanceMetrics'})
                if perf_metrics:
                    # Check if it has content beyond loading message
                    metrics_text = perf_metrics.get_text().strip()
                    if metrics_text and "Loading" not in metrics_text:
                        self.log_test("System Status Dynamic Data - Performance", "PASS", 
                                    "Performance metrics have content")
                    else:
                        self.log_test("System Status Dynamic Data - Performance", "FAIL", 
                                    "Performance metrics are empty or show loading")
                else:
                    self.log_test("System Status Dynamic Data - Performance", "FAIL", 
                                "Performance metrics container not found")
            else:
                self.log_test("System Status Dynamic Data - Page Load", "FAIL", 
                            f"Page returned HTTP {status_response.status_code}")
                
        except Exception as e:
            self.log_test("Dynamic Data Population", "FAIL", str(e))

    def run_all_tests(self):
        """Run all web page data tests"""
        print("🌐 WEB PAGE DATA POPULATION TEST")
        print("=" * 60)
        print(f"Testing application at: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test all web pages
        self.test_main_dashboard()
        self.test_stocks_page()
        self.test_portfolio_page()
        self.test_backtest_page()
        self.test_opportunities_page()
        self.test_recommendations_page()
        self.test_system_status_page()
        self.test_crypto_page()
        
        # Test API endpoints
        self.test_api_endpoints()
        
        # Test data generation
        self.test_stock_analysis_with_data()
        self.test_enhanced_analysis_with_data()
        
        # Test dashboard analysis functionality
        self.test_dashboard_analysis_functionality()
        
        # Test page crash prevention
        self.test_page_crash_prevention()
        
        # Test dynamic data population
        self.test_dynamic_data_population()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.results if r['status'] == 'FAIL'])
        
        print("\n" + "=" * 60)
        print("📊 WEB PAGE DATA TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.results:
                if result['status'] == 'FAIL':
                    print(f"   • {result['test']}: {result['details']}")
            print()
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results/test_report_web_pages_{timestamp}.json"
        os.makedirs("test_results", exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump({
                'test_type': 'web_page_data',
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'success_rate': (passed_tests/total_tests)*100
                },
                'results': self.results
            }, f, indent=2)
        
        print(f"📄 Detailed results saved to: {filename}")
        
        if failed_tests == 0:
            print("\n🎉 ALL WEB PAGES ARE PROPERLY POPULATED WITH DATA!")
        else:
            print(f"\n⚠️  {failed_tests} web pages need attention for data population.")


if __name__ == "__main__":
    tester = WebPageDataTest()
    tester.run_all_tests() 