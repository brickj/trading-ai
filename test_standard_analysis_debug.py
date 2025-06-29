#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.web.app import analyze_single_stock

def test_standard_analysis():
    print("🧪 Testing Standard Analysis Debug Output")
    print("=" * 50)
    
    try:
        result = analyze_single_stock("AAPL")
        print(f"\n✅ Analysis completed successfully")
        print(f"📋 Result keys: {list(result.keys())}")
        print(f"🔍 Has options_recommendation: {'options_recommendation' in result}")
        
        if 'options_recommendation' in result:
            options = result['options_recommendation']
            if isinstance(options, dict):
                print(f"📋 Options recommendation keys: {list(options.keys())}")
                print(f"📋 Options action: {options.get('action', 'N/A')}")
            else:
                print(f"📋 Options recommendation type: {type(options)}")
                print(f"📋 Options recommendation value: {options}")
        else:
            print("❌ No options_recommendation found in result")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_standard_analysis() 