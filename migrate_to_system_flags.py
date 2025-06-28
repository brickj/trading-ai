#!/usr/bin/env python3
"""
Migration script to move from file-based flags to database-based system_flags.
This script is safe to run multiple times and won't break existing functionality.
"""

import os
import sys
import psycopg2
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.config import Config
from src.core.database import get_db_connection
from src.core.logger import log_error, log_system_event

def create_system_flags_table():
    """Create the system_flags table if it doesn't exist."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                print("❌ Cannot connect to database")
                return False
            
            with conn.cursor() as cur:
                # Create system_flags table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS system_flags (
                        flag_name VARCHAR(100) PRIMARY KEY,
                        flag_value TEXT NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                
                # Create index for performance
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_system_flags_updated
                    ON system_flags(updated_at);
                """)
                
                conn.commit()
                print("✅ System flags table created successfully")
                return True
                
    except Exception as e:
        print(f"❌ Error creating system_flags table: {e}")
        log_error(f"Migration failed - system_flags table creation: {e}")
        return False

def migrate_file_flags_to_database():
    """Migrate existing file-based flags to database."""
    migrations = [
        {
            'file': '.historical_data_2year_update_date',
            'flag_name': 'historical_data_2year_update_date',
            'description': 'Date when 2-year historical data check was last performed'
        },
        {
            'file': '.sp500_update_date',
            'flag_name': 'sp500_update_date', 
            'description': 'Date when S&P 500 symbols table was last updated'
        }
    ]
    
    migrated_count = 0
    
    for migration in migrations:
        file_path = migration['file']
        flag_name = migration['flag_name']
        description = migration['description']
        
        # Check if file exists
        if os.path.exists(file_path):
            try:
                # Read the file content
                with open(file_path, 'r') as f:
                    flag_value = f.read().strip()
                
                # Insert into database
                with get_db_connection() as conn:
                    if conn is None:
                        continue
                    
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO system_flags (flag_name, flag_value, description, updated_at)
                            VALUES (%s, %s, %s, NOW())
                            ON CONFLICT (flag_name) 
                            DO UPDATE SET flag_value = EXCLUDED.flag_value, updated_at = NOW()
                        """, (flag_name, flag_value, description))
                        conn.commit()
                
                print(f"✅ Migrated {file_path} -> {flag_name} = {flag_value}")
                migrated_count += 1
                
            except Exception as e:
                print(f"❌ Failed to migrate {file_path}: {e}")
                log_error(f"Migration failed for {file_path}: {e}")
    
    return migrated_count

def test_system_flags():
    """Test the system_flags functionality."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return False
            
            with conn.cursor() as cur:
                # Test setting a flag
                cur.execute("""
                    INSERT INTO system_flags (flag_name, flag_value, description)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (flag_name) 
                    DO UPDATE SET flag_value = EXCLUDED.flag_value, updated_at = NOW()
                """, ("migration_test", "2024-01-01", "Test flag for migration verification"))
                
                # Test getting a flag
                cur.execute("SELECT flag_value FROM system_flags WHERE flag_name = %s", ("migration_test",))
                result = cur.fetchone()
                
                if result and result[0] == "2024-01-01":
                    print("✅ System flags functionality test passed")
                    
                    # Clean up test data
                    cur.execute("DELETE FROM system_flags WHERE flag_name = %s", ("migration_test",))
                    conn.commit()
                    return True
                else:
                    print("❌ System flags functionality test failed")
                    return False
                    
    except Exception as e:
        print(f"❌ System flags test failed: {e}")
        return False

def main():
    """Run the migration safely."""
    print("🔄 Starting migration to database-based system flags...")
    print("=" * 60)
    
    # Step 1: Create the system_flags table
    print("Step 1: Creating system_flags table...")
    if not create_system_flags_table():
        print("❌ Migration failed at step 1")
        return False
    
    # Step 2: Test the functionality
    print("\nStep 2: Testing system_flags functionality...")
    if not test_system_flags():
        print("❌ Migration failed at step 2")
        return False
    
    # Step 3: Migrate existing file flags
    print("\nStep 3: Migrating existing file-based flags...")
    migrated_count = migrate_file_flags_to_database()
    print(f"✅ Migrated {migrated_count} file-based flags to database")
    
    # Step 4: Show current system flags
    print("\nStep 4: Current system flags in database:")
    try:
        with get_db_connection() as conn:
            if conn is None:
                return False
            
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT flag_name, flag_value, description, updated_at 
                    FROM system_flags 
                    ORDER BY updated_at DESC
                """)
                results = cur.fetchall()
                
                if results:
                    for row in results:
                        print(f"   • {row[0]} = {row[1]} ({row[2]}) - Updated: {row[3]}")
                else:
                    print("   No system flags found in database")
                    
    except Exception as e:
        print(f"❌ Error listing system flags: {e}")
    
    print("\n🎉 Migration completed successfully!")
    print("\n📝 Next steps:")
    print("   1. The system_flags table is now ready")
    print("   2. Existing file-based flags have been migrated")
    print("   3. You can now safely delete the .historical_data_2year_update_date file")
    print("   4. Update the startup.py code to use database flags (optional)")
    
    log_system_event("Migration to database-based system flags completed successfully")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 