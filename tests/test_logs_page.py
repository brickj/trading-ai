"""
Test suite for the logs page functionality.
"""
import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

import pytest
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError

# Import database connection
from src.core.database import get_db_connection
from psycopg2.extras import RealDictCursor

class TestLogsPage:
    """Test suite for the logs page functionality."""
    
    def setup_method(self):
        """Setup test data before each test method."""
        # Ensure test directory exists
        os.makedirs("test-results", exist_ok=True)
        
        # Ensure logs table exists
        if not self._verify_database():
            self._create_logs_table()
        
        # Insert test data
        self._insert_test_logs()
        
        # Verify data was actually inserted
        self._verify_test_data_inserted()
    
    def teardown_method(self):
        """Clean up after each test method."""
        # Clean up test data
        self._cleanup_test_data()
    
    def _cleanup_test_data(self) -> None:
        """Clean up test data from the database."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM logs WHERE category = 'test';")
                    conn.commit()
                    print("Cleaned up test logs")
        except Exception as e:
            print(f"Error cleaning up test data: {e}")
    
    def _verify_database(self) -> bool:
        """Verify that the logs table exists and is accessible."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # A more robust way to check if a table exists
                    cur.execute("SELECT to_regclass('public.logs');")
                    table_exists_result = cur.fetchone()
                    if table_exists_result is None or table_exists_result[0] is None:
                        print("Logs table does not exist")
                        return False

                    # COUNT(*) should always return a row, but we check for None to be safe
                    cur.execute("SELECT COUNT(*) FROM logs;")
                    count_result = cur.fetchone()
                    if count_result is None:
                        print("Could not retrieve log count from database.")
                        return False

                    log_count = count_result[0]
                    print(f"Found {log_count} logs in database")
                    return True  # Table exists, even if empty
        except Exception as e:
            print(f"Error verifying database: {e}")
            return False
    
    def _create_logs_table(self) -> None:
        """Create the logs table if it doesn't exist."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS logs (
                            id SERIAL PRIMARY KEY,
                            timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                            level VARCHAR(20) NOT NULL,
                            logger VARCHAR(255),
                            module VARCHAR(255),
                            function VARCHAR(255),
                            line INTEGER,
                            message TEXT NOT NULL,
                            exception TEXT,
                            traceback TEXT,
                            extra JSONB,
                            category VARCHAR(100),
                            session_id VARCHAR(100)
                        );
                    """)
                    conn.commit()
                    print("Created logs table")
        except Exception as e:
            print(f"Error creating logs table: {e}")
            raise
    
    def _insert_test_logs(self) -> None:
        """Insert test logs into the database."""
        test_logs = [
            {
                'level': 'INFO',
                'message': 'Test info log message - Application started successfully',
                'category': 'test',
                'module': 'test_module',
                'function': 'test_function',
                'logger': 'test_logger'
            },
            {
                'level': 'ERROR',
                'message': 'Test error log message - Database connection failed',
                'category': 'test',
                'module': 'test_module',
                'function': 'test_error_function',
                'exception': 'TestException: Something went wrong',
                'logger': 'test_logger'
            },
            {
                'level': 'WARN',
                'message': 'Test warning message - High memory usage detected',
                'category': 'test',
                'module': 'test_module',
                'function': 'test_warning_function',
                'logger': 'test_logger'
            },
            {
                'level': 'DEBUG',
                'message': 'Test debug message - Processing user request',
                'category': 'test',
                'module': 'test_module',
                'function': 'test_debug_function',
                'logger': 'test_logger'
            },
            {
                'level': 'INFO',
                'message': 'Test info log message - User authentication successful',
                'category': 'test',
                'module': 'test_module',
                'function': 'test_auth_function',
                'logger': 'test_logger'
            }
        ]
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Clear existing test logs
                    cur.execute("DELETE FROM logs WHERE category = 'test';")
                    
                    # Insert test logs
                    for i, log in enumerate(test_logs):
                        cur.execute("""
                            INSERT INTO logs 
                            (level, message, category, module, function, exception, logger, timestamp)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW() - INTERVAL '%s minutes')
                        """, (
                            log['level'],
                            log['message'],
                            log['category'],
                            log.get('module'),
                            log.get('function'),
                            log.get('exception'),
                            log.get('logger'),
                            i  # Stagger timestamps
                        ))
                    
                    conn.commit()
                    print(f"Inserted {len(test_logs)} test logs")
        except Exception as e:
            print(f"Error inserting test logs: {e}")
            raise
    
    def _verify_test_data_inserted(self) -> None:
        """Verify that test data was actually inserted into the database."""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT COUNT(*) as count FROM logs WHERE category = 'test';")
                    count_result = cur.fetchone()
                    if count_result is None:
                        raise Exception("Could not get test log count from database")
                    
                    test_log_count = count_result['count']
                    print(f"Verified {test_log_count} test logs in database")
                    
                    if test_log_count == 0:
                        raise Exception("No test logs found in database after insertion")
                    
                    # Also verify total log count
                    cur.execute("SELECT COUNT(*) as count FROM logs;")
                    total_count_result = cur.fetchone()
                    if total_count_result is None:
                        raise Exception("Could not get total log count from database")
                    
                    total_log_count = total_count_result['count']
                    print(f"Total logs in database: {total_log_count}")
                    
                    if total_log_count == 0:
                        raise Exception("No logs found in database at all")
                        
        except Exception as e:
            print(f"Error verifying test data: {e}")
            raise
    
    def _get_logs_from_db(self) -> list:
        """Fetch all logs from the database."""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM logs WHERE category = 'test' ORDER BY timestamp DESC;")
                    return cur.fetchall()
        except Exception as e:
            print(f"Error fetching logs from database: {e}")
            raise
    
    def _insert_test_logs(self) -> None:
        """Insert test logs into the database."""
        test_logs = [
            {
                'level': 'INFO',
                'message': 'Test info log message - Application started successfully',
                'category': 'test',
                'module': 'test_module',
                'function': 'test_function',
                'logger': 'test_logger'
            },
            {
                'level': 'ERROR',
                'message': 'Test error log message - Database connection failed',
                'category': 'test',
                'module': 'test_module',
                'function': 'test_error_function',
                'exception': 'TestException: Something went wrong',
                'logger': 'test_logger'
            },
            {
                'level': 'WARN',
                'message': 'Test warning message - High memory usage detected',
                'category': 'test',
                'module': 'test_module',
                'function': 'test_warning_function',
                'logger': 'test_logger'
            },
            {
                'level': 'DEBUG',
                'message': 'Test debug message - Processing user request',
                'category': 'test',
                'module': 'test_module',
                'function': 'test_debug_function',
                'logger': 'test_logger'
            },
            {
                'level': 'INFO',
                'message': 'Test info log message - User authentication successful',
                'category': 'test',
                'module': 'test_module',
                'function': 'test_auth_function',
                'logger': 'test_logger'
            }
        ]
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Clear existing test logs
                    cur.execute("DELETE FROM logs WHERE category = 'test';")
                    
                    # Insert test logs
                    for i, log in enumerate(test_logs):
                        cur.execute("""
                            INSERT INTO logs 
                            (level, message, category, module, function, exception, logger, timestamp)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW() - INTERVAL '%s minutes')
                        """, (
                            log['level'],
                            log['message'],
                            log['category'],
                            log.get('module'),
                            log.get('function'),
                            log.get('exception'),
                            log.get('logger'),
                            i  # Stagger timestamps
                        ))
                    
                    conn.commit()
                    print(f"Inserted {len(test_logs)} test logs")
        except Exception as e:
            print(f"Error inserting test logs: {e}")
            raise
    
    def _verify_test_data_inserted(self) -> None:
        """Verify that test data was actually inserted into the database."""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT COUNT(*) as count FROM logs WHERE category = 'test';")
                    count_result = cur.fetchone()
                    if count_result is None:
                        raise Exception("Could not get test log count from database")
                    
                    test_log_count = count_result['count']
                    print(f"Verified {test_log_count} test logs in database")
                    
                    if test_log_count == 0:
                        raise Exception("No test logs found in database after insertion")
                    
                    # Also verify total log count
                    cur.execute("SELECT COUNT(*) as count FROM logs;")
                    total_count_result = cur.fetchone()
                    if total_count_result is None:
                        raise Exception("Could not get total log count from database")
                    
                    total_log_count = total_count_result['count']
                    print(f"Total logs in database: {total_log_count}")
                    
                    if total_log_count == 0:
                        raise Exception("No logs found in database at all")
                        
        except Exception as e:
            print(f"Error verifying test data: {e}")
            raise

    def test_logs_page_fully_populated(self, page: Page, base_url: str) -> None:
        """Test that the logs page is fully populated with log entries."""
        if not base_url:
            base_url = "http://localhost:5001"
        
        try:
            # Enable console logging for debugging
            console_messages = []

            def handle_console(msg):
                console_messages.append({
                    'type': msg.type,
                    'text': msg.text,
                    'location': msg.location,
                    'args': [str(arg) for arg in msg.args]
                })
                print(f"CONSOLE {msg.type}: {msg.text}")

            page.on("console", handle_console)

            # Enable request/response logging
            api_requests = []

            def handle_request(request):
                if '/api/logs' in request.url:
                    api_requests.append({
                        'url': request.url,
                        'method': request.method,
                        'headers': request.headers,
                        'post_data': request.post_data
                    })

            def handle_response(response):
                if '/api/logs' in response.url and api_requests:
                    try:
                        api_requests[-1]['response'] = response.json()
                        api_requests[-1]['status'] = response.status
                    except Exception as e:
                        api_requests[-1]['response'] = response.text()
                        api_requests[-1]['status'] = response.status
                        api_requests[-1]['error'] = str(e)

            page.on("request", handle_request)
            page.on("response", handle_response)

            # Go to logs page
            print(f"Navigating to {base_url}/logs")
            response = page.goto(f"{base_url}/logs")
            print(f"Page loaded with status: {response.status if response else 'No response'}")

            # Wait for the page to fully load
            print("Waiting for log container...")
            page.wait_for_selector("#logContainer", state="visible", timeout=10000)

            # Wait for loading to complete (spinner to disappear)
            print("Waiting for loading to complete...")
            page.wait_for_selector("#logContainer .spinner-border", state="hidden", timeout=10000)

            # Check for JavaScript errors first
            js_errors = [msg for msg in console_messages if msg['type'] == 'error']
            if js_errors:
                print("\n=== JAVASCRIPT ERRORS DETECTED ===")
                for error in js_errors:
                    print(f"Error: {error['text']}")

            # Wait for logs to load
            print("Waiting for logs to load...")
            page.wait_for_selector(".log-entry", state="visible", timeout=10000)
            log_entries_count = page.locator(".log-entry").count()
            print(f"Found {log_entries_count} log entries on page")

            # Verify we have log entries
            if log_entries_count == 0:
                print("ERROR: No log entries found on page!")
                page.screenshot(path="test-results/logs_page_no_entries.png")
                raise AssertionError("No log entries found on page")

            # First, verify the page has fully rendered by checking for log entries
            page.wait_for_selector(".log-entry", state="visible", timeout=5000)
            
            # Take a full page screenshot for debugging
            page.screenshot(path="test-results/logs_page_full.png")
            
            # Get all log entries and their HTML for debugging
            log_entries = page.locator(".log-entry").all()
            if not log_entries:
                page.screenshot(path="test-results/no_log_entries_found.png")
                raise AssertionError("No log entries found on the page")
            
            # Check if timestamps are visible in the DOM
            timestamp_elements = page.locator(".log-timestamp").all()
            if not timestamp_elements:
                page.screenshot(path="test-results/no_timestamp_elements.png")
                raise AssertionError("No timestamp elements found on the page")
            
            print(f"Found {len(timestamp_elements)} timestamp elements on the page")
            
            # Take a screenshot of the first few log entries for debugging
            for i in range(min(5, len(log_entries))):
                log_entries[i].screenshot(path=f"test-results/log_entry_{i}.png")
            
            # Get the HTML of the first few log entries for debugging
            for i in range(min(5, len(log_entries))):
                print(f"Log entry {i} HTML:", log_entries[i].inner_html())
            
            # Check if timestamps are actually visible in the UI
            timestamp_containers = page.locator(".log-timestamp").all()
            if not timestamp_containers:
                page.screenshot(path="test-results/no_timestamp_containers.png")
                raise AssertionError("No timestamp containers found with class 'log-timestamp'")
            
            print(f"Found {len(timestamp_containers)} timestamp containers")
            
            # Check the first few timestamps in detail
            for i, container in enumerate(timestamp_containers[:5]):
                # Check visibility
                is_visible = container.is_visible()
                print(f"Timestamp {i} is_visible(): {is_visible}")
                
                # Check if the element is in the viewport and has dimensions
                try:
                    bbox = container.bounding_box()
                    print(f"Timestamp {i} bounding box: {bbox}")
                    if not bbox or bbox['width'] == 0 or bbox['height'] == 0:
                        page.screenshot(path=f"test-results/timestamp_no_dimensions_{i}.png")
                        raise AssertionError(f"Timestamp {i} has no dimensions")
                except Exception as e:
                    page.screenshot(path=f"test-results/timestamp_bbox_error_{i}.png")
                    raise AssertionError(f"Error getting bounding box for timestamp {i}: {str(e)}")
                
                # Check text content
                try:
                    text = container.text_content()
                    print(f"Timestamp {i} text: {text}")
                    if not text or not text.strip():
                        page.screenshot(path=f"test-results/timestamp_empty_{i}.png")
                        raise AssertionError(f"Timestamp {i} is empty")
                    
                    # Verify timestamp format (e.g., "7/7/2025, 10:45:23 PM")
                    import re
                    timestamp_pattern = re.compile(
                        r'^\d{1,2}/\d{1,2}/\d{2,4},\s+\d{1,2}:\d{2}:\d{2}\s+(?:AM|PM)$',
                        re.IGNORECASE
                    )
                    
                    if not timestamp_pattern.match(text.strip()):
                        page.screenshot(path=f"test-results/invalid_timestamp_format_{i}.png")
                        raise AssertionError(
                            f"Timestamp '{text}' does not match expected format (MM/DD/YYYY, HH:MM:SS AM/PM)"
                        )
                    
                except Exception as e:
                    page.screenshot(path=f"test-results/timestamp_error_{i}.png")
                    raise AssertionError(f"Error checking timestamp {i}: {str(e)}")
            
            # If we got here, timestamps appear to be present and valid
            print("Timestamps appear to be present and valid in the first 5 log entries")

            # Verify at least one log entry is present
            first_entry = page.locator(".log-entry").first
            expect(first_entry).to_be_visible()
            print("Test completed successfully!")
    
        except PlaywrightTimeoutError as e:
            print(f"Timeout error: {e}")
            page.screenshot(path="test-results/logs_page_timeout_error.png")
            raise
        except Exception as e:
            print(f"Test failed: {e}")
            page.screenshot(path="test-results/logs_page_error.png")
            raise

    def test_logs_filtering(self, page: Page, base_url: str) -> None:
        """Test that log filtering works."""
        if not base_url:
            base_url = "http://localhost:5001"
        
        try:
            # Navigate to logs page
            page.goto(f"{base_url}/logs")
            
            # Wait for logs to load
            page.wait_for_selector("#logContainer", state="visible", timeout=10000)
            page.wait_for_selector("#logContainer .spinner-border", state="hidden", timeout=10000)
            
            # Test filtering by log level
            print("Testing ERROR level filter...")
            page.select_option("select#logLevel", "ERROR")
            page.wait_for_timeout(1000)  # Wait for API call
            
            # Verify only ERROR logs are shown
            error_logs = page.locator(".log-entry").count()
            print(f"Found {error_logs} error logs after filtering")
            
            if error_logs > 0:
                # Verify all visible logs are ERROR level
                for i in range(error_logs):
                    # Look for any badge with ERROR text since the class might vary
                    log_level = page.locator(".log-entry").nth(i).locator("text=ERROR").first
                    expect(log_level).to_be_visible()
            
            # Test filtering by log type
            print("Testing log type filter...")
            page.select_option("select#logType", "api")
            page.wait_for_timeout(1000)  # Wait for API call
            
            # Verify logs are filtered by type
            api_logs = page.locator(".log-entry").count()
            print(f"Found {api_logs} API logs after filtering")
            
        except Exception as e:
            print(f"Error during log filtering test: {e}")
            page.screenshot(path="test-results/logs_filtering_error.png")
            raise
    
    def test_logs_search_ui(self, page: Page, base_url: str) -> None:
        """Test that log search UI elements are present and interactive."""
        if not base_url:
            base_url = "http://localhost:5001"
        
        try:
            # Navigate to logs page
            page.goto(f"{base_url}/logs")
            
            # Wait for page to load
            page.wait_for_selector("#logContainer", state="visible", timeout=10000)
            
            # Verify search button is present
            search_btn = page.locator('button[title="Search Logs"]')
            expect(search_btn).to_be_visible()
            
            # Click search button to open modal
            search_btn.click()
            
            # Verify search modal elements
            expect(page.locator("#searchQuery")).to_be_visible()
            expect(page.locator("#performSearchBtn")).to_be_visible()
            

            
        except Exception as e:
            print(f"Error during search UI test: {e}")
            page.screenshot(path="test-results/logs_search_ui_error.png")
            raise
