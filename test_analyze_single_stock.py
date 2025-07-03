#!/usr/bin/env python3
"""
Test script to directly check the analyze_single_stock function and debug the target_gain and stop_loss fields
"""
import sys
import os
import json
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the analyze_single_stock function
from src.web.app import analyze_single_stock

def main():
    """Test the analyze_single_stock function directly"""
    print("Testing analyze_single_stock function directly...")
    
    # Call analyze_single_stock with a test symbol
    symbol = "AAPL"
    result = analyze_single_stock(symbol)
    
    # Print the result
    print(f"\nResult type: {type(result)}")
    print(f"Result keys: {list(result.keys())}")
    
    # Check specifically for target_gain and stop_loss
    print(f"\ntarget_gain: '{result.get('target_gain', 'NOT FOUND')}'")
    print(f"stop_loss: '{result.get('stop_loss', 'NOT FOUND')}'")
    
    # Save the result to a file
    with open("direct_analyze_result.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\nFull result saved to direct_analyze_result.json")

if __name__ == "__main__":
    main()
