#!/usr/bin/env python3
"""
Script to populate market_movers table with valid data
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.resolve()
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from src.web.app import preload_stock_data

def main():
    print("Starting market_movers population...")
    try:
        preload_stock_data()
        print("✅ Successfully populated market_movers table")
    except Exception as e:
        print(f"❌ Error populating market_movers: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 