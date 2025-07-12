#!/usr/bin/env python3
"""
Debug script for scalping API datetime serialization issue
"""

import sys
import os
sys.path.append('src')

from src.core.scalping_analyzer import scalping_analyzer
import json

def test_scalping_api():
    """Test the scalping API and see where the error occurs"""
    print("Testing scalping API...")
    
    try:
        # Test the API method directly
        result = scalping_analyzer.get_scalping_opportunities_api()
        print("API result:", result)
        
        # Try to serialize to JSON
        json_str = json.dumps(result)
        print("JSON serialization successful")
        print("JSON result:", json_str)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scalping_api() 