#!/usr/bin/env python3
"""
Trading AI Test Suite Runner
Runs both unit tests and integration tests with proper Flask app management
"""

import unittest
import sys
import os
import argparse
import time
from datetime import datetime

# Add project root to Python path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

def run_unit_tests():
    """Run unit tests"""
    print("🧪 Running Unit Tests...")
    print("=" * 60)

    # Discover and run unit tests
    loader = unittest.TestLoader()
    unit_dir = os.path.join(os.path.dirname(__file__), 'unit')
    suite = loader.discover(unit_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)

    return result

def run_integration_tests():
    """Run integration tests with Flask app management"""
    print("\n🌐 Running Integration Tests...")
    print("=" * 60)

    try:
        # Import the integration test runner
        from run_integration_tests import IntegrationTestRunner

        runner = IntegrationTestRunner()

        # Check if Flask app is already running
        flask_was_running = runner.is_flask_running()

        if not flask_was_running:
            print("🚀 Starting Flask app for integration tests...")
            if not runner.start_flask_app():
                print("❌ Failed to start Flask app - skipping integration tests")
                return None
        else:
            print("✅ Using existing Flask app instance")

        # Run integration tests
        success = runner.run_integration_tests()

        # Clean up if we started the Flask app
        if not flask_was_running and runner.flask_process:
            runner.stop_flask_app()

        return success

    except ImportError as e:
        print(f"⚠️ Could not import integration test runner: {e}")
        print("📝 Running integration tests manually...")

        # Fallback to manual integration test running
        loader = unittest.TestLoader()
        integration_dir = os.path.join(os.path.dirname(__file__), 'integration')
        suite = loader.discover(integration_dir, pattern='test_*.py')

        runner = unittest.TextTestRunner(verbosity=2, buffer=True)
        result = runner.run(suite)

        return result.wasSuccessful()

def print_test_summary(unit_result, integration_success):
    """Print comprehensive test summary"""
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    # Unit test summary
    if unit_result:
        unit_total = unit_result.testsRun
        unit_failures = len(unit_result.failures)
        unit_errors = len(unit_result.errors)
        unit_skipped = len(unit_result.skipped) if hasattr(unit_result, 'skipped') else 0
        unit_passed = unit_total - unit_failures - unit_errors - unit_skipped
        unit_success_rate = (unit_passed / unit_total * 100) if unit_total > 0 else 0

        print(f"📋 Unit Tests:")
        print(f"   Total: {unit_total}")
        print(f"   ✅ Passed: {unit_passed}")
        print(f"   ❌ Failed: {unit_failures}")
        print(f"   💥 Errors: {unit_errors}")
        print(f"   ⏭️ Skipped: {unit_skipped}")
        print(f"   📈 Success Rate: {unit_success_rate:.1f}%")
    else:
        print("📋 Unit Tests: Not run")

    # Integration test summary
    print(f"🌐 Integration Tests:")
    if integration_success is True:
        print("   ✅ All integration tests passed")
    elif integration_success is False:
        print("   ❌ Some integration tests failed")
    else:
        print("   ⏭️ Integration tests skipped (Flask app not available)")

    # Overall summary
    overall_success = True
    if unit_result and not unit_result.wasSuccessful():
        overall_success = False
    if integration_success is False:
        overall_success = False

    print(f"\n🎯 Overall Result: {'✅ SUCCESS' if overall_success else '❌ SOME TESTS FAILED'}")

    # Recommendations
    if not overall_success:
        print("\n💡 Recommendations:")
        if unit_result and (unit_result.failures or unit_result.errors):
            print("   • Fix failing unit tests first")
        if integration_success is False:
            print("   • Ensure Flask app is running for integration tests")
            print("   • Check API endpoints and database connectivity")
        if integration_success is None:
            print("   • Start Flask app: python3 -m flask --app src.web.app run --port=5001")

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description='Trading AI Test Suite')
    parser.add_argument('--unit-only', action='store_true',
                       help='Run only unit tests')
    parser.add_argument('--integration-only', action='store_true',
                       help='Run only integration tests')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    print("🚀 Trading AI Test Suite")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    unit_result = None
    integration_success = None

    try:
        if not args.integration_only:
            unit_result = run_unit_tests()

        if not args.unit_only:
            integration_success = run_integration_tests()

        print_test_summary(unit_result, integration_success)

        # Determine exit code
        exit_code = 0
        if unit_result and not unit_result.wasSuccessful():
            exit_code = 1
        if integration_success is False:
            exit_code = 1

        return exit_code

    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())