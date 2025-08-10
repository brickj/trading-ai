#!/usr/bin/env python3

from src.core.database import get_db_connection
from datetime import date
import traceback

def test_weekly_plan():
    try:
        print("Testing database connection...")
        with get_db_connection() as conn:
            print("Database connection successful")
            with conn.cursor() as cursor:
                print("Executing query...")
                cursor.execute('SELECT COUNT(*) as count FROM weekly_plan_events WHERE week_start_date = %s', (date(2025, 8, 4),))
                result = cursor.fetchone()
                count = result['count']
                print(f'Count for week 2025-08-04: {count}')
                
                cursor.execute('SELECT event_date, event_name, event_type FROM weekly_plan_events WHERE week_start_date = %s', (date(2025, 8, 4),))
                events = cursor.fetchall()
                print(f'Events: {events}')
                
    except Exception as e:
        print(f'Error: {e}')
        print(f'Error type: {type(e)}')
        traceback.print_exc()

if __name__ == "__main__":
    test_weekly_plan()
