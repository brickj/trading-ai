#!/usr/bin/env python3
"""
Debug database connection
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_psycopg_connection():
    """Test direct psycopg connection"""
    try:
        import psycopg2
        from src.core.config import Config
        
        # Direct psycopg2 connection
        conn = psycopg2.connect(
            host="127.0.0.1",
            port="5432",
            database="trading_db",
            user="trading_user",
            password="trading_password"
        )
        
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM market_movers")
            count = cur.fetchone()[0]
            print(f"Direct psycopg2 connection: {count} rows")
            
            cur.execute("SELECT symbol, type, change_percent FROM market_movers ORDER BY timestamp DESC LIMIT 3")
            rows = cur.fetchall()
            for row in rows:
                print(f"  {row[0]}: {row[1]} ({row[2]}%)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Direct psycopg2 error: {e}")
        return False

def test_app_connection():
    """Test app's database connection"""
    try:
        from src.core.database import get_db_connection
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM market_movers")
                count = cur.fetchone()[0]
                print(f"App's get_db_connection: {count} rows")
                
                cur.execute("SELECT symbol, type, change_percent FROM market_movers ORDER BY timestamp DESC LIMIT 3")
                rows = cur.fetchall()
                for row in rows:
                    print(f"  {row[0]}: {row[1]} ({row[2]}%)")
        
        return True
        
    except Exception as e:
        print(f"App's connection error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test config values"""
    try:
        from src.core.config import Config
        print(f"Database URL: {Config.DATABASE_URL}")
        return True
    except Exception as e:
        print(f"Config error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Database Connections...")
    print("=" * 40)
    
    print("\n1. Testing config...")
    test_config()
    
    print("\n2. Testing direct psycopg2 connection...")
    test_psycopg_connection()
    
    print("\n3. Testing app's database connection...")
    test_app_connection()
