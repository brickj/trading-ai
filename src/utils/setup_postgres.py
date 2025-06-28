#!/usr/bin/env python3
"""
PostgreSQL Database Setup Script for Trading AI Platform.
Creates database, user, and cache table structure.
"""

import psycopg2
import sys
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from src.core.config import Config

def create_database_and_user():
    """Create PostgreSQL database and user for Trading AI."""
    
    print("🗄️ Setting up PostgreSQL database for Trading AI...")
    
    # Default connection to postgres database as superuser
    admin_conn_params = {
        'host': Config.DB_HOST,
        'port': Config.DB_PORT,
        'database': 'postgres',  # Connect to default postgres database
        'user': 'postgres',      # Default superuser
        'password': input("Enter PostgreSQL superuser (postgres) password: ")
    }
    
    try:
        # Connect as superuser
        conn = psycopg2.connect(**admin_conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print(f"📋 Creating database: {Config.DB_NAME}")
        
        # Check if database exists
        cur.execute("""
            SELECT 1 FROM pg_database WHERE datname = %s
        """, (Config.DB_NAME,))
        
        if cur.fetchone():
            print(f"⚠️ Database '{Config.DB_NAME}' already exists")
        else:
            # Create database
            cur.execute(f'CREATE DATABASE {Config.DB_NAME}')
            print(f"✅ Database '{Config.DB_NAME}' created successfully")
        
        # Check if user exists
        cur.execute("""
            SELECT 1 FROM pg_roles WHERE rolname = %s
        """, (Config.DB_USER,))
        
        if cur.fetchone():
            print(f"⚠️ User '{Config.DB_USER}' already exists")
        else:
            # Create user
            cur.execute(f"""
                CREATE USER {Config.DB_USER} WITH PASSWORD '{Config.DB_PASSWORD}'
            """)
            print(f"✅ User '{Config.DB_USER}' created successfully")
        
        # Grant privileges
        cur.execute(f'GRANT ALL PRIVILEGES ON DATABASE {Config.DB_NAME} TO {Config.DB_USER}')
        print(f"✅ Granted all privileges on '{Config.DB_NAME}' to '{Config.DB_USER}'")
        
        # Connect to the new database and grant schema privileges
        cur.execute(f'\\c {Config.DB_NAME}')
        cur.execute(f'GRANT ALL ON SCHEMA public TO {Config.DB_USER}')
        print(f"✅ Granted schema privileges to '{Config.DB_USER}'")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False

def create_cache_table():
    """Create the cache table structure."""
    
    print(f"📋 Creating cache table: {Config.CACHE_TABLE_NAME}")
    
    try:
        # Connect to the trading database
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        
        cur = conn.cursor()
        
        # Create cache table
        cur.execute(f'''
            CREATE TABLE IF NOT EXISTS {Config.CACHE_TABLE_NAME} (
                cache_key VARCHAR(500) PRIMARY KEY,
                data JSONB NOT NULL,
                category VARCHAR(100) DEFAULT 'general',
                created_at TIMESTAMP DEFAULT NOW(),
                expires_at TIMESTAMP NOT NULL,
                access_count INTEGER DEFAULT 1,
                last_accessed TIMESTAMP DEFAULT NOW()
            );
        ''')
        
        # Create indexes for performance
        cur.execute(f'''
            CREATE INDEX IF NOT EXISTS idx_{Config.CACHE_TABLE_NAME}_expiry 
            ON {Config.CACHE_TABLE_NAME}(expires_at);
        ''')
        
        cur.execute(f'''
            CREATE INDEX IF NOT EXISTS idx_{Config.CACHE_TABLE_NAME}_category 
            ON {Config.CACHE_TABLE_NAME}(category);
        ''')
        
        cur.execute(f'''
            CREATE INDEX IF NOT EXISTS idx_{Config.CACHE_TABLE_NAME}_created 
            ON {Config.CACHE_TABLE_NAME}(created_at);
        ''')
        
        conn.commit()
        print(f"✅ Cache table '{Config.CACHE_TABLE_NAME}' created with indexes")
        
        # Test cache functionality
        print("🧪 Testing cache functionality...")
        
        from src.core.cache import get_cache
        cache = get_cache()
        
        # Test cache operations
        test_key = "setup_test"
        test_data = {"test": True, "timestamp": "2024-01-01"}
        
        # Set test data
        success = cache.set(test_key, test_data, timeout=60, category="test")
        if success:
            print("✅ Cache SET operation successful")
        else:
            print("❌ Cache SET operation failed")
            return False
        
        # Get test data
        retrieved_data = cache.get(test_key)
        if retrieved_data and retrieved_data.get("test") == True:
            print("✅ Cache GET operation successful")
        else:
            print("❌ Cache GET operation failed")
            return False
        
        # Clean up test data
        cache.delete(test_key)
        print("✅ Cache DELETE operation successful")
        
        # Get cache stats
        stats = cache.get_stats()
        print(f"📊 Cache statistics: {stats}")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating cache table: {e}")
        return False

def test_database_connection():
    """Test database connection with the trading user."""
    
    print("🧪 Testing database connection...")
    
    try:
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        
        cur = conn.cursor()
        cur.execute('SELECT version()')
        version = cur.fetchone()[0]
        print(f"✅ Database connection successful!")
        print(f"📋 PostgreSQL version: {version}")
        
        # Test table access
        cur.execute(f'''
            SELECT COUNT(*) FROM {Config.CACHE_TABLE_NAME}
        ''')
        count = cur.fetchone()[0]
        print(f"📊 Cache table has {count} entries")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def create_recommendations_table():
    """Create the recommendations table structure."""
    
    print(f"📋 Creating recommendations table: recommendations")
    
    try:
        # Connect to the trading database
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        
        cur = conn.cursor()
        
        # Create recommendations table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS recommendations (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                recommendation_type VARCHAR(50), 
                action VARCHAR(10),
                strike_price DECIMAL(10,2),
                days_to_expiry INTEGER,
                option_price DECIMAL(10,2),
                sentiment_confidence DECIMAL(5,4),
                historical_confidence DECIMAL(5,4),
                final_confidence DECIMAL(5,4),
                sentiment_score DECIMAL(5,4),
                current_stock_price DECIMAL(10,2),
                reasoning TEXT,
                actual_outcome DECIMAL(5,4),
                outcome_timestamp TIMESTAMP,
                profitable BOOLEAN
            );
        ''')
        
        # Create indexes for performance
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_recommendations_symbol 
            ON recommendations(symbol);
        ''')
        
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_recommendations_timestamp 
            ON recommendations(timestamp);
        ''')
        
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_recommendations_action 
            ON recommendations(action);
        ''')
        
        conn.commit()
        print(f"✅ Recommendations table 'recommendations' created with indexes")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating recommendations table: {e}")
        return False

def main():
    """Main setup routine."""
    
    print("🚀 PostgreSQL Database Setup for Trading AI Platform")
    print("=" * 60)
    
    print(f"📋 Configuration:")
    print(f"   Host: {Config.DB_HOST}:{Config.DB_PORT}")
    print(f"   Database: {Config.DB_NAME}")
    print(f"   User: {Config.DB_USER}")
    print(f"   Cache Table: {Config.CACHE_TABLE_NAME}")
    print()
    
    # Step 1: Create database and user
    print("Step 1: Creating database and user...")
    if not create_database_and_user():
        print("❌ Database setup failed!")
        sys.exit(1)
    print()
    
    # Step 2: Test connection
    print("Step 2: Testing database connection...")
    if not test_database_connection():
        print("❌ Connection test failed!")
        sys.exit(1)
    print()
    
    # Step 3: Create cache table
    print("Step 3: Creating cache table and testing...")
    if not create_cache_table():
        print("❌ Cache table setup failed!")
        sys.exit(1)
    print()
    
    # Step 4: Create recommendations table
    print("Step 4: Creating recommendations table...")
    if not create_recommendations_table():
        print("❌ Recommendations table setup failed!")
        sys.exit(1)
    print()
    
    print("🎉 PostgreSQL setup completed successfully!")
    print()
    print("📋 Next steps:")
    print("1. Start your Trading AI application")
    print("2. The PostgreSQL cache will be used automatically")
    print("3. Monitor cache performance at /api/performance_status")
    print()
    print("⚡ Performance benefits:")
    print("- Persistent cache across application restarts")
    print("- Concurrent access from multiple processes")
    print("- Automatic expiry and cleanup")
    print("- Detailed cache statistics and monitoring")
    print("- Better memory usage and performance")
    print("- Recommendation tracking for enhanced backtesting")

if __name__ == "__main__":
    main() 