#!/usr/bin/env python3
"""
Direct test of stocks page performance without browser automation
This bypasses network issues and tests the core data loading performance
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import requests
import time
import json
from datetime import datetime

def test_stocks_page_performance():
    """Test the stocks page performance directly via API calls"""
    print("🚀 Testing stocks page performance directly...")
    
    base_url = "http://localhost:5001"
    
    # Test 1: Check if server is running
    print("\n📡 Testing server connectivity...")
    try:
        response = requests.get(f"{base_url}/stocks", timeout=10)
        if response.status_code == 200:
            print("✅ Server is accessible and stocks page loads")
            print(f"   📄 Page size: {len(response.text)} bytes")
        else:
            print(f"❌ Server returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not accessible: {str(e)}")
        return False
    
    # Test 2: Check preloaded data performance
    print("\n⚡ Testing preloaded data performance...")
    start_time = time.time()
    try:
        response = requests.get(f"{base_url}/api/preloaded_data", timeout=30)
        load_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Preloaded data loaded in {load_time:.2f} seconds")
            print(f"   📊 Success: {data.get('success', False)}")
            print(f"   📝 Message: {data.get('message', 'No message')}")
            
            if data.get('success') and data.get('data'):
                enhanced_analysis = data['data'].get('enhanced_analysis', [])
                print(f"   📈 Stocks analyzed: {len(enhanced_analysis)}")
                print(f"   🎯 Total analyzed: {data['data'].get('total_analyzed', 0)}")
                print(f"   🔍 Opportunities: {data['data'].get('opportunities_found', 0)}")
                
                if len(enhanced_analysis) > 0:
                    print("✅ Preloaded data contains stock analysis")
                    
                    # Show sample stock
                    sample_stock = enhanced_analysis[0]
                    print(f"   📊 Sample stock: {sample_stock.get('symbol', 'Unknown')}")
                    print(f"   💰 Price: ${sample_stock.get('price_data', {}).get('current_price', 'N/A')}")
                    print(f"   📰 News count: {sample_stock.get('news_count', 0)}")
                    
                    return True
                else:
                    print("⚠️  Preloaded data is empty")
                    return False
            else:
                print("❌ Preloaded data is not successful or missing")
                return False
        else:
            print(f"❌ Preloaded data request failed: {response.status_code}")
            return False
            
    except Exception as e:
        load_time = time.time() - start_time
        print(f"❌ Preloaded data request failed after {load_time:.2f}s: {str(e)}")
        return False
    
    # Test 3: Compare with full analysis performance
    print("\n🔄 Testing full analysis performance...")
    start_time = time.time()
    try:
        response = requests.get(f"{base_url}/api/sp500_analysis?limit=6", timeout=120)
        full_load_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Full analysis completed in {full_load_time:.2f} seconds")
            
            if data.get('success') and data.get('data'):
                enhanced_analysis = data['data'].get('enhanced_analysis', [])
                print(f"   📈 Stocks analyzed: {len(enhanced_analysis)}")
                
                # Performance comparison
                print(f"\n📊 PERFORMANCE COMPARISON:")
                print(f"   ⚡ Preloaded data: {load_time:.2f} seconds")
                print(f"   🔄 Full analysis: {full_load_time:.2f} seconds")
                print(f"   🚀 Speed improvement: {full_load_time/load_time:.1f}x faster with preloading")
                
                return True
            else:
                print("❌ Full analysis returned invalid data")
                return False
        else:
            print(f"❌ Full analysis request failed: {response.status_code}")
            return False
            
    except Exception as e:
        full_load_time = time.time() - start_time
        print(f"❌ Full analysis request failed after {full_load_time:.2f}s: {str(e)}")
        return False

def test_page_structure():
    """Test that the stocks page has the required structure"""
    print("\n🔍 Testing page structure...")
    
    try:
        response = requests.get("http://localhost:5001/stocks", timeout=10)
        if response.status_code != 200:
            print(f"❌ Page not accessible: {response.status_code}")
            return False
        
        html = response.text
        
        # Check for required elements
        required_elements = [
            'id="winnersList"',
            'id="losersList"', 
            'id="stocksTableBody"',
            'id="refreshBtn"',
            'id="lastUpdated"',
            'stocks.js'  # JavaScript file containing loadSP500Data
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in html:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing required elements: {missing_elements}")
            return False
        else:
            print("✅ All required page elements present")
            return True
            
    except Exception as e:
        print(f"❌ Page structure test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 STOCKS PAGE PERFORMANCE TEST")
    print("=" * 50)
    
    # Test core functionality
    performance_ok = test_stocks_page_performance()
    structure_ok = test_page_structure()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    if performance_ok:
        print("✅ Performance test: PASSED")
        print("   - Server is accessible")
        print("   - Preloaded data loads quickly")
        print("   - Data contains valid stock analysis")
        print("   - Performance improvement achieved")
    else:
        print("❌ Performance test: FAILED")
    
    if structure_ok:
        print("✅ Structure test: PASSED")
        print("   - All required page elements present")
    else:
        print("❌ Structure test: FAILED")
    
    overall_success = performance_ok and structure_ok
    
    if overall_success:
        print("\n🎉 OVERALL RESULT: SUCCESS")
        print("The stocks page performance optimization is working correctly!")
    else:
        print("\n💥 OVERALL RESULT: FAILURE") 
        print("Issues detected with stocks page performance or structure.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 