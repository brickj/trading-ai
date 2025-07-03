#!/usr/bin/env python3
"""
Test script to check what's being returned by the standard and enhanced analysis endpoints
"""
import requests
import json
import time

# Base URL for the API
BASE_URL = "http://localhost:5001"

def test_standard_analysis():
    """Test the standard analysis endpoint"""
    print("Testing standard analysis endpoint...")
    url = f"{BASE_URL}/api/analyze_stock"
    payload = {"symbol": "AAPL"}
    
    try:
        response = requests.post(url, json=payload)
        response_data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Cache Status: {response_data.get('cache_status')}")
        print(f"Response Keys: {list(response_data.keys())}")
        
        if 'data' in response_data:
            print(f"Data Keys: {list(response_data['data'].keys())}")
            
        # Save the full response to a file for inspection
        with open("standard_analysis_response.json", "w") as f:
            json.dump(response_data, f, indent=2)
            print("Full response saved to standard_analysis_response.json")
            
        return response_data
    except Exception as e:
        print(f"Error testing standard analysis: {e}")
        return None

def test_enhanced_analysis():
    """Test the enhanced analysis endpoint"""
    print("\nTesting enhanced analysis endpoint...")
    url = f"{BASE_URL}/api/enhanced_analysis"
    payload = {"symbol": "AAPL"}
    
    try:
        response = requests.post(url, json=payload)
        response_data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Cache Status: {response_data.get('cache_status')}")
        print(f"Response Keys: {list(response_data.keys())}")
        
        if 'data' in response_data:
            print(f"Data Keys: {list(response_data['data'].keys())}")
            
        # Save the full response to a file for inspection
        with open("enhanced_analysis_response.json", "w") as f:
            json.dump(response_data, f, indent=2)
            print("Full response saved to enhanced_analysis_response.json")
            
        return response_data
    except Exception as e:
        print(f"Error testing enhanced analysis: {e}")
        return None

def compare_responses(standard_response, enhanced_response):
    """Compare the standard and enhanced responses"""
    print("\nComparing responses...")
    
    if not standard_response or not enhanced_response:
        print("Cannot compare responses - one or both are missing")
        return
    
    standard_data = standard_response.get('data', {})
    enhanced_data = enhanced_response.get('data', {})
    
    # Get all unique keys from both responses
    all_keys = set(standard_data.keys()) | set(enhanced_data.keys())
    
    print("Fields comparison (standard vs enhanced):")
    for key in sorted(all_keys):
        standard_has = key in standard_data
        enhanced_has = key in enhanced_data
        
        if standard_has and enhanced_has:
            print(f"✅ {key}: Both have this field")
        elif standard_has:
            print(f"🔵 {key}: Only in standard analysis")
        else:
            print(f"🟠 {key}: Only in enhanced analysis")
    
    # Check for empty or missing fields in standard analysis
    print("\nEmpty or missing fields in standard analysis:")
    for key in standard_data:
        value = standard_data[key]
        if value == "" or value == 0 or value == [] or value == {}:
            print(f"⚠️ {key}: Empty or zero value: {value}")

if __name__ == "__main__":
    print("API Response Test")
    print("=" * 50)
    
    # Test both endpoints
    standard_response = test_standard_analysis()
    
    # Wait a bit to avoid rate limiting
    time.sleep(1)
    
    enhanced_response = test_enhanced_analysis()
    
    # Compare the responses
    compare_responses(standard_response, enhanced_response)
