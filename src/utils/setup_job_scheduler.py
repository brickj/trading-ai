#!/usr/bin/env python3
"""
Job Scheduler Setup Script
==========================

This script initializes the job_schedules table with default jobs for
preloading opportunities data each trading day.
"""

import sys
import os
from datetime import time

# Add project root to path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

from src.core.database import get_db_connection, ensure_job_schedules_table


def setup_default_jobs():
    """Set up default job schedules for the trading platform"""

    # Ensure the job_schedules table exists
    ensure_job_schedules_table()

    # Default jobs configuration
    default_jobs = [
        {
            "job_name": "preload_news_opportunities",
            "run_time": time(9, 40),  # 9:40 AM ET
            "enabled": True,
            "description": "Preload news-driven trading opportunities",
        },
        {
            "job_name": "preload_watchlist_opportunities",
            "run_time": time(9, 45),  # 9:45 AM ET
            "enabled": True,
            "description": "Preload watchlist-based trading opportunities",
        },
        {
            "job_name": "preload_stock_data",
            "run_time": time(9, 35),  # 9:35 AM ET
            "enabled": True,
            "description": "Preload S&P 500 market movers data",
        },
        {
            "job_name": "run_scalping_analysis",
            "run_time": time(9, 55),  # 9:55 AM ET
            "enabled": True,
            "description": "Run scalping analysis for short-term opportunities",
        },
        {
            "job_name": "populate_weekly_plan",
            "run_time": time(2, 0),  # 2:00 AM ET (Monday mornings)
            "enabled": True,
            "description": "Populate weekly market calendar data (earnings, economic events, Fed meetings)",
        },
    ]

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for job in default_jobs:
                    # Insert or update job schedule
                    cur.execute(
                        """
                        INSERT INTO job_schedules (job_name, run_time, enabled)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (job_name) DO UPDATE SET 
                            run_time = EXCLUDED.run_time,
                            enabled = EXCLUDED.enabled
                    """,
                        (job["job_name"], job["run_time"], job["enabled"]),
                    )

                    print(
                        f"✅ Configured job: {job['job_name']} at {job['run_time']} ({job['description']})"
                    )

                conn.commit()

        print(f"\n🎉 Successfully configured {len(default_jobs)} default jobs!")
        print("\n📅 Job Schedule (Eastern Time):")
        print("  2:00 AM - Weekly Market Plan Population (Mondays)")
        print("  9:35 AM - S&P 500 Preload")
        print("  9:40 AM - News-Driven Opportunities")
        print("  9:45 AM - Watchlist Opportunities")
        print("  9:55 AM - Scalping Analysis")
        print("\n💡 Daily jobs run Monday-Friday on trading days.")
        print("   Weekly jobs run Monday mornings to refresh market calendar.")
        print("   You can modify schedules via the System Status page.")

    except Exception as e:
        print(f"❌ Error setting up job schedules: {e}")
        return False

    return True


def verify_job_setup():
    """Verify that jobs were set up correctly"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT job_name, run_time, enabled FROM job_schedules ORDER BY run_time"
                )
                jobs = cur.fetchall()

                if not jobs:
                    print("❌ No jobs found in database")
                    return False

                print("\n📋 Current Job Configuration:")
                for job_name, run_time, enabled in jobs:
                    status = "✅ Enabled" if enabled else "❌ Disabled"
                    print(f"  {run_time} - {job_name} ({status})")

                return True

    except Exception as e:
        print(f"❌ Error verifying job setup: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Setting up Trading AI Job Scheduler...")
    print("=" * 50)

    if setup_default_jobs():
        print("\n🔍 Verifying job setup...")
        if verify_job_setup():
            print("\n✅ Job scheduler setup completed successfully!")
            print("\n📝 Next steps:")
            print("  1. Start the application: python start_app.py")
            print("  2. Visit System Status page to manage job schedules")
            print("  3. Jobs will run automatically on trading days")
        else:
            print("\n❌ Job verification failed")
            sys.exit(1)
    else:
        print("\n❌ Job setup failed")
        sys.exit(1)
