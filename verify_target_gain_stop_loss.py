#!/usr/bin/env python3
"""
Direct test to verify that target_gain and stop_loss fields are correctly populated
in the analyze_single_stock function output.
"""
import sys
import os
import json
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the analyze_single_stock function directly
from src.web.app import analyze_single_stock

def test_analyze_single_stock_fields():
    """Test that analyze_single_stock correctly populates target_gain and stop_loss fields"""
    print("Testing analyze_single_stock function directly...")
    
    try:
        # Call analyze_single_stock directly with a test symbol
        symbol = "AAPL"
        result = analyze_single_stock(symbol)
        
        # Check if result is a dictionary
        if not isinstance(result, dict):
            print(f"❌ ERROR: Result is not a dictionary: {type(result)}")
            return False
        
        # Print the keys in the result
        print(f"Result keys: {list(result.keys())}")
        
        # Check if target_gain and stop_loss fields are present
        target_gain_present = "target_gain" in result
        stop_loss_present = "stop_loss" in result
        
        # Get the values
        target_gain = result.get("target_gain", None)
        stop_loss = result.get("stop_loss", None)
        
        print(f"Target Gain present: {target_gain_present}, value: {target_gain}")
        print(f"Stop Loss present: {stop_loss_present}, value: {stop_loss}")
        
        # Check if the values are properly populated (not empty or None)
        target_gain_valid = target_gain_present and target_gain is not None and target_gain != ""
        stop_loss_valid = stop_loss_present and stop_loss is not None and stop_loss != ""
        
        # Save the result to a file for inspection
        with open("direct_test_result.json", "w") as f:
            json.dump(result, f, indent=2, default=str)
        print("Saved result to direct_test_result.json")
        
        # Print the test results
        print("\nTest Results:")
        print(f"Target Gain field present: {target_gain_present}")
        print(f"Target Gain populated: {target_gain_valid}")
        print(f"Stop Loss field present: {stop_loss_present}")
        print(f"Stop Loss populated: {stop_loss_valid}")
        
        # Overall test result
        if target_gain_valid and stop_loss_valid:
            print("\n✅ TEST PASSED: analyze_single_stock correctly populates target_gain and stop_loss fields")
            return True
        else:
            print("\n❌ TEST FAILED: analyze_single_stock does not correctly populate target_gain and stop_loss fields")
            return False
            
    except Exception as e:
        print(f"Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_analyze_single_stock_fields()
