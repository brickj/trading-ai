#!/usr/bin/env python3
"""
Comprehensive Test Runner for Trading AI Application
Runs all unit tests and integration tests
"""
import unittest
import sys
import os
import time
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

def run_unit_tests():
    """Run all unit tests"""
    print("🧪 Running Unit Tests")
    print("=" * 50)
    
    # Discover and run unit tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'unit')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_integration_tests():
    """Run all integration tests"""
    print("\n🔗 Running Integration Tests")
    print("=" * 50)
    
    # Discover and run integration tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'integration')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_comprehensive_test():
    """Run the comprehensive system test"""
    print("\n🚀 Running Comprehensive System Test")
    print("=" * 50)
    
    # Import and run comprehensive test
    from comprehensive_system_test import ComprehensiveSystemTest
    
    test = ComprehensiveSystemTest()
    try:
        test.runTest()
        return True
    except Exception as e:
        print(f"❌ Comprehensive test failed: {e}")
        return False

def run_specific_test(test_name):
    """Run a specific test by name"""
    print(f"\n🎯 Running Specific Test: {test_name}")
    print("=" * 50)
    
    # Map test names to test modules
    test_modules = {
        'stocks': 'tests.unit.test_stocks_page',
        'crypto': 'tests.unit.test_crypto_page',
        'opportunities': 'tests.unit.test_opportunities_page',
        'system': 'tests.unit.test_system_status',
        'comprehensive': 'tests.comprehensive_system_test'
    }
    
    if test_name not in test_modules:
        print(f"❌ Unknown test: {test_name}")
        print(f"Available tests: {', '.join(test_modules.keys())}")
        return False
    
    try:
        # Import and run specific test
        module_name = test_modules[test_name]
        module = __import__(module_name, fromlist=[''])
        
        # Find test classes in the module
        test_classes = [cls for cls in module.__dict__.values() 
                       if isinstance(cls, type) and issubclass(cls, unittest.TestCase)]
        
        if not test_classes:
            print(f"❌ No test classes found in {module_name}")
            return False
        
        # Run the first test class found
        test_class = test_classes[0]
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except Exception as e:
        print(f"❌ Error running {test_name} test: {e}")
        return False

def main():
    """Main test runner"""
    print("🧪 Trading AI - Test Suite")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == 'unit':
            success = run_unit_tests()
        elif test_type == 'integration':
            success = run_integration_tests()
        elif test_type == 'comprehensive':
            success = run_comprehensive_test()
        elif test_type in ['stocks', 'crypto', 'opportunities', 'system']:
            success = run_specific_test(test_type)
        else:
            print(f"❌ Unknown test type: {test_type}")
            print("Available options: unit, integration, comprehensive, stocks, crypto, opportunities, system")
            return 1
    else:
        # Run all tests by default
        print("Running all tests...")
        
        unit_success = run_unit_tests()
        integration_success = run_integration_tests()
        comprehensive_success = run_comprehensive_test()
        
        success = unit_success and integration_success and comprehensive_success
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    if success:
        print("✅ All tests passed!")
        print("🎉 Application is ready for deployment")
        return 0
    else:
        print("❌ Some tests failed")
        print("🔧 Please fix the failing tests before deployment")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code) 