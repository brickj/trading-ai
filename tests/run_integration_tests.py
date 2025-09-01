#!/usr/bin/env python3
"""
Integration Test Runner
Properly handles Flask app startup and integration testing
"""

import subprocess
import time
import sys
import os
import signal
import requests
import unittest

# Add project root to Python path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

class IntegrationTestRunner:
    """Manages Flask app lifecycle for integration testing"""

    def __init__(self):
        self.flask_process = None
        self.flask_url = "http://localhost:5001"

    def start_flask_app(self):
        """Start the Flask app in a subprocess"""
        print("🚀 Starting Flask app for integration tests...")

        # Check if Flask app is already running
        if self.is_flask_running():
            print("✅ Flask app is already running")
            return True

        try:
            # Start Flask app
            env = os.environ.copy()
            env['FLASK_ENV'] = 'testing'

            self.flask_process = subprocess.Popen([
                sys.executable, '-m', 'flask',
                '--app', 'src.web.app',
                'run', '--host=0.0.0.0', '--port=5001'
            ],
            cwd=project_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
            )

            # Wait for Flask to start
            for attempt in range(30):  # 30 second timeout
                if self.is_flask_running():
                    print("✅ Flask app started successfully")
                    return True
                time.sleep(1)
                print(f"⏳ Waiting for Flask app... ({attempt + 1}/30)")

            print("❌ Flask app failed to start within 30 seconds")
            return False

        except Exception as e:
            print(f"❌ Error starting Flask app: {e}")
            return False

    def is_flask_running(self):
        """Check if Flask app is responding"""
        try:
            response = requests.get(f"{self.flask_url}/api/system/status", timeout=2)
            return response.status_code in [200, 404, 500]  # Any response means it's running
        except requests.exceptions.RequestException:
            return False

    def stop_flask_app(self):
        """Stop the Flask app subprocess"""
        if self.flask_process:
            print("🛑 Stopping Flask app...")
            self.flask_process.terminate()
            try:
                self.flask_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.flask_process.kill()
                self.flask_process.wait()
            print("✅ Flask app stopped")

    def run_integration_tests(self):
        """Run the integration tests"""
        print("🧪 Running integration tests...")

        # Discover and run integration tests
        loader = unittest.TestLoader()
        integration_dir = os.path.join(os.path.dirname(__file__), 'integration')
        suite = loader.discover(integration_dir, pattern='test_*.py')

        runner = unittest.TextTestRunner(verbosity=2, buffer=True)
        result = runner.run(suite)

        return result.wasSuccessful()

def main():
    """Main test runner function"""
    runner = IntegrationTestRunner()

    try:
        # Check if Flask app needs to be started
        flask_was_running = runner.is_flask_running()

        if not flask_was_running:
            # Start Flask app
            if not runner.start_flask_app():
                print("❌ Failed to start Flask app - integration tests cannot run")
                return 1
        else:
            print("✅ Using existing Flask app instance")

        # Run integration tests
        success = runner.run_integration_tests()

        if success:
            print("✅ All integration tests passed!")
            return 0
        else:
            print("❌ Some integration tests failed")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️ Integration tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        return 1
    finally:
        # Only stop Flask if we started it
        if not flask_was_running and runner.flask_process:
            runner.stop_flask_app()

if __name__ == '__main__':
    sys.exit(main())