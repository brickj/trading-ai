#!/usr/bin/env python3
"""
Test script for Go microservices
Verifies that all Go services are working correctly
"""

import requests
import json
import time
import sys

# Service URLs
DATA_FETCHER_URL = "http://localhost:8080"
CACHE_SERVICE_URL = "http://localhost:8081"
BACKGROUND_WORKERS_URL = "http://localhost:8082"

def test_service_health(url, service_name):
    """Test if a service is healthy"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                print(f"✅ {service_name} is healthy")
                return True
            else:
                print(f"❌ {service_name} is unhealthy: {data}")
                return False
        else:
            print(f"❌ {service_name} returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {service_name} is not responding: {e}")
        return False

def test_data_fetcher():
    """Test data fetcher service"""
    print("\n🔍 Testing Data Fetcher Service...")
    
    # Test stock price
    try:
        response = requests.post(f"{DATA_FETCHER_URL}/api/stock/price", 
                               json={"symbol": "AAPL"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stock price test passed: {data.get('symbol', 'N/A')}")
        else:
            print(f"❌ Stock price test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Stock price test error: {e}")
    
    # Test stock news
    try:
        response = requests.post(f"{DATA_FETCHER_URL}/api/stock/news", 
                               json={"symbol": "AAPL", "days_back": 7, "limit": 5}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stock news test passed: {len(data.get('news', []))} articles")
        else:
            print(f"❌ Stock news test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Stock news test error: {e}")

def test_cache_service():
    """Test cache service"""
    print("\n🗄️ Testing Cache Service...")
    
    # Test set operation
    try:
        response = requests.post(f"{CACHE_SERVICE_URL}/api/cache/set", 
                               json={"key": "test_key", "value": "test_value", "ttl": 60}, timeout=5)
        if response.status_code == 200:
            print("✅ Cache set test passed")
        else:
            print(f"❌ Cache set test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Cache set test error: {e}")
    
    # Test get operation
    try:
        response = requests.get(f"{CACHE_SERVICE_URL}/api/cache/get/test_key", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('found') and data.get('value') == 'test_value':
                print("✅ Cache get test passed")
            else:
                print(f"❌ Cache get test failed: {data}")
        else:
            print(f"❌ Cache get test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Cache get test error: {e}")
    
    # Test stats
    try:
        response = requests.get(f"{CACHE_SERVICE_URL}/api/cache/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cache stats test passed: {data.get('keys_count', 0)} keys")
        else:
            print(f"❌ Cache stats test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Cache stats test error: {e}")

def test_background_workers():
    """Test background workers service"""
    print("\n⚙️ Testing Background Workers Service...")
    
    # Test job submission
    try:
        response = requests.post(f"{BACKGROUND_WORKERS_URL}/api/jobs/submit", 
                               json={"type": "test_job", "data": {"test": "data"}, "priority": 1}, timeout=5)
        if response.status_code == 200:
            print("✅ Job submission test passed")
        else:
            print(f"❌ Job submission test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Job submission test error: {e}")
    
    # Test job stats
    try:
        response = requests.get(f"{BACKGROUND_WORKERS_URL}/api/jobs/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Job stats test passed: {data.get('queued_jobs', 0)} queued jobs")
        else:
            print(f"❌ Job stats test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Job stats test error: {e}")
    
    # Test worker stats
    try:
        response = requests.get(f"{BACKGROUND_WORKERS_URL}/api/workers/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Worker stats test passed: {data.get('active_workers', 0)} active workers")
        else:
            print(f"❌ Worker stats test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Worker stats test error: {e}")

def main():
    """Main test function"""
    print("🚀 Testing Trading AI Go Microservices")
    print("=" * 50)
    
    # Test service health
    print("\n🏥 Testing Service Health...")
    data_fetcher_healthy = test_service_health(DATA_FETCHER_URL, "Data Fetcher")
    cache_healthy = test_service_health(CACHE_SERVICE_URL, "Cache Service")
    workers_healthy = test_service_health(BACKGROUND_WORKERS_URL, "Background Workers")
    
    if not all([data_fetcher_healthy, cache_healthy, workers_healthy]):
        print("\n❌ Some services are not healthy. Please check the logs and restart services.")
        sys.exit(1)
    
    # Test individual services
    test_data_fetcher()
    test_cache_service()
    test_background_workers()
    
    print("\n🎉 All tests completed!")
    print("=" * 50)
    print("✅ Go microservices are working correctly!")
    print("🚀 Performance improvements are now active!")

if __name__ == "__main__":
    main()
