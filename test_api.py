#!/usr/bin/env python3
import requests
import json
import sys
import pprint

def test_standard_analysis():
    """Test the standard analysis endpoint"""
    print("Testing standard analysis...")
    url = "http://localhost:5001/api/analyze_stock"
    payload = {"symbol": "AAPL", "ai_provider": "ollama"}
    headers = {"Content-Type": "application/json"}
    
    try:
        print(f"Sending request to {url} with payload: {payload}")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Check if response is successful
        if data.get("status") != "success":
            print(f"❌ API returned error: {data}")
            return False
            
        result = data.get("data", {})
        print("\nAPI Response Keys:")
        print(list(result.keys()))
        
        # Check for required fields
        required_fields = [
            "symbol", 
            "current_price",
            "sentiment_score", 
            "confidence",
            "action"
        ]
        
        missing_fields = [field for field in required_fields if field not in result]
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
            
        # Check for position recommendations
        if "position_recommendations" not in result:
            print("❌ Missing position_recommendations")
            return False
        
        # Check if position_recommendations has valid data
        position_recs = result.get("position_recommendations", {})
        print("\nPosition Recommendations:")
        pprint.pprint(position_recs)
        
        if not position_recs or "$1000" not in position_recs:
            print(f"❌ Invalid position_recommendations: {position_recs}")
            return False
            
        # Check for day trading notes
        if "day_trading_notes" not in result:
            print("❌ Missing day_trading_notes")
            return False
            
        # Check if day_trading_notes has valid data
        day_trading_notes = result.get("day_trading_notes", [])
        print("\nDay Trading Notes:")
        pprint.pprint(day_trading_notes)
        
        if not day_trading_notes or len(day_trading_notes) < 1:
            print(f"❌ Invalid day_trading_notes: {day_trading_notes}")
            return False
            
        # Check for template variables in day_trading_notes
        for note in day_trading_notes:
            if "{" in note or "}" in note:
                print(f"❌ Template variable found in note: {note}")
                return False
                
        # Check for template variables in position_recommendations
        for key in position_recs.keys():
            if "${" in key:
                print(f"❌ Template variable found in position key: {key}")
                return False
                
        print("✅ Standard analysis test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing standard analysis: {str(e)}")
        return False

def test_enhanced_analysis():
    """Test the enhanced analysis endpoint"""
    print("\nTesting enhanced analysis...")
    url = "http://localhost:5001/api/enhanced_analysis"
    payload = {"symbol": "AAPL", "ai_provider": "ollama"}
    headers = {"Content-Type": "application/json"}
    
    try:
        print(f"Sending request to {url} with payload: {payload}")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Check if response is successful
        if data.get("status") != "success":
            print(f"❌ API returned error: {data}")
            return False
            
        result = data.get("data", {})
        print("\nEnhanced API Response Keys:")
        print(list(result.keys()))
        
        # Check for required fields based on actual API structure
        required_fields = [
            "symbol", 
            "price_data",
            "sentiment_analysis"
        ]
        
        missing_fields = [field for field in required_fields if field not in result]
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
            
        # Check if recommendations section exists
        if not any(key.endswith('recommendations') for key in result.keys()):
            print(f"❌ Missing recommendations section in response")
            return False
            
        # Check for stock_recommendations or options_recommendations
        if 'recommendations' in result:
            recommendations = result.get("recommendations", [])
            if not recommendations or not isinstance(recommendations, list) or len(recommendations) == 0:
                print(f"❌ Invalid recommendations: {recommendations}")
                return False
        elif 'stock_recommendations' in result:
            stock_recommendations = result.get("stock_recommendations", [])
            if not stock_recommendations or not isinstance(stock_recommendations, list) or len(stock_recommendations) == 0:
                print(f"❌ Invalid stock_recommendations: {stock_recommendations}")
                return False
        elif 'options_recommendations' in result:
            options_recommendations = result.get("options_recommendations", [])
            if not options_recommendations or not isinstance(options_recommendations, list) or len(options_recommendations) == 0:
                print(f"❌ Invalid options_recommendations: {options_recommendations}")
                return False
        else:
            print(f"❌ No recommendations found in response")
            return False
            
        print("✅ Enhanced analysis test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing enhanced analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    standard_result = test_standard_analysis()
    enhanced_result = test_enhanced_analysis()
    
    if standard_result and enhanced_result:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
