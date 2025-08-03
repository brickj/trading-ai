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
        "host": Config.DATABASE_CONFIG["host"],
        "port": Config.DATABASE_CONFIG["port"],
        "database": "postgres",  # Connect to default postgres database
        "user": "rick",  # Default superuser for local dev
        "password": "",  # Assume no password for local superuser
    }

    try:
        # Connect as superuser
        conn = psycopg2.connect(**admin_conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        print(f"📋 Creating database: {Config.DATABASE_CONFIG['database']}")

        # Check if database exists
        cur.execute(
            """
            SELECT 1 FROM pg_database WHERE datname = %s
        """,
            (Config.DATABASE_CONFIG["database"],),
        )

        if cur.fetchone():
            print(f"⚠️ Database '{Config.DATABASE_CONFIG['database']}' already exists")
        else:
            # Create database
            cur.execute(f"CREATE DATABASE {Config.DATABASE_CONFIG['database']}")
            print(
                f"✅ Database '{Config.DATABASE_CONFIG['database']}' created successfully"
            )

        # Check if user exists
        cur.execute(
            """
            SELECT 1 FROM pg_roles WHERE rolname = %s
        """,
            (Config.DATABASE_CONFIG["user"],),
        )

        if cur.fetchone():
            print(f"⚠️ User '{Config.DATABASE_CONFIG['user']}' already exists")
        else:
            # Create user
            cur.execute(f"""
                CREATE USER {Config.DATABASE_CONFIG["user"]} WITH PASSWORD '{Config.DATABASE_CONFIG["password"]}'
            """)
            print(f"✅ User '{Config.DATABASE_CONFIG['user']}' created successfully")

        # Grant privileges
        cur.execute(
            f"GRANT ALL PRIVILEGES ON DATABASE {Config.DATABASE_CONFIG['database']} TO {Config.DATABASE_CONFIG['user']}"
        )
        print(
            f"✅ Granted all privileges on '{Config.DATABASE_CONFIG['database']}' to '{Config.DATABASE_CONFIG['user']}'"
        )

        cur.close()
        conn.close()

        # Connect to the new database to grant schema privileges
        conn = psycopg2.connect(
            host=Config.DATABASE_CONFIG["host"],
            port=Config.DATABASE_CONFIG["port"],
            database=Config.DATABASE_CONFIG["database"],
            user=Config.DATABASE_CONFIG["user"],
            password=Config.DATABASE_CONFIG["password"],
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        cur.execute(f"GRANT ALL ON SCHEMA public TO {Config.DATABASE_CONFIG['user']}")
        print(f"✅ Granted schema privileges to '{Config.DATABASE_CONFIG['user']}'")

        cur.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False


def test_database_connection():
    """Test database connection with the trading user."""

    print("🧪 Testing database connection...")

    try:
        conn = psycopg2.connect(
            host=Config.DATABASE_CONFIG["host"],
            port=Config.DATABASE_CONFIG["port"],
            database=Config.DATABASE_CONFIG["database"],
            user=Config.DATABASE_CONFIG["user"],
            password=Config.DATABASE_CONFIG["password"],
        )

        cur = conn.cursor()
        cur.execute("SELECT version()")
        version_row = cur.fetchone()
        if not version_row:
            print("❌ Could not determine PostgreSQL version.")
            return False

        version = version_row[0]
        print("✅ Database connection successful!")
        print(f"📋 PostgreSQL version: {version}")

        # Test table access
        cur.execute("""
            SELECT COUNT(*) FROM api_cache
        """)
        count_row = cur.fetchone()
        if count_row is None:
            print("❌ Could not get count from api_cache table.")
            return False

        count = count_row[0]
        print(f"📊 Cache table has {count} entries")

        cur.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False


def create_recommendations_table():
    """Create the recommendations table structure."""

    print("📋 Creating recommendations table: recommendations")

    try:
        # Connect to the trading database
        conn = psycopg2.connect(
            host=Config.DATABASE_CONFIG["host"],
            port=Config.DATABASE_CONFIG["port"],
            database=Config.DATABASE_CONFIG["database"],
            user=Config.DATABASE_CONFIG["user"],
            password=Config.DATABASE_CONFIG["password"],
        )

        cur = conn.cursor()

        # Create recommendations table
        cur.execute("""
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
        """)

        # Create indexes for performance
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_recommendations_symbol 
            ON recommendations(symbol);
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_recommendations_timestamp 
            ON recommendations(timestamp);
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_recommendations_action 
            ON recommendations(action);
        """)

        conn.commit()
        print("✅ Recommendations table 'recommendations' created with indexes")

        cur.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ Error creating recommendations table: {e}")
        return False


def main():
    """Main function to run the setup."""
    print("🚀 PostgreSQL Database Setup for Trading AI Platform")
    print("============================================================")
    print("📋 Configuration:")
    print(f"   Host: {Config.DATABASE_CONFIG['host']}:{Config.DATABASE_CONFIG['port']}")
    print(f"   Database: {Config.DATABASE_CONFIG['database']}")
    print(f"   User: {Config.DATABASE_CONFIG['user']}")
    print("")

    if not create_database_and_user():
        sys.exit(1)

    if not create_recommendations_table():
        sys.exit(1)

    if not test_database_connection():
        sys.exit(1)

    print("\n🎉 All database setup steps completed successfully!")
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
