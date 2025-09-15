#!/usr/bin/env python3
"""
Web Page Data Test
Tests the data population and functionality of web pages
"""

import requests
import json
import time
import re
import sys
import os
from datetime import datetime

# Add the src directory to the path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import database connection function
try:
    from core.database import get_db_connection
except ImportError:
    # Fallback: try direct import
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from src.core.database import get_db_connection

def validate_database_data_consistency():
    """Validate that page data matches database data"""
    validation_results = {
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    print("🔍 Validating Database Data Consistency")
    print("=" * 50)
    
    # Test scalping signals data consistency
    try:
        print("Testing scalping signals data consistency...")
        
        # Get data from database
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT ticker, sentiment_score, recommendation, created_at 
                    FROM scalping_signals 
                    ORDER BY created_at DESC 
                    LIMIT 10
                """)
                db_signals = cur.fetchall()
        
        # Get data from API
        api_response = requests.get("http://127.0.0.1:5001/api/scalping/opportunities", timeout=30)
        if api_response.status_code == 200:
            api_data = api_response.json()
            api_signals = api_data.get('data', [])
            
            # Compare data
            if len(db_signals) > 0 and len(api_signals) > 0:
                # Check if API data matches database structure
                db_symbols = {signal['ticker'] for signal in db_signals}  # ticker is first column
                api_symbols = {signal.get('ticker') for signal in api_signals}  # API also uses ticker
                
                if db_symbols.intersection(api_symbols):
                    print("  ✅ Scalping signals data consistency: PASSED")
                    validation_results["passed"] += 1
                else:
                    print("  ❌ Scalping signals data consistency: FAILED - No matching symbols")
                    validation_results["failed"] += 1
                    validation_results["errors"].append("Scalping signals: No matching symbols between DB and API")
            else:
                print("  ⚠️  Scalping signals data consistency: SKIPPED - No data available")
        else:
            print("  ❌ Scalping signals data consistency: FAILED - API error")
            validation_results["failed"] += 1
            validation_results["errors"].append("Scalping signals: API returned error")
            
    except Exception as e:
        print(f"  ❌ Scalping signals data consistency: ERROR - {str(e)}")
        validation_results["failed"] += 1
        validation_results["errors"].append(f"Scalping signals: {str(e)}")
    
    # Test recommendations data consistency
    try:
        print("Testing recommendations data consistency...")
        
        # Get data from database
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT symbol, action, final_confidence, timestamp 
                    FROM recommendations 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                """)
                db_recommendations = cur.fetchall()
        
        # Get data from API
        api_response = requests.get("http://127.0.0.1:5001/api/recommendations", timeout=30)
        if api_response.status_code == 200:
            api_data = api_response.json()
            api_recommendations = api_data.get('data', [])
            
            # Compare data
            if len(db_recommendations) > 0 and len(api_recommendations) > 0:
                db_symbols = {rec['symbol'] for rec in db_recommendations}  # symbol is first column
                api_symbols = {rec.get('symbol') for rec in api_recommendations}
                
                if db_symbols.intersection(api_symbols):
                    print("  ✅ Recommendations data consistency: PASSED")
                    validation_results["passed"] += 1
                else:
                    print("  ❌ Recommendations data consistency: FAILED - No matching symbols")
                    validation_results["failed"] += 1
                    validation_results["errors"].append("Recommendations: No matching symbols between DB and API")
            else:
                print("  ⚠️  Recommendations data consistency: SKIPPED - No data available")
        else:
            print("  ❌ Recommendations data consistency: FAILED - API error")
            validation_results["failed"] += 1
            validation_results["errors"].append("Recommendations: API returned error")
            
    except Exception as e:
        print(f"  ❌ Recommendations data consistency: ERROR - {str(e)}")
        validation_results["failed"] += 1
        validation_results["errors"].append(f"Recommendations: {str(e)}")
    
    # Test market movers data consistency
    try:
        print("Testing market movers data consistency...")
        
        # Get data from database
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT symbol, change_percent, volume, timestamp 
                    FROM market_movers 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                """)
                db_movers = cur.fetchall()
        
        # Get data from API
        api_response = requests.get("http://127.0.0.1:5001/api/market_movers", timeout=30)
        if api_response.status_code == 200:
            api_data = api_response.json()
            api_movers = []
            if 'data' in api_data:
                # Market movers API returns gainers and losers arrays
                gainers = api_data['data'].get('gainers', [])
                losers = api_data['data'].get('losers', [])
                api_movers = gainers + losers
            
            # Compare data
            if len(db_movers) > 0 and len(api_movers) > 0:
                db_symbols = {mover['symbol'] for mover in db_movers}  # symbol is first column
                api_symbols = {mover.get('symbol') for mover in api_movers}
                
                if db_symbols.intersection(api_symbols):
                    print("  ✅ Market movers data consistency: PASSED")
                    validation_results["passed"] += 1
                else:
                    print("  ❌ Market movers data consistency: FAILED - No matching symbols")
                    validation_results["failed"] += 1
                    validation_results["errors"].append("Market movers: No matching symbols between DB and API")
            else:
                print("  ⚠️  Market movers data consistency: SKIPPED - No data available")
        else:
            print("  ❌ Market movers data consistency: FAILED - API error")
            validation_results["failed"] += 1
            validation_results["errors"].append("Market movers: API returned error")
            
    except Exception as e:
        print(f"  ❌ Market movers data consistency: ERROR - {str(e)}")
        validation_results["failed"] += 1
        validation_results["errors"].append(f"Market movers: {str(e)}")
    
    return validation_results

def check_for_mock_data(page_content, page_name):
    """Check for mock data patterns that shouldn't appear in production"""
    mock_patterns = {
        # Crypto page mock data patterns
        'crypto_mock_prices': [
            r'\$112,258\.40',  # BTC mock price
            r'\$4,575\.58',    # ETH mock price
            r'\$196\.38',      # SOL mock price
            r'\$0\.9998',      # USDT mock price
        ],
        'crypto_mock_actions': [
            r'<span class="badge bg-secondary">HOLD</span>',
            r'<span class="badge bg-success">BUY</span>',
        ],
        'crypto_mock_stats': [
            r'id="cryptoGainers">1</h4>',
            r'id="cryptoLosers">0</h4>',
            r'id="cryptoVolume">5</h4>',
            r'id="cryptoVolatility">15\.2%</h4>',
            r'id="bullishCount">1</h4>',
            r'id="bearishCount">0</h4>',
            r'id="neutralCount">4</h4>',
            r'id="avgSentiment">0\.04</h4>',
        ],
        # Recommendations page mock data patterns
        'recommendations_mock_data': [
            r'Jul 30, 2025 2:30 PM',
            r'<span class="symbol-badge">AAPL</span>',
            r'<span class="symbol-badge">TSLA</span>',
            r'\$150\.25',
            r'\$155\.80',
            r'\$245\.80',
            r'\$242\.50',
            r'\+3\.7%',
            r'-1\.3%',
        ],
        # Generic mock data patterns (excluding legitimate placeholder text)
        'generic_mock': [
            r'Loading real-time winners data\.\.\.',
            r'Loading real-time losers data\.\.\.',
            r'No stock data available',
        ]
    }
    
    found_mock_data = []
    
    for category, patterns in mock_patterns.items():
        for pattern in patterns:
            if re.search(pattern, page_content):
                found_mock_data.append(f"{category}: {pattern}")
    
    return found_mock_data

def test_web_page_data():
    """Test that web pages load with proper data"""
    base_url = "http://localhost:5001"
    
    print("🧪 Testing Web Page Data Population")
    print("=" * 50)
    
    # Test pages that should load with data
    test_pages = [
        "/",
        "/stocks", 
        "/crypto",
        "/portfolio",
        "/opportunities",
        "/foreign_markets_overview",
        "/recommendations",
        "/logs"
    ]
    
    results = {
        "total_pages": len(test_pages),
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    for page in test_pages:
        try:
            print(f"Testing page: {page}")
            response = requests.get(f"{base_url}{page}", timeout=30)
            
            if response.status_code == 200:
                # Check for mock data in the page content
                mock_data_found = check_for_mock_data(response.text, page)
                
                if mock_data_found:
                    print(f"  ❌ {page} - Mock data detected!")
                    for mock_item in mock_data_found:
                        print(f"    - {mock_item}")
                    results["failed"] += 1
                    results["errors"].append(f"{page}: Mock data detected - {', '.join(mock_data_found)}")
                else:
                    print(f"  ✅ {page} - Status: {response.status_code} (No mock data)")
                    results["passed"] += 1
            else:
                print(f"  ❌ {page} - Status: {response.status_code}")
                results["failed"] += 1
                results["errors"].append(f"{page}: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {page} - Error: {str(e)}")
            results["failed"] += 1
            results["errors"].append(f"{page}: {str(e)}")
    
    # Test API endpoints that provide data to pages
    api_endpoints = [
        "/api/dashboard/data",
        "/api/sp500_analysis",
        "/api/crypto_analysis", 
        "/api/portfolio",
        "/api/news_opportunities",
        "/api/watchlist_opportunities",
        "/api/recommendations",
        "/api/system_status"
    ]
    
    print("\n🧪 Testing API Endpoints")
    print("=" * 50)
    
    for endpoint in api_endpoints:
        try:
            print(f"Testing API: {endpoint}")
            response = requests.get(f"{base_url}{endpoint}", timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        # Check for success field if present
                        if 'success' in data:
                            if data['success']:
                                print(f"  ✅ {endpoint} - Success: True")
                                results["passed"] += 1
                            else:
                                print(f"  ⚠️  {endpoint} - Success: False")
                                results["failed"] += 1
                                results["errors"].append(f"{endpoint}: API returned success=False")
                        # Check for data field (common pattern)
                        elif 'data' in data:
                            print(f"  ✅ {endpoint} - Valid JSON with data field")
                            results["passed"] += 1
                        # Any valid JSON response is considered a pass
                        else:
                            print(f"  ✅ {endpoint} - Valid JSON response")
                            results["passed"] += 1
                    else:
                        print(f"  ⚠️  {endpoint} - Response is not a dictionary")
                        results["failed"] += 1
                        results["errors"].append(f"{endpoint}: Response is not a dictionary")
                except json.JSONDecodeError:
                    print(f"  ⚠️  {endpoint} - Invalid JSON response")
                    results["failed"] += 1
                    results["errors"].append(f"{endpoint}: Invalid JSON")
            else:
                print(f"  ❌ {endpoint} - Status: {response.status_code}")
                results["failed"] += 1
                results["errors"].append(f"{endpoint}: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {endpoint} - Error: {str(e)}")
            results["failed"] += 1
            results["errors"].append(f"{endpoint}: {str(e)}")
    
    # Test data consistency between APIs and pages
    print("\n🔍 Testing Data Consistency")
    print("=" * 50)
    
    # Test crypto data consistency
    try:
        print("Testing crypto data consistency...")
        crypto_api_response = requests.get(f"{base_url}/api/crypto_analysis", timeout=30)
        crypto_page_response = requests.get(f"{base_url}/crypto", timeout=30)
        
        if crypto_api_response.status_code == 200 and crypto_page_response.status_code == 200:
            api_data = crypto_api_response.json()
            page_content = crypto_page_response.text
            
            # Check if page shows loading state instead of mock data
            if "Loading crypto data..." in page_content:
                print("  ✅ Crypto page shows loading state (no mock data)")
                results["passed"] += 1
            else:
                # Check for specific crypto symbols that should come from API
                if api_data.get('success') and 'data' in api_data:
                    api_crypto_symbols = []
                    if 'crypto_data' in api_data['data']:
                        for crypto in api_data['data']['crypto_data']:
                            api_crypto_symbols.append(crypto.get('symbol', ''))
                    
                    # Check if page contains hardcoded crypto symbols
                    hardcoded_symbols = ['BTC', 'ETH', 'SOL', 'USDT']
                    found_hardcoded = []
                    for symbol in hardcoded_symbols:
                        if f'<h5>{symbol}</h5>' in page_content:
                            found_hardcoded.append(symbol)
                    
                    if found_hardcoded:
                        print(f"  ❌ Crypto page contains hardcoded symbols: {found_hardcoded}")
                        results["failed"] += 1
                        results["errors"].append(f"Crypto page: Hardcoded symbols detected - {found_hardcoded}")
                    else:
                        print("  ✅ Crypto page data appears dynamic")
                        results["passed"] += 1
                else:
                    print("  ⚠️  Crypto API data structure unexpected")
                    results["failed"] += 1
                    results["errors"].append("Crypto API: Unexpected data structure")
        else:
            print("  ❌ Failed to fetch crypto data for consistency check")
            results["failed"] += 1
            results["errors"].append("Crypto consistency: Failed to fetch data")
    except Exception as e:
        print(f"  ❌ Crypto consistency check failed: {str(e)}")
        results["failed"] += 1
        results["errors"].append(f"Crypto consistency: {str(e)}")
    
    # Test recommendations data consistency
    try:
        print("Testing recommendations data consistency...")
        rec_api_response = requests.get(f"{base_url}/api/recommendations", timeout=30)
        rec_page_response = requests.get(f"{base_url}/recommendations", timeout=30)
        
        if rec_api_response.status_code == 200 and rec_page_response.status_code == 200:
            page_content = rec_page_response.text
            
            # Check for hardcoded recommendation data
            hardcoded_patterns = [
                r'Jul 30, 2025 2:30 PM',
                r'<span class="symbol-badge">AAPL</span>',
                r'<span class="symbol-badge">TSLA</span>',
                r'\$150\.25',
                r'\$155\.80',
                r'\+3\.7%',
                r'-1\.3%'
            ]
            
            found_hardcoded = []
            for pattern in hardcoded_patterns:
                if re.search(pattern, page_content):
                    found_hardcoded.append(pattern)
            
            if found_hardcoded:
                print(f"  ❌ Recommendations page contains hardcoded data: {len(found_hardcoded)} patterns")
                results["failed"] += 1
                results["errors"].append(f"Recommendations page: Hardcoded data detected - {len(found_hardcoded)} patterns")
            else:
                print("  ✅ Recommendations page data appears dynamic")
                results["passed"] += 1
        else:
            print("  ❌ Failed to fetch recommendations data for consistency check")
            results["failed"] += 1
            results["errors"].append("Recommendations consistency: Failed to fetch data")
    except Exception as e:
        print(f"  ❌ Recommendations consistency check failed: {str(e)}")
        results["failed"] += 1
        results["errors"].append(f"Recommendations consistency: {str(e)}")
    
    # Test database data consistency
    print("\n🔍 Testing Database Data Consistency")
    print("=" * 50)
    
    db_validation_results = validate_database_data_consistency()
    results["passed"] += db_validation_results["passed"]
    results["failed"] += db_validation_results["failed"]
    results["errors"].extend(db_validation_results["errors"])
    
    # Print summary
    print("\n📊 Test Results Summary")
    print("=" * 50)
    print(f"Total tests: {results['total_pages'] + len(api_endpoints)}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Success rate: {(results['passed'] / (results['total_pages'] + len(api_endpoints))) * 100:.1f}%")
    
    if results["errors"]:
        print("\n❌ Errors encountered:")
        for error in results["errors"]:
            print(f"  - {error}")
    
    return results["failed"] == 0

if __name__ == "__main__":
    success = test_web_page_data()
    exit(0 if success else 1)














