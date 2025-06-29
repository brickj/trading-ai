#!/usr/bin/env python3
"""
Simple test to verify debug panel captures requests and responses
"""

import requests
import json
import time

def test_debug_panel():
    """Test that debug panel shows requests and responses"""
    base_url = "http://localhost:5001"
    
    print("🧪 Testing Debug Panel Functionality")
    print("=" * 50)
    
    # Test 1: Standard Analysis
    print("\n1. Testing Standard Analysis...")
    standard_data = {"symbol": "AAPL", "ai_provider": "ollama"}
    
    try:
        response = requests.post(f"{base_url}/api/analyze_stock", json=standard_data, timeout=30)
        print(f"   ✅ Request sent: POST /api/analyze_stock")
        print(f"   ✅ Response received: {response.status_code}")
        print(f"   ✅ Debug panel should show this request and response")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    time.sleep(2)
    
    # Test 2: Enhanced Analysis  
    print("\n2. Testing Enhanced Analysis...")
    enhanced_data = {"symbol": "TSLA"}
    
    try:
        response = requests.post(f"{base_url}/api/enhanced_analysis", json=enhanced_data, timeout=30)
        print(f"   ✅ Request sent: POST /api/enhanced_analysis")
        print(f"   ✅ Response received: {response.status_code}")
        print(f"   ✅ Debug panel should show this request and response")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("📋 MANUAL VERIFICATION REQUIRED:")
    print("1. Open http://localhost:5001 in browser")
    print("2. Look at the debug panel at the bottom")
    print("3. Verify it shows both requests and responses")
    print("4. Check that request data includes method, URL, symbol")
    print("5. Check that response data shows status and JSON content")
    print("=" * 50)

if __name__ == "__main__":
    test_debug_panel() 