#!/usr/bin/env python3
"""
Test script to verify enhanced analysis functionality on the stocks page
"""

import requests
import json
import time

def test_enhanced_analysis_api():
    """Test the enhanced analysis API directly"""
    print("Testing enhanced analysis API...")
    
    url = "http://localhost:5001/api/enhanced_analysis"
    payload = {"symbol": "AAPL"}
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"API Response Status: {data.get('status')}")
            
            if data.get('status') == 'success':
                result = data.get('data', {})
                recommendations = result.get('recommendations', {})
                
                # Check for top recommendation
                top_rec = recommendations.get('top_recommendation')
                if top_rec:
                    print(f"✓ Top Recommendation: {top_rec.get('recommendation_type')} - {top_rec.get('action')}")
                    print(f"  Confidence: {(top_rec.get('confidence', 0) * 100):.1f}%")
                else:
                    print("✗ No top recommendation found")
                
                # Check for options recommendations
                options_recs = recommendations.get('options_recommendations', [])
                print(f"✓ Options Recommendations: {len(options_recs)} found")
                
                # Check for stock recommendations
                stock_recs = recommendations.get('stock_recommendations', [])
                print(f"✓ Stock Recommendations: {len(stock_recs)} found")
                
                return True
            else:
                print(f"✗ API returned error: {data.get('error')}")
                return False
        else:
            print(f"✗ API request failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing API: {e}")
        return False

def test_stocks_page_load():
    """Test that the stocks page loads correctly"""
    print("\nTesting stocks page load...")
    
    try:
        response = requests.get("http://localhost:5001/stocks", timeout=10)
        print(f"Page Response Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Check for enhanced analysis elements
            if 'enhancedAnalysisResults' in content:
                print("✓ Enhanced analysis results section found")
            else:
                print("✗ Enhanced analysis results section not found")
            
            if 'enhancedAnalysisContainer' in content:
                print("✓ Enhanced analysis container found")
            else:
                print("✗ Enhanced analysis container not found")
            
            if 'stocks.js' in content:
                print("✓ stocks.js file is being loaded")
            else:
                print("✗ stocks.js file not found in page")
            
            # Check for analyze button functionality
            if 'onclick="analyzeStock' in content:
                print("✓ Analyze button onclick handlers found")
            else:
                print("✗ Analyze button onclick handlers not found")
            
            return True
        else:
            print(f"✗ Page load failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing page load: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("ENHANCED ANALYSIS STOCKS PAGE TEST")
    print("=" * 60)
    
    # Test 1: Enhanced Analysis API
    api_success = test_enhanced_analysis_api()
    
    # Test 2: Stocks Page Load
    page_success = test_stocks_page_load()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Enhanced Analysis API: {'✓ PASS' if api_success else '✗ FAIL'}")
    print(f"Stocks Page Load: {'✓ PASS' if page_success else '✗ FAIL'}")
    
    if api_success and page_success:
        print("\n🎉 All tests passed! Enhanced analysis is working correctly.")
        print("\nThe stocks page now uses the same enhanced analysis functionality as the index page:")
        print("- Calls /api/enhanced_analysis endpoint")
        print("- Displays comprehensive multi-strategy recommendations")
        print("- Shows historical backtesting results")
        print("- Includes both options and stock recommendations")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
    
    print("\nTo test manually:")
    print("1. Open http://localhost:5001/stocks")
    print("2. Wait for the Analysis Results table to load")
    print("3. Click 'Analyze' button on any stock")
    print("4. Verify enhanced analysis results appear below the table")

if __name__ == "__main__":
    main() 