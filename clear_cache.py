#!/usr/bin/env python3
"""
Simple cache clearing script
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from core.cache import clear_cache
    print("🧹 Clearing application cache...")
    
    success = clear_cache()
    if success:
        print("✅ Cache cleared successfully")
    else:
        print("❌ Failed to clear cache")
        
except Exception as e:
    print(f"❌ Error clearing cache: {e}")
    print("Make sure you're in the project root directory")
