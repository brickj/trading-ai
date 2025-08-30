#!/usr/bin/env python3
"""
Clear specific cache keys for stocks page
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from core.cache import cache
    
    # Clear specific cache keys
    keys_to_clear = [
        "sp500_analysis",
        "top_gainers_losers_3",
        "sp500_analysis_service"
    ]
    
    print("🧹 Clearing specific cache keys for stocks page...")
    
    for key in keys_to_clear:
        try:
            # Generate the hash for the key
            import hashlib
            key_hash = hashlib.sha256(key.encode()).hexdigest()
            
            # Delete from cache using the database connection directly
            from core.database import get_db_connection
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM api_cache WHERE key_hash = %s", (key_hash,))
                    deleted = cursor.rowcount
                    conn.commit()
                    
            if deleted > 0:
                print(f"✅ Cleared cache key: {key}")
            else:
                print(f"ℹ️  Cache key not found: {key}")
                
        except Exception as e:
            print(f"⚠️  Error clearing {key}: {e}")
    
    print("🎯 Specific cache clearing complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Make sure you're in the project root directory")
