#!/usr/bin/env python3
"""
Test script to verify API endpoints are working correctly
"""

import requests
import json
import time
from datetime import datetime

def test_api_endpoint(url, method='POST', data=None, expected_status=200):
    """Test an API endpoint and return results"""
    print(f"\n🧪 Testing {method} {url}")
    print(f"📤 Request data: {json.dumps(data, indent=2) if data else 'None'}")
    
    try:
        if method == 'POST':
            response = requests.post(url, json=data, timeout=30)
        else:
            response = requests.get(url, timeout=30)
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response headers: {dict(response.headers)}")
        
        if response.status_code == expected_status:
            try:
                response_data = response.json()
                print(f"✅ SUCCESS - Status {response.status_code}")
                print(f"📊 Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
                return True, response_data
            except json.JSONDecodeError:
                print(f"⚠️  WARNING - Status {response.status_code} but response is not JSON")
                print(f"📄 Response text: {response.text[:200]}...")
                return True, response.text
        else:
            print(f"❌ FAILED - Expected status {expected_status}, got {response.status_code}")
            print(f"📄 Response text: {response.text[:200]}...")
            return False, response.text
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR - Request failed: {e}")
        return False, str(e)

def main():
    """Run all API tests"""
    base_url = "http://localhost:5001"
    
    print("🚀 Starting API Endpoint Tests")
    print("=" * 50)
    print(f"📍 Testing against: {base_url}")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Standard Analysis
    print("\n" + "="*50)
    print("TEST 1: Standard Analysis Endpoint")
    print("="*50)
    
    standard_data = {
        "symbol": "AAPL",
        "ai_provider": "ollama"
    }
    
    success1, result1 = test_api_endpoint(
        f"{base_url}/api/analyze_stock",
        method='POST',
        data=standard_data,
        expected_status=200
    )
    
    # Test 2: Enhanced Analysis
    print("\n" + "="*50)
    print("TEST 2: Enhanced Analysis Endpoint")
    print("="*50)
    
    enhanced_data = {
        "symbol": "TSLA"
    }
    
    success2, result2 = test_api_endpoint(
        f"{base_url}/api/enhanced_analysis",
        method='POST',
        data=enhanced_data,
        expected_status=200
    )
    
    # Test 3: Invalid endpoint (should fail)
    print("\n" + "="*50)
    print("TEST 3: Invalid Endpoint (Should Fail)")
    print("="*50)
    
    invalid_data = {
        "symbol": "INVALID"
    }
    
    success3, result3 = test_api_endpoint(
        f"{base_url}/api/invalid_endpoint",
        method='POST',
        data=invalid_data,
        expected_status=404
    )
    
    # Test 4: Homepage (should work)
    print("\n" + "="*50)
    print("TEST 4: Homepage Endpoint")
    print("="*50)
    
    success4, result4 = test_api_endpoint(
        f"{base_url}/",
        method='GET',
        expected_status=200
    )
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    tests = [
        ("Standard Analysis", success1),
        ("Enhanced Analysis", success2),
        ("Invalid Endpoint", success3),
        ("Homepage", success4)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, success in tests:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The API endpoints are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        exit(1) 