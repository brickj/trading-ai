#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_function_direct():
    print("🧪 Testing analyze_single_stock Function Directly")
    print("=" * 50)
    
    try:
        from src.web.app import analyze_single_stock
        print("✅ Successfully imported analyze_single_stock function")
        
        # Call the function directly
        result = analyze_single_stock("AAPL")
        print(f"✅ Function call completed")
        print(f"📋 Result type: {type(result)}")
        
        if isinstance(result, dict):
            print(f"📋 Result keys: {list(result.keys())}")
            has_options = 'options_recommendation' in result
            print(f"✅ Has options_recommendation: {has_options}")
            
            if has_options:
                options = result['options_recommendation']
                if isinstance(options, dict):
                    print(f"📋 Options action: {options.get('action', 'N/A')}")
                else:
                    print(f"📋 Options type: {type(options)}")
                print("🎉 SUCCESS: Function includes options_recommendation!")
            else:
                print("❌ FAILED: Function does NOT include options_recommendation")
                print(f"📋 Available fields: {list(result.keys())}")
        else:
            print(f"❌ Function returned non-dict: {result}")
            
    except Exception as e:
        print(f"❌ Function call failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_function_direct() 