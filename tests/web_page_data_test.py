#!/usr/bin/env python3
"""
Web Page Data Test
Tests the data population and functionality of web pages
"""

import requests
import json
import time
from datetime import datetime

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
                print(f"  ✅ {page} - Status: {response.status_code}")
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
                    if isinstance(data, dict) and 'success' in data:
                        if data['success']:
                            print(f"  ✅ {endpoint} - Success: True")
                            results["passed"] += 1
                        else:
                            print(f"  ⚠️  {endpoint} - Success: False")
                            results["failed"] += 1
                            results["errors"].append(f"{endpoint}: API returned success=False")
                    else:
                        print(f"  ✅ {endpoint} - Valid JSON response")
                        results["passed"] += 1
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









