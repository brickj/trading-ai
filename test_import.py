#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_import():
    print("🧪 Testing OptionsStrategy Import")
    print("=" * 50)
    
    try:
        from src.trading.enhanced_trading_strategy import OptionsStrategy
        print("✅ Successfully imported OptionsStrategy")
        
        # Test creating an instance
        options_strategy = OptionsStrategy()
        print("✅ Successfully created OptionsStrategy instance")
        
        # Test the get_recommendation method
        test_data = {
            "symbol": "AAPL",
            "current_price": 196.58,
            "sentiment_score": -0.1,
            "confidence": 0.6
        }
        
        result = options_strategy.get_recommendation(
            "AAPL", 
            {"current_price": 196.58}, 
            {"sentiment_score": -0.1, "confidence": 0.6},
            {"action": "HOLD", "signal_strength": 0}
        )
        
        print(f"✅ Successfully called get_recommendation")
        print(f"📋 Result type: {type(result)}")
        print(f"📋 Result keys: {list(result.keys()) if isinstance(result, dict) else 'not dict'}")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_import() 